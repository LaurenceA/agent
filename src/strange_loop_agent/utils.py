from pyrsistent import PVector, PMap, PSet, pvector, pmap, pset

def is_pvector(x):
    assert isinstance(x, PVector)
    all_persistent(x)

def is_pmap(x):
    assert isinstance(x, PMap)
    all_persistent(x)

def Messages(*ms):
    result = pvector(ms)
    is_messages(result)
    return result
 
def Message(role, content):
    result = pmap({'role': role, 'content': content})
    is_message(result)
    return result

def Content(*blocks):
    result = pvector(blocks)
    is_content(result)
    return result

def Block(typ, kwargs):
    result = pmap({'type': typ, **kwargs})
    is_block(result)
    return result

def TextBlock(text):
    result = Block('text', {'text':text})
    is_text_block(result)
    return result
    
def ToolResultBlock(tool_use_id, content):
    result = Block('tool_result', {'tool_use_id':tool_use_id, 'content':content})
    is_tool_result_block(result)
    return result

def ToolUseBlock(_id, name, _input):
    result = Block('tool_use', {'id': _id, 'name': name, 'input': _input})
    is_tool_use_block(result)
    return result

def is_messages(messages):
    assert isinstance(messages, PVector)
    for m in messages:
        is_message(m)

def is_message(message):
    assert isinstance(message, PMap)
    assert message.keys() == pset(['role', 'content'])
    assert isinstance(message["role"], str)
    is_content(message["content"])

def is_content(content):
    assert isinstance(content, PVector)
    for block in content:
        is_block(block)

def is_block(block):
    assert isinstance(block, PMap)

def is_text_block(block):
    is_block(block)
    assert block.keys() == pset(['type', 'text'])
    assert block['type'] == 'text'
    assert isinstance(block['type'], str)
    assert isinstance(block['text'], str)

def is_tool_result_block(block):
    is_block(block)
    assert block.keys() == pset(['type', 'tool_use_id', 'content'])
    assert block['type'] == 'tool_result'
    assert isinstance(block['tool_use_id'], str)
    assert isinstance(block['content'], str)

def is_tool_use_block(block):
    is_block(block)
    assert block.keys() == pset(['type', 'id', 'name', 'input'])
    assert block['type'] == 'tool_use'
    assert isinstance(block['id'], str)
    assert isinstance(block['name'], str)
    assert isinstance(block['input'], dict)
     

def all_persistent(xs):
    if isinstance(xs, (int, str)):
        pass
    elif isinstance(xs, (PVector, tuple, PSet)):
        for x in xs:
            all_persistent(x)
    elif isinstance(xs, PMap):
        for k, v in xs.items():
            all_persistent(k)
            all_persistent(v)
    else:
        raise Exception(f"{type(xs)} is not persistent")
        
