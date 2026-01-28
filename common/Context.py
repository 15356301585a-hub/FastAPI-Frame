import json
from contextvars import ContextVar


class ContextAPI(object):
    def __init__(self):
        self.data = {
            'request_id': None,
            'request_url': None,
            'request_ip': None,
            'request_method': None,
        }
        self.token = []
        self.var: ContextVar[dict] = ContextVar("request_context",default=self.data)
    def set(self, key, value):
        request_context = self.var.get()
        request_context[key] = value
        token = self.var.set(request_context)
        self.token.append(token)
    def get(self, key):
        return self.var.get()[key]
    def reset(self):
        for t in reversed(self.token):
            try:
                self.var.reset(t)
            except:pass
        self.token.clear()

context = ContextAPI()