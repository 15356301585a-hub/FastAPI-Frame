import inspect
import traceback
from fastapi import Request, FastAPI
from starlette.responses import JSONResponse
from common.R import R
from config.LoggerConfig import logger, tools


def Exception_Handler(app:FastAPI):
    @app.exception_handler(Exception)
    async def custom_exception_handler(request:Request, exc:Exception):
        error_info = traceback.format_exc()
        logger.error(error_info)
        return JSONResponse(R(500, message=str(exc)))
