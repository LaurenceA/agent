#from .check_update import check_update
from .smart_merge import smart_merge
from .diff import diff


def file_change(path, update):
    """
    Computes, but does not apply, the change to the path represented by update.
    Returns:
        before_full_file: the full file before the change
        after_full_file: the full file after the change
        diff: a diff (e.g. for printing to the user).
        to_be_implemented_comment_line_numbers: a diff (e.g. for printing to the user).
    """
    #Get rid of initial and final new line
    print(repr(update))
    if update[:2] == '\n':
        update = update[2:]
    if update[-2:] == '\n':
        update = update[:-2]
    print(repr(update))

    #If there's currently no file, then just use the update.
    if not path.path.exists():
        return None, update, update

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

    #Do the smart merge.
    after = smart_merge(before, update)

    #Merge it back into the file, taking account of parts.
    if 0 < len(path.parts):
        before_full_file_lines = before_full_file.split('\n')
        after_full_file = '\n'.join(before_full_file_lines[:ts.start_line]) + after + '\n'.join(before_full_file_lines[ts.end_line:])
    else:
        after_full_file = after

    _diff = diff(before_full_file, after_full_file, 'before', 'after')

    return before_full_file, after_full_file, _diff
