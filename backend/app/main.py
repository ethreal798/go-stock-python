"""FastAPI 应用入口。

包含 CORS 配置、路由注册、启动/关闭事件、WebSocket 端点。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware

from app.config import settings
from app.core.database import close_db
from app.core.exception_handler import (
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.logging import RequestLoggingMiddleware, setup_logging
from app.core.middleware import ResponseWrapperMiddleware
from app.core.rate_limiter import get_limiter, get_rate_limit_exception_handler
from app.core.redis import close_redis
from app.core.websocket import ws_manager
from app.routers import (
    agent,
    ai_rag,
    auth,
    cron_tasks,
    funds,
    kline,
    market,
    news,
    settings as settings_router,
    stocks,
)

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭。"""
    # ---- 启动 ----
    logger.info("Starting %s v%s ...", settings.APP_NAME, settings.APP_VERSION)

    # 导入任务模块，触发 @register_task 装饰器注册
    import app.services.scheduler.tasks  # noqa: F401

    yield  # 应用运行中

    # ---- 关闭 ----
    logger.info("Shutting down ...")

    # 关闭 Redis
    await close_redis()
    logger.info("Redis connection closed")

    # 关闭数据库
    await close_db()
    logger.info("Database connection closed")


# ============================================================
# 创建 FastAPI 应用实例
# ============================================================

# 初始化限流器（连接 Redis）
limiter: Limiter = get_limiter()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="stockmate 后端服务 - 股票分析应用",
    lifespan=lifespan,
)

# 将 limiter 绑定到 app，使装饰器可用
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, get_rate_limit_exception_handler())

# ---- 注册全局异常处理器，统一错误响应格式 ----
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ---- 统一响应格式中间件 (必须在其他中间件之前添加，确保作为最内层) ----
app.user_middleware = [
    Middleware(ResponseWrapperMiddleware),
] + app.user_middleware

# Request ID, status code and latency are persisted without logging query strings.
app.add_middleware(RequestLoggingMiddleware)

# ---- CORS 中间件 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 速率限制中间件 ----
app.add_middleware(SlowAPIMiddleware)

# ---- 注册路由 ----
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(stocks.router, prefix=settings.API_PREFIX)
app.include_router(funds.router, prefix=settings.API_PREFIX)
app.include_router(market.router, prefix=settings.API_PREFIX)
app.include_router(agent.router, prefix=settings.API_PREFIX)
app.include_router(ai_rag.router, prefix=settings.API_PREFIX)
app.include_router(news.router, prefix=settings.API_PREFIX)
app.include_router(settings_router.router, prefix=settings.API_PREFIX)
app.include_router(cron_tasks.router, prefix=settings.API_PREFIX)
app.include_router(kline.router, prefix=settings.API_PREFIX)


# ============================================================
# WebSocket 端点
# ============================================================


@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str) -> None:
    """WebSocket 连接端点。

    支持的频道：
    - stocks: 股票实时行情推送
    - alerts: 预警消息推送
    - news: 新闻资讯推送
    """
    await ws_manager.connect(websocket, channel)
    try:
        while True:
            # 接收客户端消息（保持连接活跃）
            data = await websocket.receive_text()
            # 可选：处理客户端发送的指令
            logger.debug("WS received on channel=%s: %s", channel, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ============================================================
# 健康检查
# ============================================================


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """健康检查端点。"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["root"])
async def root() -> dict:
    """根路径，返回 API 信息。"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }
