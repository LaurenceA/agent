import pytest
from strange_loop_agent.detect_unchanged import unchanged_unimplmented_comments, unchanged_comment
from strange_loop_agent.treesitter_comments import Comment

def test_unchanged_comment():
    # Test cases that should return True
    assert unchanged_comment(Comment("# ... (rest of code unchanged)", 1, 1))
    assert unchanged_comment(Comment("Rest of code is unchanged.", 1, 1))
    assert unchanged_comment(Comment("# Unchanged code here.", 1, 1))
    assert unchanged_comment(Comment("... (previous code unchanged).", 1, 1))

    # Test cases that should return False
    assert not unchanged_comment(Comment("# to be implemented", 1, 1))
    assert not unchanged_comment(Comment("# this function does xyz", 1, 1))
    assert not unchanged_comment(Comment("# Important: This is a crucial part of the code", 1, 1))
    assert not unchanged_comment(Comment("# TODO: Implement error handling", 1, 1))

def test_unchanged_unimplmented_comments():
    code = """
def example_function():
    # This is a normal comment
    print("Hello, world!")
    
    # ... (rest of code unchanged)
    
    # TODO: Implement error handling
    
    # Unchanged code here.
    
    return True
"""
    result = unchanged_comments(code)
    
    assert len(result) == 2
    assert "... (rest of code unchanged)" in result[0].text
    assert "Unchanged code here." in result[1].text

def test_unchanged_unimplmented_comments_no_unchanged():
    code = """
def another_function():
    # This function does something important
    print("Important stuff happening")
    
    # TODO: Add more functionality
    
    return False
"""
    result = unchanged_comments(code)
    
    assert len(result) == 0

def test_unchanged_unimplmented_comments_empty_code():
    code = ""
    result = unchanged_comments(code)
    
    assert len(result) == 0
