import os
import json
import subprocess

from dataclasses import dataclass, replace
from typing import Optional
from pyrsistent import PVector, PMap, PSet, pvector, pmap, pset

from .models import Model, openai_client, anthropic_client
from .messages import append_text_to_messages, append_block_to_messages
from .tools import tools_internal
from .parse_file_writes import file_open_delimiter, file_close_delimiter, parse_file_writes

from .utils import is_messages

default_config = {
    'max_tokens' : 4096,
    'hash_dir' : '.agent',
}

if os.path.exists('.claude-config'):
    with open(file_path, 'r') as file:
        repo_config = json.load(file)
else:
    repo_config = {}

config = {**default_config, **repo_config}

def call_terminal(command):
    stdout = subprocess.run(command, shell=True, capture_output=True, text=True).stdout
    assert 0 < len(stdout)
    return stdout.strip()

system_message = f"""You are a part of an agentic system for programming.

Try to be brief when responding to user requests.  Tokens are expensive!

Don't ask for permission.  Just call the tools.  The agent wrapper handles asking the user for permission.

Try to minimize the number of files you have in the context.  Discard any files from the context you don't need.

When you want to write to a file, use the following format:
{file_open_delimiter}path/to/file
<file contents>{file_close_delimiter}
These files are automatically written successfully.

A brief description of the system you are running on:
OS name: {call_terminal('uname -s')}
OS version: {call_terminal('uname -r')}
Architecture: {call_terminal('uname -m')}
System name: {call_terminal('uname -n')}

The project root directory is:
{os.getcwd()}
Don't navigate, or modify anything outside, this directory.

"""


#### App state:
@dataclass(frozen=True)
class State:
    system_message: str
    project_dir: str                # Must be imported as part of the first call to main if this is to work.
    tracked_files: PMap             # Dict mapping tracked file names to current hashes.
    max_tokens: int                 # Max tokens for any completion
    hash_dir: str                   # Directory with ...
    weak_model: Model               # Weak model
    strong_model: Model             # Strong model
    messages: PVector               # All the persistent messages.

    def track_file(self, path):
        return replace(state, tracked_files=self.tracked_files.add(path))

    def append_text(self, role, text, error_if_not_role_alternate=False):
        messages = append_text_to_messages(
            self.messages, 
            role, 
            text, 
            error_if_not_role_alternate=error_if_not_role_alternate
        )

        is_messages(messages)
        return replace(self, messages=messages)

    def append_block(self, role, block, error_if_not_role_alternate=False):
        messages = append_block_to_messages(
            self.messages, 
            role, 
            block, 
            error_if_not_role_alternate=error_if_not_role_alternate
        )
        return replace(self, messages=messages)

    def abs_path(self, rel_path):
        return os.path.join(self.project_dir, rel_path)

    def append_state_to_messages(self):
        assert 0==len(self.messages) or self.messages[-1]["role"] == "user"
        tracked_file_string = '\n'.join(self.tracked_files)

        result = f"Tracked files:\n{tracked_file_string}"

        #append_text_to_messages('user', '
        #for file_path in state.context_files:
        #    abs_path = os.path.join(state.project_dir, file_path)
        #    try:
        #        with open(abs_path, 'r') as file:
        #            file_content = file.read()
        #        result.append(f"File path: {file_path}\nFile contents:\n{file_content}")
        #    except Exception as e:
        #        result.append(f"File path: {file_path}\nError loading file:\n{e}")
        #result = '\n\n\n\n'.join(result)
        #if state.file_for_writing is not None:
        #    result = result + f'You have {state.file_for_writing} open.  Anything you say will go straight to this file.  So only say code!  You must say the full code file.  You cannot e.g. say that the rest of the code is the same.'
        messages = append_text_to_messages(self.messages, 'user', result)
        is_messages(messages)
        print(messages)
        return messages

    def assistant_api_call(self):
        assert self.messages[-1]["role"] == "user"
        return self.strong_model.response(self.system_message, self.append_state_to_messages(), tools=tools_internal)

def initialize_state():
    #Set up tracked files
    git_ls_files = subprocess.run('git ls-files', shell=True, capture_output=True, text=True)
    if git_ls_files.returncode == 0:
        #Use git's tracked files if git exists, and we are in a pre-existing repo.
        tracked_files = pvector(git_ls_files.stdout.strip().split('\n'))
    else:
        #Use git's tracked files if git exists, and we are in a pre-existing repo.
        raise NotImplementedError()

    return State(
        system_message = system_message,
        project_dir = os.getcwd(),
        max_tokens = config["max_tokens"],
        hash_dir = config["hash_dir"],
        tracked_files = tracked_files,
        weak_model = Model(openai_client, 'gpt-4o-mini'),
        #strong_model = Model(anthropic_client, 'claude-3-5-sonnet-20240620')
        strong_model = Model(anthropic_client, 'claude-3-haiku-20240307'),
        messages = pvector(),
    )
