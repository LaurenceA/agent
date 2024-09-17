import os
import subprocess

from .formatting import print_system, print_code
from .files import file_tools_internal, open_files

tools_internal = {**file_tools_internal}

def report_run_command_in_shell(command):
    print_system(f"About to run command in shell: {command}")

def run_command_in_shell(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    exitcode = result.returncode

    output = f'command: {command}\nexitcode: {exitcode}\nstdout:\n{stdout}'
    if stderr:
        output = output + 'stderr:\n' + stderr

    return output

tools_internal["run_command_in_shell"] = {
    "function" : run_command_in_shell,
    "report_function": report_run_command_in_shell,
    "description" : "Runs a command in the shell. Reports stdout, stderr and the exit code.  The command must return immediately, and not be interactive (e.g. an interpreter).",
    "long_args": [],
    "input_schema" : {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The command which will be passed directly to the terminal/shell, with no further processing",
            },
        },
        "required": ["command"],
    },
}

def list_files(path):
    return run_command_in_shell(f"find {path} -type f -not -path '*/\\.*'")

def report_list_files(path):
    print_system(f"About to list files in {path}")

tools_internal["list_files"] = {
    "function" : list_files,
    "report_function": report_list_files,
    "description" : "Lists all files in the specified directory and in subdirectories. Excludes hidden files, or files in hidden directories. This tool is implemented by calling the linux `find` shell command.",
    "long_args": [],
    "input_schema" : {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path, from the current working directory",
            }
        },
        "required": ["path"],
    }
}


#def plus(a, b):
#    return str(int(a) + int(b))
#
#def report_plus(a, b):
#    print_system(f"About to add {a} and {b}")
#
#tools_internal["plus"] ={
#    "function" : plus,
#    "report_function": report_plus,
#    "description" : "Adds two quantities",
#    "long_args": [],
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#            "a": {
#                "type": "string",
#                "description": "The first quantity to add",
#            },
#            "b": {
#                "type": "string",
#                "description": "The second quantity to add",
#            },
#        },
#        "required": ["a", "b"],
#    }
#}




def write_file(file_path, code):
    try:
        with open(file_path, 'w') as file:
            file.write(code)
        open_files.add(file_path)
        
        return "File written successfully"
    except Exception as e:
        return f"An error occured: {e}"

def report_write_file(file_path, code):
    print_system(f"About to write file with filename: {file_path}")
    print_code(code)

tools_internal["write_file"] ={
    "function" : write_file,
    "report_function": report_write_file,
    "description" : "Writes a new file, or overwrites that file if it is already present. Writes the file with code provided in the code argument. This function MUST be called with both the file_path and code arguments. This function leaves the file open (so its content is available to the assistant).",
    "long_args": ["code"],
    "input_schema" : {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The relative path to the file, starting from the project root directory",
            },
            "code": {
                "type": "string",
                "description": "The content to write to the file.  This must be the full file.  You can't say e.g. rest of the file remains unchanged.  This argument could therefore be very long.",
            },
        },
        "required": ["file_path", "code"],
    }
}

def change_working_directory(path):
    try:
        os.chdir(path)
        return f"Changed directory to {os.getcwd()}"
    except Exception as e:
        return f"An error occurred: {e}"

def report_change_working_directory(path):
    return f"About to change directory to path"

tools_internal["change_working_directory"] ={
    "function" : change_working_directory,
    "report_function" : report_change_working_directory,
    "description" : "Changes the current working directory.  Equivalent to cd in the shell, or os.chdir in Python",
    "long_args": [],
    "input_schema" : {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The directory to move to",
            }
        },
        "required": ["path"],
    }
}


tools_openai = []
tools_anthropic = []

# Strip internal info like long_args and report_function, and format appropriately for the Anthropic + OpenAI APIs.

for toolname, tooldef in tools_internal.items():
    tools_anthropic.append({
        "name" : toolname,
        "description": tooldef["description"],
        "input_schema": tooldef["input_schema"],
    })
    tools_openai.append({
        "name" : toolname,
        "description" : tooldef["description"],
        "parameters" : tooldef["input_schema"],
        "additional_parameter" : False,
    })

