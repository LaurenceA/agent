import openai
import anthropic

from .utils import is_messages

_openai_client = openai.OpenAI()
_anthropic_client = anthropic.Anthropic()

class Client:
    pass

class OpenAIClient(Client):
    def tools(self, tools):
        result = []
        for toolname, tooldef in tools.items():
            result.append({
                "type" : "function",
                "function" : {
                    "name" : toolname,
                    "description" : tooldef["description"],
                    "parameters" : tooldef["input_schema"],
                    "additional_parameter" : False,
                }
            })
        return result

    def response(self, model, system_message, messages, cache, **kwargs):
        #Ignores the cache argument.
        if 'tools' in kwargs:
            kwargs['tools'] = self.tools(kwargs['tools'])

        system_message = {
            "role" : "system",
            "content" : system_message
        }
        messages = [system_message, *messages]
        response = _openai_client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )
        return response

    def response_to_text(self, response):
        assert 1==len(response.choices)
        return response.choices[0].message.content

class AnthropicClient(Client):
    def tools(self, tools):
        result = []
        for toolname, tooldef in tools.items():
            result.append({
                "name" : toolname,
                "description": tooldef["description"],
                "input_schema": tooldef["input_schema"],
            })
        return result

    def response(self, model, system_message, messages, cache, **kwargs):
        is_messages(messages)

        if 'tools' in kwargs:
            kwargs['tools'] = self.tools(kwargs['tools'])

        if cache:
            #Uses caching.  So it starts by appending cache_control to the previous user messages.
            messages = [*messages]
            if 1 <= len(messages):
                assert messages[-1]["role"] == "user"
                messages[-1]               = {**messages[-1]}
                messages[-1]["content"]    = [ *messages[-1]["content"]]
                messages[-1]["content"][0] = {**messages[-1]["content"][0], "cache_control" : {"type": "ephemeral"}}

            if 3 <= len(messages):
                messages[-3]               = {**messages[-3]}
                messages[-3]["content"]    = [ *messages[-3]["content"]]
                messages[-3]["content"][0] = {**messages[-3]["content"][0], "cache_control" : {"type": "ephemeral"}}

        funcs = {
            True: _anthropic_client.beta.prompt_caching.messages.create,
            False: _anthropic_client.messages.create,
        }

        response = funcs[cache](
            model=model,
            system=system_message,
            messages = messages,
            max_tokens = 4096,
            **kwargs,
        )
        return response

    def response_to_text(self, response):
        assert 1 == len(response.content)
        return response.content[0].text

openai_client = OpenAIClient()
anthropic_client = AnthropicClient()

class Model:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def response(self, system_message, messages, cache=True, **kwargs):
        return self.client.response(self.model, system_message, messages, cache, **kwargs)

    def response_text(self, system_message, messages, cache=True, **kwargs):
        response = self.response(system_message, messages, cache=cache, **kwargs)
        return self.client.response_to_text(response)
