import os
from pathlib import Path

from utils import not_binary

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

def dict_eq(d1, d2):
    """
    Tests equality of two dictionaries, by first checking that the keys are all equal,
    then checking that the values are the same using `is`.
    """
    if frozenset(d1.keys()) != frozenset(d2.keys()):
        return False
    else:
        return all(d1[k] is d2[k] for k in d1)

def listdir_tracked(path):
    """
    Lists directories and non-binary files that aren't hidden (i.e. don't start with a '.').
    """
    assert isinstance(path, Path)
    assert file_path.is_dir()

    result = []
    for filename in os.listdir(path):
        abs_path = os.path.join(path, filename)

        if ('.' != filename[0]) and (os.path.isdir(abs_path) or not_binary_file(abs_path)):
            result.append(filename)
    return result

def getsize_file(path):
    """
    Returns a very, _very_ rough approximation of the number of tokesn in the file as the
    number of bytes divided by 4.
    """
    assert isinstance(path, Path)
    assert not file_path.is_dir()

    return os.path.getsize(path) / 4

def getsize(path):
    """
    For a file, returns the size of the file, measured in approximate tokens.
    For a directory, returns the total number of tokens in all tracked files in that directory (recursively)
    """
    assert isinstance(path, Path)

    if path.is_dir():
        return sum(self.getsize(child_path) for child_path in self.listdir_tracked(path))
    else:
        return self.getsize_file(path)

def summary(path, flow_down_tokens, prev_summary, sources):
    """
    Summarises a file or directory.
    """
    assert isinstance(path, Path)

    if path.is_dir():
        return self.dir_summary(path, flow_down_tokens, prev_summary, sources)
    else:
        return self.file_summary(path, flow_down_tokens, prev_summary, sources)

def dir_summary(path, flow_down_tokens, prev_summary, sources):
    """
    Summarises a directory.
    """
    assert isinstance(path, Path)
    assert path.is_dir()

    if prev_summary is not None:
        assert prev_summary.path == path

    child_paths = listdir_tracked(path)

    if flow_down_tokens is None:
        if isinstance(prev_summary, DirSummaryEmpty):
            return prev_summary
        else:
            return DirSummaryEmpty()
    else:
    if 10 * len(child_paths) < tokens:
        #If all path of files in this directory will fit into context
        sizes = [self.getsize(child_path) for child_path in child_paths]
        total_size = sum(sizes)

        new_summaries = {}
        for child_path, size in zip(child_paths, sizes):
            child_tokens = tokens * (size / total_size)
            if isinstance(prev_summary, DirSummary):
                child_prev_summary = prev_summary.get(child_path)
            else:
                child_prev_summary = None
            
            new_summaries[child_path] = self.summary(child_path, child_tokens, child_prev_summary, sources)

        if isinstance(prev_summary, DirSummaryFiles) and dict_eq(new_summaries, prev_summary.summaries):
            return prev_summary
        else:
            return DirSummaryFiles(path, new_summaries)
    else:
        #If the paths won't fit into context
        if isinstance(prev_summary, DirSummaryEmpty):
            return prev_summary
        else:
            return DirSummaryEmpty(path)

def file_summary(self, path, tokens, prev_summary, sources):
    if prev_summary is not None:
        assert prev_summary.path == path

    filesize = self.getsize_file(path)

    if filesize < tokens:
        #If we have enough tokens, include the whole file in the summary.
        with open(path, "r") as file:
            file_contents = file.read()

        if isinstance(prev_summary, FileSummaryFull) and prev_summary.file_contents == file_contents:
            return prev_contents
        else:
            return FileSummaryFull(path, file_contents)

    #elif filesize/4 < tokens:
    #    #GPT-4o summary of file.

    #elif filesize/8 < tokens:
    #    #tree-sitter summary of file

    else:
        #If we just have enough tokens for the path, include just the path.
        if isinstance(prev_summary, FileSummaryPath):
            return prev_summary
        else:
            return FileSummaryPath(path)


# Abstract classes
class Summary():
    pass

class SummaryEmpty():
    def dump():
        return ""

class SummaryFull():
    def __init__(self, path, summaries)
        isinstance(path, str)
        isinstance(summaries, dict)
        self.path = path
        self.summaries = summaries

class DirSummary(Summary):
    pass

class FileSummary(Summary):
    pass

# Concrete classes

class FileSummaryFull(FileSummary, SummaryFull):
    def dump():
        return f'ls {self.path}\n' + '\n'

class DirSummaryFull(DirSummary):
    def __init__(self, path, summaries):
        """
        Summaries is a dict mapping an absolute paths to a summary.
        """
        isinstance(path, str)
        isinstance(summaries, dict)
        self.path = path
        self.summaries = summaries

    def dump(self):
        return ''.join([x.dump() for x in self.summaries.values()])


class FileSummaryFull(FileSummary):
    def __init__(self, path, file_contents):
        self.path = path
        self.file_contents = file_contents

    def dump(self):
        return f"\n\n\nFile: {self.path}\nContents:\n{self.file_contents}\n\n\n"



class DirSummaryEmpty(DirSummary, EmptySummary):
    pass

class FileSummaryEmpty(FileSummary, EmptySummary):
    pass


sc = SummaryConfig()
summary = sc.summary('/Users/laurence_ai/Dropbox/git/agent/src/strange_loop_agent', 100000000, None, None)
