import re
import json
from pydantic import BaseModel
from typing import List

from .models import Model, openai_client, anthropic_client
model = Model(openai_client, 'gpt-4o-mini')

system_message = "You are a helpful assistant."
instruction = "Identify the line numbers in this code file that correspond to comments such as `#... (previous code unchanged)` or `#... (unchanged code)` that indicate unchanged code from the original file is to be included there.  Also identify line numbers corresponding to comments indicating that there is unimplmented functionality for the user to include, such as `implement x here`"

class Lines(BaseModel):
    unchanged_comment_line_numbers: List[int]
    to_be_implemented_comment_line_numbers: List[int]

def check_update(update: str):
    update_lines = update.split('\n')
    update_with_line_numbers = '\n'.join([f"{i}: {line}" for (i, line) in enumerate(update_lines)])

    prompt = f"{instruction}\n\nHere's the file:\n{update_with_line_numbers}"

    response = json.loads(model.single_shot_response(system_message, prompt, response_format=Lines))

    breakpoint()

    return response['unchanged_comment_line_numbers'], response['to_be_implemented_comment_line_numbers']

## In-line test
#if __name__ == "__main__":
#    # Test case
#    test_write_text = """
## This is unchanged
## This is also unchanged
#
#def some_function():
#    # TODO: Implement this functionality
#    pass
#
## TODO: Implement another functionality
#
## This is also unchanged
#"""
#
#    print("Running test with the following input:")
#    print(test_write_text)
#    print("\nCalling check_write function...")
#
#    unchanged, to_be_implemented = check_write(test_write_text)
#
#    print("\nTest Results:")
#    print(f"Unchanged comment line numbers: {unchanged}")
#    print(f"To-be-implemented comment line numbers: {to_be_implemented}")
#
#    # Basic assertions
#    assert len(unchanged) > 0, "Expected at least one unchanged comment line"
#    assert len(to_be_implemented) > 0, "Expected at least one to-be-implemented comment line"
#    assert 1 in unchanged, "Expected first line to be identified as unchanged"
#    assert 2 in unchanged, "Expected second line to be identified as unchanged"
#    assert 10 in unchanged, "Expected last line to be identified as unchanged"
#    assert any(line in to_be_implemented for line in [4, 5]), "Expected 'TODO: Implement this functionality' to be identified as to-be-implemented"
#    assert 8 in to_be_implemented, "Expected 'TODO: Implement another functionality' to be identified as to-be-implemented"
#
#    print("\nAll assertions passed successfully!")
