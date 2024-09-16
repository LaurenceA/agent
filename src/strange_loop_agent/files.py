import os

from .formatting import print_system

open_files = []
file_tools_internal = {}
project_dir = os.getcwd() #Must be imported as part of the first call to main if this is to work.

def num_open_files():
    return len(open_files)

def report_open_file(file_path):
    print_system(f"About to open {file_path}")

def open_file(file_path):
    abs_path = os.path.join(project_dir, file_path)

    if os.path.exists(abs_path):
        if file_path not in open_files:
            open_files.append(file_path)
            return "{file_path} added to open files"
        else:
            return "{file_path} already in open files"
    else:
        return "{file_path} does not exist"

def report_close_file(file_path):
    print_system(f"About to close {file_path}")

def close_file(file_path):
    if file_path in open_files:
        open_files.remove(file_path)
        return "{file_path} closed"
    else:
        return "{file_path} was not open"

def report_close_all_files():
    print_system("About to close all files")

def close_all_files():
    open_files = []
    return "All files closed"

file_tools_internal["open_file"] ={
    "function" : open_file,
    "report_function" : report_open_file,
    "description" : "Opens a file, putting the full file contents in every prompt",
    "input_schema" : {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file, from the project root directory, not the current working directory.",
            }
        },
        "required": ["file_path"],
    }
}

file_tools_internal["close_file"] ={
    "function" : close_file,
    "report_function" : report_close_file,
    "description" : "Closes a file, which stops the full contents being placed in every prompt",
    "input_schema" : {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The path to the file, from the project root directory, not the current working directory.",
            }
        },
        "required": ["file_path"],
    }
}

file_tools_internal["close_all_files"] ={
    "function" : report_close_all_files,
    "report_function" : report_close_file,
    "description" : "Closes all open files. So there are now no files having their contents placed at the start of every prompt",
    "input_schema" : {
        "type": "object",
        "properties": {
        },
        "required": [],
    }
}

def validate_open_files():
    result = []
    for file_path in open_files:
        abs_path = os.path.join(project_dir, file_path)
        if not os.path.exists(abs_path):
            close_file(file_path)
            result.append(f"Open file {file_path} does not exist, closing")
    if 0 == len(result):
        return None
    else:
        return '\n'.join(result)
            
def string_for_all_open_files():
    files_content = ["Open files: {open_files}"]
    for file_path in open_files:
        abs_path = os.path.join(project_dir, file_path)
        with open(abs_path, 'r') as file:
            file_content = file.read()
        #try:
        #    file_content = os.read(abs_path)
        #except Exception as e:
        #    file_content = str(e)
        file_content = f"File path: {file_path}\nFile contents:\n{file_content}"
        files_content.append(file_content)
    return '\n\n\n\n'.join(files_content)