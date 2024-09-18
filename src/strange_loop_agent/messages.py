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
