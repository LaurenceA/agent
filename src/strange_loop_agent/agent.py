import json
import anthropic
import colorama

from .tools import tools_anthropic, tools_openai, tools_internal
from .formatting import print_assistant, input_user, print_system, print_ua, print_internal_error

client = anthropic.Anthropic()

system_message = """
You are a part of an agentic system for programming.

Try to be brief when responding to user requests.  Tokens are expensive!

Don't ask for permission.  Just call the tools.  The agent wrapper handles asking the user for permission.
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


def get_and_process_response(messages):
    """
    Takes user input, and does the things ...
    """ 
    output_messages = [*messages]

    print_ua("\nAssistant:")

    response = client.messages.create(
        model="claude-3-haiku-20240307",
        #model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        system=system_message,
        tools=tools_anthropic,
        messages = output_messages,
    )

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

            #Append tool call itself to messages.
            tool_call = {
                "type": "tool_use",
                "id": block.id,
                "name": function_name,
                "input": args,
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

            tools_internal[function_name]['report_function'](**args)
            confirmed = confirm_proceed()

            if confirmed:
                function = tools_internal[function_name]['function']
                result = function(**args)
            else:
                result = "User refused the use of the tool."

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
 
            #The tool use agent is "user".  If the user refused to use the tool, let the user provide some more context:
            #Otherwise, get a new response from the LLM
            if confirmed:
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
