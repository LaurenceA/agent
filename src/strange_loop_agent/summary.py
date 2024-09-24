import os
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

def max_none(x, y):
    if   (x is not None) and (y is not None):
        return max(x, y)
    elif y is not None:
        return y
    elif x is not None:
        return x
    else:
        return None

def summary(path, flow_down_tokens, prev_summary, sources):
    assert isinstance(path, FullPath)

    if prev_summary is not None:
        assert prev_summary.path == path
        flow_down_tokens = max_none(flow_down_tokens, prev_summary.flow_down_tokens)

    pathsize_tokens = path.getsize() / 4

    if flow_down_tokens is None:
        return empty
    elif (not path.is_dir()) and (pathsize_tokens < flow_down_tokens):
        #We're in a code file / block, and we have enough tokens to just paste the literal code.
        return CodeLiteral(path, flow_down_tokens, path.read())
    elif (not path.is_dir()) and (flow_down_tokens < pathsize_tokens / 8):
        #We're in a code file / block, and we have too few tokens to recursively summarise.
        return CodeSummary(path, None, {}, path.signature())
    else:
        #We're in a directory or code block, and we have enough tokens to recursively summarise.
        child_paths = path.iter_tracked()

        sizes = [child_path.getsize() for child_path in child_paths]
        total_size = sum(sizes) + 1 #+1 avoids divide by zero.
        children = {}

        for child_path, size in zip(child_paths, sizes):
            child_tokens = flow_down_tokens * (size / total_size)
            if prev_summary is not None:
                child_prev_summary = prev_summary.children[child_path.name()]
            else:
                child_prev_summary = None
            children[child_path.name()] = summary(child_path, child_tokens, child_prev_summary, sources)

        if path.is_dir():
            return DirSummary(path, flow_down_tokens, children, tuple(path.listdir()))
        else:
            return CodeSummary(path, flow_down_tokens, children, path.signature())


# Abstract classes

class SummaryLiteralEmpty:
    pass

class Dir(): pass
class Code(): pass

class Summary(SummaryLiteralEmpty):
    def __init__(self, path, flow_down_tokens, children, extra):
        isinstance(path, FullPath)
        isinstance(flow_down_tokens, int)
        isinstance(children, dict)
        assert is_hashable(extra)

        self.path = path
        self.children = children
        self.flow_down_tokens = flow_down_tokens
        self.extra = extra

        hashable_dict = tuple(children.items())
        self._hash = hash((path, flow_down_tokens, hashable_dict, extra))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return self._hash

class DirSummary(Summary, Dir):
    pass # extra is a list of files.

class CodeSummary(Summary, Code):
    pass # extra is an optional summary of the file/block

class CodeLiteral(SummaryLiteralEmpty):
    def __init__(self, path, flow_down_tokens, code):
        isinstance(path, FullPath)
        isinstance(flow_down_tokens, int)
        isinstance(code, str)

        self.path = path
        self.code = code

        self._hash = hash((path, flow_down_tokens, code))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return self._hash

class Empty(SummaryLiteralEmpty):
    def dump():
        return ""

empty = Empty()

path = full_path('.')
summary = summary(path, 10000, None, [])
