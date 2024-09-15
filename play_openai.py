import os
import json
import openai

from openai import OpenAI
client = OpenAI()

tools = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Given a file name (file_name) and file contents (contents), write the contents to the file).  Overwrite the file if it is already there.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The file name.",
                    },
                    "content": {
                        "type": "string",
                        "description": "The file content.",
                    },
                },
                "required": ["filename, content"],
                "additionalProperties": False,
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all the files in the project directory",
            "parameters": {
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        }
    }
]

def write_file(file_name, content):
    with open(file_name, 'w') as file:
        file.write(content)

messages = [
    {"role": "system", "content": "You are a helpful assistant.  You have a write_function tool.  Please use it to write any code files requested by the user."},
    {"role": "user", "content": "Hi, can you write a hello world file in C?"}
]

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)

tool_call = response.choices[0].message.tool_calls[0]
function_name = tool_call.function.arguments
arguments = json.loads(tool_call.function.arguments)



