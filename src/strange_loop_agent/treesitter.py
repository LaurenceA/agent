from tree_sitter import Language, Parser
from tree_sitter_languages import get_language, get_parser
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class CodeSummary:
    signature: str
    start_line: int
    last_line: int
    children: List['CodeSummary']

@dataclass
class ModuleSummary:
    start_line: int
    last_line: int
    children: List['CodeSummary']

def extract_unified_signatures(code: str) -> ModuleSummary:
    parser = get_parser('python')
    tree = parser.parse(bytes(code, "utf8"))

    query = get_language('python').query("""
    (function_definition) @function.def
    (class_definition) @class.def
    """)

    module_summary = ModuleSummary(0, 100000, [])

    stack = [module_summary]

    for capture in query.captures(tree.root_node):
        node, node_type = capture
        
        # Make new CodeSummary block.
        signature = node.text.decode('utf8').split('\n')[0].strip()
        start_line = node.start_point[0]
        last_line = node.end_point[0]
        new_summary = CodeSummary(signature, start_line, last_line, [])

        while start_line > stack[-1].last_line:
            stack.pop()

        # Add the new summary to the current top of the stack
        stack[-1].children.append(new_summary)
        stack.append(new_summary)

    return module_summary

# Example usage
code = """
def outer_function(x):
    def inner_function(y):
        return y * 2
    return inner_function(x)

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

class AnotherClass(BaseClass):
    def another_method(self) -> None:
        pass

def another_module_function():
    pass
"""

module_summary = extract_unified_signatures(code)

def print_summaries(summaries, indent=""):
    for summary in summaries:
        print(f"{indent}Lines {summary.start_line}-{summary.last_line}: {summary.signature}")
        if summary.children:
            print_summaries(summary.children, indent + "  ")

print("Module Structure:")
print_summaries(module_summary.children)
