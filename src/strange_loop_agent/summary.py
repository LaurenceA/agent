"""
Ultimately, there is a collection of Summary's.
Each Summary represents a summary of something that has already been given to the agent.  This could be:
  A file
  A directory
  A git repo
For example, a summary of a directory is just the files in that directory, while the summary of a file could be the function/class definitions extracted by treesitter, or it could just be the full file.

Critically, each time we run the agent, we check whether the summaries are still valid: they might have been invalidated by user actions that we can't see.  It they have been invalidated, then we update the summary, and return a message (string) to the agent.

* Key operation is adding a new source, which gives rise to one or more new summary blocks.
* A summary block corresponds to a directory, a code file, or a part of a code file (like a class).
* A summary block prints a string.  These strings can be diff'ed if something changes.
* Summary blocks are represented in a dict, mapping paths to the summary.
* New summary blocks are created by requesting "Use 1000 tokens to tell me about this path".
  - Asking for a directory recurses through directories
  - Asking for a codefile / codeblock just gives a single summary block.
* What do they print?
  - Directories just print the file / subdirectory names.  - Codefiles/blocks either print a summary of the code to some depth, or the full code.
* What happens when we update a pre-existing summary block? 
  - We diff the summary text.  
  - For code files, this requires that we record the depth, but not the number of tokens.
* What happens when a new summary block is added? Obvious.
* What happens when a summary block is deleted (i.e. its path no longer exists)?  We print a message saying that.
* What happens when a summary block is moved (i.e. its content still exists, but at a different path)?  Hard.  We can't always know where it moved to.
"""

import os
from typing import Dict, List, Tuple

from .FullPath import FullPath, full_path
from .treesitter import treesitter_ast

#### Classes for summaries
class Summary():
    def tokens(self):
        return len(self.contents) / 4

class DirSummary(Summary):
    def __init__(self, path):
        path.assert_valid_dir()
        self.path = path
        self.contents = '\n'.join(path.listdir_all())

    def new_message(self):
        return f'<directory, path={self.path}>\n{self.contents}\n</directory>'

    def update_message(self, prev_summary):
        return file_list_update_message(self.path, prev_summary.contents, self.contents)

    def update(self):
        return DirSummary(self.path)

class GitSummary(Summary):
    def __init__(self, path):
        path.assert_valid_dir()

        result = self.git_ls_files()
        if result.return_code!=0:
            raise Exception("{path} is not a valid git repo")

        self.path = path
        self.contents = result.stdout

    def git_ls_files(self):
        return subprocess.run(f'git --git-dir={self.path} ls-files', shell=True, capture_output=True, text=True)

    def new_message(self):
        return f'<git_repo, path={self.path}>\n{self.contents}\n</git_repo>'

    def update_message(self, prev_summary):
        return file_list_update_message(self.path, prev_summary.contents, self.contents)

    def update(self):
        return GitSummary(self.path)

class CodeSummary(Summary):
    def __init__(self, path, depth):
        path.assert_valid_code()
        self.path = path
        self.depth = depth

        self.treesitter_ast = path.treesitter_ast()
        if depth <= 3:
            self.contents = self.treesitter_ast.code
        else:
            self.contents = self.treesitter_ast.summarize(depth)

    def new_message(self):
        return f'<file, path={self.path}>\n{self.contents}\n</file>'

    def update_message(self, prev_summary):
        return f'<file, path={self.path}>\n{self.contents}\n</file>'

    def update(self):
        return CodeSummary(self.path, self.depth)
        #returns a new summary, based on the path and depth

def file_list_update_message(path, original_filenames:str, updated_filenames:str):
    """
    Takes two lists of filenames, as a single string with newlines between filenames, and returns changes.
    """
    original_filenames = set(original_filenames.split('\n'))
    updated_filenames = set(updated_filenames.split('\n'))

    new_filenames = list(updated_filenames.difference(original_filenames))
    deleted_filenames = list(original_filenames.difference(updated_filenames))

    new_filenames = '\n'.join(['    ' + filename for filename in new_filenames])
    deleted_filenames = '\n'.join(['    ' + filename for filename in deleted_filenames])


    result = f'<directory_update path={path}>\n'
    if new_filenames:
        result = result + f'  <new_files>\n{new_filenames}\n  </new_files>\n'
    if deleted_filenames:
        result = result + f'  <deleted_files>\n{deleted_filenames}\n  </deleted_files>\n'
    result = result + '</directory_update>'
    return result
    
    

