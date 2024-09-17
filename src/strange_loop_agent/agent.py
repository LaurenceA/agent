import os
import json
import anthropic
import subprocess
import readline #Just importing readline enables nicer features for the builtin Python input.

from .tools import tools_anthropic, tools_openai, tools_internal, run_command_in_shell
from .formatting import print_assistant, input_user, print_system, print_ua, print_internal_error
from .files import validate_open_files, string_for_all_open_files, num_open_files, project_dir

client = anthropic.Anthropic()

def call_terminal(command):
    stdout = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
    assert 0 < len(stdout)
    return stdout.strip()

#all_files_in_project_at_launch = call_terminal("find . -type f -not -path '*/\\.*'")
all_files_in_project_at_launch = call_terminal("git ls-tree -r HEAD --name-only")

system_message = f"""You are a part of an agentic system for programming.

Try to be brief when responding to user requests.  Tokens are expensive!

Don't ask for permission.  Just call the tools.  The agent wrapper handles asking the user for permission.

Try to minimize the number of files you have open.  Make sure that you only have open the files you need!

A brief description of the system you are running on:
OS name: {call_terminal('uname -s')}
OS version: {call_terminal('uname -r')}
Architecture: {call_terminal('uname -m')}
System name: {call_terminal('uname -n')}

The project root directory is:
{project_dir}
Don't navigate, or modify anything outside, this directory.

The files currently tracked by git are:
{all_files_in_project_at_launch}
"""

def confirm_proceed():
    while True:
        user_input = input("Proceed, (y/n): ").lower().strip()
        if user_input == 'y':
            return True
        elif user_input == 'n':
            return False
        else:
            print_system("Invalid input. Please enter 'y' or 'n'.")

def cache_final_two_user_messages(messages):
    """
    Mirrors the strategy in https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#continuing-a-multi-turn-conversation

    Does not modify the argument in-place.
    """

    messages = [*messages]
    if 1 <= len(messages):
        assert messages[-1]["role"] == "user"
        messages[-1]               = {**messages[-1]}
        messages[-1]["content"]    = [ *messages[-1]["content"]]
        messages[-1]["content"][0] = {**messages[-1]["content"][0], "cache_control" : {"type": "ephemeral"}}

    if 3 <= len(messages):
        messages[-3]               = {**messages[-3]}
        messages[-3]["content"]    = [ *messages[-3]["content"]]
        messages[-3]["content"][0] = {**messages[-3]["content"][0], "cache_control" : {"type": "ephemeral"}}

    return messages

def add_open_files_to_messages(messages):
    messages = [*messages]
    if 1 <= len(messages) and 1 <= num_open_files():
        assert messages[-1]["role"] == "user"

        messages[-1]            = {**messages[-1]}
        messages[-1]["content"] = [ *messages[-1]["content"]]

        messages[-1]["content"].append({
            "type" : "text",
            "text" : string_for_all_open_files(),
        })

    return messages


def get_and_process_response(persistent_messages):
    """
    Takes user input, and does the things ...
    """ 
    
    #The last message must be a user message.
    assert messages[-1]["role"] == "user"

    preprocessed_messages = add_open_files_to_messages(cache_final_two_user_messages(persistent_messages))

    print_ua("\nAssistant:")

    #print(preprocessed_messages)

    response = client.beta.prompt_caching.messages.create(
        #model="claude-3-haiku-20240307",
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        system=system_message,
        tools=tools_anthropic,
        messages = preprocessed_messages
    )
    #For logging
    #print(response.usage.input_tokens)
    #print(response.usage.output_tokens)
    #print(response.usage.cache_creation_input_tokens)
    #print(response.usage.cache_read_input_tokens)

    output_messages = [*persistent_messages]

    for block in response.content:
        if block.type == 'text':
            output_messages.append({
                "role" : "assistant",
                "content": [{
                    "type": "text",
                    "text": block.text,
                }],
            })
            print_assistant(block.text)

        elif block.type == 'tool_use':
            function_name = block.name
            args = block.input


            #Abbreviate very long arguments.
            abbreviated_args = {**args}
            for argname in tools_internal[function_name]['long_args']:
                if argname in abbreviated_args:
                    abbreviated_args[argname] = "..."

            #Append tool call itself to messages.
            tool_call = {
                "type": "tool_use",
                "id": block.id,
                "name": function_name,
                "input": abbreviated_args,
            }

            #The tool call has an assistant role, so would usually be appended to the content of the previous text block.
            if output_messages[-1]["role"] == "assistant":
                output_messages[-1]["content"].append(tool_call)
            else:
                output_messages.append({
                    "role": "assistant",
                    "content": [tool_call],
                })

            #Append the tool call result to messages, with a user role
            #If the user refuses to run the tool call, then have "User refused the use of the tool" as the result.

            required_args = tools_internal[function_name]["input_schema"]["required"]
            all_required_args_present = all(argname in args for argname in required_args)

            user_refused_permission = False
            if not all_required_args_present:
                result = f"{function_name} requires {required_args}, but given {[*args.keys()]}"
                print(output_messages)
            else:
                tools_internal[function_name]['report_function'](**args)
                user_refused_permission = not confirm_proceed()

                if user_refused_permission:
                    result = "User refused the use of the tool."
                else:
                    function = tools_internal[function_name]['function']
                    result = function(**args)

            tool_use_result_content = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content" : result,
            }
                
            output_messages.append({
                "role": "user",
                "content": [
                    tool_use_result_content,
                ]
            })

            print_system(result)
 
            #If the user refused to use the tool, pass back immediately to user to provide more context.
            #Otherwise, recursively call LLM
            if not user_refused_permission:
                output_messages = get_and_process_response(output_messages)
            
        else:
            print_internal_error(block)

    return output_messages
    
messages = []
while True:
    print_ua('\nUser:')
    user_input = input_user().strip()
    if user_input == "exit":
        break
    elif user_input == "clear_context":
        messages = []
    else:
        user_content = {
            "type": "text",
            "text": user_input,
        }
        
        #Dialogue must alternate between assistant and user.
        #If the previous message was a user message (because a tool call was refused), then append to that user message.
        #Otherwise, start a new user message.
        if len(messages) > 0 and messages[-1]["role"] == "user":
            messages[-1]["content"].append(user_content)
        else:
            messages.append({
                "role": "user",
                "content": [user_content],
            })
        messages = get_and_process_response(messages)
