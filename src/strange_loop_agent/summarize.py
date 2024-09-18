import re
pattern = r'^\((\d+)-(\d+)\) (.*?)$\n(.*?)$'

system_message = "You are a helpful assistant."

instruction = """Take the following code file and summarize it.  For each section you pick out, start your description with a line in the following format:
(<start_line>-<end_line>) <section_name>
<description>

For functions, make sure you describe the arguments and their types.
The file is:

"""

previous_summary_instruction = """
Here is a summary written for the previous version of the file.  You may need to update the line numbers.  You should just copy <section_name> and <description> if the summary of the previous version of the file is still accurate.  If the file has changed so much that the previous summary isn't accurate, then you should change it.

The previous summary is:

"""


def summarize(state, path, previous_summary=None):
    with open(state.abs_path(path), 'r') as file:
        lines = file.readlines()

    lines_with_nums = []
    for i in range(len(lines)):
        lines_with_nums.append(f'{i}:{lines[i]}')

    file_with_line_nos = '\n'.join(lines_with_nums)
    prompt = instruction + file_with_line_nos
    if previous_summary:
        prompt = prompt + previous_summary_instruction + previous_summary

    message = [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}]

    response = state.weak_model.response_text(system_message, message)

    print(response)

    return re.findall(pattern, response, re.MULTILINE)
