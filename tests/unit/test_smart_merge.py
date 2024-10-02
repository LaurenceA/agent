import pytest
from strange_loop_agent.smart_merge import smart_merge, Section, Sections

def test_smart_merge_basic():
    original = r"""
def file_change(path, after):
    #Get rid of initial and final new line
    if after[:2] == '\n':
        after = after[2:]
    if after[-2:] == '\n':
        after = after[:-2]

    if unchanged_comments(after):
        raise AgentException("There was a comment indicating unchanged code in the proposed write.  You need to write _all_ the code.  If the write is very long, try to write to a specific function/class/method using e.g. <write path=/path/to/file#function_name>.")

    #If there's currently no file, then just use the after.
    if not path.path.exists():
        return None, after, after

    #If there is a file, it needs to be a valid code file.
    path.assert_can_write() #raises AgentCantWriteException

    #If there is a file, then open it.
    with path.path.open('r') as file:
        before_full_file = file.read()

    #If there's parts, then load up only the part that we're using.
    if 0 < len(path.parts):
        ts = path.treesitter_ast()
        before = ts.code
    else:
        before = before_full_file

    #Merge it back into the file, taking account of parts.
    if 0 < len(path.parts):
        before_full_file_lines = before_full_file.split('\n')
        after_full_file = '\n'.join(before_full_file_lines[:ts.start_line]) + after + '\n'.join(before_full_file_lines[ts.end_line:])
    else:
        after_full_file = after

    _diff = diff(before_full_file, after_full_file, 'before', 'after')

    return before_full_file, after_full_file, _diff
"""
    update = r"""
    # ... (unchanged)
    if 0 < len(path.parts):
        ts = path.treesitter_ast().run()
        before = ts.code
    else:
        before = before_full_file
    # ... (unchanged)
"""
    expected = r"""
def file_change(path, after):
    #Get rid of initial and final new line
    if after[:2] == '\n':
        after = after[2:]
    if after[-2:] == '\n':
        after = after[:-2]

    if unchanged_comments(after):
        raise AgentException("There was a comment indicating unchanged code in the proposed write.  You need to write _all_ the code.  If the write is very long, try to write to a specific function/class/method using e.g. <write path=/path/to/file#function_name>.")

    #If there's currently no file, then just use the after.
    if not path.path.exists():
        return None, after, after

    #If there is a file, it needs to be a valid code file.
    path.assert_can_write() #raises AgentCantWriteException

    #If there is a file, then open it.
    with path.path.open('r') as file:
        before_full_file = file.read()

    #If there's parts, then load up only the part that we're using.
    if 0 < len(path.parts):
        ts = path.treesitter_ast().run()
        before = ts.code
    else:
        before = before_full_file

    #Merge it back into the file, taking account of parts.
    if 0 < len(path.parts):
        before_full_file_lines = before_full_file.split('\n')
        after_full_file = '\n'.join(before_full_file_lines[:ts.start_line]) + after + '\n'.join(before_full_file_lines[ts.end_line:])
    else:
        after_full_file = after

    _diff = diff(before_full_file, after_full_file, 'before', 'after')

    return before_full_file, after_full_file, _diff
"""    
    result = smart_merge(original, update)
    assert result == expected
