from contextvars import ContextVar
from typing import Optional, Dict


class ContextAPI(object):
    def __init__(self):
        # 关键：不共享 default，不共用 token 列表
        self.var: ContextVar[Optional[Dict]] = ContextVar("request_context", default=None)

    def set(self, key, value):
        # 获取当前协程独立的上下文
        ctx = self.var.get()

        # 第一次访问 → 创建全新上下文（每个协程独立）
        if ctx is None:
            ctx = {
                'request_id': None,
                'request_url': None,
                'request_ip': None,
                'request_method': None,
                'request_token': None,
            }

        # 赋值
        ctx[key] = value

        # 重新设置回当前上下文
        self.var.set(ctx)

    def get(self, key):
        ctx = self.var.get()
        if ctx is None:
            return None
        return ctx.get(key)

    def clear(self):
        # 只清空当前协程自己的上下文，不影响别人
        self.var.set(None)

    def reset(self):
        # 兼容你原来的写法
        self.clear()


# 全局单例，但并发安全
context = ContextAPI()