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
* There is an undo command, that undoes the previous user command + assistant response.
  - This should be used liberally, as avoids building up a huge context!
  - Rewinds the state of the agent + all the files written by the agent.
  - Doesn't rewind state changes from commands run by the agent, as these commands could do anything, and we can't track that.

## Summaries approach N

## TODOs:
* how to integrate LSP info like where a function is called?
  - just get Claude to write requests for the LSP?

* Labels for code blocks:
  - Integrate them into files as the full contents are printed.
  - Include a comment in the system prompt to avoid calling them

* undo: 
  - state records optional info about how to undo/redo changes to the file system from that step.
  - deleted files are hard, but okay if you undo step-by-step.
  - specifically, you have dict mapping 

* overseer "agent":
  - Runs concurrently with the main agent.
  - Quite weak model (4o-mini / haiku?)
  - Just takes the last user input + the model's response (e.g. not context).
  - Asks two questions:
    - Is it on-topic?
    - Is it finished with the task?
    - Is it going round in circles?
  - If any of these are true, stop, and optionally undo a couple of times.

* recursive agent calling:
  - agent can call itself as a tool.
  - usual use is:
    - top-level agent gets asked a complex task.
    - it breaks it up into smaller tasks.
    - gives each smaller task to its own agent.
    - useful for managing context, because each smaller task has 

* Search tools:
  - Google search tool.
  - Load webpage tool.

* Summaries:
  - if you change a sufficiently long block, you should diff it!
  - if you ask to explore e.g. a long function or script with no heirarchical structure, then standard explore might not print any information.  You need to force some info printed.
  - Summaries: make sure that writing files interacts correctly with sources.
  - Summaries: Optional GPT-4o-mini summaries.
  - Summaries: Anything other than function / class definitions (e.g. Haskell typedef)?
  - Summaries: .gitignore format for paths to ignore.

* Allow agent to use interactive tools.

* How to cross-reference context vs line numbers in error messages?
  - The problem is that error messages come with line numbers in the underlying files.
  - However, we don't really want to embed the line numbers in code summaries, because then you have to update the code summaries every time the line numbers change.  And that could happen alot if you change something higher in the file.
  - The solution is to take the error message and:
    - Use GPT-4o mini to take the error message, and return the filenames + linenumbers referred to in the error message.
    - Translate these filenames + linenumbers into relative paths (e.g. path to a function + line number within the function).
    - Put these back into the error message.
