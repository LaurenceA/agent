from .formatting import print_system

write_tools_internal = {}

#def open_file_for_writing(state, file_path):
#    try:
#        with open(file_path, 'w') as file:
#            file.write(code)
#        context_files.add(file_path)
#        
#        return "File written successfully"
#    except Exception as e:
#        return f"An error occured: {e}"

def report_open_file_for_writing(state, file_path):
    print_system(f"About to open {file_path} opened for writing")

def open_file_for_writing(state, file_path):
    state = state.open_file_for_writing(file_path)
    return state, f"{file_path} opened for writing"
     

write_tools_internal["open_file_for_writing"] ={
    "function" : open_file_for_writing,
    "report_function" : report_open_file_for_writing,
    "description" : "Opens a file, in preparation for writing to it.  When a file is open, your output is being pushed directly to the file, so you should ONLY return the code itself!",
    "long_args": [],
    "input_schema" : {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The relative path to the file, starting from the project root directory",
            },
        },
        "required": ["file_path"],
    }
}
#
#write_tools_internal["open_file_for_writing"] ={
#    "function" : close_file,
#    "description" : "Closes the file that is currently being written.",
#    "long_args": [],
#    "input_schema" : {
#        "type": "object",
#        "properties": {
#        },
#        "required": [],
#    }
#}
