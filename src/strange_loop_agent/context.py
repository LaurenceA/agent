import os

from .formatting import print_system

context_tools_internal = {}

def report_add_file_to_context(state, file_path):
    print_system(f"About to add {file_path} to context")

def add_file_to_context(state, file_path):
    abs_path = os.path.join(state.project_dir, file_path)

    if os.path.exists(abs_path):
        state = state.add_file_to_context(file_path)
        result = f"{file_path} added to context"
    else:
        result = f"{file_path} does not exist"

    return state, result

def report_remove_file_from_context(state, file_path):
    print_system(f"About to remove {file_path} from context")

def discard_file_from_context(state, file_path):
    state = state.discard_file_from_context(file_path)
    return state, f'Discarded {file_path} from context'

def report_clear_context(state):
    print_system("About to clear context")

def clear_context(state):
    state = state.clear_context()
    return state, "Context cleared"

def report_report_context(state):
    print_system("About to report all files in the context")

def report_context(state):
    return state, 'Files in context:\n' + '\n'.join(state.context_files)

context_tools_internal["add_file_to_context"] ={
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


context_tools_internal["discard_file_from_context"] ={
    "function" : discard_file_from_context,
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

context_tools_internal["clear_context"] ={
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

context_tools_internal["report_context"] ={
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
