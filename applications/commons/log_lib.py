import base64
import datetime
import hashlib
import json
import logging
import sys
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

from applications.commons.exception import APIBreakException
from applications.commons.utils import CacheFunc


class ClientAuthentication(object):
    PEGASUS = {}
    DEMETER = {}
    HERMES = {}
    ComputerVisionVietNam = {}
    FE = {}
    SES = {}
    OLYMPUS = {}

    @classmethod
    def get_hexdigits(cls, _string: str):
        return hashlib.md5(_string.encode()).hexdigest()

    @classmethod
    def authentication(cls, authentication_key):

        try:
            authentication_key = base64.b64decode(authentication_key).decode("ascii")
            client_id = authentication_key.split(":")[0]
            hash_password = authentication_key.split(":")[-1]
            if not hasattr(settings, "API_AUTHENTICATION"):
                print("Must be set API_AUTHENTICATION in settings")
                return "", False
            if not isinstance(settings.API_AUTHENTICATION, dict):
                print("API_AUTHENTICATION must be dictionary")
                return "", False
            print(client_id)
            password = settings.API_AUTHENTICATION.get(client_id, {}).get("password")
            if hash_password == cls.get_hexdigits(password):
                return client_id, True
        except Exception as e:
            print(f"Api authentication failed with {e}")
            return "", False

    @classmethod
    def make_authentication(cls, client_id, password):
        hash_pass = hashlib.md5(password.encode())
        id_pass = '{}:{}'.format(client_id, hash_pass.hexdigest())
        id_pass_enc = id_pass.encode("ascii")
        return '{}'.format(base64.b64encode(id_pass_enc).decode("ascii"))

    @classmethod
    def make_basic_authentication(cls, client_id, password):
        id_pass = '{}:{}'.format(client_id, password)
        return '{}'.format(base64.b64encode(id_pass.encode()).decode("ascii"))

    @classmethod
    def load_service_authentication(cls):
        if hasattr(settings, "SERVICE_AUTHENTICATION") and isinstance(settings.SERVICE_AUTHENTICATION, dict):
            for service_name, data in settings.SERVICE_AUTHENTICATION.items():
                authorization = ""
                if data.get("authentication_type", "") == "hash":
                    authorization = f'Basic {cls.make_authentication(data["client_id"], data["client_password"])}'
                if data.get("authentication_type", "") == "basic":
                    authorization = f'Basic {cls.make_basic_authentication(data["client_id"], data["client_password"])}'
                setattr(cls, service_name, {
                    "host": data["host"],
                    "protocol": data["protocol"],
                    "url": f'{data["protocol"]}://{data["host"]}',
                    "headers": {
                        "Authorization": authorization
                    }
                })


ClientAuthentication.load_service_authentication()


class ConfigVariable:
    @classmethod
    def get_config(cls, key, _default=False):
        cache_func = CacheFunc(cache_key=key)
        return cache_func.get_cache(_default=_default)

    @classmethod
    def set_config(cls, key, value):
        cache_func = CacheFunc(cache_key=key)
        cache_func.set_cache(value, timeout=60 * 60 * 24 * 30 * 365)


