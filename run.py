from common.session import requests
import uvicorn
from fastapi import Request

from common.R import R
from config.LoggerConfig import logger
from config.StartConfig import CreateApp
from config.ConfigData import apiConfig

app = CreateApp()
@app.get("/")
async def index(request:Request):
    logger.info('请求成功')
    resp = requests.get('https://www.baidu.com').text
    return R(result=resp)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=apiConfig.get('port'),access_log=False)

