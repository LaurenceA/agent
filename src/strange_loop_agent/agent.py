import json
import anthropic

from tools import tools_anthropic, tools_openai, tools_internal

client = anthropic.Anthropic()

system_message = """
You are a part of an agentic system for programming.

The user is asked for permission before any tool is used.  The user may refuse to use a tool if they don't want you to use it.
"""

def confirm_proceed():
    while True:
        user_input = input("Proceed, (y/n): ").lower().strip()
        if user_input == 'y':
            return True
        elif user_input == 'n':
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")

def user_input_to_message(user_input):
    """
    Converts raw user input into a well-formatted message for use in OpenAI or Anthropic APIs
    """
    return {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": user_input,
            },
        ]
    }

def get_and_process_response(messages):
    """
    Takes user input, and does the things ...
    """ 
    output_messages = [*messages]

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1000,
        system=system_message,
        tools=tools_anthropic,
        messages = output_messages,
    )

    print("Assistant:")

    for block in response.content:
        if block.type == 'text':
            output_messages.append({
                "role" : "assistant",
                "content": [{
                    "type": "text",
                    "text": block.text,
                }],
            })
            print(block.text)

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

            print(f'About to call:\n{function_name}({args})')
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

            print(result)
 
            #Get a new response, so the model can comment on the results.
            if confirmed:
                output_messages = get_and_process_response(output_messages)
            
        else:
            print(block)

    return output_messages
    
messages = []
while True:
    user_input = input('User:\n')
    messages.append(user_input_to_message(user_input))
    messages = get_and_process_response(messages)
    
    