SummaryDict = Dict[FullPath, Summary]
SummaryList = List[Tuple[FullPath, Summary]]
Messages = List[str]
Source = Tuple[FullPath, int]
Sources = List[Source]




#### Converting a raw list of tokens per source into new summaries.
def new_summaries_from_token_sources(sources: Sources) -> SummaryDict:
    #Gather all new sources.
    result_list = []
    for source_path, source_max_tokens in sources:
        result_list = result_list + new_summaries_from_token_source(source_path, source_max_tokens)

    #Could be duplicates because this takes multiple sources.  De-duplicate.
    result_dict = {} 
    for path, summary in result_list:
        insert = True
        if (path in result_dict) and isinstance(summary, CodeSummary):
            prev_summary = result_dict[path]
            if prev_summary.depth > depth:
                insert = False
        if insert:
            result_dict[path] = summary

    return result_dict

def new_summaries_from_token_source(path: FullPath, max_tokens:int) -> SummaryList:
    """
    Try summaries of different depths, measuring the number of tokens they produce.
    Once they produce too many tokens, use the previous depth.
    """
    prev_summaries = new_summaries_from_depth(path, depth=1)
    for depth in range(1, 4): #1,2,3
        summaries = new_summaries_from_depth(path, depth)

        summary_tokens = sum(summary.tokens() for (path, summary) in summaries)
        if max_tokens < summary_tokens:
            break

        prev_summaries = summaries

    return prev_summaries

def new_summaries_from_depth(path: FullPath, depth:int) -> SummaryList:
    path.assert_is_valid()
    assert 1 <= depth 

    if path.is_valid_code():
        result = [(path, CodeSummary(path, depth))]
    else:
        assert path.is_valid_dir()
        result = [(path, DirSummary(path))]
        if 2 <= depth:
            for child_path in path.iter_tracked():
                result = result + new_summaries_from_depth(child_path, depth-1)

    return result



def update_delete_summaries(summaries: SummaryDict) -> (SummaryDict, Messages):
    updated_summaries = {}
    messages = []

    for full_path, summary in summaries.items():
        try:
            updated_summary = summary.update()
            if summary.contents != updated_summary.contents:
                messages.append(updated_summary.update_message(summary))
            updated_summaries[full_path] = updated_summary
        except AgentException as e:
            messages.append("Previous summary invalid. " + str(e))

    return (updated_summaries, messages)

def add_summaries(summaries:SummaryDict, new_summaries:SummaryDict):
    updated_summaries = {**summaries}
    messages = []

    #New summaries may have unnecessary new summaries, e.g. those that we already have,
    #or those where we already have a deeper code summary.
    for full_path, new_summary in new_summaries.items():
        insert = False
        if full_path not in summaries:
            insert = True

        if full_path in summaries:
            summary = summaries[full_path]
            if isinstance(summary, CodeSummary) and isinstance(new_summary, CodeSummary):
                if new_summary.depth > summary.depth:
                    insert = True

        if insert:
            updated_summaries[full_path] = new_summary
            messages.append(new_summary.new_message())
    
    return (updated_summaries, messages)



def add_summaries_from_token_sources(prev_summaries:SummaryDict, sources: List[Tuple[FullPath, int]]) -> (SummaryDict, Messages):
    checked_sources = []
    invalid_messages = []
    for full_path, tokens in sources:
        try:
            full_path.assert_is_valid()
            checked_sources.append((full_path, tokens))
        except AgentException as e:
            invalid_messages.append(e)

    new_summaries = new_summaries_from_token_sources(checked_sources)
    summaries, messages = add_summaries(prev_summaries, new_summaries)
    return summaries, messages + invalid_messages


#fp = full_path('src/')
#ns, ms = update_summaries_from_token_sources({}, [(fp, 10000)])
