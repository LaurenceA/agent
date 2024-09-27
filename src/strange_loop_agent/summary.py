import os
import operator
from typing import Dict, List
from FullPath import FullPath, full_path

"""
There are two key ideas here.

## tokens for recursive summarisation

The key idea here is that summaries are computed recursively, i.e.
if you get the summary for the root directory of a project, then
you recursively get summaries of all folders / files in that project.

The problem with this is that its difficult to control the amount of 
summary that's produced.  e.g. for a very small project, you might 
just want to include all the code.  Whereas for a very large project,
you might want very brief summaries.

We manage this by having a tokens parameter, which should be roughly
the length of the summary in tokens. This quantity is ``conserved'' 
as you recurse through the directories. e.g. if you have
tokens_parent_dir = 400
in a parent directory, then you might split this up to give
tokens_child_dir = 200
tokens_file1 = 100
tokens_file2 = 100
This way, you can do recursive summarisation, while sensibly
controlling the size of the summary.

However, that raises a few of questions: 

First, how do we set the amount of tokens to send to each file / 
subdirectory? We use a heursistic: set tokens proportional to size of 
the file (or for a directory, the size of all the files in that 
directory, recursing through the directory structure).

Second, what if the user requests to summarise a particular directory 
more deeply? In that case, we add a "source" of tokens at that
directory. These sources are provided as a list. That means you need
to recurse through all the files / folders.

Third, where to start the tree?  At the project root, or the file system
root?  We choose the file system root, as that allows you to move to 
different projects, or capture e.g. library source code in your summaries.

Fourth, if you start from the root of the file system, you probably don't
want summaries from the root of the file system.  The solution is to have
a parameter, flow_down_tokens=None, initially.  When you have 
flow_down_tokens=None, and there are no sources within the file/
subdirectory, then you use an EmptySummary.

## Diffing summaries for efficient context updates.

So far, we have described how to generate "full" summaries. At the start,
you compute the summary for the project and paste it into the context.
However, what happens when the agent / user updates a file? We could
recompute the summary, but that could waste money (e.g. if we're using
an API call for the summary), and potentially expand the context far too
much. Instead, we should:
  update incrementally, only updating for files that have changed.
  compute a diff between the new and old summaries.

#### Update incrementally, only updating for files that have changed.
* For a file, keep the hash/edit timestamp, so you can tell when it has changed 
  and recompute the summary.
* If a file is the same, use the corresponding node from the previous tree.
* That way, for diffing, and for working out whether all the files in a directory
  are the same (so you know whether to use the previous directory summary node)
  you look at whether all the underlying files / directory summaries are the 
  same using `is`

#### Compute a diff.
* Easy if you've done your incremental updates correctly.
* Just recurse through the summary tree, and only include nodes that aren't
  equal to the corresponding node in the previous tree (using is).
* Flag if file deleted.

#### Diff for file write.
Needs special treatment to avoid including the same info in the context twice.
You can either:
* Delete the "write" from the conversation log, and include it only in the diff.
* Keep the "write" in the conversation log, and don't include the summary diff.

## Folders

How to print folders?  To print folders, print the folder name + file 
names (i.e. not full file paths).  That saves tokens, but gives full 
information.  

When to print folders? Of course, you don't want to print the contents of 
everything starting from the root directory.  So only print the contents of
a directory when flow_down_tokens!=None.

How to diff folders?  Include in the context when a file is added or removed.

## Hidden files/folders

When printing a the contents of a directory, print the all files and folders,
so the agent can see all the files.  But assign zero weight to hidden/non-binary 
files/folders.

The agent can then: 
* load a binary file by name
* put a source on e.g. a hidden file / directory if they want

## Files

Files are split up into CodeSummary blocks.

The paths are e.g. /absolute/path/to/file#class_name#method_name.

## Visibility + configurability

Problem: there are lots of files you don't want to include in the summary.
Solutions:
* For visibility, command to print tracked + untracked files.
* For configurability, .gitignore like format.
"""

#def dict_eq(d1, d2):
#    """
#    Tests equality of two dictionaries, by first checking that the keys are all equal,
#    then checking that the values are the same using `is`.
#    """
#    if frozenset(d1.keys()) != frozenset(d2.keys()):
#        return False
#    else:
#        return all(d1[k] is d2[k] for k in d1)

def is_hashable(obj):
    try:
        hash(obj)
        return True
    except TypeError:
        return False

def binary_none(f):
    def inner(x, y):
        if   (x is not None) and (y is not None):
            return f(x, y)
        elif y is not None:
            return y
        elif x is not None:
            return x
        else:
            return None

    return inner
