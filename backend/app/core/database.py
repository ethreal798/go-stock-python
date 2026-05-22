"""异步 SQLAlchemy 数据库配置。"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # SQLite 特殊配置：允许跨线程使用
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.DATABASE_URL
    else {},
)

# 异步会话工厂
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 声明基类，所有 ORM 模型需继承此类。"""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入：获取异步数据库会话。

    使用方式::
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """初始化数据库：创建所有表（开发阶段使用，生产用 Alembic 迁移）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库连接池。"""
    await engine.dispose()
