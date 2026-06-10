import asyncio
import json
import threading
import urllib
from typing import TypedDict, Optional, Unpack
from rnet import Client, Emulation, EmulationOption, EmulationOS, HeaderMap, Proxy
import rnet

_loop: asyncio.AbstractEventLoop | None = None
_loop_lock = threading.Lock()

def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    global _loop
    with _loop_lock:
        if _loop is None or _loop.is_closed():
            _loop = asyncio.new_event_loop()
            threading.Thread(
                target=_loop.run_forever,
                daemon=True,
                name="async_loop_thread"
            ).start()
        return _loop


class SessionInitKwargs(TypedDict, total=False):
    emulation: Emulation  # 请求指纹
    emulation_os: EmulationOS  # 操作系统
    skip_http2: bool  # 是否跳过http2.0
    skip_headers: bool  # 是否跳过自动设置的headers
    timeout: int  # 请求超时时长
    verify_ssl: bool  # 验证ssl 默认True


class SessionRequest(TypedDict, total=False):
    url: str  # 请求链接
    headers: Optional[dict | HeaderMap]  # 请求头
    data: Optional[dict | bytes | str]  # 请求data/form/body
    json: Optional[dict]
    cookies: Optional[dict]
    params: Optional[dict]
    proxy: str
    timeout: int  # 超时时间
    allow_redirects: bool  # 自动重定向 默认True

class utils:
    def handler_data(self,kws):
        data = kws.get('data',{})
        if data:
            del kws['data']
            headers = {k.lower(): v.lower() for k, v in kws.get('headers',{}).items()}
            content_type = headers.get('content-type')
            if content_type:
                if 'application/x-www-form-urlencoded' in content_type:
                    kws['body'] = data
                elif 'application/json' in content_type:
                    if type(data) is dict:
                        kws['body'] = json.dumps(data,separators=(',',':'))
                    else:
                        kws['body'] = data
                else:
                    kws['body'] = data
        return kws
    def handler_json(self,kws):
        json_data = kws.get('json',{})
        if json_data:
            del kws['json']
            kws['body'] = json.dumps(json_data,separators=(',',':'))
        return kws
    def handler_params(self,kws):
        params = kws.get('params',{})
        if params:
            del kws['params']
            kws['query'] = {}
            for k, v in params.items():
                kws['query'][k] = str(v)
        return kws
    def handler_headers(self,kws):
        headers = kws.get('headers',{})
        headers_new = {k.lower(): v.lower() for k, v in kws.get('headers',{}).items()}
        if kws.get('json'):
            if 'application/json' not in headers_new['content-type']:
                headers['content-type'] = 'application/json'
        if not headers_new.get('accept'):
            headers['Accept'] = '*/*'
        if not headers_new.get('accept-encoding'):
            headers['Accept-Encoding'] = 'gzip, deflate, br'
        kws['headers'] = headers
        return kws
    def handler_cookie(self,kws):
        cookies = kws.get('cookies',{})
        headers = kws.get('headers',{})
        if cookies:
            cookiesStr = ""
            for key, value in cookies.items():
                cookiesStr += f"{key}={value};"
            headers["Cookie"] = cookiesStr
            kws['headers'] = headers
        return kws
    def handler_proxy(self,kws):
        proxy = kws.get('proxy', '')
        if proxy:
            if 'http://' not in proxy:
                proxy = 'http://' + proxy
            kws['proxy'] = Proxy.all(url=proxy)
        return kws

    def handler_kwargs(self,kws):
        if not kws.get('timeout'):
            kws['timeout'] = 30
        if kws.get('allow_redirects') is None:
            kws['allow_redirects'] = True
        kws = self.handler_data(kws)
        kws = self.handler_json(kws)
        kws = self.handler_params(kws)
        kws = self.handler_headers(kws)
        kws = self.handler_cookie(kws)
        return self.handler_proxy(kws)

class Response:
    def __init__(self, response: rnet.Response, url: str):
        content_bytes = []
        for chunk in response.stream():
            if chunk is not None:
                content_bytes.append(chunk)
        content = b''.join(content_bytes)

        self.url = url
        self.content = content
        self.headers = response.headers
        self._cookies = response.cookies
        self.cookies = {}
        self.status_code = response.status.as_int()
        self.text = None
        self._json = None
        try:
            self.text = content.decode('utf-8')
        except:
            pass
        try:
            self._json = json.loads(self.text)
        except:
            pass

        for cookie in self._cookies:
            self.cookies[cookie.name] = cookie.value

        if self.headers.get('location'):
            location = self.headers.get('location').decode('utf-8')
            if 'http' not in location:
                parseResult = urllib.parse.urlparse(self.url)
                location = parseResult.scheme + '://' + parseResult.netloc + location
            self.headers['location'] = location

    def json(self):
        return self._json


class Session(object):
    def __init__(self, **kwargs: SessionInitKwargs):
        self.utils = utils()
        disguise = EmulationOption(emulation=kwargs.get("emulation", Emulation.Chrome142),
                                   emulation_os=kwargs.get("emulation_os", EmulationOS.Android),
                                   skip_headers=kwargs.get("skip_headers", True),
                                   skip_http2=kwargs.get("skip_http2", True))
        self.session = Client(emulation=disguise, timeout=kwargs.get('timeout', 30),http1_only=kwargs.get('http1',True),
                              verify=kwargs.get('verify_ssl', False))

    def get(self, url, **kwargs: Unpack[SessionRequest]):
        loop = _get_or_create_event_loop()
        future = asyncio.run_coroutine_threadsafe(self.request(url, rnet.Method.GET, **kwargs), loop)
        return future.result()

    def post(self, url, **kwargs: Unpack[SessionRequest]):
        loop = _get_or_create_event_loop()
        future = asyncio.run_coroutine_threadsafe(self.request(url, rnet.Method.POST, **kwargs), loop)
        return future.result()

    async def async_get(self, url, **kwargs: Unpack[SessionRequest]):
        return await self.request(url, rnet.Method.GET, **kwargs)

    async def async_post(self, url, **kwargs: Unpack[SessionRequest]):
        return await self.request(url, rnet.Method.POST, **kwargs)

    async def request(self, url, method, **kwargs):
        kws = self.utils.handler_kwargs(kwargs)
        resp = await self.session.request(method, url, **kws)
        return Response(resp, url)


requests = Session()