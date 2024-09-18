import os
import json
import subprocess
import readline #Just importing readline enables nicer features for the builtin Python input.

from .formatting import print_assistant, input_user, print_system, print_ua, print_internal_error, print_code
from .diff import diff
from .tools import tools_internal
from .parse_file_writes import file_open_delimiter, file_close_delimiter, parse_file_writes
from .state import initialize_state
from .summarize import summarize

def call_terminal(command):
    stdout = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
    assert 0 < len(stdout)
    return stdout.strip()

system_message = f"""You are a part of an agentic system for programming.

Try to be brief when responding to user requests.  Tokens are expensive!

Don't ask for permission.  Just call the tools.  The agent wrapper handles asking the user for permission.

Try to minimize the number of files you have in the context.  Discard any files from the context you don't need.

When you want to write to a file, use the following format:
{file_open_delimiter}path/to/file
<file contents>{file_close_delimiter}
These files are automatically written successfully.

A brief description of the system you are running on:
OS name: {call_terminal('uname -s')}
OS version: {call_terminal('uname -r')}
Architecture: {call_terminal('uname -m')}
System name: {call_terminal('uname -n')}

The project root directory is:
{os.getcwd()}
Don't navigate, or modify anything outside, this directory.

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
            return confirm_proceed()


def update_state_assistant(state):
    """
    Takes user input, and does the things ...
    """ 
    print(state)
    
    #The last message must be a user message.
    assert state.messages[-1]["role"] == "user"

    print_ua("\nAssistant:")

    response = state.assistant_api_call(system_message)

    for block in response.content:
        if block.type == 'text':
            #if state.file_for_writing is None:
            # Standard text response.
            state = state.append_text("assistant", block.text)
            print_assistant(block.text)

            #for path, proposed_text in parse_file_writes(block.text):
            #    abs_path = os.path.join(state.project_dir, path)
            #    if os.path.exists(abs_path):
            #        with open(abs_path, 'r') as current_file:
            #            original_text = current_file.read()
            #        print(diff(original_text, proposed_text, "original", "proposed"))
            #    else:
            #        print_code(proposed_text)

            parsed_file_writes = parse_file_writes(block.text)
            if 0 < len(parsed_file_writes):
                errors = []
                user_refused_permission = not confirm_proceed()
                if user_refused_permission:
                    errors.append("User refused permission")
                else:
                    for path, proposed_text in parse_file_writes(block.text):
                        try:
                            with open(state.abs_path(path), 'w') as file:
                                file.write(proposed_text)
                            state = state.track_file(path)
                        except Exception as e:
                            errors.append(f"An error occured writing {path}: {e}")
                if 0 < len(errors):
                    errors = '\n'.join(errors)
                    state = state.append_text("user", errors)

                
            #else:
            #    # Text in file write mode.
            #    print_system(f"About to write the following to {state.file_for_writing}")
            #    proposed_text = block.text

            #    abs_path = os.path.join(state.project_dir, state.file_for_writing)
            #    if os.path.exists(abs_path):
            #        with open(abs_path, 'r') as current_file:
            #            original_text = current_file.read()
            #        print(diff(original_text, proposed_text, "original", "proposed"))
            #    else:
            #        print_code(proposed_text)

            #    user_refused_permission = not confirm_proceed()
            #    if user_refused_permission:
            #        result = "User refused permission to write the file"
            #    else:
            #        try:
            #            abs_path = os.path.join(state.project_dir, state.file_for_writing)
            #            with open(abs_path, 'w') as file:
            #                file.write(block.text)
            #            state = state.add_file_to_context(state.file_for_writing)
            #            
            #            result = "File written successfully.  File contents omitted from the context."
            #        except Exception as e:
            #            result= f"An error occured: {e}"
            #        
            #    print_system(result)
            #    state = state.append_text('user', result)
            #    state = state.close_file_for_writing()
            #    state = update_state_assistant(state)

        elif block.type == 'tool_use':
            # Tool call.
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

            #The tool call has an assistant role.
            state = state.append_content("assistant", tool_call)

            #Append the tool call result to messages, with a user role
            #If the user refuses to run the tool call, then have "User refused the use of the tool" as the result.

            required_args = tools_internal[function_name]["input_schema"]["required"]
            all_required_args_present = all(argname in args for argname in required_args)

            user_refused_permission = False
            if not all_required_args_present:
                result = f"Tool {function_name} requires arguments {required_args}, but given {[*args.keys()]}"
                print(output_messages)
            else:
                #Call the report function.  It should print directly, and not return anything.
                assert tools_internal[function_name]['report_function'](state, **args) is None
                user_refused_permission = not confirm_proceed()

                if user_refused_permission:
                    result = "User refused the use of the tool."
                else:
                    function = tools_internal[function_name]['function']

                    #Running the function shouldn't change messages.
                    prev_messages = state.messages
                    state, result = function(state, **args)
                    assert state.messages is prev_messages

            tool_use_result_content = {
                "type": "tool_result",
                "tool_use_id": block.id,
                "content" : result,
            }
                
            #Tool result has role user.
            state = state.append_content("user", tool_use_result_content)

            print_system(result)
 
            #If the user refused to use the tool, pass back immediately to user to provide more context.
            #Otherwise, recursively call LLM
            if not user_refused_permission:
                state = update_state_assistant(state)
            
        else:
            print_internal_error(block)

    return state

def update_state_user(state, user_input):
    """
    Handles a user message.
    """

    #Dialogue must alternate between assistant and user.
    #If the previous message was a user message (because a tool call was refused), then append to that user message.
    #Otherwise, start a new user message.
    return state.append_text("user", user_input)

state = initialize_state()

while True:
    print_ua('\nUser:')
    user_input = input_user().strip()
    if user_input == "exit":
        break
    else:
        state = update_state_user(state, user_input)
        state = update_state_assistant(state)
