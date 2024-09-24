import os
from typing import Optional
from tree_sitter import Parser
from tree_sitter_languages import get_language, get_parser

# Dictionary mapping file extensions to programming languages
EXTENSION_TO_LANGUAGE = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.cs': 'c_sharp',
    '.rb': 'ruby',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.hs': 'haskell',
    '.ml': 'ocaml',
    '.lua': 'lua',
    '.sh': 'bash',
    '.pl': 'perl',
    '.r': 'r',
    '.m': 'matlab',
    '.sql': 'sql',
}

# List of languages to try with tree-sitter
LANGUAGES_TO_TRY = [
    'python',
    'javascript',
    'typescript',
    'java',
    'c',
    'cpp',
    'c_sharp',
    'ruby',
    'go',
    'rust',
    'php',
    'swift',
    'kotlin',
    'scala',
    'haskell',
    'ocaml',
    'lua',
    'bash',
    'perl',
    'r',
]

def detect_language(file_path: str) -> Optional[str]:
    """
    Detect the programming language of a given file.
    First checks the file extension, then falls back to tree-sitter parsing.
    """
    # Check file extension first
    _, extension = os.path.splitext(file_path)
    if extension in EXTENSION_TO_LANGUAGE:
        return EXTENSION_TO_LANGUAGE[extension]

    # If extension not found, use tree-sitter
    with open(file_path, 'rb') as file:
        content = file.read()
    
    best_match = None
    highest_score = 0

    for lang_name in LANGUAGES_TO_TRY:
        try:
            parser = get_parser(lang_name)
            tree = parser.parse(content)
            
            # Calculate a simple score based on the number of recognized nodes
            score = len(list(tree.root_node.walk()))
            
            if score > highest_score:
                highest_score = score
                best_match = lang_name
        except Exception:
            # If a language parser is not available, skip it
            continue

    return best_match

# Example usage
if __name__ == "__main__":
    file_path = "example_code.txt"
    detected_language = detect_language(file_path)
    if detected_language:
        print(f"Detected language: {detected_language}")
    else:
        print("Could not detect the programming language.")
