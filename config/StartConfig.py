import asyncio
import json
import uuid

from fastapi import FastAPI,Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from common.Context import context
from common.rs import R
from config.ConfigData import apiConfig
from config.ExceptError import Exception_Handler
from config.LoggerConfig import logger
from utils.ApiUtils import getRequestData


async def beforeRequest(request:Request):
    await getRequestData(request)
    return request,False

async def afterRequest(request,response):
    resp = str(b"".join([part async for part in response.body_iterator]), "utf-8")
    res = json.loads(resp)
    logger.info('接口返回值：'+resp)
    return JSONResponse(res)

def CreateApp():
    app=FastAPI()
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                       allow_headers=["*"])
    Exception_Handler(app)

    @app.middleware("http")
    async def middleware(request: Request, call_next):
        request,su=await beforeRequest(request)
        if su:
            return request
        # 设置上下文参数
        context.set("request_id",str(uuid.uuid4()))
        context.set("request_url",request.url.path)
        context.set("request_ip",request.client.host)
        context.set("request_method",request.method)

        # 记录请求参数
        ReqData = await getRequestData(request)
        for k,v in ReqData.items():
            if isinstance(v,dict):
                v = json.dumps(v)
            if k!='headers':
                logger.info('接口请求参数 '+k+'：'+v)
            else:
                if apiConfig['logger']['saveHeaders']:
                    logger.info('接口请求头部参数信息：'+v)

        response = await asyncio.wait_for(call_next(request), 60)
        resp = await afterRequest(request, response)

        # 重置上下文参数
        context.reset()

        return resp

    return app