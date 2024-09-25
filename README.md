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

## TODOs:

* Summaries: take sources and derive the "roots" (i.e. don't start from the file directory root).
* Summaries diffs:
  - Implement diff_dump(self, other) methods.
  - Crappy initial approach: just repeat whenever different.
    - files in a folder
    - code in a file
    - code literal
* Summaries: make sure that writing files interacts correctly with sources
* Summaries: Get rid of .encode, and just use length of the string.
* Summaries: Use a path to index into summary.
* Summaries: sources for README?
* Summaries: Optional GPT-4o-mini summaries.
* Summaries: Anything other than function / class definitions (e.g. Haskell typedef)?
* Summaries: Move formatting of treesitter code in dump()
* Summaries: ... e.g. under class when there's methods we haven't include.
* System prompt describing path/to/file#class_name.


* Sources: Tool to add new sources.
* Sources: Add a source in the starting directory.

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