class LogMessage(object):

    @staticmethod
    def debug_on():
        ConfigVariable.set_config("log-debug", True)

    @staticmethod
    def debug_off():
        ConfigVariable.get_config("log-debug")

    def __init__(self, logger=None, func_name="", user="", client_id="", trace_id=None, service_name=None):
        self._logger = self.get_logger(logger)
        self.func_name = func_name
        self.user = user
        self.client_id = client_id
        self.tracer = None
        self.span = None
        self.trace_id = uuid.uuid1().hex if not trace_id else trace_id
        self.service_name = service_name if service_name else settings.SERVICE_NAME

    def set_user_log(self, username):
        self.user = username

    @property
    def pub_logger(self):
        return self._logger

    @staticmethod
    def get_logger(logger=None):
        if isinstance(logger, (logging.Logger, logging.RootLogger)):
            return logger
        else:
            return logging.getLogger("" if not logger else logger)

    @staticmethod
    def logs_message(level, message, logger_obj):
        level = level.upper()
        logger_level = {
            'CRITICAL': 50,
            'ERROR': 40,
            'WARNING': 30,
            'INFO': 20,
            'DEBUG': 10,
            'NOTSET': 0
        }
        logger_obj.log(logger_level.get(level), message)

    def log(self, lv, message, func_name="", ):
        log_message = {
            'func_name': self.func_name if not func_name else func_name,
            'message': message,
            'user': self.user,
            "traceback": "trace-id-{}".format(self.trace_id),
            "time": f"{datetime.datetime.now()}"
        }
        # print(log_message)
        self.logs_message(lv, log_message, self._logger)

    def info(self, message, func_name=""):
        self.log("info", message, func_name)

    def error(self, message, func_name=""):
        self.log("error", message, func_name)

    def warning(self, message, func_name=""):
        self.log("warning", message, func_name)

    def debug(self, message, func_name=""):
        if ConfigVariable.get_config("log-debug", _default=False) or settings.DEBUG:
            self.log("info", message, func_name)
        pass

    @classmethod
    def init_log(cls, func_name, logger=None, user="", client_id="", init_span=True, service_name=""):
        if not logger:
            init_service_name = service_name if service_name else settings.SERVICE_NAME
            log_message = cls(func_name=func_name, user=user, service_name=init_service_name)
        elif isinstance(logger, cls):
            user = logger.user
            init_service_name = service_name if service_name else logger.service_name
            log_message = cls(func_name=func_name, logger=logger.pub_logger, user=user, client_id=logger.client_id, trace_id=logger.trace_id, service_name=init_service_name)
        elif isinstance(logger, MixingLog):
            user = logger.default.user
            init_service_name = service_name if service_name else logger.default.service_name
            log_message = cls(func_name=func_name, logger=logger.default.pub_logger, user=user, client_id=logger.client_id, trace_id=logger.default.trace_id, service_name=init_service_name)
        else:
            init_service_name = service_name if service_name else settings.SERVICE_NAME
            log_message = cls(func_name=func_name, logger=logger, user=user, client_id=client_id, service_name=init_service_name)
        return log_message


class MixingLog(object):
    def __init__(self, func_name="", user=None, init_span=True, _parent_logger=None, client_id="", service_name=None):
        self.func_name = func_name
        self.user = user
        self.default = None
        self.client_id = client_id
        self._parent_logger = _parent_logger
        self.span = None
        self.init_span = init_span
        self.service_name = service_name if service_name else settings.SERVICE_NAME
        self.init_log_base_settings()

    @property
    def trace_id(self):
        return self.default.trace_id if self.default else uuid.uuid1().hex

    def set_user_log(self, username):
        self.user = username
        if self.default:
            self.default.set_user_log(username)

    def init_log_base_settings(self):
        if self.init_span:
            if isinstance(self._parent_logger, (LogMessage, MixingLog)):
                self.user = self._parent_logger.user
                self.client_id = self._parent_logger.client_id
        self.default = LogMessage(logger="", func_name=self.func_name, client_id=self.client_id, user=self.user, service_name=self.service_name)
        self.span = self.default.span
        for i in settings.LOGGING["loggers"].keys():
            if i:
                setattr(self, i, LogMessage(logger=i, func_name=self.func_name, user=self.user, client_id=self.client_id, service_name=self.service_name))

    def set_component(self, value):
        return self.default.set_component(value)

    def info(self, message, func_name=""):
        self.default.info(message, func_name)

    def error(self, message, func_name=""):
        self.default.error(message, func_name)

    def warning(self, message, func_name=""):
        self.default.warning(message, func_name)

    def log(self, lv, message, func_name=""):
        self.default.log(lv, message, func_name)

    def debug(self, message, func_name=""):
        self.default.debug(message, func_name)


class APIResponse(object):
    def __init__(self, **kwargs):
        self.code_status = 0
        self.message = ""
        self.errors = {}
        self.data_resp = {}
        self.kwargs = {}

    def check_message(self, message):
        self.message = self.message if self.message else message

    def check_code(self, code_status):
        self.code_status = self.code_status if self.code_status else code_status

    def add_errors(self, error):
        if isinstance(error, list):
            self.errors.update(error)
        else:
            self.errors.update(error)

    def get_code(self, code=1200):
        return self.code_status if self.code_status else code

    def make_format(self):
        if self.errors:
            code_status = self.get_code(1400)
            message = self.message
            result = False
        else:
            code_status = self.get_code(1200)
            message = self.message if self.message else 'Success'
            result = True
        return dict(result=result, message=message, status_code=code_status, data=self.data_resp, error=self.errors, **self.kwargs)


def log_traceback(trac_back, e, _logger, log_type="info"):
    _logger.log(log_type, "{} - {}".format(e.__class__.__name__, str(e)))
    for i in range(8):
        if not i:
            continue
        if not trac_back:
            break
        if log_type == "info":
            _logger.log(log_type, 'Trace back exception at func {} - in line {}'.format(trac_back.tb_frame.f_code.co_name, trac_back.tb_lineno))
        else:
            _logger.log(log_type, 'Trace back exception at func {} - in line {}'.format(trac_back.tb_frame.f_code.co_name, trac_back.tb_lineno))
        trac_back = trac_back.tb_next