max_none = binary_none(max)
add_none = binary_none(operator.add)

def summary_node(path, sources, flow_down_tokens, prev_summary):
    assert isinstance(path, FullPath)
    #Either directory or code, but not both
    path_is_dir = path.is_valid_dir() 
    assert path_is_dir != path.is_valid_code() 
    

    total_tokens = flow_down_tokens
    for source_path, source_tokens in sources.items():
        #total_tokens is all available tokens, from sources above and below
        if source_path.is_in(path):
            total_tokens = add_none(total_tokens, source_tokens)
        #flow_down_tokens is just tokens that arise from sources above, and right here.
        if source_path == path:
            flow_down_tokens = add_none(flow_down_tokens, source_tokens)

    code_literal_cond = (not path_is_dir) and (total_tokens is not None) and (path.getsize()/4 < total_tokens)
    code_literal_cond = code_literal_cond or (isinstance(prev_summary, CodeLiteral) and path.is_valid_text_file())

    if code_literal_cond:
        #We're in a code file / block, and we have enough tokens to just paste the literal code.
        return code_literal(path)
    elif (total_tokens is not None) or isinstance(prev_summary, Branch):
        #We can't just paste the code (either because we don't have enough tokens, or we're in a dir).

        #Pass any tokens further down?
        #This is a global setting (for all children), so that we can terminate the tree without
        #exploring every node, and making sure that we always have all children at a Branch node.
        if (flow_down_tokens is not None) and (flow_down_tokens < 20):
            flow_down_tokens = None

        child_paths = path.iter_tracked()
        if flow_down_tokens is not None:
            #Heuristic for splitting up tokens to child nodes
            sizes = [child_path.getsize() for child_path in child_paths]
            total_size = sum(sizes) + 1 #+1 avoids divide by zero.
            child_tokens = [flow_down_tokens * (size / total_size) for size in sizes]
        else:
            child_tokens = [None for _ in child_paths]
           
        children = {}
        for child_path, child_tokens in zip(child_paths, child_tokens):
            if prev_summary is not None:
                child_prev_summary = prev_summary.children.get(child_path.name())
            else:
                child_prev_summary = None

            children[child_path.name()] = summary_node(child_path, sources, child_tokens, child_prev_summary)

        return summary_branch(path, children, flow_down_tokens, prev_summary)
    else:
        #total_tokens is None and prev_summary is neither CodeLiteralLeaf or SummaryBranch.
        return summary_leaf(path)

def summary_branch(path, children, flow_down_tokens, prev_summary):
    assert path.is_valid()

    if path.is_valid_dir() and ((flow_down_tokens is not None) or isinstance(prev_summary, DirBranchDisplay)):
        #Directory, that should be displayed
        return DirBranchDisplay(path, tuple(path.listdir_all()), children)
    elif path.is_valid_dir():
        #Directory that shouldn't be displayed
        return DirBranchNoDisplay(path, tuple(path.listdir_all()), children)
    elif 0 == len(path.parts):
        #Code file
        return CodeFileOverviewBranch(path, "", children)
    else:
        #Code block
        return CodeBlockOverview(path, path.signature(), children)

def summary_leaf(path):
    assert path.is_valid()

    if path.is_valid_dir():
        #Directory
        return DirLeaf(path, "")
    elif 0 == len(path.parts):
        #Code file
        return CodeFileOverviewLeaf(path, "")
    else:
        #Code block
        return CodeBlockOverview(path, path.signature(), {})

def code_literal(path):
    if 0==len(path.parts):
        return CodeFileLiteral(path, path.read())
    else:
        return CodeBlockLiteral(path, path.read())

def summary(sources, prev_summary):
    init_path = full_path('/Users/laurence_ai/Dropbox/git')
    assert init_path.is_dir()
    return summary_node(init_path, sources, None, prev_summary)


"""
Classes to represent the summaries.
* Overview vs Literal makes sense for code, and indicates whether 
  it just includes all the code, or has an overview e.g. of methods.
* Branch vs Leaf indicates whether the file / folder has child nodes.  
  Important to know which very explicitly, because we want to a  
  "section" in the summary for all the branches.

dump returns a list of strings for: 
* DirLeaf (Empty list)
* DirBranch (List of everything in directory)
* CodeFileLeaf (Empty list)
* CodeFileBranch (One element list)
* CodeFileLiteral (One element list)

dump returns a string for:
* CodeBlock
"""

#Abstract
class Summary: 
    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return self._hash

