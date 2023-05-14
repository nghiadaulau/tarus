import json

import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

from applications.services.telegram import *
from applications.commons.utils import *
import openai
import datetime


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def index(request):
    data = request.data
    if data.get("message"):
        message = TelegramPrivateMessage(**data.get("message", {}))
        if not message:
            return Response({"result": "ok"}, status=200)
        if message.is_bot_command:
            if message.message.startswith("/information"):
                Telegram.get_information_boss(message.chat.chat_id)
                return Response({"result": "ok"}, status=200)
            if message.message.startswith("/bug"):
                Telegram.send_message(chat_id=message.chat.chat_id,
                                      message=escape_message("@thienduong13 Có bug kìa bạn ơi. Fix bug nào."))
                bug = message.message.replace("/bug", "")
                Telegram.send_message(chat_id=message.chat.chat_id, message=escape_message(f"Information of bug: {bug}"))
        timing = datetime.datetime.now() + datetime.timedelta(hours=7)
        if validate_message(message, timing):
            Telegram.send_message(5117860309, escape_message(str(data)))
            return Response({"result": "ok"}, status=200)
        if message.new_chat_member:
            if str(message.new_chat_member.get("id")) == settings.BOT_ID:
                for chat_id, _ in settings.FRIDAY.get("boss", {}).items():
                    mload = f"Hey boss, I was were to Group {message.chat.title}"
                    Telegram.send_message(chat_id=chat_id, message=mload, parse_mode='MarkdownV2')
        elif message.chat.chat_id == "5117860309":
            if message.is_bot_command and message.message == "/get_config":
                mload = escape_message(f"Present config is {json.dumps(settings.FRIDAY)}")
                Telegram.send_message(message.chat.chat_id, mload)

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
        if message.message.__contains__("@tarus"):
            Telegram.send_message(5117860309, escape_message(str(data)))
            if message.message_from.username == "thienduong13":
                Telegram.send_message(chat_id=message.chat.chat_id,
                                      message=escape_message("Hello boss. What advice do you have?"))
            else:
                Telegram.send_message(chat_id=message.chat.chat_id, message=escape_message("Hi there, what can I do for you? Sorry for the inconvenience, I am currently only born to serve certain tasks."))
        if message.chat.type.__contains__("private"):
            Telegram.send_message(5117860309, escape_message(str(data)))
            if message.message_from.username == "thienduong13":
                Telegram.send_message(chat_id=message.chat.chat_id,
                                      message=escape_message("Hello boss. What advice do you have?"))
            else:
                Telegram.send_message(chat_id=message.chat.chat_id, message=escape_message("Hi there, what can I do for you? Sorry for the inconvenience, I am currently only born to serve certain tasks."))
    return Response({"result": "ok"}, status=200)