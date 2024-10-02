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






#def report_git_ls_files(path):
#    return f"About to a git repo at: {path}"
#
#def git_ls_files(state, path):
#    return not_implemented
#
#def check_git_ls_files(state, paths):
#    pass
#
#tools_internal["git_ls_files"] = {
#    "function" : git_ls_files,
#    "report_function": report_git_ls_files,
#    "check_function": check_git_ls_files,
#    "description" : "Prints all the files in the git repo at path.",
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#            "command": {
#                "type": "string",
#                "description": "The path to the git repo.",
#            },
#        },
#        "required": ["path"],
#    },
#}
#
#
#def report_ls(path):
#    return f"About to print a directory at: {path}"
#
#def ls(state, path):
#    return not_implemented
#
#def check_ls(state, paths):
#    pass
#
#tools_internal["ls"] = {
#    "function" : ls,
#    "report_function": report_ls,
#    "check_function": check_ls,
#    "description" : "Same as running ls: prints all the files in the directory specified by the path.",
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#            "command": {
#                "type": "string",
#                "description": "The path to the directory.",
#            },
#        },
#        "required": ["path"],
#    },
#}
#
#
#
#
#def report_ls_recursive(path):
#    return f"About to print a directory at: {path}"
#
#def ls_recursive(state, path):
#    return not_implemented
#
#def check_ls_recursive(state, paths):
#    pass
#
#tools_internal["ls_recursive"] = {
#    "function" : ls_recursive,
#    "report_function": report_ls_recursive,
#    "check_function": check_ls_recursive,
#    "description" : "Same as running ls -R path: prints all the files in the directory specified by the path, recursing through all the directories.  Note, does not explicitly recurse into some directories, such as those that are hidden.",
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#            "command": {
#                "type": "string",
#                "description": "The path to the directory.",
#            },
#        },
#        "required": ["path"],
#    },
#}
