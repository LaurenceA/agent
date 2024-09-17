import os

def append_text_to_messages(messages, role, text, error_if_not_role_alternate=False):
    content = {'type': 'text', 'text': text}
    return append_content_to_messages(messages, role, content, error_if_not_role_alternate=error_if_not_role_alternate)

def append_content_to_messages(messages, role, content, error_if_not_role_alternate=False):
    """
    Assumes content is a dict, e.g. {'type': 'text', 'text': '...'}
    """
    assert role in ["user", "assistant"]

    messages=[*messages]
    if 1<=len(messages) and messages[-1]["role"] == role:
        #Same role as previous message
        assert not error_if_not_role_alternate
        messages[-1] = {**messages[-1]}
        messages[-1]["content"] = [*messages[-1]["content"], content]
    else:
        #Role has alternated, so we need a new message.
        messages.append({"role": role, "content": [content]})
    return messages

def cache_final_two_user_messages(messages):
    """
    Mirrors the strategy in https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#continuing-a-multi-turn-conversation

    Does not modify the argument in-place.
    """

    messages = [*messages]
    if 1 <= len(messages):
        assert messages[-1]["role"] == "user"
        messages[-1]               = {**messages[-1]}
        messages[-1]["content"]    = [ *messages[-1]["content"]]
        messages[-1]["content"][0] = {**messages[-1]["content"][0], "cache_control" : {"type": "ephemeral"}}

    if 3 <= len(messages):
        messages[-3]               = {**messages[-3]}
        messages[-3]["content"]    = [ *messages[-3]["content"]]
        messages[-3]["content"][0] = {**messages[-3]["content"][0], "cache_control" : {"type": "ephemeral"}}

    return messages


def add_context_to_messages(state, messages):
    return append_text_to_messages(messages, 'user', state_as_a_string(state))

def preprocess_messages(state):
    return add_context_to_messages(state, cache_final_two_user_messages(state.messages))

def num_context_files(state):
    return len(state.context_files)
            
def state_as_a_string(state):
    result = ["Context files: {state.context_files}"]
    for file_path in state.context_files:
        abs_path = os.path.join(state.project_dir, file_path)
        try:
            with open(abs_path, 'r') as file:
                file_content = file.read()
            result.append(f"File path: {file_path}\nFile contents:\n{file_content}")
        except Exception as e:
            result.append(f"File path: {file_path}\nError loading file:\n{e}")
    result = '\n\n\n\n'.join(result)
    if state.file_for_writing is not None:
        result = result + f'You have {state.file_for_writing} open.  Anything you say will go straight to this file.  So only say code!  You must say the full code file.  You cannot e.g. say that the rest of the code is the same.'
    return result
