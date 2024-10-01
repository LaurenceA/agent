import re
import json
from pydantic import BaseModel
from typing import List

from .models import Model, openai_client, anthropic_client
model = Model(openai_client, 'gpt-4o-mini')

system_message = "You are a helpful assistant."

class Section(BaseModel):
    section_number: int
    start_line: int
    end_line: int
class Sections(BaseModel):
    sections: List[Section]

def smart_merge(original, update):
    #Ensures that you include a block from the last unchanged comment to the end
    #unchanged_comment_line_numbers.append(len(update_lines)) 
    #update_lines = update.split('\n')
    #last_comment_line = 0
    #update_sections = []
    #for unchanged_comment_line_number in unchanged_comment_line_numbers:
    #    _update = '\n'.join(update_lines[last_comment_line:unchanged_comment_line_number])
    #    if _update.strip(): #Don't include if nothing present.
    #        update_sections.append(_update)

    #Find all the comments that look like #... (something unchanged)
    #that are left by Claude when it doesn't change something.
    splits = [*re.finditer(r'(\n*\s*#\s*\.{3}\s*\(.*?unchanged.*?\)\s*\n*)', update, flags=re.MULTILINE | re.IGNORECASE)]

    #Gather the updated text, i.e. that between the unchanged comments.
    start_index = 0
    update_sections = []
    update_sections_for_prompt = []
    for i, split in enumerate(splits):
        _update = update[start_index:split.start()]
        if _update.strip(): #Don't include if nothing present.
            update_sections.append(_update)
        start_index = split.end()

    #Include a final section (after all the split comments)
    _update = update[start_index:]
    if _update.strip():
        update_sections.append(_update)

    #Create a prompt for GPT-4o mini, telling it to give us the line numbers in the
    #original doc for the updated sections.

    update_sections_for_prompt = '\n\n\n\n\n'.join([f'Section {i}:\n{update_}' for (i, update_) in enumerate(update_sections)])

    original_split = original.split('\n')
    original_with_line_numbers = '\n'.join([f"{i}: {line}" for (i, line) in enumerate(original_split)])

    prompt = f"Identify the start and end line numbers for the following sections:\n{update_sections_for_prompt} in the following file:\n{original_with_line_numbers}"

    response = json.loads(model.single_shot_response(system_message, prompt, response_format=Sections))

    #Extract the result in a dict mapping section number to start and end line numbers.
    line_num_dict = {}
    for section in response["sections"]:
        line_num_dict[section["section_number"]] = (section["start_line"], section["end_line"]+1)

    #Tests for this dict (flakey, as depends on LLM success).
    #Test we have line numbers for all sections.
    assert frozenset(range(len(update_sections))) == frozenset(line_num_dict.keys())
    #Convert line nums to list
    line_nums = [line_num_dict[i] for i in range(len(update_sections))]

    #Test line numbers are non-overlapping.
    prev_end_line = -1
    for start_line, end_line in line_nums:
        assert prev_end_line < start_line 
        prev_end_line = end_line

    #Now extract sections to keep, based on the line numbers for the updated sections.
    keep_sections = []
    prev_end_line = 0
    for start_line, end_line in line_nums:
        keep_sections.append('\n'.join(original_split[prev_end_line:start_line]))
        prev_end_line = end_line
    keep_sections.append('\n'.join(original_split[prev_end_line:]))

    #And combine the updated and orignal sections.
    result = []
    for i in range(len(update_sections)):
        result.append(keep_sections[i])
        result.append(update_sections[i])
    result.append(keep_sections[len(update_sections)])

    return '\n'.join(result)
