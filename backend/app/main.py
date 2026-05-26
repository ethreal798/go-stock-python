"""FastAPI 应用入口。

包含 CORS 配置、路由注册、启动/关闭事件、WebSocket 端点。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import close_db, init_db
from app.core.redis import close_redis
from app.core.websocket import ws_manager
from app.routers import agent, cron_tasks, kline, market, news, settings as settings_router, stocks
from app.services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭。"""
    # ---- 启动 ----
    logger.info("Starting %s v%s ...", settings.APP_NAME, settings.APP_VERSION)

    # 初始化数据库
    await init_db()
    logger.info("Database initialized")

    # 启动调度器
    scheduler_service.start()
    logger.info("Scheduler started")

    yield  # 应用运行中

    # ---- 关闭 ----
    logger.info("Shutting down ...")

    # 关闭调度器
    scheduler_service.shutdown()
    logger.info("Scheduler stopped")

    # 关闭 Redis
    await close_redis()
    logger.info("Redis connection closed")

    # 关闭数据库
    await close_db()
    logger.info("Database connection closed")


# ============================================================
# 创建 FastAPI 应用实例
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="python-stock 后端服务 - 股票分析应用",
    lifespan=lifespan,
)

# ---- CORS 中间件 ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 注册路由 ----
app.include_router(stocks.router, prefix=settings.API_PREFIX)
app.include_router(market.router, prefix=settings.API_PREFIX)
app.include_router(agent.router, prefix=settings.API_PREFIX)
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