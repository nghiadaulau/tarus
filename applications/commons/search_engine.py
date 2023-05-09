import json
import uuid

from django.conf import settings
import requests

from applications.commons.log_lib import trace_func


class SearchEngine(object):
    def __init__(self, **kwargs):
        self.url = self.get_search_engine_url()
        self.get_success = True
        self.error_data = []

    @staticmethod
    def get_search_engine_url():
        if settings.SEARCH_ENGINE_USERNAME and settings.SEARCH_ENGINE_PASSWORD:
            url = f'{settings.SEARCH_ENGINE_PROTOCOL}://{settings.SEARCH_ENGINE_USERNAME}:{settings.SEARCH_ENGINE_PASSWORD}@{settings.SEARCH_ENGINE_HOST}:{settings.SEARCH_ENGINE_PORT}'
        elif settings.SEARCH_ENGINE_PORT:
            url = f'{settings.SEARCH_ENGINE_PROTOCOL}://{settings.SEARCH_ENGINE_HOST}:{settings.SEARCH_ENGINE_PORT}'
        else:
            url = f'{settings.SEARCH_ENGINE_PROTOCOL}://{settings.SEARCH_ENGINE_HOST}'
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
            if settings.IS_BETA:
                logger.debug('Log body SearchEngine - {}'.format(json.dumps(body)))
            data = response.json()
            if settings.IS_BETA:
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
