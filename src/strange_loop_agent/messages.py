import os
from pyrsistent import PVector, PMap, PSet, pvector, pmap, pset
from .utils import is_messages, is_content, is_message, is_block, Messages, Message, Content, TextBlock

def append_text_to_messages(messages, role, text, error_if_not_role_alternate=False):
    block = TextBlock(text)
    return append_block_to_messages(messages, role, block, error_if_not_role_alternate=error_if_not_role_alternate)

def append_block_to_messages(messages, role, block, error_if_not_role_alternate=False):
    """
    Assumes content is a dict, e.g. {'type': 'text', 'text': '...'}
    """
    assert role in ["user", "assistant"]
    is_messages(messages)
    is_block(block)

    if 1<=len(messages) and messages[-1]["role"] == role:
        #Same role as previous message
        assert not error_if_not_role_alternate
        content = messages[-1]["content"].append(block)
        message = messages[-1].set("content", content)
        messages = messages.set(-1, message)
    else:
        #Role has alternated, so we need a new message.
        message = Message(role, Content(block))
        messages = messages.append(message)
    is_messages(messages)
    return messages
