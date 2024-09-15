import os
import subprocess

tools_internal = {}

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
    "description" : "Runs a command in the shell. Reports stdout, stderr and the exit code.  The command must return immediately, and not be interactive (e.g. an interpreter).",
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

tools_internal["list_files"] = {
    "function" : list_files,
    "description" : "Lists all files in the current directory and in subdirectories. Excludes hidden files, or files in hidden directories. This tool is implemented by calling the linux `find` shell command.",
    "input_schema" : {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "This tool lists all tools in a directory.  The path argument specifies that directory.",
            }
        },
        "required": ["path"],
    }
}

def write_file(file_name, content):
    with open(file_name, 'w') as file:
        file.write(content)

tools_internal["write_file"] ={
    "function" : write_file,
    "description" : "Writes a new file, or overwrites that file if it is already present.  file_name specifies the file name, and content specifies the content to be written to the file",
    "input_schema" : {
        "type": "object",
        "properties": {
            "file_name": {
                "type": "string",
                "description": "This tool lists all tools in a directory.  The path argument specifies that directory.",
            }
        },
        "required": ["path"],
    }
}

def change_working_directory(path):
    try:
        os.chdir(path)
        return(os.getcwd())
    except Exception as e:
        return f"An error occurred: {e}"

tools_internal["change_working_directory"] ={
    "function" : change_working_directory,
    "description" : "Changes the current working directory.  Equivalent to cd in the shell, or os.chdir in Python",
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

