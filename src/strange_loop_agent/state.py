import os
import subprocess

from dataclasses import dataclass, replace
from typing import Optional

from .models import Model, openai_client, anthropic_client
from .messages import append_text_to_messages, append_content_to_messages
from .tools import tools_internal

#### App state:
@dataclass(frozen=True)
class State:
    project_dir: str                # Must be imported as part of the first call to main if this is to work.
    tracked_files: list             # List of files tracked by the LLM.
    weak_model: Model               # Weak model
    strong_model: Model             # Strong model
    messages: list                  # All the persistent messages.

    def track_file(self, path):
        return replace(state, tracked_files=[*self.tracked_files, path])

    def append_text(self, role, text, error_if_not_role_alternate=False):
        messages = append_text_to_messages(
            self.messages, 
            role, 
            text, 
            error_if_not_role_alternate=error_if_not_role_alternate
        )
        return replace(self, messages=messages)

    def append_content(self, role, content, error_if_not_role_alternate=False):
        messages = append_content_to_messages(
            self.messages, 
            role, 
            content, 
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
        return append_text_to_messages(self.messages, 'user', result)

    def assistant_api_call(self, system_message):
        assert self.messages[-1]["role"] == "user"
        return self.strong_model.response(system_message, self.append_state_to_messages(), tools=tools_internal)

def initialize_state():
    #Set up tracked files
    git_ls_files = subprocess.run('git ls-files', shell=True, capture_output=True, text=True)
    if git_ls_files.returncode == 0:
        #Use git's tracked files if git exists, and we are in a pre-existing repo.
        tracked_files = git_ls_files.stdout.strip().split('\n')
    else:
        #Use git's tracked files if git exists, and we are in a pre-existing repo.
        raise NotImplementedError()

    return State(
        project_dir = os.getcwd(),
        tracked_files = tracked_files,
        weak_model = Model(openai_client, 'gpt-4o-mini'),
        #strong_model = Model(anthropic_client, 'claude-3-5-sonnet-20240620')
        strong_model = Model(anthropic_client, 'claude-3-haiku-20240307'),
        messages = [],
    )
