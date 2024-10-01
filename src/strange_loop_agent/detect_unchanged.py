import concurrent.futures

from .models import Model, openai_client, anthropic_client
model = Model(openai_client, 'gpt-4o-mini')

from .treesitter_comments import comments

system_message = "You are a helpful assistant"

class Bool(BaseModel):
    bool: bool

def unchanged_unimplmented_comments(code: str):
    _comments = comments(code)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        is_unchanged = list(executor.map(_comment, iterable))

    breakpoint()

    return [comment for (comment, unchanged) in zip(comments, is_unchanged) if unchanged]
        

def unchanged_comment(comment):
    prompt = """
Does the following code indicate that there is unchanged code that goes here?
Examples which would indicate unchanged code:
# ... (rest of code unchanged).
Rest of code is unchanged.
# Unchanged code here.
... (previous code unchanged).
Examples which wouldn't indicate unchanged code:
# to be implemented
# this function does xyz
The comment is:
{comment.text}
Answer True for yes and False for no."""
    return json.loads(model.single_shot_response(system_message, prompt, response_format=Bool)).bool
