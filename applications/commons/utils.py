import base64
import copy
import datetime
import json
import random
import string
import time

import phonenumbers
from django.apps import apps
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.core.cache import cache
from unidecode import unidecode
from applications.services.telegram import *
from rest_framework.response import Response


class CustomObject:
    custom_object = True

    def to_json(self):
        res = copy.deepcopy(self.__dict__)
        for key, value in res.items():
            if hasattr(value, "custom_object") and value.custom_object and hasattr(value, "__dict__"):
                child = copy.deepcopy(value.__dict__)
                res.update({key: child})
        return res


def json_load(_str):
    try:
        return json.loads(_str)
    except Exception as e:
        return None


def str2list(_str: str, key=","):
    try:
        return _str.split(key)
    except Exception as e:
        return None


class CacheFunc(object):
    def __init__(self, _patten_key="", value_key=None, timeout=0, _default=None, cache_key=""):
        self._patten_key = _patten_key
        self.value_key = value_key
        self.timeout = timeout
        self._default = _default if _default else {}
        self.cache_key = self.generate_cache_key() if not cache_key else cache_key

    def generate_cache_key(self):
        cache_key = self._patten_key.format(**self.value_key)
        return cache_key

    def set_cache(self, data, timeout=None):
        try:
            if not timeout:
                timeout = self.timeout
            cache.set(self.cache_key, data, timeout)
        except Exception as e:
            print(e)
            return False
        return True

    def clear_cache(self):
        try:
            cache.delete(self.cache_key)
        except Exception as e:
            print(e)
            return False
        return True

    def get_cache(self, _default=None):
        if not _default:
            _default = self._default
        data = _default
        try:
            data = cache.get(self.cache_key, _default)
        except Exception as e:
            print(e)
        return data


def random_string(str_len, type_ran="all"):
    letters = ""
    if type_ran == "all" or type_ran == "ascii_uppercase":
        letters += string.ascii_uppercase
    if type_ran == "all" or type_ran == "digits":
        letters += string.digits
    return "".join(random.choices(letters, k=str_len))


def create_permission_app(my_app_name):
    create_permissions(apps.get_app_config(my_app_name))


def phone_validate(phone_number, country_code=84):
    error_message = 'The phone number has incorrect format'
    res = {
        "result": False,
        "message": error_message,
        "phone": ""
    }
    if phone_number == '7733120162':
        country_code = 1
    try:
        is_mobile_number = int(phone_number) > 0
        region = phonenumbers.COUNTRY_CODE_TO_REGION_CODE.get(int(country_code))
    except Exception as e:
        res['message'] = f"{res['message']} - With {e}"
    else:
        if is_mobile_number and region:
            try:
                phone = phonenumbers.parse(phone_number, region[0])
            except Exception as e:
                res['message'] = f"{res['message']} - With {e}"
            else:
                if str(phone.country_code) not in settings.PHONE_NUMBER_DEFAULT_CODE:
                    res['message'] = f"{res['message']} - With The country code of this phone number is not supported."
                phone = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
                res['result'] = True
                res['message'] = 'OK'
                res['phone'] = phone
    return res


def remove_accent(s):
    return unidecode(s).lower()


def upper_case_name(s):
    name = []
    for i in str(s).split(" "):
        name.append(str(i).capitalize())
    return " ".join(name)


def datetime2timestamp(d):
    return time.mktime(d.timetuple())


def timestamp2datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)


def base64decode2binary(base64_str):
    return base64.b64decode(base64_str)


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


def validate_message(message):
    if message.casefold().__contains__("sex"):
        Telegram.delete_message(chat_id=message.chat.chat_id,
                                message_id=message.message_id)
        Telegram.send_message(chat_id=message.chat.chat_id,
                              message=escape_message("Ê ê, viết bậy mày. Tao xóa nha."))
        return True
    return False
