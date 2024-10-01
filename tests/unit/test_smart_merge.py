import pytest
from strange_loop_agent.smart_merge import smart_merge, Section, Sections

def test_smart_merge_basic():
    original = """def hello():
    print("Hello, World!")
    # Some comment
    print("How are you?")
"""
    update = """def hello():
    print("Hello, Universe!")
    # ... (unchanged)
    print("How are you?")
"""
    expected = """def hello():
    print("Hello, Universe!")
    # Some comment
    print("How are you?")
"""
    result = smart_merge(original, update)
    return result
    #assert result == expected

def test_smart_merge_multiple_sections():
    original = """def greet(name):
    print(f"Hello, {name}!")
    # Some comment
    print("How are you?")
    # Another comment
    print("Goodbye!")
"""
    update = """def greet(name):
    print(f"Greetings, {name}!")
    # ... (unchanged)
    print("How are you doing?")
    # ... (unchanged)
    print("Farewell!")
"""
    expected = """def greet(name):
    print(f"Greetings, {name}!")
    # Some comment
    print("How are you doing?")
    # Another comment
    print("Farewell!")
"""
    result = smart_merge(original, update)
    assert result == expected

def test_smart_merge_no_changes():
    original = """def hello():
    print("Hello, World!")
    # Some comment
    print("How are you?")
"""
    update = """def hello():
    # ... (unchanged)
    print("Hello, World!")
    # ... (unchanged)
    print("How are you?")
    # ... (unchanged)
"""
    result = smart_merge(original, update)
    assert result == original

def test_smart_merge_with_additions():
    original = """def calculate(a, b):
    result = a + b
    return result
"""
    update = """def calculate(a, b):
    # ... (unchanged)
    result = a + b
    print(f"The result is: {result}")
    return result
"""
    expected = """def calculate(a, b):
    result = a + b
    print(f"The result is: {result}")
    return result
"""
    result = smart_merge(original, update)
    assert result == expected

def test_smart_merge_with_deletions():
    original = """def process_data(data):
    # Validate input
    if not isinstance(data, list):
        raise ValueError("Input must be a list")
    
    # Process data
    result = [item * 2 for item in data]
    
    # Log result
    print(f"Processed {len(data)} items")
    
    return result
"""
    update = """def process_data(data):
    # ... (unchanged)
    if not isinstance(data, list):
        raise ValueError("Input must be a list")
    
    # Process data
    result = [item * 2 for item in data]
    
    return result
"""
    expected = """def process_data(data):
    # Validate input
    if not isinstance(data, list):
        raise ValueError("Input must be a list")
    
    # Process data
    result = [item * 2 for item in data]
    
    return result
"""
    result = smart_merge(original, update)
    assert result == expected

def test_section_model():
    section = Section(section_number=0, start_line=1, end_line=3)
    assert section.section_number == 0
    assert section.start_line == 1
    assert section.end_line == 3

def test_sections_model():
    sections = Sections(sections=[
        Section(section_number=0, start_line=1, end_line=3),
        Section(section_number=1, start_line=5, end_line=7)
    ])
    assert len(sections.sections) == 2
    assert sections.sections[0].section_number == 0
    assert sections.sections[1].start_line == 5

if __name__ == "__main__":
    pytest.main()
