import os
import json
import subprocess
import shutil

from dataclasses import dataclass, replace
from typing import Optional

from .models import Model, openai_client, anthropic_client
from .tools import tools_internal
from .utils import hash_file
from .system_message import system_message

from .messages import Messages
from .formatting import color

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


#### App state:
@dataclass(frozen=True)
class State:
    system_message: str
    project_dir: str                # Must be imported as part of the first call to main if this is to work.
    tracked_files: dict             # Dict mapping tracked file names to current hashes.
    max_tokens: int                 # Max tokens for any completion
    hash_dir: str                   # Directory with ...
    weak_model: Model               # Weak model
    strong_model: Model             # Strong model
    messages: Messages
    console_log: list

    def track_file(self, path):
        return replace(state, tracked_files=self.tracked_files.add(path))

    def append_text(self, role, text):
        messages = self.messages.append_text(role, text)
        return replace(self, messages=messages)

    def append_block(self, role, block):
        messages = self.messages.append_block(role, block)
        return replace(self, messages=messages)

    def abs_path(self, rel_path):
        return os.path.join(self.project_dir, rel_path)

    def append_state_to_messages(self):
        self.messages.assert_ready_for_user_input()
        tracked_file_string = '\n'.join([*self.tracked_files.keys()])

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
        return self.messages.append_text('user', result)

    def assistant_api_call(self):
        self.messages.assert_ready_for_assistant()
        return self.strong_model.response(self.system_message, self.append_state_to_messages(), tools=tools_internal)

    def track_file_write(self, paths):
        """
        Should be called after you write one or more files.
        """
        assert isinstance(paths, list)
        list_tracked_files = set(self.tracked_files.keys()).intersection(paths)
        tracked_files = update_hashes(self.hash_dir, tracked_file_list)
        return replace(self, tracked_files=tracked_files)

    def update_hashes(self):
        """
        Should be called just before the assistant, so that you can restore the state to just before the assistant messed stuff up.
        If the user messes stuff up, that's on them...
        """
        tracked_files = update_hashes(self.hash_dir, list(self.tracked_files.keys()))

    def print(self, string):
        print(string)
        return replace(self, console_log=[*self.console_log, string])

    def print_User(self):
        return self.print(color.BOLD+"\nUser:"+color.RESET)

    def print_Assistant(self):
        return self.print(color.BOLD+"\nAssistant:"+color.RESET)

    def print_system(self, string):
        return self.print(color.GREEN+string+color.RESET)

    def print_assistant(self, string):
        return self.print(color.BLUE+string+color.RESET)

    def print_code(self, string):
        return self.print(color.DARKGREY+string+color.RESET)

    def print_internal_error(self, string):
        return self.print(color.RED+string+color.RESET)

    def input_user(self):
        return self.input(color.PURPLE, color.RESET)

    def input(self, start, end):
        user_string = input(start).strip()
        print(end, end='')
        full_string = start+user_string+end

        return replace(self, console_log=[*self.console_log, full_string]), user_string

    def confirm_proceed(self, message="Proceed,"):
        while True:
            self, user_input = self.input(message + "(y/n): ", "")
            if user_input == 'y':
                return self, True
            elif user_input == 'n':
                return self, False
            else:
                self = self.print_system("Invalid input. Please enter 'y' or 'n'.")
                return self.confirm_proceed()



def update_hashes(hash_dir, tracked_file_list):
    """
    Updates the hashed files.  
    """
    tracked_files = {}
    for file_path in tracked_file_list:
        _hash = hash_file(file_path)
        hash_path = os.path.join(hash_dir, _hash)
        
        if not os.path.exists(hash_path):
            shutil.copy(file_path, hash_path)
        tracked_files[file_path] = _hash
    return tracked_files

def initialize_state():
    #Set up tracked files
    git_ls_files = subprocess.run('git ls-files', shell=True, capture_output=True, text=True)
    if git_ls_files.returncode == 0:
        #Use git's tracked files if git exists, and we are in a pre-existing repo.
        tracked_file_list = git_ls_files.stdout.strip().split('\n')
    else:
        #Use git's tracked files if git exists, and we are in a pre-existing repo.
        raise NotImplementedError()

    #### Set up hash files
    hash_dir = config['hash_dir']
    #Make a hash directory if it doesn't exist
    if not os.path.exists(hash_dir):
        os.makedirs(hash_dir, exist_ok=False)

    #Hash all tracked files if they don't already exist.
    tracked_files = update_hashes(hash_dir, tracked_file_list)

    #Remove all hashed files that aren't referenced
    for _hash in os.listdir(hash_dir):
        if _hash not in tracked_files:
            os.remove(os.path.join(hash_dir, _hash))

    return State(
        system_message = system_message,
        project_dir = os.getcwd(),
        max_tokens = config["max_tokens"],
        hash_dir = hash_dir,
        tracked_files = tracked_files,
        weak_model = Model(openai_client, 'gpt-4o-mini'),
        #strong_model = Model(anthropic_client, 'claude-3-5-sonnet-20240620')
        strong_model = Model(anthropic_client, 'claude-3-haiku-20240307'),
        messages = Messages([]),
        console_log = [],
    )