def extract_leading_spaces(s):
    return s[:len(s) - len(s.lstrip())]

#Abstract
class Branch(Summary): 
    def __init__(self, path, extra, children):
        if children is None:
            children = {}
        assert isinstance(path, FullPath)
        assert isinstance(children, dict)
        assert is_hashable(extra)

        self.path = path
        self.children = children
        self.extra = extra

        hashable_dict = tuple(children.items())
        self._hash = hash((path, hashable_dict, extra))

        self.validate()

    def validate(self):
        pass

#Abstract
def directory_summary_line(path):
    assert path.is_valid()
    assert 0 == len(path.parts)
    if path.is_valid_dir():
        typ = 'directory'
    elif path.is_valid_code():
        typ = 'text'
    else:
        typ = 'binary'
    return f'{path.path.name} ({typ})'

#Abstract
class DirBranch(Branch):
    def validate(self):
        assert all(isinstance(c, (Dir, CodeFile)) for c in self.children.values())

    def dump_children(self):
        results = []
        for child in self.children.values():
            child_dump = child.dump()
            assert isinstance(child_dump, list)
            results = results + child_dump
        return results

#Concrete
class DirBranchDisplay(DirBranch): 
    def dump(self) -> List[str]:
        result = f'Full contents of directory {self.path.path}:\n'
        result = result + '\n'.join([directory_summary_line(node.path) for node in self.children.values()])
        
        return [result, *self.dump_children()]

#Concrete
class DirBranchNoDisplay(DirBranch): 
    def dump(self) -> List[str]:
        return self.dump_children()

#Abstract
class CodeBlockOverview(Branch):
    def validate(self):
        assert all(isinstance(c, CodeBlock) for c in self.children.values())

    def dump(self):
        assert 0 < len(self.path.parts)
        parts = '#'.join(self.path.parts)

        if hasattr(self, 'children') and (0 < len(self.children)):
            #Function or class with children
            child_dumps = ''.join([child.dump() for child in self.children.values()])
            return add_parts(self.path, '  ', self.extra) + child_dumps
        elif 0 < len(self.extra):
            #Function or class without children
            indent = extract_leading_spaces(self.extra)
            return add_parts(self.path, '  ', self.extra)
        else:
            #Code block
            return add_parts(self.path, '', '')

    def not_function_class(self):
        return 0 == len(self.extra)

#Concrete
class CodeFileOverviewBranch(Branch): 
    def validate(self):
        assert all(isinstance(c, CodeBlock) for c in self.children.values())

    def dump(self):
        child_dumps = '\n'.join([child.dump() for child in self.children.values()])
        return [f"FILE: {self.path.path}:\n\n{child_dumps}"]

def add_parts(path, indent, line):
    parts = '#'.join(path.parts)
    return f"{line.rstrip()}{indent}#PATH:#{parts}\n"
    
   

#Abstract
class Leaf(Summary): 
    def __init__(self, path, extra):
        assert isinstance(path, FullPath)
        assert is_hashable(extra)

        self.path = path
        self.extra = extra

        self._hash = hash((path, extra))

#Concrete
class DirLeaf(Leaf): 
    """
    Doesn't include the files in the directory, just the directory path

    Extra is empty
    """
    def dump(self) -> List[str]:
        assert not self.extra
        return []

#Concrete
class CodeFileOverviewLeaf(Leaf): 
    """
    Doesn't include any info about the code, just the path

    Extra is empty
    """
    def dump(self) -> List[str]:
        assert not self.extra
        return []

#Abstract
class CodeLiteral(Leaf): 
    pass

#Concrete
class CodeFileLiteral(CodeLiteral): 
    def dump(self) -> List[str]:
        return [f'Start of #{parts}:\n{self.extra}\nEnd of #{parts}\n']

#Concrete
class CodeBlockLiteral(CodeLiteral): 
    def dump(self) -> List[str]:
        lines = self.extra.split('\n')
        line0 = add_parts(self.path, lines[0])
        lines = [line0, *lines[1:]]
        
        return '\n'.join(lines)



Dir = (DirBranch, DirLeaf)
CodeFile = (CodeFileOverviewBranch, CodeFileOverviewLeaf, CodeFileLiteral)
CodeBlock = (CodeBlockOverview, CodeBlockLiteral)

path = full_path('.')
#summary = summary({full_path('src'): 10000}, None)
summary = summary_node(path, {full_path('src/strange_loop_agent/summary.py'): 100}, None, None)
print('\n\n\n\n'.join(summary.dump()))
