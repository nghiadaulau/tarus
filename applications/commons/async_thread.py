import threading
import time

from applications.commons.exception import DictResultBlockInfinityException


class DictResultAsync(object):

    def __init__(self, block_time=0.00000001, _max_block_time=1):
        self._block = None
        self.data = {}
        self._block_time = block_time
        self._max_block_time = _max_block_time

    def block(self):
        self._block = True

    def unblock(self):
        self._block = False

    def update(self, update_data):
        t = 0
        while self._block:
            t += 1
            time.sleep(self._block_time)
            if t > self._max_block_time / self._block_time:
                raise DictResultBlockInfinityException()
        self.block()
        self.data.update(update_data)
        self.unblock()


class InputFunc(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class AsyncThread(object):
    def __init__(self, target_func):
        self.target_func = target_func
        self.input_args = []
        self.threads = []

    def add(self, *args, **kwargs):
        input_func = InputFunc(*args, **kwargs)
        self.input_args.append(input_func)

    def run(self, daemon=True):
        for _input in self.input_args:
            x = threading.Thread(target=self.target_func, args=_input.args, kwargs=_input.kwargs, daemon=daemon)
            x.start()
            self.threads.append(x)

    def wait(self):
        for x in self.threads:
            x.wait()

