from applications.services.telegram import *
from applications.commons.utils import *
import subprocess


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


def validate_message(message, timing):
    validate = False
    if message.message.casefold().__contains__("sex"):
        Telegram.delete_message(chat_id=message.chat.chat_id,
                                message_id=message.message_id)
        Telegram.send_message(chat_id=message.chat.chat_id,
                              message=escape_message("Ê ê, viết bậy mày. Tao xóa nha."))
        validate = True
    if 2 <= timing.hour < 5:
        username = f"@{message.message_from.username}" if message.message_from.username else ''
        Telegram.send_message(chat_id=message.chat.chat_id,
                              message=escape_message(
                                  f"{username} Ngủ thôi trễ rồi {message.message_from.first_name}. Tao block trong chốc lát á nha. Đi ngủ đi sáng mai dậy thấy"))
        Telegram.restrict(chat_id=message.chat.chat_id, user_id=message.message_from.id)
        validate = True
    return validate


MEMBER = {
    "huy": 5344050801,
    "thảo": 5294271027,
    "nam": 5333702189,
    "minh": 5662519208
}


def bot_command(message):
    if message.message.startswith("/information"):
        Telegram.get_information_boss(message.chat.chat_id)
    elif message.message.startswith("/bug"):
        Telegram.send_message(chat_id=message.chat.chat_id,
                              message=f"[Boss](tg://user?id=5117860309) Hú hú hú bug bug bug")
        bug = message.message.replace("/bug", "")
        Telegram.send_message(chat_id=message.chat.chat_id, message=escape_message(f"Information of bug: {bug}"))
    elif message.message.startswith("/spam"):
        command = message.message.split(" ")
        if len(command) == 2:
            for _ in range(10):
                Telegram.send_message(chat_id=message.chat.chat_id,
                                      message=f"[{command[1]}](tg://user?id={MEMBER.get(command[1].lower())}) Hú hú hú bug bug bug")
        else:
            Telegram.send_message(chat_id=message.chat.chat_id,
                                  message="Format is not valid")

    else:
        Telegram.send_message(chat_id=message.chat.chat_id, message=escape_message(
            "Sorry, Your command sent is not supported. Please contact the @thienduong13 to update with new features."))
