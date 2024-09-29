import os
import json
import subprocess
import readline #Just importing readline enables nicer features for the builtin Python input.

from .diff import diff
from .tools import tools_internal
from .state import initialize_state
#from .summarize import summarize
from .parse_file_writes import parse_writes

from .messages import TextBlock, ToolUseBlock, ToolResultBlock


def update_state_assistant(state):
    """
    Takes user input, and does the things ...
    """ 
    
    #The last message must be a user message.
    state.messages.assert_ready_for_assistant()

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
            for path, proposed_text in parsed_writes:
                state, user_gave_permission = state.confirm_proceed(f"Confirm write of {path}")
                user_refused_permission = not user_gave_permission

                if user_refused_permission:
                    errors.append(f"User refused permission to write {path}")
                else:
                    state = state.track_file(path.path)
                    path.write(proposed_text)
                    state = state.track_file(path.path)
                    try:
                        path.write(proposed_text)
                    except Exception as e:
                        errors.append(f"An error occured writing {path}: {e}")

            if errors:
                errors = '\n'.join(errors)
                state = state.append_text("assistant", errors)
                state = state.print_system(errors)

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

            required_args = tools_internal[function_name]["input_schema"]["required"]
            all_required_args_present = all(argname in args for argname in required_args)

            user_refused_permission = False
            if not all_required_args_present:
                result = f"Tool {function_name} requires arguments {required_args}, but given {[*args.keys()]}"
                print(output_messages)
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
                    result = function(**args)
                    assert state.messages is prev_messages

            tool_result_block = ToolResultBlock(block.id, result)
                
            #Tool result has role user.
            state = state.append_block("user", tool_result_block)

            state = state.print_system(result)
 
            #If the user refused to use the tool, pass back immediately to user to provide more context.
            #Otherwise, recursively call LLM
            if not user_refused_permission:
                state = update_state_assistant(state)
            
        else:
            state = state.print_internal_error(block)

    return state

def update_state_user(state, user_input):
    """
    Handles a user message.
    """

    #Dialogue must alternate between assistant and user.
    #If the previous message was a user message (because a tool call was refused), then append to that user message.
    #Otherwise, start a new user message.
    return state.append_text("user", user_input)

state = initialize_state()
states = []

while True:
    state = state.print_User()
    state, user_input = state.input_user()
    if user_input == "exit":
        break
    if user_input == "undo":
        break
    else:
        #Save the state just before you use the assistant.
        states.append(state)
        state = update_state_user(state, user_input)
        state = update_state_assistant(state)
