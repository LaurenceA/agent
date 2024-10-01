from dataclasses import dataclass
from typing import List
from tree_sitter_languages import get_parser

@dataclass
class Comment:
    text: str
    start_line: int
    end_line: int

def extract_comments(source_code: str) -> List[Comment]:
    # Get the Python parser
    parser = get_parser('python')
    
    # Parse the code
    tree = parser.parse(bytes(source_code, "utf8"))
    
    comments = []
    cursor = tree.walk()
    
    reached_root = False
    while not reached_root:
        if cursor.node.type == 'comment':
            start_point, end_point = cursor.node.start_point, cursor.node.end_point
            start_line, _ = start_point
            end_line, _ = end_point
            comment_text = source_code.splitlines()[start_line:end_line+1]
            comment_text = '\n'.join(comment_text).strip()
            comments.append(Comment(text=comment_text, start_line=start_line, end_line=end_line+1))
        
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
