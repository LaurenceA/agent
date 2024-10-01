import json
from pydantic import BaseModel

from .models import Model, openai_client, anthropic_client
model = Model(openai_client, 'gpt-4o-mini')

system_message = "You are a helpful assistant"

class Result(BaseModel):
    trying_to_print_file: bool
    trying_to_print_directory: bool
    trying_to_create_empty_file: bool
    trying_to_write: bool
    trying_to_modify: bool

instruction = """
Does the following command look like it is trying to print the contents of a file? An example would be:
cat filename
But commands like grep and find are fine, as they're often used to search.

Alternatively, does the command look like it is trying to print the contents of a directory?  An example would be:
ls -l

Alternatively, does the following command look like it is trying to create a new empty file? An example would be:
touch new_file

Alternatively, does it look like it is trying to write to a file? An example would be:
echo -e '#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}' > hello_world.c

Or does it look like it is trying to edit a file? An example would be:
sed -i '' 'original_line/new_line'

If you don't recognise the command, return False for all of the above.

The command is:
"""
def check_command(command):
    return json.loads(model.single_shot_response(system_message, instruction+command, response_format=Result))
