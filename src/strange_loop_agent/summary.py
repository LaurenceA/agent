import os
from FullPath import FullPath, full_path, is_valid_code
from treesitter import treesitter_ast
from typing import Dict, List, Tuple

#### Classes for summaries
class Summary():
    def tokens(self):
        return (len(self.new_header) + len(self.contents)) / 4

class DirSummary(Summary):
    def __init__(self, path):
        assert path.is_valid_dir()
        self.contents = '\n'.join(path.listdir_all())

        self.new_header = f'Full contents of directory {path}:\n'
        self.update_header = f'Changes to contents of directory {path}:\n'

    def update(self):
        return SummaryDir(self.path)

    #def diff(self, other):

class CodeSummary(Summary):
    def __init__(self, path, depth):
        assert path.is_valid_code()
        self.depth = depth

        self.treesitter_ast = path.treesitter_ast()
        if depth <= 3:
            self.contents = self.treesitter_ast.code
        else:
            self.contents = self.treesitter_ast.summarize(depth)

        self.new_header = f'Code at {path}:\n'
        self.update_header = f'Changes to code at {path}:\n'

    def update(self):
        return SummaryCode(self.path, self.depth)
        #returns a new summary, based on the path and depth

    #def diff(self, other):

SummaryDict = Dict[FullPath, Summary]
SummaryList = List[Tuple[FullPath, Summary]]
Messages = List[str]




#### Converting a raw list of tokens per source into new summaries.
def new_summaries_from_token_sources(sources: List[Tuple[FullPath,int]]) -> SummaryDict:
    #Gather all new sources.
    result_list = []
    for source_path, source_max_tokens in sources:
        result_list = result_list + new_summaries_from_token_source(source_path, source_max_tokens)

    #De-duplicate
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
    assert path.is_valid()
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




#### Updating the previous list of summaries.
def update_summaries_from_new_summaries(prev_summaries:SummaryDict, new_summaries: SummaryDict) -> (SummaryDict, Messages):
    messages = []

    #Removes messages that no longer exist.
    prev_summaries, messages = delete_summaries(prev_summaries, messages)

    #Moves brand new messages (i.e. where there wasn't a message of that type or depth before) from new_summaries to prev_summaries
    prev_summaries, new_summaries, messages = add_summaries(prev_summaries, new_summaries, messages)

    #Applies any updates (i.e. for messages of the same type)
    prev_summaries, new_summaries, messages = update_summaries(prev_summaries, new_summaries, messages)

    assert 0 == len(new_summaries)
    return prev_summaries, messages
    
def delete_summaries(prev_summaries:SummaryDict, messages:Messages) -> (SummaryDict, Messages):
    updated_prev_summaries = {**prev_summaries}

    for full_path, summary in prev_summaries.items():
        still_valid_dir = isinstance(summary, DirSummary) and full_path.is_valid_dir()
        still_valid_code = isinstance(summary, CodeSummary) and full_path.is_valid_code()
        if still_valid_dir or still_valid_code:
            updated_prev_summaries[full_path] = summary
        else:
            if not os.access(path.path, os.R_OK):
                messages.append(f"No longer have read permission for {path.path}")
            elif not path.path.exists():
                messages.append(f"{path} has been deleted or renamed")
            elif isinstance(summary, DirSummary):
                messages.append(f"{path} is no longer a directory (e.g. it has changed to a file)")
            elif isinstance(summary, CodeSummary) and not is_valid_code(path.path):
                messages.append(f"{path} is no longer a code file (e.g. it has changed to a binary file or a directory")
            elif isinstance(summary, CodeSummary) and not path.exists():
                messages.append(f"{path} has been deleted or renamed")
            else:
                breakpoint()
    return (updated_prev_summaries, messages)

def add_summaries(prev_summaries:SummaryDict, new_summaries:SummaryDict, messages:list):
    updated_prev_summaries = {**prev_summaries}
    updated_new_summaries = {**new_summaries}

    for full_path, new_summary in new_summaries.items():
        replace = False
        if full_path not in prev_summaries:
            replace = True

        if full_path in prev_summaries:
            prev_summary = prev_summaries[full_path]
            if isinstance(prev_summary, CodeSummary) and isinstance(new_summary, CodeSummary):
                if new_summary.depth > prev_summary.depth:
                    replace = True

        if replace:
            updated_prev_summaries[full_path] = new_summary
            messages.append(new_summary.new_header + new_summary.contents)
            del updated_new_summaries[full_path]
    
    return (updated_prev_summaries, updated_new_summaries, messages)


def update_summaries(prev_summaries: SummaryDict, new_summaries: SummaryDict, messages: Messages) -> (SummaryDict, SummaryDict, Messages):
    updated_prev_summaries = {**prev_summaries}
    updated_new_summaries = {**new_summaries}

    for full_path, new_summary in new_summaries.items():
        replace = False
        if full_path in prev_summaries:
            prev_summary = prev_summaries[full_path] 
            if type(prev_summary) == type(new_summary):
                replace = True
        
        if replace:
            updated_prev_summaries[full_path] = new_summary
            messages.append(new_summary.update_header + diff(original=prev_summary.content, new=new_summary.content))
            del updated_new_summaries[full_path]

    return updated_prev_summaries, updated_new_summaries, messages



#### Integrating everything
def update_summaries_from_token_sources(prev_summaries:SummaryDict, sources: List[Tuple[FullPath, int]]) -> (SummaryDict, Messages):
    new_summaries = new_summaries_from_token_sources(sources)
    return update_summaries_from_new_summaries(prev_summaries, new_summaries)


ns, ms = update_summaries_from_token_sources({}, [(full_path('src/strange_loop_agent/summary.py'), 10000)])
