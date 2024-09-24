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

## Next steps:
* Implement undo.
* Check file writing (in particular, you can't write untracked files that already exist).

## Features:
* Rewinding / undo, supported by functional architecture, plus git-like file store.
  - Does mean that you can't write to previously untracked files.

## TODOs:

* Deal with repeated function/class definitions in treesitter.
* Summaries: take sources and derive the "roots" (i.e. don't start from the file directory root).

* How to cross-reference context vs line numbers in error messages?
  - The problem is that error messages come with line numbers in the underlying files.
  - However, we don't really want to embed the line numbers in code summaries, because then you have to update the code summaries every time the line numbers change.  And that could happen alot if you change something higher in the file.
  - The solution is to take the error message and:
    - Use GPT-4o mini to take the error message, and return the filenames + linenumbers referred to in the error message.
    - Translate these filenames + linenumbers into relative paths (e.g. path to a function + line number within the function).
    - Put these back into the error message.


* Updates to persistent summaries:
  - Agent diffs are in the code anyway.
  - If user updates file, then redo file summary for that file, and past diff into context.

* Summary primitives:
  - Summarise file with GPT-4o mini.
  - Tree sitter to extract function/class definitions in file.

* Undo files:
  - Only undo files written by us!

* Tasks:
  - Contextual summary (so the agent knows what to edit).
  - Agents selects a bunch of functions to edit.

* Summaries:
  - Generated in one shot for a full file.
  - But represented as line numbers, title, description.
  - Key idea is to incrementally update summaries.
  - When a file is overwritten (either by user or by agent), need to regenerate summary.
  - Ask LLM to keep summary same as previous summary where it is still relevant.
  - So that caching works well, summaries are dumped into context at start.  Updated summaries are placed into context as necessary.
  - Line numbers are expected to change rapidly, so: 
    - Line numbers aren't included in summaries.
    - LLM identifies sections (e.g. for writing) by title, not line number.

* Print diffs for file writes.
* Keep line numbers out of summary.  Store them separately, so that you can update them easily.
* Reductions in context + context tool use:
  - Takes fully cached messages, including summaries.
  - Runs a special prompt asking for the context required for that query.
* Tracked files
  - This is a new component of the state, describing all files tracked by the agent.
  - Starts as all files tracked by git, if project is a git repo (git ls-files).
  - Otherwise, pass all files to GPT-4o mini.
  - Tools to add files to tracked files.  Automatically add new files to tracked files.
  - Tracked files are associated with a current summary and a file hash.
  - The summaries come from GPT-4o mini / tree-sitter.
  - The summaries come with line ranges, which can also be opened.
* Internet search, especially for documentation.
  - Google search / Bing API.
  - Use 4o-mini to convert website?  Or a library like Mozilla's readability
* Swappable OpenAI and Anthropic prompts.
* Report file diffs.
* Read from interactive terminals using 4o-mini.

## Improvements:

* Open sub-parts of files, based on info in the summary.
