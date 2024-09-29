import os
import subprocess

from .summary import update_summaries_from_token_sources
from .FullPath import full_path

tools_internal = {}

def report_run_command_in_shell(command):
    return f"About to run command in shell: {command}"

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

def report_explore(paths):
    return f"About to explore: {paths}"

def explore(state, paths):
    sources = [(full_path(path), 1000) for path in paths]
    updated_summaries, messages = update_summaries_from_token_sources(state.summaries, sources)

    return updated_summaries, '\n\n\n'.join(messages)

tools_internal["explore"] = {
    "function" : explore,
    "report_function": report_explore,
    "description" : "Explores a given path.  For a directory, it will print the contents of the directory.  For a file it will print a summary of the file, or the file itself if it is short.",
    "input_schema" : {
        "type": "object",
        "properties": {
            "paths": {
                "type": "array",
                "items": {
                    "type" : "string",
                },
                "description": 'The paths to explore. These could be paths to a file /path/to/file, function /path/to/file#function_name, class /path/to/file#class_name or method /path/to/file#class_name#method_name.'
            },
        },
        "required": ["paths"],
    },
}
