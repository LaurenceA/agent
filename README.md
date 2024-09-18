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

* Refine the prompt when in "file-writing" mode.  e.g. state whether the file exists.  Add the file to context etc.
* Open sub-parts of files, based on info in the summary.
* Optimize prompt caching.
* Input format.  Arrows work through readline.  But don't have e.g. multi-line input.
* Hard-code context / file printing stuff 
