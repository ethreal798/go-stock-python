"""全局异常处理器，统一错误响应格式。

将所有异常转换为统一的 {code, msg, data} 格式，
便于前端统一处理错误响应。
"""

import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.response import ApiResponse

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 HTTPException-业务层主动抛出的异常（如 404、403），返回统一错误格式。"""
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.error(msg=msg).model_dump(),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求参数校验异常。"""
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        error_loc = first_error.get("loc", [])
        field = error_loc[-1] if error_loc else "unknown"
        msg = f"参数校验失败: {field} - {first_error.get('msg', '未知错误')}"
    else:
        msg = "参数校验失败"

    return JSONResponse(
        status_code=422,
        content=ApiResponse.error(msg=msg).model_dump(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底捕获所有未预期的异常--处理所有未捕获的异常。"""
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ApiResponse.error(msg="服务器内部错误").model_dump(),
    )
