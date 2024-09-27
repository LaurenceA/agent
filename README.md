# Strange Loop Agent
This is a Python package for the Strange Loop Agent project.

## Installation
To install this package, clone the repository and run:

```
pip install -e .
```

## Usage

The main entry point for this package is `strange_loop_agent.agent`. You can run it using:

```
python -m strange_loop_agent.agent
```

or if you've installed the package:

```
strange_loop_agent
```

The agent assumes you're running it run from the project root directory.

## Project Structure

```
strange_loop_agent/
├── src/
│   └── strange_loop_agent/
│       ├── __init__.py
│       ├── agent.py
│       └── tools.py
├── setup.py
└── README.md
```

## Development

To set up a development environment, we recommend using a virtual environment:

```
python -m venv .venv
source venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
pip install -e .
```

This will install the package in editable mode, allowing you to make changes to the source code and immediately see the effects.

## Features:
* Summaries:
  - You set a token budget for the summary, which then "flows" through the directory tree.
  - The model can add extra token budget at interesting nodes.
  - Summaries are cache-friendly: we keep the summary in the cache, and update only new information.
  - Summaries are updated both for externally updated and agent-written files.
* The model has a unified FullPath abstraction, allowing it to refer to class/function/methods within a file.
  - e.g. `path/to/file#class_name#method_name`
* Rewinding / undo, supported by functional architecture, plus git-like file store.
  - Does mean that you can't write to previously untracked files.

## Summaries approach N
* Key operation is adding a new source, which gives rise to one or more new summary blocks.
* A summary block corresponds to a directory, a code file, or a part of a code file (like a class).
* A summary block prints a string.  These strings can be diff'ed if something changes.
* Summary blocks are represented in a dict, mapping paths to the summary.
* New summary blocks are created by requesting "Use 1000 tokens to tell me about this path".
  - Asking for a directory recurses through directories
  - Asking for a codefile / codeblock just gives a single summary block.
* What do they print?
  - Directories just print the file / subdirectory names.
  - Codefiles/blocks either print a summary of the code to some depth, or the full code.
* What happens when we update a pre-existing summary block? 
  - We diff the summary text.  
  - For code files, this requires that we record the depth, but not the number of tokens.
* What happens when a new summary block is added? Obvious.
* What happens when a summary block is deleted (i.e. its path no longer exists)?  We print a message saying that.
* What happens when a summary block is moved (i.e. its content still exists, but at a different path)?  Hard.  We can't always know where it moved to.
* Don't record tokens used previously.
* There is a function, taking a path (and, for code, a depth), and returning a summary block.
  - If path no longer correponds 
* Datastructures:
  - new_sources: Dict[FullPath, tokens:int].
  - prev_summaries: Dict[FullPath, (typ, depth, str)], type of block (e.g. directory, depth (only relevant for code) and string representation).
  - diff: List[str], string represents a message about diffs, deletions etc.
* Functions:
  - typ(full_path, depth) (returns the type, i.e. code vs directory).
  - str(full_path, depth) (returns the actual string representation).
* Algorithm is:
  - There is a list of diffs, which starts empty.
  - For every new source, compute the new nodes (recursing through directories).  Add them all to the list of diffs + the record of summaries.
  - See whether any of the old nodes have changed (i.e. text changed), deleted (i.e. path no longer exists), or changed type (i.e. weirdly went from a directory to a code file).  Modify the prev_summaries + add 

## TODOs:
* Summaries: make sure that writing files interacts correctly with sources.
* Summaries: Use a path to index into summary.
* Summaries: Special treatment for README.
* Summaries: Optional GPT-4o-mini summaries.
* Summaries: Anything other than function / class definitions (e.g. Haskell typedef)?
* Summaries: .gitignore format for paths to ignore.
* System prompt describing path format (i.e. path/to/file#class_name#function_name)
* Sources: Tool to add new sources.


* How to cross-reference context vs line numbers in error messages?
  - The problem is that error messages come with line numbers in the underlying files.
  - However, we don't really want to embed the line numbers in code summaries, because then you have to update the code summaries every time the line numbers change.  And that could happen alot if you change something higher in the file.
  - The solution is to take the error message and:
    - Use GPT-4o mini to take the error message, and return the filenames + linenumbers referred to in the error message.
    - Translate these filenames + linenumbers into relative paths (e.g. path to a function + line number within the function).
    - Put these back into the error message.

* Undo files:
  - Only undo files written by us!
  - Allows us to get rid of the awkward "project" abstraction.

* Add sources tool.
