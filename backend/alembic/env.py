"""Alembic 异步迁移环境配置。"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.models import Base
from app.config import settings

# Alembic Config 对象，提供 .ini 文件中的配置
config = context.config

# 优先从环境变量读取数据库 URL，如果没有则使用 settings.DATABASE_URL
database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# 如果是异步驱动，需要转换为同步驱动用于 Alembic（因为 Alembic 主要是同步运行的）
# 注意：Alembic 迁移通常使用同步连接，即使应用是异步的
if database_url.startswith("postgresql+asyncpg"):
    database_url = database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

# 设置 sqlalchemy.url（覆盖 .ini 中的值）
config.set_main_option("sqlalchemy.url", database_url)

# 解析 Python 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置 MetaData 目标，用于 autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移。

    仅生成 SQL 脚本，不连接数据库。
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """执行迁移的内部函数。"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线模式运行异步迁移。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口。"""
    # 检查是否是异步 URL，如果是则使用同步版本
    url = config.get_main_option("sqlalchemy.url")
    if url.startswith("postgresql+asyncpg"):
        # 对于 Alembic，我们使用同步驱动
        from sqlalchemy import create_engine
        from sqlalchemy.engine import Connection

        connectable = create_engine(url.replace("postgresql+asyncpg", "postgresql+psycopg2"))

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
            )

            with context.begin_transaction():
                context.run_migrations()
    else:
        # 对于 SQLite 等，可以直接用异步方式
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
