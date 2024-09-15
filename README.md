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

* Persistent summary of project.
  - One summary for each file in the project.
  - The summary is associated with a hash for the file.
  - When you use the summary, check the file hashes.
  - Summary contains info on all functions/classes/globals.
* Have a set of open files, which are pasted at the end of the messages.
  - Tools to open/close files.
  - Could also open sub-parts of files, based on info in the summary.
* Internet search, especially for documentation.
  - Google search / Bing API.
  - Use 4o-mini to convert website?  Or a library like Mozilla's readability
* Tool to display file in context.
* Read from interactive terminals using 4o-mini.

## Finetuning:

* Prompt caching.
* Input format.  Arrows work through readline.  But don't have e.g. multi-line input.
