import os
import subprocess

from .formatting import print_system, print_code
from .context import context_tools_internal

tools_internal = {}

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

#def report_track_file(state, path):
#    print_system(f"About to add tracked file: {path}")
#
#def track_file(state, path):
#    return state, f"Successfully tracked {path}"
#
#tools_internal["track_file"] = {
#    "function" : track_file,
#    "report_function": report_track_file,
#    "description" : "Tracks a file, so that a summary is presented in the context. All the files in the repo + any new files that are written by the agent are automatically tracked, so do not need to be added using this tool.",
#    "long_args": [],
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#            "path": {
#                "type": "string",
#                "description": "The path to the file to be tracked",
#            },
#        },
#        "required": ["path"],
#    },
#}
