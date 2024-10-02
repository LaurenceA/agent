import re
from dataclasses import dataclass
from typing import List, Union

@dataclass
class Write:
    path: str
    text: str

@dataclass
class Replace:
    path: str
    pattern: str
    replacement: str

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
                raise ValueError("Unclosed <write> tag")
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
                raise ValueError("Unclosed <replace> tag")
            content = text[start:end]
            pattern_match = re.search(r'<pattern>(.*?)</pattern>', content, re.DOTALL)
            replacement_match = re.search(r'<replacement>(.*?)</replacement>', content, re.DOTALL)
            if not pattern_match or not replacement_match:
                raise ValueError("Invalid <replace> structure")
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
