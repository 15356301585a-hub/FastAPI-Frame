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
        disguise = EmulationOption(emulation=kwargs.get("emulation", Emulation.Chrome142),
                                   emulation_os=kwargs.get("emulation_os", EmulationOS.Android),
                                   skip_headers=kwargs.get("skip_headers", True),
                                   skip_http2=kwargs.get("skip_http2", True))
        self.session = Client(emulation=disguise, timeout=kwargs.get('timeout', 30),
                              verify=kwargs.get('verify_ssl', False))

    def get(self, url, **kwargs: Unpack[SessionRequest]):
        loop = _get_or_create_event_loop()
        future = asyncio.run_coroutine_threadsafe(self.request(url, rnet.Method.GET, **kwargs), loop)
        return future.result()

    async def post(self, url, **kwargs: Unpack[SessionRequest]):
        loop = _get_or_create_event_loop()
        future = asyncio.run_coroutine_threadsafe(self.request(url, rnet.Method.POST, **kwargs), loop)
        return future.result()

    async def request(self, url, method, **kwargs):
        kws = {
            "timeout": kwargs.get("timeout", 30),
            "allow_redirects": kwargs.get("allow_redirects", True),
            "query": kwargs.get("params", {}),
            "json": kwargs.get("json", None),
        }
        if kws.get('query'):
            for k, v in kws.get('query').items():
                if type(v) is not str:
                    kws['query'][k] = str(v)

        cookies = kwargs.get("cookies", {})
        headers = kwargs.get("headers", {})
        data = kwargs.get('data', {})
        if cookies:
            cookiesStr = ""
            for key, value in cookies.items():
                cookiesStr += f"{key}={value};"
            headers["Cookie"] = cookiesStr

        headerDict = {}
        for header, value in headers.items():
            headerDict[header.lower()] = value

        if 'application/x-www-form-urlencoded' in headerDict.get('content-type',''):
            kws['form'] = data
        elif 'application/json' in headerDict.get('content-type',''):
            if type(data) == str:
                kws['body'] = data
            elif type(data) == dict:
                if kws['json'] is None:
                    kws['json'] = data
        else:
            kws['body'] = data

        proxy = kwargs.get('proxy', '')
        if proxy:
            kws['proxy'] = Proxy.all(url=proxy)

        kws['headers'] = headers
        resInfo = await self.session.request(method, url, **kws)

        return Response(resInfo, url)


requests = Session()
