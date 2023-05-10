from applications.commons.log_lib import trace_func
from applications.commons.request_base import RequestFetch
from django.conf import settings


class MessageFromChatGPT(object):
    def __init__(self, **kwargs):
        self.content = str(kwargs.get("message").get("content"))
        self.role = str(kwargs.get("message").get("role"))


class ChatGPT:
    request = RequestFetch(protocol="https", host_name="api.openai.com", service_name="ChatGPT")

    @classmethod
    @trace_func()
    def send(cls, message, **kwargs):
        uri = "/v1/chat/completions"
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": message
                }
            ]
        }
        header = {
            "Authorization": f"Bearer {settings.CHATGPT}"
        }
        return cls.request.fetch(uri=uri, body=payload, header=header, **kwargs)
