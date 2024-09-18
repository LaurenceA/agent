import re

file_open_delimiter = "!!Write file!! "
file_close_delimiter = "\n!!File written succesfully!!"

def parse_file_writes(text):
    open_delimiter_locations = [m.end() for m in re.finditer(file_open_delimiter, text)]
    close_delimiter_locations = [m.start() for m in re.finditer(file_close_delimiter, text)]

    #Same number of open and close delimiters.
    N = len(open_delimiter_locations)
    assert N == len(close_delimiter_locations) 

    #Close is after open within the pair.
    for i in range(N):
        assert open_delimiter_locations[i] < close_delimiter_locations[i]

    #No nesting (always a close before the new open).
    for i in range(1, N):
        assert close_delimiter_locations[i-1] < open_delimiter_locations[i] 

    result = []
    for i in range(N):
        result.append(text[open_delimiter_locations[i] : close_delimiter_locations[i]].split('\n', 1))
    return result
