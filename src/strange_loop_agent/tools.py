import os
import subprocess

from .formatting import print_system, print_code
from .context import context_tools_internal
from .write import write_tools_internal

tools_internal = {}#{**context_tools_internal}#, **write_tools_internal}

def report_run_command_in_shell(state, command):
    print_system(f"About to run command in shell: {command}")

def run_command_in_shell(state, command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    exitcode = result.returncode

    output = f'command: {command}\nexitcode: {exitcode}\nstdout:\n{stdout}'
    if stderr:
        output = output + 'stderr:\n' + stderr

    return state, output

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

#def list_files(state, path):
#    return run_command_in_shell(state, f"find {path} -type f -not -path '*/\\.*'")
#
#def report_list_files(state, path):
#    print_system(f"About to list files in {path}")
#
#tools_internal["list_files"] = {
#    "function" : list_files,
#    "report_function": report_list_files,
#    "description" : "Lists all files in the specified directory and in subdirectories. Excludes hidden files, or files in hidden directories. This tool is implemented by calling the linux `find` shell command.",
#    "long_args": [],
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#            "path": {
#                "type": "string",
#                "description": "The path, from the current working directory",
#            }
#        },
#        "required": ["path"],
#    }
#}





#def change_working_directory(state, path):
#    try:
#        os.chdir(path)
#        return f"Changed directory to {os.getcwd()}"
#    except Exception as e:
#        return f"An error occurred: {e}"
#
#def report_change_working_directory(state, path):
#    return f"About to change directory to path"
#
#tools_internal["change_working_directory"] ={
#    "function" : change_working_directory,
#    "report_function" : report_change_working_directory,
#    "description" : "Changes the current working directory.  Equivalent to cd in the shell, or os.chdir in Python",
#    "long_args": [],
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#            "path": {
#                "type": "string",
#                "description": "The directory to move to",
#            }
#        },
#        "required": ["path"],
#    }
#}
