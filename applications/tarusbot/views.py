import json

import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from applications.services.telegram import *
import openai
import datetime


def escape_message(msg: str) -> str:
    special_chars = '_*[]()~`>#+-=|{}.!'
    pre_code_chars = '`\\'
    link_emoji_chars = ')\\'
    valid_emoji_chars = set(range(1, 127)) - set(map(ord, special_chars)) - set(map(ord, pre_code_chars))
    valid_emoji_chars.update([13, 10])  # carriage return and line feed
    result = []
    i = 0
    while i < len(msg):
        c = msg[i]
        if c == '\\':
            if i + 1 < len(msg) and ord(msg[i + 1]) in valid_emoji_chars:
                result.append(msg[i + 1])
                i += 1
            else:
                result.append('\\\\')
        elif c in pre_code_chars:
            result.append('\\' + c)
        elif c in link_emoji_chars and '(...)' in ''.join(result):
            result.append('\\' + c)
        elif c in special_chars:
            result.append('\\' + c)
        elif c == '_' and i + 2 < len(msg) and msg[i:i + 3] == '___':
            result.append('__\r')
            i += 2
        else:
            result.append(c)
        i += 1
    return ''.join(result)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def index(request):
    data = request.data
    if data.get("message"):
        message = TelegramPrivateMessage(**data.get("message", {}))
        if not message:
            return Response({"result": "ok"}, status=200)
        if message.new_chat_member:
            if str(message.new_chat_member.get("id")) == settings.BOT_ID:
                for chat_id, _ in settings.FRIDAY.get("boss", {}).items():
                    mload = f"Hey boss, I was were to Group {message.chat.title}"
                    Telegram.send_message(chat_id=chat_id, message=mload, parse_mode='MarkdownV2')
        elif message.chat.chat_id == "5117860309":
            if message.is_bot_command and message.message == "/get_config":
                mload = escape_message(f"Present config is {json.dumps(settings.FRIDAY)}")
                a = Telegram.send_message(message.chat.chat_id, mload)

            if message.is_bot_command and message.message.startswith("/update_config"):
                try:
                    data = message.message.split("/update_config")[-1].strip(" ")
                    data = json.loads(data)
                    settings.FRIDAY = data
                    with open(f"{settings.BASE_DIR}/config.json", "w") as f:
                        json.dump(data, f, indent=6)
                except Exception as e:
                    Telegram.send_message(message.chat.chat_id, f"Update config error wit {e}")
                else:
                    Telegram.send_message(message.chat.chat_id, f"Success update {settings.FRIDAY}")
        elif settings.FRIDAY.get("group", {}).get(str(message.chat.chat_id)):
            Telegram.send_message(message.chat.chat_id, f"Recogidasdknasjkdnas")
        if message.message.casefold().__contains__("sex"):
            Telegram.delete_message(chat_id=message.chat.chat_id,
                                    message_id=message.message_id)
            Telegram.send_message(chat_id=message.chat.chat_id,
                                  message=escape_message("Ê ê, viết bậy mày. Tao xóa nha."))
            return Response({"result": "ok"}, status=200)
        if message.message.__contains__("@tarus"):
            Telegram.send_message(5117860309, escape_message(str(data)))
            if message.message_from.username == "thienduong13":
                Telegram.send_message(chat_id=message.chat.chat_id,
                                      message=escape_message("Hello boss. What advice do you have?"))
            else:
                Telegram.send_message(chat_id=message.chat.chat_id, message="Hi there, what can I do for you?")
        if message.chat.type.__contains__("private"):
            Telegram.send_message(5117860309, escape_message(str(data)))
            if message.message_from.username == "thienduong13":
                Telegram.send_message(chat_id=message.chat.chat_id,
                                      message=escape_message("Hello boss. What advice do you have?"))
            else:
                Telegram.send_message(chat_id=message.chat.chat_id, message="Hi there, what can I do for you?")
    return Response({"result": "ok"}, status=200)
