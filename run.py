from common.session import requests
import uvicorn
from fastapi import Query

from common.module import detail
from common.rs import R
from config.LoggerConfig import logger
from config.StartConfig import CreateApp

app = CreateApp()
@app.get("/")
async def index(reqData:detail = Query(...)):
    logger.info('请求成功')
    resp = requests.get('https://www.baidu.com').text
    return R(result=resp)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080,access_log=False)

