from collections.abc import Iterable

class Block():
    pass

class TextBlock(Block):
    def __init__(self, text):
        isinstance(text, str)

        self.text = text

    def dump(self):
        return {'type': 'text', 'text': self.text}

class ToolUseBlock(Block):
    def __init__(self, _id, name, _input):
        isinstance(_id, str)
        isinstance(name, str)
        isinstance(_input, dict)
        self.id = _id
        self.name = name
        self.input = _input
    
    def dump(self):
        return {'type': 'tool_use', 'id': self.id, 'name': self.name, 'input': self.input}

class ToolResultBlock(Block):
    """
    Tool results turn up in user blocks, so also cacheable.
    """
    def __init__(self, tool_use_id, content):
        isinstance(tool_use_id, str)
        isinstance(content, str)

        self.tool_use_id = tool_use_id
        self.content = content
    
    def dump(self):
        return {'type': 'tool_result', 'tool_use_id': self.tool_use_id, 'content': self.content}

class Message():
    def __init__(self, role, blocks):
        assert role in ['user', 'assistant']
        self.role = role

        assert isinstance(blocks, Iterable)
        self.blocks = tuple(blocks)
        for block in self.blocks:
            assert isinstance(block, Block)

    def append_block(self, role, block):
        assert self.role == role
        return Message(role, [*self.blocks, block])

    def dump(self):
        content = [block.dump() for block in self.blocks]
        return {'role': self.role, 'content': content}


class Messages():
    def __init__(self, messages):
        assert isinstance(messages, Iterable)
        self.messages = tuple(messages)
        for m in self.messages:
            assert isinstance(m, Message)

    def dump(self):
        return [m.dump() for m in self.messages]

    def append_message(self, message):
        assert isinstance(message, Message)
        if 0 < len(self.messages):
            assert message.role != self.messages[-1].role
        return Messages([*self.messages, message])

    def append_block(self, role, block):
        assert isinstance(role, str)
        assert isinstance(block, Block)

        if 0 < len(self.messages) and role == self.messages[-1].role:
            #Same role as previous, so append block to previous message.
            updated_message = self.messages[-1].append_block(role, block)
            return Messages([*self.messages[:-1], updated_message])
        else:
            #Same role as previous, so make new message
            return self.append_message(Message(role, [block]))

    def append_text(self, role, text):
        return self.append_block(role, TextBlock(text))

    def assert_ready_for_user_input(self):
        return 0 == len(self.messages) or self.messages[-1].role == "assistant"

    def assert_ready_for_assistant(self):
        return 0 != len(self.messages) and self.messages[-1].role == "user"

