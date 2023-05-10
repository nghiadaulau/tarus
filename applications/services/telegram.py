from applications.commons.log_lib import trace_func
from applications.commons.request_base import RequestFetch
from django.conf import settings


class MessageFrom(object):
    def __init__(self, **kwargs):
        self.id = str(kwargs.get("id", ""))
        self.first_name = str(kwargs.get("first_name", ""))
        self.is_bot = kwargs.get("is_bot", False)
        self.username = kwargs.get("username", None)
        self.title = kwargs.get("title", "")


class Chat(object):
    def __init__(self, **kwargs):
        self.chat_id = str(kwargs.get("id", ""))
        self.title = str(kwargs.get("title", ""))
        self.first_name = str(kwargs.get("first_name", ""))
        self.is_bot = kwargs.get("is_bot", False)
        self.type = str(kwargs.get("type", ""))


class TelegramPrivateMessage(object):
    def __init__(self, **kwargs):
        self.message_id = int(kwargs.get("message_id", 0))
        self.chat = Chat(**kwargs.get("chat", {}))
        self.message_from = MessageFrom(**kwargs.get("from", {}))
        self.message = kwargs.get("text", "")
        self.group_chat_created = kwargs.get("group_chat_created", False)
        self.new_chat_member = kwargs.get("new_chat_member", {})
        self.entities = kwargs.get("entities", [])

    @property
    def is_bot_command(self):
        for i in self.entities:
            if i.get("type") == "bot_command":
                return True


class ChannelPost(object):
    def __init__(self, **kwargs):
        self.sender_chat = Chat(**kwargs.get("chat", {}))
        self.message_from = MessageFrom(**kwargs.get("sender_chat", {}))
        self.message = kwargs.get("text", "")


class Telegram:
    request = RequestFetch(protocol="https", host_name=f"api.telegram.org/bot{settings.BOT_TOKEN}",
                           service_name="Telegram")

    @classmethod
    @trace_func()
    def send_message(cls, chat_id, message, **kwargs):
        uri = "sendMessage"
        payload = {
            'chat_id': int(chat_id),
            'text': message,
            "parse_mode": "MarkdownV2"
        }
        return cls.request.fetch(uri=uri, body=payload, **kwargs)

    @classmethod
    @trace_func()
    def delete_message(cls, chat_id, message_id, **kwargs):
        uri = "deleteMessage"
        payload = {
            "chat_id": int(chat_id),
            "message_id": int(message_id)
        }
        return cls.request.fetch(uri=uri, body=payload, **kwargs)

    @classmethod
    @trace_func()
    def get_member_count(cls, chat_id, **kwargs):
        uri = "getChatMemberCount"
        payload = {
            "chat_id": int(chat_id),
        }
        return cls.request.fetch(uri=uri, body=payload, **kwargs)

    @classmethod
    @trace_func()
    def get_member(cls, chat_id, user_id, **kwargs):
        uri = "getChatMember"
        payload = {
            "chat_id": int(chat_id),
            "user_id": int(user_id)
        }
        return cls.request.fetch(uri=uri, body=payload, **kwargs)
