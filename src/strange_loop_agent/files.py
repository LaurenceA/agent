import os

from .formatting import print_system

context_files = set() #Mutable set.
file_tools_internal = {}
project_dir = os.getcwd() #Must be imported as part of the first call to main if this is to work.

def num_context_files():
    return len(context_files)

def report_add_file_to_context(file_path):
    print_system(f"About to add {file_path} to context")

def add_file_to_context(file_path):
    abs_path = os.path.join(project_dir, file_path)

    if os.path.exists(abs_path):
        context_files.add(file_path)
        return f"{file_path} added to context"
    else:
        return f"{file_path} does not exist"

def report_remove_file_from_context(file_path):
    print_system(f"About to remove {file_path} from context")

def remove_file_from_context(file_path):
    context_files.discard(file_path) # Removes without raising error is not present.
    return f"Removed {file_path} from context"

def report_clear_context():
    print_system("About to clear context")

def clear_context():
    open_files = set()
    return "Context cleared"

def report_report_context():
    print_system("About to report all files in the context")

def report_context():
    return 'Files in context:\n' + '\n'.join(open_files)

file_tools_internal["add_file_to_context"] ={
    "function" : add_file_to_context,
    "report_function" : report_add_file_to_context,
    "description" : "Adds a file to the context, putting the full file contents in every prompt",
    "long_args": [],
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


file_tools_internal["remove_file_from_context"] ={
    "function" : remove_file_from_context,
    "report_function" : report_remove_file_from_context,
    "description" : "Removes a file from the context, stopping the full contents being placed in every prompt",
    "long_args": [],
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

file_tools_internal["clear_context"] ={
    "function" : clear_context,
    "report_function" : clear_context,
    "description" : "Clears the context. So there are now no files having their contents placed at the start of every prompt",
    "long_args": [],
    "input_schema" : {
        "type": "object",
        "properties": {
        },
        "required": [],
    }
}

file_tools_internal["report_context"] ={
    "function" : report_report_context,
    "report_function" : report_context,
    "description" : "Reports all the currently open files.",
    "long_args": [],
    "input_schema" : {
        "type": "object",
        "properties": {
        },
        "required": [],
    }
}

def validate_context_files():
    result = []
    for file_path in context_files:
        abs_path = os.path.join(project_dir, file_path)
        if not os.path.exists(abs_path):
            remove_file_from_context(file_path)
            result.append(f"File in the context {file_path} does not exist; removing it from the context.")
    if 0 == len(result):
        return None
    else:
        return '\n'.join(result)
            
def full_context_as_a_string():
    result = ["Context files: {context_files}"]
    for file_path in context_files:
        abs_path = os.path.join(project_dir, file_path)
        with open(abs_path, 'r') as file:
            file_content = file.read()
        #try:
        #    file_content = os.read(abs_path)
        #except Exception as e:
        #    file_content = str(e)
        result.append(f"File path: {file_path}\nFile contents:\n{file_content}")
    return '\n\n\n\n'.join(result)
