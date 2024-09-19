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

## TODOs:

* Pyrsistent datastructures.
* Git-like architecture:
  - Keep all verions of all files in .claude folder, with filename = hash.
  - For each tracked file, remember hash.
  - Supports rewinding full agent + repo state.
  - Supports tracking user changes to files, without needing to keep full repo in memory.
* Rewinding:
  - Need to be careful when you write to an untracked file that already exists.
  - Need to emit two states: one where you track the file (remembering old version).  And another where you do the update and track the new file.
  - State needs to contain a log of everything printed so far.
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
