import os
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

"""
There are two key ideas here.

## Threshold_mult for recursive summarisation

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

Third, What if we want to summarise something outside the project root 
directory? e.g. a library function?  The solution is to have a list of
summarisation "roots".

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

## Visibility + configurability

Problem: there are lots of files you don't want to include in the summary.
Solutions:
* For visibility, command to print tracked + untracked files.
* For configurability, .gitignore like format.
"""

#def not_binary(file_path, sample_size=1024):
#    """
#    A heuristic to determine whether a file is binary (and hence should be ignored).
#
#    TODO: improve with a local LLM?
#    """
#    with open(file_path, 'rb') as file:
#        sample = file.read(sample_size)
#    
#    # Check for null bytes
#    if b'\x00' in sample:
#        return True
#
#    # Check if the sample contains mostly printable ASCII characters
#    printable_chars = sum(32 <= byte <= 126 for byte in sample)
#    return printable_chars / len(sample) > 0.7  # Adjust threshold as needed
#
#def listdir(path):
#    """
#    A list of all non-binary, non-hidden files
#
#    Returns the full path.
#    """
#    result = []
#    for child_path in os.listdir(path):
#        if not_binary(child_path) and (not child_path[0] == '.'):
#            result.append(os.path.join(path, child_path))
#
#def listdir(path):
#    """
#    Assumes everything is part of a git repo.
#    """
#    result = subprocess.run(f'git ls-tree HEAD --name-only {path}', shell=True, capture_output=True, text=True)
#    assert 0 == result.return_code
#    return result.split('\n')

default_gitignore = """
# Ignore all hidden files and directories in all folders
.*

# Don't ignore .gitignore itself
!.gitignore
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

class SummaryConfig():
    def __init__(self):
        self.gitignore_spec = PathSpec.from_lines(GitWildMatchPattern, default_gitignore.split())

    def listdir_tracked_untracked(self, path):
        """
        Lists the absolute path of all files/directories at path.
        Splits them into tracked files and untracked files.
        """
        tracked = []
        untracked = []

        for filename in os.listdir(path):
            abs_path = os.path.join(path, filename)

            if self.gitignore_spec.match_file(filename):
                untracked.append(abs_path)
            else:
                tracked.append(abs_path)
        return tracked, untracked

    def listdir_tracked(self, path):
        return self.listdir_tracked_untracked(path)[0]

    def getsize_file(self, path):
        """
        Returns a very, _very_ rough approximation of the number of tokesn in the file as the
        number of bytes divided by 4.
        """
        return os.path.getsize(path) / 4

    def getsize(self, path):
        """
        For a file, returns the size of the file, measured in approximate tokens.
        For a directory, returns the total number of tokens in all tracked files in that directory (recursively)
        """
        if os.path.isdir(path):
            return sum(self.getsize(child_path) for child_path in self.listdir_tracked(path))
        else:
            return self.getsize_file(path)

    def summary(self, path, tokens, prev_summary, sources):
        """
        Summarises a file or directory.
        """
        if os.path.isdir(path):
            return self.dir_summary(path, tokens, prev_summary, sources)
        else:
            return self.file_summary(path, tokens, prev_summary, sources)

    def dir_summary(self, path, tokens, prev_summary, sources):
        """
        Summarises a directory.
        """
        if prev_summary is not None:
            assert prev_summary.path == path

        child_paths = self.listdir_tracked(path)

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

class Summary():
    pass

class DirSummary(Summary):
    pass

class DirSummaryEmpty(DirSummary):
    """
    Too many filenames to include in the summary!
    """
    def __init__(self, path):
        isinstance(path, str)
        self.path = path

    def dump(self):
        return self.path + '(directory)'

class DirSummaryFiles(DirSummary):
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


class FileSummary(Summary):
    pass

class FileSummaryFull(FileSummary):
    def __init__(self, path, file_contents):
        self.path = path
        self.file_contents = file_contents

    def dump(self):
        return f"\n\n\nFile: {self.path}\nContents:\n{self.file_contents}\n\n\n"

class FileSummaryPath(FileSummary):
    def __init__(self, path):
        self.path = path

    def dump(self):
        return self.path + '\n'

sc = SummaryConfig()
summary = sc.summary('/Users/laurence_ai/Dropbox/git/agent/src/strange_loop_agent', 100000000, None, None)
