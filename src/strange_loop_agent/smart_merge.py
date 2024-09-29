import re
import json
from pydantic import BaseModel
from typing import List

from models import Model, openai_client, anthropic_client
from messages import Messages
model = Model(openai_client, 'gpt-4o-mini')

system_message = "You are a helpful assistant."
instruction = "Combine the following original file, with the update to give the full file."

class Section(BaseModel):
    section_number: int
    start_line: int
    end_line: int
class Sections(BaseModel):
    sections: List[Section]

def merge(original, update):
    splits = [*re.finditer(r'(\n*\s*#\s*\.{3}\s*\(.*?unchanged.*?\)\s*\n*)', update, flags=re.MULTILINE | re.IGNORECASE)]
    start_index = 0

    update_sections = []
    update_sections_for_prompt = []
    for i, split in enumerate(splits):
        end_index = split.start()
        update_sections.append(update[start_index:end_index])
        update_sections_for_prompt.append(f'Section {i}:\n{update[start_index:end_index]}')
        start_index = split.end()

    update_sections_for_prompt = '\n\n\n\n\n'.join(update_sections_for_prompt)

    original_split = original.split('\n')
    original_with_line_numbers = '\n'.join([f"{i}: {line}" for (i, line) in enumerate(original_split)])

    prompt = f"Identify the start and end line numbers for the following sections:\n{update_sections_for_prompt} in the following file:\n{original_with_line_numbers}"

    messages = Messages([])
    messages = messages.append_text('user', prompt)
    response = json.loads(model.response_text(system_message, messages, False, response_format=Sections))

    line_num_dict = {}
    for section in response["sections"]:
        line_num_dict[section["section_number"]] = (section["start_line"], section["end_line"]+1)

    #Flaky tests (depends on LLM success)
    #Test we have line numbers for all sections.
    assert frozenset(range(len(splits))) == frozenset(line_num_dict.keys())
    #Convert line nums to list
    line_nums = [line_num_dict[i] for i in range(len(splits))]

    #Test line numbers are non-overlapping.
    prev_end_line = -1
    for start_line, end_line in line_nums:
        assert prev_end_line < start_line 
        prev_end_line = end_line

    keep_sections = []
    prev_end_line = 0
    for start_line, end_line in line_nums:
        keep_sections.append('\n'.join(original_split[prev_end_line:start_line]))
        prev_end_line = end_line
    keep_sections.append('\n'.join(original_split[prev_end_line:]))

    result = []
    for i in range(len(splits)):
        result.append(keep_sections[i])
        result.append(update_sections[i])
    result.append(keep_sections[len(splits)])

    return '\n'.join(result)

#def merge(original, update):
#    prompt = f"Combine the following original file, with the update.  Respond with ONLY the new file.  Respond ONLY with text from the original file, or the update. Keep all comments and formatting exactly the same. Original file:\n{original} \n\n\n\n\nUpdate file:\n{update}"
#    messages = Messages([])
#    messages = messages.append_text('user', prompt)
#    return model.response_text(system_message, messages, False)

with open("summary.py", 'r') as file:
    original = file.read()

with open("updated_summary.py", 'r') as file:
    update = file.read()

merged = merge(original, update)

with open("merged_summary.py", 'w') as file:
    file.write(merged)
