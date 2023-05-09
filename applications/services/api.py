from applications.commons.log_lib import trace_func
from applications.commons.request_base import RequestFetch
import requests


class Simsimi:
    @classmethod
    @trace_func()
    def have_message(cls, message, **kwargs):
        url = "https://api.simsimi.vn/v1/simtalk"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "text": message,
            "lc": "vn",
            "key": ""
        }
        return requests.post(url, headers=headers, data=data).json()
