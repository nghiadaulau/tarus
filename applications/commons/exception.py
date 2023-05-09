class APIWarningException(Exception):
    def __init__(self, message='', error='', http_status=200):
        self.error = error
        self.http_status = http_status
        super(APIWarningException, self).__init__(message)


class APIBreakException(Exception):
    def __init__(self, message='', error="", http_status=200):
        self.error = error
        self.http_status = http_status
        super(APIBreakException, self).__init__(message)


class DictResultBlockInfinityException(Exception):
    def __init__(self, error=""):
        self.message = "Dict result has been block infinity"
        self.error = error
        super(DictResultBlockInfinityException, self).__init__(self.message)
