import os
import json
import subprocess
import shutil
from pathlib import Path

from dataclasses import dataclass, replace
from typing import Optional

from .models import Model, openai_client, anthropic_client
from .tools import tools_internal
from .utils import hash_file
from .system_message import system_message
from .summary import SummaryDict, add_summaries_from_token_sources, update_delete_summaries
from .FullPath import full_path

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
    max_tokens: int                 # Max tokens for any completion
    hash_dir: str                   # Directory with ...
    weak_model: Model               # Weak model
    strong_model: Model             # Strong model
    messages: Messages
    summaries: SummaryDict
    console_log: list

    def append_text(self, role, text):
        messages = self.messages.append_text(role, text)
        return replace(self, messages=messages)

    def append_block(self, role, block):
        messages = self.messages.append_block(role, block)
        return replace(self, messages=messages)

    def append_state_to_messages(self):
        """
        Can be used to insert temporary info (i.e. that won't be cached) into messages.
        Currently unused as its probably best to use the cache properly.
        """
        self.messages.assert_ready_for_user_input()
        return self.messages#.append_text('user', result)

    def assistant_api_call(self):
        self.messages.assert_ready_for_assistant()
        return self.strong_model.response(self.system_message, self.append_state_to_messages(), tools=tools_internal)

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

    def print_initial_message(self):
        return self.print(color.RED+'Welcome to the agent'+color.RESET)

    def input_user(self):
        return self.input(color.PURPLE, color.RESET)

    def input(self, start, end):
        user_string = input(start).strip()
        print(end, end='')
        full_string = start+user_string+end

        return replace(self, console_log=[*self.console_log, full_string]), user_string

    def confirm_proceed(self, message="Proceed,"):
        while True:
            self, user_input = self.input(message + " (y/n): ", "")
            if user_input == 'y':
                return self, True
            elif user_input == 'n':
                return self, False
            else:
                self = self.print_system("Invalid input. Please enter 'y' or 'n'.")
                return self.confirm_proceed()

    def add_summaries(self, paths):
        sources = [(full_path(path), 10000) for path in paths]
        updated_summaries, messages = add_summaries_from_token_sources(self.summaries, sources)
        self = replace(self, summaries = updated_summaries)

        return self, '\n\n\n'.join(messages.values())

    def update_summaries(self):
        updated_summaries, messages = update_delete_summaries(self.summaries)
        self = replace(self, summaries = updated_summaries)

        return self, '\n\n\n'.join(messages.values())


def initialize_state():
    #### Set up hash files
    hash_dir = Path(config['hash_dir'])
    #Make a hash directory if it doesn't exist
    if not os.path.exists(hash_dir):
        os.makedirs(hash_dir, exist_ok=False)

    #Remove all hashed files that aren't referenced
    for _hash in os.listdir(hash_dir):
        os.remove(os.path.join(hash_dir, _hash))

    return State(
        system_message = system_message,
        max_tokens = config["max_tokens"],
        hash_dir = hash_dir,
        weak_model = Model(openai_client, 'gpt-4o-mini'),
        strong_model = Model(anthropic_client, 'claude-3-5-sonnet-20240620'),
        #strong_model = Model(anthropic_client, 'claude-3-haiku-20240307'),
        messages = Messages([]),
        summaries = {},
        console_log = [],
    )
