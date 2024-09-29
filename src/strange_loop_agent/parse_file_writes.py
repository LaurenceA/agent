import re
from .FullPath import full_path

file_open_delimiter = r'<write\s+path\s*=\s*(?:"([^"]*)"|\'([^\']*)\')\s*>'
file_close_delimiter = '</write>'

def parse_writes(text):
    open_delimiters = [*re.finditer(file_open_delimiter, text)]
    close_delimiters = [*re.finditer(file_close_delimiter, text)]

    #Same number of open and close delimiters.
    N = len(open_delimiters)
    assert N == len(close_delimiters)

    open_delimiter_locations = [m.end() for m in open_delimiters]
    close_delimiter_locations = [m.start() for m in close_delimiters]

    #Close is after open within the pair.
    for i in range(N):
        assert open_delimiter_locations[i] < close_delimiter_locations[i]

    #No nesting (always a close before the new open).
    for i in range(1, N):
        assert close_delimiter_locations[i-1] < open_delimiter_locations[i] 

    paths = []
    for match in open_delimiters:
        assert (match.group(1) is None) != (match.group(2) is None)
        if match.group(1) is not None:
            paths.append(match.group(1))
        else:
            paths.append(match.group(2))

    result = []
    for i in range(N):
        result.append((full_path(paths[i]), text[open_delimiter_locations[i] : close_delimiter_locations[i]]))#.split('\n', 1))
    return result



#from bs4 import BeautifulSoup
#from .FullPath import full_path
#
#def parse_writes(response: str):
#    result = {}
#    soup = BeautifulSoup(response, 'html.parser')
#    write_file_tags = soup.find_all('write_file')
#
#    # Process each found tag
#    for tag in write_file_tags:
#        path = tag.get('path')  # Get the 'path' attribute
#        content = tag.string
#        assert content
#        result[full_path(path)] = content
#    return result
