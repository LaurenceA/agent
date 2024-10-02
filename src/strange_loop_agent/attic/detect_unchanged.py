import concurrent.futures
import json
from pydantic import BaseModel

from .models import Model, openai_client, anthropic_client
model = Model(openai_client, 'gpt-4o-mini')

from .treesitter_comments import extract_comments

system_message = "You are a helpful assistant"

class Bool(BaseModel):
    bool: bool

def unchanged_comments(code: str):
    _comments = extract_comments(code)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        is_unchanged = list(executor.map(unchanged_comment, _comments))

    return [comment for (comment, unchanged) in zip(_comments, is_unchanged) if unchanged]
        

def unchanged_comment(comment):
    prompt = f"""
Does the following code indicate that there is unchanged code that goes here?
Examples which would indicate unchanged code:
Rest of code is unchanged.
# Unchanged code here.
% ... (previous code unchanged).
Examples which wouldn't indicate unchanged code:
# to be implemented
% this function does xyz
The comment is:
{comment.text}
Answer True for yes and False for no."""
    return json.loads(model.single_shot_response(system_message, prompt, response_format=Bool))['bool']

