"""
Uses tree sitter to split code files into blocks
"""

import math
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from typing import Dict, List
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class TreeSitterCodeSummary:
    name : str
    signature : str
    start_line : int
    last_line : int
    code : str
    children : Dict[str, 'TreeSitterCodeSummary']

@dataclass
class TreeSitterModuleSummary:
    start_line : int
    last_line : int
    code : str
    children : Dict[str, 'TreeSitterCodeSummary']

def function_class_treesitter_summaries(code: str):
    """
    Uses tree_sitter to extract function and class definitions.

    Line numbers are standard Python (zero based, ranges run from start_line -> end_line+1

    Returns a dict mapping name -> TreeSitterCode Summary (just function and class definitions).
    """
    parser = get_parser('python')
    tree = parser.parse(bytes(code, "utf8"))
    query = get_language('python').query("""
    (function_definition
      name: (identifier) @function.name) @function.def
    (class_definition
      name: (identifier) @class.name) @class.def
    """)
    
    module_summary = TreeSitterModuleSummary(0, len(code.split('\n')), code, {})
    stack = [module_summary]
    
    for capture in query.captures(tree.root_node):
        node, capture_type = capture
        
        if capture_type.endswith('.def'):
            code = node.text.decode('utf8')
            signature = code.split('\n')[0].strip()
            start_line = node.start_point[0]
            last_line = node.end_point[0] + 1
            
            name_node = next(capture for capture in query.captures(node) if capture[1].endswith('.name'))[0]
            name = name_node.text.decode('utf8')
            
            new_summary = TreeSitterCodeSummary(name, signature, start_line, last_line, code, {})
            
            while start_line > stack[-1].last_line:
                stack.pop()
            
            stack[-1].children[name] = new_summary
            stack.append(new_summary)
    
    return module_summary

def summarize_code_with_blocks(code: str):
    """
    Adds an non-empty code blocks.

    Returns a dict mapping name -> TreeSitterCode Summary (also with blocks)
    """
    summaries = function_class_treesitter_summaries(code).children
    summaries_list = [*summaries.items()]
    lines = code.split('\n')

    # Collect the start and last line numbers of every block, where
    # there is a block between every top-level function/class definition.
    block_start_end = []
    end_line_prev_block = 0
    for name, func_class in summaries.items():
        start_line_next_block = func_class.start_line
        block_start_end.append((end_line_prev_block, start_line_next_block))
        end_line_prev_block = func_class.last_line
    block_start_end.append((end_line_prev_block, len(lines)))

    # Strip any empty lines.
    block_num = 0
    result = {}
    for i in range(len(block_start_end)):
        start_line, last_line = block_start_end[i]

        lines_between = lines[start_line: last_line]

        if 0 < len(lines_between):
            block_num = block_num+1
            code_between = '\n'.join(lines_between).strip()

            name = f"%code_block_{block_num}"

            result[name] = TreeSitterCodeSummary(
                        name=name,
                        signature="",
                        start_line=start_line,
                        last_line=last_line,
                        code=code_between,
                        children={}
                    )

        if i < len(block_start_end)-1:
            name, summary = summaries_list[i]
            result[name] = summary

    return TreeSitterModuleSummary(0, len(code.split('\n')), code, result)

# Cache that maps file hash to the summary.
# string (hash) -> list[TreeSitterCodeSummary]
#cache = {}
#
#def summarize_code_file(path):
#    key = hash_file(path)
#    if key not in cache:
#        cache[key] = summarize_code_with_blocks(path.read())
#    return cache[key]

def summarize(path):
    assert isinstance(path, Path)
    with path.open('r') as file:
        code = file.read()
    return summarize_code_with_blocks(code)
    

## Example usage
#code = """import xyx
#
#
#
#
#def outer_function(x):
#    def inner_function(y):
#        return y * 2
#    return inner_function(x)
#
#oc = OuterClass(123)
#
#def module_function(arg1: int, arg2: str) -> bool:
#    return True
#
#class OuterClass:
#    def __init__(self, param1: str):
#        self.param1 = param1
#    
#    def outer_method(self) -> None:
#        pass
#    
#    class InnerClass:
#        def inner_method(self, x: int) -> str:
#            return str(x)
#
#print("Hello, World!")
#
#class AnotherClass(BaseClass):
#    def another_method(self) -> None:
#        pass
#
#def another_module_function():
#    pass
#
#run_some_stuff()
#run_some_other_stuff()
#"""
#
#def print_code_line_num(code):
#    for i, line in enumerate(code.split('\n')):
#        print(f'{i}: {line}')
#  
#
#summaries = summarize_code_with_blocks(code)
#
#def print_summaries(summaries, indent=""):
#    for summary in summaries.children.values():
#        print(f"{indent}Lines {summary.start_line}-{summary.last_line}: {summary.name}: {summary.signature}")
#        print_summaries(summary, indent + "  ")
#
#print("Module Structure:")
#print_summaries(summaries)
