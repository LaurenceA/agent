import os
import json
import subprocess
import readline #Just importing readline enables nicer features for the builtin Python input.
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path

from .state import State
from .diff import diff
from .tools import tools_internal
from .state import initialize_state
#from .summarize import summarize
from .parse_file_writes import parse_writes

from .messages import TextBlock, ToolUseBlock, ToolResultBlock


@dataclass
class FileUndoInfo:
    path: Path
    before: Optional[str]
    after: str

@dataclass
class StateUndoInfo:
    state: State
    files_undo_info: List[FileUndoInfo]

def update_state_assistant(state, undo_state):
    """
    Takes user input, and does the things ...
    """ 

    state_undo_info = [] # dict mapping Path to string (full contents of the file).
    
    #The last message must be a user message.
    state.messages.assert_ready_for_assistant()

    #Check for any external updates since the model was last run.
    state, messages = state.update_summaries()
    if messages:
        messages = 'External updates to summarised files and folders: \n\n' + messages
        state = state.print_system(messages)
        state = state.append_text("user", messages)

    state = state.print_Assistant()

    response = state.assistant_api_call()

    for block in response.content:
        if block.type == 'text':
            #if state.file_for_writing is None:
            # Standard text response.
            state = state.append_text("assistant", block.text)
            state = state.print_assistant(block.text)

            parsed_writes = parse_writes(block.text)

            errors = []
            files_undo_info = []
            for path, proposed_text in parsed_writes:
                state, user_gave_permission = state.confirm_proceed(f"Confirm write of {path}")
                user_refused_permission = not user_gave_permission

                if user_refused_permission:
                    errors.append(f"User refused permission to write {path}")
                else:
                    try:
                        #Record file contents before modification.  Any read errors are captured.
                        if path.path.exists():
                            with path.path.open() as file:
                                before = file.read()
                        else:
                            before = None

                        path.write(proposed_text)

                        #Record file contents after modification; really shouldn't error.
                        with path.path.open() as file:
                            after = file.read()
                        files_undo_info.append(FileUndoInfo(path=path.path, before=before, after=after))
                        state = state.append_text("user", f'{path} successfully written')
                    except Exception as e:
                        errors.append(f"An error occured writing {path}: {e}")



            state_undo_info.append(StateUndoInfo(state=undo_state, files_undo_info=files_undo_info))
            
            if errors:
                errors = '\n'.join(errors)
                state = state.append_text("assistant", errors)
                state = state.print_system(errors)

            #Update the summaries, but don't print any messages (as all that info
            #is contained in the assistant response anyway).
            state, messages = state.update_summaries()

        elif block.type == 'tool_use':
            # Tool call.
            function_name = block.name
            args = block.input

            #Append tool call itself to messages.
            tool_use_block = ToolUseBlock(block.id, function_name, args)

            #The tool call has an assistant role.
            state = state.append_block("assistant", tool_use_block)

            #Append the tool call result to messages, with a user role
            #If the user refuses to run the tool call, then have "User refused the use of the tool" as the result.

            if function_name not in tools_internal:
                result = f"Tool {function_name} not avaliable"
            else:
                required_args = tools_internal[function_name]["input_schema"]["required"]
                all_required_args_present = all(argname in args for argname in required_args)

                user_refused_permission = False
                if not all_required_args_present:
                    result = f"Tool {function_name} requires arguments {required_args}, but given {[*args.keys()]}"
                else:
                    #Call the report function.  It should print directly, and not return anything.
                    state = state.print_system(tools_internal[function_name]['report_function'](**args))
                    state, user_gave_permission = state.confirm_proceed()
                    user_refused_permission = not user_gave_permission

                    if user_refused_permission:
                        result = "User refused the use of the tool."
                    else:
                        function = tools_internal[function_name]['function']

                        #Running the function shouldn't change messages.
                        prev_messages = state.messages
                        state, result = function(state, **args)
                        assert state.messages is prev_messages

            tool_result_block = ToolResultBlock(block.id, result)
                
            #Tool result has role user.
            state = state.append_block("user", tool_result_block)

            state = state.print_system(result)
 
            #If the user refused to use the tool, pass back immediately to user to provide more context.
            #Otherwise, recursively call LLM
            if not user_refused_permission:
                state, later_state_undo_info = update_state_assistant(state, state)
                state_undo_info = state_undo_info + later_state_undo_info
            
        else:
            state = state.print_internal_error(block)

    return state, state_undo_info

def update_state_user(state, user_input):
    """
    Handles a user message.
    """

    #Dialogue must alternate between assistant and user.
    #If the previous message was a user message (because a tool call was refused), then append to that user message.
    #Otherwise, start a new user message.
    return state.append_text("user", user_input)

state = initialize_state()
state = state.print_initial_message()
undo_info = []
redo_info = []

while True:
    state_before_user_input = state
    state = state.print_User()
    state, user_input = state.input_user()
    if user_input == "exit":
        break
    elif user_input == "undo":
        if 0 < len(undo_info):
            ud = undo_info[-1]
            undo_info = undo_info[:-1]
            state = ud.state
            print('\n\n\n\n\n\n\n')
            print('\n'.join(state.console_log))
            for file_undo_info in ud.files_undo_info:
                path = file_undo_info.path
                before = file_undo_info.before

                if before is not None:
                    with path.open('w') as file:
                        file.write(before)
                else:
                    path.unlink()
    else:
        #Save the state just before you use the assistant.
        state = update_state_user(state, user_input)
        state, new_undo_info = update_state_assistant(state, undo_state=state_before_user_input)
        undo_info = undo_info + new_undo_info
