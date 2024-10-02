"""
Uses tree sitter to split code files into blocks
"""

import math
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from typing import Dict, List
from dataclasses import dataclass, field
from pathlib import Path

class TreeSitterAST:
    def __init__(self, signature, start_index, end_index, code, children):
        assert isinstance(signature, (str, type(None)))
        assert isinstance(start_index, int)
        assert isinstance(end_index, int)
        assert isinstance(code, str)
        assert isinstance(children, dict)

        self.signature = signature
        self.start_index = start_index
        self.end_index = end_index
        self.code = code
        self.children = children

    def summarize(self, depth, parts=()):
        if self.signature is None:
            #Signature is only None for a file.
            assert 0 == len(parts)
            assert 0 < depth
            result = []
        elif self.signature == '':
            #Signature should only be empty string for a code block, which is one layer down from the top.
            assert 1 == len(parts)
            result = [f'#PATH#{parts[0]}']
        else:
            #Function or class
            joined_parts = '#'.join(parts)
            result = [f'{self.signature}  #PATH#{joined_parts}']

        if 0 < depth:
            result = [*result, *[v.summarize(depth-1, parts=(*parts, k)) for (k,v) in self.children.items()]]

        #Empty line between definitions at the top-level.
        sep = '\n\n' if self.signature is None else '\n'
        return sep.join(result)

    def exists(self, parts: List[str]):
        """
        and checks whether a path specified by parts exists
        """
        if len(parts) == 0:
            return True
        elif parts[0] in self.children:
            return self.children[parts[0]].exists(parts[1:])
        else:
            return False

    def index(self, parts: List[str]):
        """
        Takes a treesitter parse of a file, and extracts the path specified by parts.
        """
        if len(parts) == 0:
            return self
        else:
            return self.children[parts[0]].index(parts[1:])    

def treesitter_ast(all_code: str):
    """
    Uses tree_sitter to extract function and class definitions.

    Character indices are used instead of line numbers.

    Returns a dict mapping name -> TreeSitterCode Summary (just function and class definitions).
    """
    parser = get_parser('python')
    tree = parser.parse(bytes(all_code, "utf8"))
    query = get_language('python').query("""
    (function_definition
      name: (identifier) @function.name) @function.def
    (class_definition
      name: (identifier) @class.name) @class.def
    """)
    
    module_summary = TreeSitterAST(None, 0, len(all_code), all_code, {})
    stack = [module_summary]
    
    for capture in query.captures(tree.root_node):
        node, capture_type = capture
        
        if capture_type.endswith('.def'):
            start_index = node.start_byte
            end_index = node.end_byte

            code = all_code[start_index:end_index]
            signature = all_code[start_index:all_code.index('\n', start_index)]
            
            name_node = next(capture for capture in query.captures(node) if capture[1].endswith('.name'))[0]
            base_name = name_node.text.decode('utf8')

            #Deals with repeated definitions of the same symbol.
            i = 1
            name = base_name
            while name in stack[-1].children:
                i += 1
                name = base_name + str(i)
            
            new_summary = TreeSitterAST(signature, start_index, end_index, code, {})
            
            while start_index > stack[-1].end_index:
                stack.pop()
            
            stack[-1].children[name] = new_summary
            stack.append(new_summary)
    
    return module_summary
#def treesitter_ast_with_other_code_blocks(code: str):
#    """
#    Adds an non-empty code blocks.
#
#    Returns a dict mapping name -> TreeSitterCode Summary (also with blocks)
#    """
#    summaries = treesitter_ast_just_function_class(code).children
#    summaries_list = [*summaries.items()]
#    lines = code.split('\n')
#
#    # Collect the start and end line numbers of every block, where
#    # there is a block between every top-level function/class definition.
#    block_start_end = []
#    end_line_prev_block = 0
#    for name, func_class in summaries.items():
#        start_line_next_block = func_class.start_line
#        block_start_end.append((end_line_prev_block, start_line_next_block))
#        end_line_prev_block = func_class.end_line
#    block_start_end.append((end_line_prev_block, len(lines)))
#
#    # Strip any empty lines.
#    block_num = 0
#    result = {}
#    for i in range(len(block_start_end)):
#        start_line, end_line = block_start_end[i]
#
#        lines_between = lines[start_line: end_line]
#
#        if any(0 < len(line.strip()) for line in lines_between):
#            block_num = block_num+1
#            code_between = '\n'.join(lines_between)
#
#            name = f"%code_block_{block_num}"
#
#            result[name] = TreeSitterAST(
#                        signature='',
#                        start_line=start_line,
#                        end_line=end_line,
#                        code=code_between,
#                        children={}
#                    )
#
#        if i < len(block_start_end)-1:
#            name, summary = summaries_list[i]
#            result[name] = summary
#
#    return TreeSitterAST(None, 0, len(code.split('\n')), code, result)
#def treesitter_ast(path):
#    assert isinstance(path, Path)
#    with path.open('r') as file:
#        code = file.read()
#    return treesitter_ast_with_other_code_blocks(code)#    
#
# Example usage
code = """import xyx




def outer_function(x):
    def inner_function(y):
        return y * 2
    return inner_function(x)

oc = OuterClass(123)

def module_function(arg1: int, arg2: str) -> bool:
    return True

class OuterClass:
    def __init__(self, param1: str):
        self.param1 = param1
    
    def outer_method(self) -> None:
        pass
    
    class InnerClass:
        def inner_method(self, x: int) -> str:
            return str(x)

print("Hello, World!")

class AnotherClass(BaseClass):
    def another_method(self) -> None:
        pass

def another_module_function():
    pass

run_some_stuff()
run_some_other_stuff()
"""

