# Strange Loop Coding Agent
*Warning: alpha quality code.  Run at your own risk, ideally in a sandboxed environment.*

This is a Python package for the Strange Loop terminal-based coding agent.  

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

The agent is designed to be used alongside a code editor in `tmux`.

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
* There is an undo command, that undoes the previous user command + assistant response.
  - This should be used liberally, as avoids building up a huge context!
  - Rewinds the state of the agent + all the files written by the agent.
  - Doesn't rewind state changes from commands run by the agent, as these commands could do anything, and we can't track that.
* Doesn't integrate with Git.  The agent can still use Git through the terminal.  This is nice because:
  - It doesn't require you to be working in a git repo to operate.
  - It doesn't make a mess of your Git history.

