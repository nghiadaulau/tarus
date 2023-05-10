import copy
import json
import uuid

import requests
from django.conf import settings

from applications.commons.log_lib import trace_func


class RequestFetch(object):
    POST = "post"
    GET = "get"
    PUT = "put"

    def __init__(self, protocol, host_name, service_name="", header=None, gis=None, cert=True):
        self.service_name = service_name
        self._host_name = host_name
        self.gis = gis
        self.protocol = protocol
        self.cert = cert
        self.default_header = {} if not header else header
        self.url = "{}://{}".format(self.protocol, self._host_name)

    def get_header(self, header=None):
        default_header = copy.deepcopy(self.default_header)
        if self.gis:
            default_header.update({
                "gis": self.gis
            })
        if header:
            default_header.update(header)
        return default_header

    @trace_func()
    def fetch(self, uri='', body=None, files=None, logger=None, header=None, method="post", timeout=100, params=None, log_resp=True, **kwargs):

        if uri.startswith("/"):
            full_url = "{}{}".format(self.url, uri) if uri else self.url
        else:
            full_url = "{}/{}".format(self.url, uri) if uri else self.url

        func_call = getattr(requests, method)
        header = self.get_header(header)
        func_name = uri.replace("/", "_").replace("-", "_")
        logger.debug("call {} with url {} body {}".format(func_name, full_url, body))
        data = {
            "result": False
        }
        body = body if body else {}
        try:
            response = func_call(full_url, json=body, headers=header, files=files, verify=self.cert, timeout=timeout, params=params if params else {})
            # print(response.text)
            data.update(http_status=response.status_code)
        except Exception as e:
            logger.error(f"call {func_name} error with {e}")
        else:
            try:
                data.update({"json_resp": response.json()})
                data["result"] = True

            except Exception as e:
                logger.error(f"parse data error with {response.content} and exception {e}")
            else:
                if log_resp:
                    logger.debug('Call API {} SUCCESS: {}'.format(func_name, data))

        return data


class SearchEngine(object):
    def __init__(self, **kwargs):
        self.url = self.get_search_engine_url()
        self.get_success = True
        self.error_data = []

    @staticmethod
    def get_search_engine_url():
        if settings.SEARCH_ENGINE.get("username") and settings.SEARCH_ENGINE.get("password"):
            url = f'{settings.SEARCH_ENGINE["protocol"]}://{settings.SEARCH_ENGINE["username"]}:{settings.SEARCH_ENGINE["password"]}@{settings.SEARCH_ENGINE["host"]}:{settings.SEARCH_ENGINE.get("port", 80)}'
        else:
            url = f'{settings.SEARCH_ENGINE["protocol"]}://{settings.SEARCH_ENGINE["host"]}:{settings.SEARCH_ENGINE.get("port", 80)}'
        return url

    @trace_func()
    def put_data(self, index_name, body, _id=None, logger=None):
        _id = uuid.uuid1().hex if not _id else _id
        url = f"{self.url}/{index_name}/_doc/{_id}"
        resp = {
            "result": False,
            "data": {}
        }
        response = requests.post(url=url, verify=False, json=body)
        try:
            logger.info(f'Put event meta to SearchEngine - body {body} with result {response.json()["result"]}')
            resp["result"] = True
            resp["data"] = {
                "resp": response.json()["result"],
                "id": _id
            }

        except Exception as e:
            logger.error(f'Put meta to SearchEngine Failed - body {body} with result {response.text} and error {e}')
        return resp

    @trace_func()
    def search_data(self, index_name, body, logger=None):
        url = f"{self.get_search_engine_url()}/{index_name}/_search?ignore_unavailable=true"
        data = {}
        self.get_success = True
        try:
            response = requests.get(url=url, verify=False, json=body)
            logger.debug('Get data in SearchEngine - index {} - filter {} with shard data {}'.format(index_name, json.dumps(body), response.text))
            if settings.DEBUG:
                logger.debug('Log body SearchEngine - {}'.format(json.dumps(body)))
            data = response.json()
            if settings.DEBUG:
                logger.debug('Log response SearchEngine - {}'.format(data))
        except Exception as e:
            self.get_success = False
            self.error_data.append(str(e))
            logger.error('Get data in SearchEngine - index {} - filter {} with shard data {}'.format(index_name, json.dumps(body), str(e)))
        return data

    @trace_func()
    def remove_index(self, index_name, logger=None):
        url = f"{self.get_search_engine_url()}/{index_name}?ignore_unavailable=true"
        data = None
        self.get_success = True
        try:
            response = requests.delete(url=url, verify=False)
            if response.json()["acknowledged"]:
                logger.debug('Remove index {} successful'.format(index_name))
        except Exception as e:
            self.get_success = False
            self.error_data.append(str(e))
            logger.error('Error remove index {} with error {}'.format(index_name, str(e)))
        return data
