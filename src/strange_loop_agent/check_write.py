
import re
import json
from pydantic import BaseModel
from typing import List

from models import Model, openai_client, anthropic_client
from messages import Messages
model = Model(openai_client, 'gpt-4o-mini')

system_message = "You are a helpful assistant."
instruction = "Identify the line numbers in this code file that correspond to unchanged code in unchanged_comment_line_numbers, and to functionality that is to be implemented in to_be_implemented_comment_line_numbers."

class Lines(BaseModel):
    unchanged_comment_line_numbers: List[int]
    to_be_implemented_comment_line_numbers: List[int]


def check_write(write_text: str):
    write_text_split = write_text.split('\n')
    original_with_line_numbers = '\n'.join([f"{i}: {line}" for (i, line) in enumerate(write_text_split)])

    prompt = f"{instruction}\n\nHere's the file:\n{original_with_line_numbers}"

    response = json.loads(model.single_shot_response(system_message, prompt, response_format=Lines))

    return response['unchanged_comment_line_numbers'], response['to_be_implemented_comment_line_numbers']