def trace_api(specific_logger="", serializer=None, service_name=None, class_response=APIResponse, check_content_type=True, check_request_auth=True):
    def decorator(func):
        def inner(request, **kwargs):
            _response = class_response(api_func=func.__name__)
            client_id = ""
            if check_request_auth:
                api_authentication = request.headers.get("Authorization", "")
                if not api_authentication:
                    _response.add_errors({"message": "Authentication API not provide"})
                    _response.message = "Authentication API failed"
                    _response.code_status = 1403
                    return Response(_response.make_format(), status=status.HTTP_403_FORBIDDEN)
                client_id, is_authenticated = ClientAuthentication.authentication(api_authentication.split(" ")[-1])
                if not is_authenticated:
                    _response.add_errors({"message": "Authentication API not provide"})
                    _response.message = "Authentication API failed"
                    _response.code_status = 1403
                    return Response(_response.make_format(), status=status.HTTP_403_FORBIDDEN)

            kwargs.update(_response=_response)
            func_name = f"{func.__name__}"
            req_username = request.user.username if request.user.username else ""
            if specific_logger == "":
                _logger = LogMessage.init_log(func_name, user=req_username, client_id=client_id, service_name=service_name)
            elif specific_logger == "mix":
                _logger = MixingLog(func_name=func_name, user=req_username, client_id=client_id, service_name=service_name)
            else:
                _logger = LogMessage.init_log(func_name, logger=specific_logger, user=req_username, client_id=client_id, service_name=service_name)
            _logger.debug("<-------START------->")
            _logger.debug(f'Input request {request.data}')
            _logger.debug(f'Input params {request.query_params}')
            if check_content_type and 'x-www-form-urlencoded' not in request.content_type and 'form-data' not in request.content_type and 'application/json' not in request.content_type:
                _response.check_message('Content-type has incorrect format')
                _response.add_errors({
                    "header": {
                        "message": "Content-type has incorrect format"
                    }
                })
                _response.check_code(1406)
                _logger.warning("<-------END------->")
                return Response(_response.make_format(), status=status.HTTP_200_OK)
            kwargs.update(request=request, data_ser=None, logger=_logger)
            if serializer:
                data_ser = serializer(data=request.data)
                if not data_ser.is_valid():
                    _response.check_message('Data input is invalid.')
                    _response.check_code(1400)
                    ctx = []
                    for key_error in data_ser.errors.keys():
                        print(data_ser.errors[key_error])
                        ctx.append({
                            'field': key_error,
                            'message': data_ser.errors[key_error][0]
                        })
                    _response.add_errors({
                        "serializer": {
                            "errors": ctx
                        }
                    })

                    _logger.info('Error: {}'.format(ctx))
                    return Response(_response.make_format(), status=status.HTTP_200_OK)
                kwargs.update(data_ser=data_ser.data)

            try:
                func(**kwargs)
            except Exception as e:
                if not isinstance(e, APIBreakException):
                    _response.check_message('Ops! Something were wrong.')
                    _response.check_code(1400)
                    _response.add_errors({"unknown_error": {
                        'field': "",
                        'message': 'An error occurred. Please try again later.' if not _response.message else _response.message
                    }})
                    log_traceback(trac_back=sys.exc_info()[-1], _logger=_logger, e=e, log_type="warning")
                else:
                    log_traceback(trac_back=sys.exc_info()[-1], _logger=_logger, e=e)
            if _response.errors:
                _logger.warning("<-------END------->")
            else:
                _logger.debug("<-------END------->")
            return Response(_response.make_format(), status=status.HTTP_200_OK)

        inner.func_name = func.__name__
        return inner

    return decorator


def trace_func(specific_logger="", service_name="", use_fn_as_service_name=False):
    def decorator(func):
        def inner(*args, **kwargs):
            func_name = func.__name__
            _parent_logger = kwargs.get("logger", "")
            init_service_name = service_name
            if isinstance(_parent_logger, LogMessage):
                init_service_name = service_name if service_name else _parent_logger.service_name
            if use_fn_as_service_name:
                init_service_name = f"{init_service_name}_{func_name}"
            if specific_logger == "":
                _logger = LogMessage.init_log(func_name, logger=_parent_logger, service_name=init_service_name)
            elif specific_logger == "mixin":
                _logger = MixingLog(func_name, _parent_logger=_parent_logger, service_name=init_service_name)
            else:
                _logger = LogMessage.init_log(func_name, logger=specific_logger, service_name=init_service_name)
            kwargs.update(logger=_logger)
            return func(*args, **kwargs)

        return inner

    return decorator
