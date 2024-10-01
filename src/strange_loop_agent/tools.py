import os
import subprocess

from dataclasses import replace

from .check_command import check_command

from .exceptions import AgentException

tools_internal = {}

def report_run_command_in_shell(command):
    return f"About to run command in shell: {command}"

def check_run_command_in_shell(state, command):
    check = check_command(command)

    if check['trying_to_print_file']:
        raise AgentException(f"Command {command} wasn't run because it looks like its trying to print a file.  Use the explore tools instead.")
    if check['trying_to_print_directory']:
        raise AgentException(f"Command {command} wasn't run because it looks like its trying to print a directory.  Use the explore tools instead.")
    if check['trying_to_create_empty_file']:
        raise AgentException(f"Command {command} wasn't run because it looks like its trying to create an empty file.  Just directly write to the file using the <write> tag instead.")
    elif check['trying_to_write']:
        raise AgentException(f"Command {command} wasn't run because it looks like its trying to write a file.  Use the <write> tag instead.")
    elif check['trying_to_modify']:
        raise AgentException(f"Command {command} wasn't run because it looks like its trying to modify a file.  Use the <write> tag instead. If the write is very long, try to write to a specific function/class/method using e.g. <write path=/path/to/file#function_name>.")

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
    "check_function": check_run_command_in_shell,
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
    return state.add_summaries(paths)

def check_explore(state, paths):
    pass

tools_internal["explore"] = {
    "function" : explore,
    "report_function": report_explore,
    "check_function": check_explore,
    "description" : "Explores a given path. For a directory, it will print the contents of the directory.  For a file it will print a summary of the file, or the file itself if it is short.",
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
