import openai
import anthropic

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
        messages = [system_message, *messages.dump()]
 
        response = _openai_client.beta.chat.completions.parse(#) chat.completions.create(
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
        if 'tools' in kwargs:
            kwargs['tools'] = self.tools(kwargs['tools'])
 
        dumped_messages = messages.dump()

        if cache:
            if 1 <= len(dumped_messages):
                assert dumped_messages[-1]['role'] == 'user'
                dumped_messages[-1]['content'][0]['cache_control'] = {"type": "ephemeral"}

            if 3 <= len(dumped_messages):
                assert dumped_messages[-3]['role'] == 'user'
                dumped_messages[-3]['content'][0]['cache_control'] = {"type": "ephemeral"}
        print(dumped_messages)

        funcs = {
            True: _anthropic_client.beta.prompt_caching.messages.create,
            False: _anthropic_client.messages.create,
        }

        response = funcs[cache](
            model=model,
            system=system_message,
            messages = messages.dump(),
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
