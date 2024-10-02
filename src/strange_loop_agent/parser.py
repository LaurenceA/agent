import re
from typing import List, Union
from .FullPath import full_path

from .exceptions import AgentException

class Write:
    def __init__(self, path: str, after: str):
        path.assert_can_write()
        self.path = full_path(path)

        #Get rid of initial and final new line
        #Note that r'\n' is two characters, but '\n' is one special newline character.
        if after[0] == '\n':
            after = after[1:]
        if after[-1] == '\n':
            after = after[:-1]
        self.after = after

    def file_change(self):
        """
        Computes, but does not apply, the change to the path represented by update.
        Returns:
            before_full_file: the full file before the change
            after_full_file: the full file after the change
            diff: a diff (e.g. for printing to the user).
            to_be_implemented_comment_line_numbers: a diff (e.g. for printing to the user).
        """

        #If there's currently no file, then just use the after.
        if not self.path.path.exists():
            return after, after

        #If there is a file, then open it.
        with path.path.open('r') as file:
            before_full_file = file.read()

        #If there's parts, then load up only the part that we're using.
        if 0 < len(path.parts):
            ts = path.treesitter_ast()
            before = ts.code
        else:
            before = before_full_file

        after = smart_merge(before, after)

        #Merge it back into the file, taking account of parts.
        if 0 < len(path.parts):
            before_full_file_lines = before_full_file.split('\n')
            after_full_file = '\n'.join(before_full_file_lines[:ts.start_line]) + after + '\n'.join(before_full_file_lines[ts.end_line:])
        else:
            after_full_file = after

        _diff = diff(before_full_file, after_full_file)

        return after_full_file, _diff

#class Replace:
#    def __init__(self, path: str, pattern: str, replacement):
#        path.assert_can_write()
#        self.path = full_path(path)
#
#        self.pattern = pattern
#        self.replacement = replacement
#
#    def file_change(self):
#        before = 
#        is self.pattern not in 

def parse_structure(text: str) -> List[Union[str, Write, Replace]]:
    """
    Takes the text returned by an agent, and returns a list of either strings,
    Writes or Replace's
    """
    result = []
    i = 0
    
    while i < len(text):
        # Check for Write structure
        write_match = re.match(r'<write path=[\'"](.+?)[\'"]>', text[i:])
        if write_match:
            path = write_match.group(1)
            start = i + write_match.end()
            end = text.find('</write>', start)
            if end == -1:
                raise AgentException("Unclosed <write> tag.  No writes or replacements performed.")
            content = text[start:end].strip()
            result.append(Write(path=path, text=content))
            i = end + len('</write>')
            continue
        
        # Check for Replace structure
        replace_match = re.match(r'<replace path=[\'"](.+?)[\'"]>', text[i:])
        if replace_match:
            path = replace_match.group(1)
            start = i + replace_match.end()
            end = text.find('</replace>', start)
            if end == -1:
                raise AgentException("Unclosed <replace> tag.  No writes or replacements performed.")
            content = text[start:end]
            pattern_match = re.search(r'<pattern>(.*?)</pattern>', content, re.DOTALL)
            replacement_match = re.search(r'<replacement>(.*?)</replacement>', content, re.DOTALL)
            if not pattern_match or not replacement_match:
                raise AgentException("Invalid <replace> structure.  No writes or replacements performed.")
            pattern = pattern_match.group(1).strip()
            replacement = replacement_match.group(1).strip()
            result.append(Replace(path=path, pattern=pattern, replacement=replacement))
            i = end + len('</replace>')
            continue
        
        # If not a special structure, accumulate plain text
        text_end = next((j for j in range(i, len(text)) if text[j:].startswith('<write') or text[j:].startswith('<replace')), len(text))
        if text_end > i:
            result.append(text[i:text_end].strip())
            i = text_end
        else:
            i += 1
    
    return result
