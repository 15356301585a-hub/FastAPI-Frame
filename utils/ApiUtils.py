import json

from fastapi import Request

async def getRequestData(request: Request):
    dic = {}
    # url请求携带参数
    query = request.url.query
    if query.strip():
        baseQuery = {}
        for q in query.split('&'):
            baseQuery[q.split('=')[0]] = q.split('=')[1]
        dic['query'] = baseQuery

    # form格式请求参数
    form = await request.form()
    if form:
        dic['form'] = {}
        for k, v in form.items():
            dic['form'][k] = v
    else:
        # json格式/body格式请求参数
        body = await request.body()
        if body:
            try:
                dic['body'] = json.loads(body)
            except:
                if isinstance(body, bytes):
                    dic['body'] = body.decode('utf-8')
                elif isinstance(body, str):
                    dic['body'] = body
    if request.headers:
        dic['headers'] = {}
        for k, v in request.headers.items():
            dic['headers'][k] = v
    return dic