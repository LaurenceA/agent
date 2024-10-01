from dataclasses import dataclass
from typing import List
from tree_sitter_languages import get_parser

@dataclass
class Comment:
    text: str
    start: int
    end: int

def extract_comments(source_code: str) -> List[Comment]:
    # Get the Python parser
    parser = get_parser('python')
    
    # Parse the code
    tree = parser.parse(bytes(source_code, "utf8"))
    
    # Helper function to get byte index from point
    def get_byte_index(source_code_bytes, point):
        row, column = point
        lines = source_code_bytes.split(b'\n')
        return sum(len(line) + 1 for line in lines[:row]) + column
    
    comments = []
    cursor = tree.walk()
    source_code_bytes = source_code.encode('utf8')
    
    reached_root = False
    while not reached_root:
        if cursor.node.type == 'comment':
            start_point, end_point = cursor.node.start_point, cursor.node.end_point
            start_index = get_byte_index(source_code_bytes, start_point)
            end_index = get_byte_index(source_code_bytes, end_point)
            comment_text = source_code_bytes[start_index:end_index].decode('utf8').strip()
            comments.append(Comment(text=comment_text, start=start_index, end=end_index))
        
        if cursor.goto_first_child():
            continue
        
        if cursor.goto_next_sibling():
            continue
        
        retracing = True
        while retracing:
            if not cursor.goto_parent():
                retracing = False
                reached_root = True
            
            if cursor.goto_next_sibling():
                retracing = False
    
    return comments


