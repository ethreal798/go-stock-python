"""Alembic 迁移环境配置。

注意：Alembic 本身是同步工具，所以数据库迁移统一使用同步驱动，
即使 FastAPI 应用用的是异步。
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool

from app.models import Base
from app.config import settings

# 添加项目根目录到 Python 路径，保证能导入 app
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


# Alembic Config 对象
config = context.config

# 读取数据库 URL
database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# 关键：统一转成同步驱动！！！
# Alembic 是同步工具，必须用同步驱动
if database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

# 设置 sqlalchemy.url
config.set_main_option("sqlalchemy.url", database_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData
target_metadata = Base.metadata

LANGGRAPH_MANAGED_TABLES = {
    "checkpoint_blobs",
    "checkpoint_migrations",
    "checkpoint_writes",
    "checkpoints",
}


def include_object(object_, name, type_, reflected, compare_to):
    """Keep LangGraph checkpointer tables outside application Alembic ownership."""
    if type_ == "table" and name in LANGGRAPH_MANAGED_TABLES:
        return False
    return True


def run_migrations_offline() -> None:
    """离线模式运行迁移。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式运行迁移。"""
    # Alembic 统一使用同步引擎，简单直接
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
