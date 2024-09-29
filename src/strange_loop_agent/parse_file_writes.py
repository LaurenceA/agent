from bs4 import BeautifulSoup
from .FullPath import full_path

def parse_writes(response: str):
    result = {}
    soup = BeautifulSoup(response, 'html.parser')
    write_file_tags = soup.find_all('write_file')

    # Process each found tag
    for tag in write_file_tags:
        path = tag.get('path')  # Get the 'path' attribute
        content = tag.string
        assert content
        result[full_path(path)] = content
    return result
