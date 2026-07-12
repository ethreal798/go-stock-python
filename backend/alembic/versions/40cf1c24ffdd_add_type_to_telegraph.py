"""add_type_to_telegraph

Revision ID: 40cf1c24ffdd
Revises: 915e431eb823
Create Date: 2026-06-03 17:49:00.736358

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "40cf1c24ffdd"
down_revision: Union[str, None] = "915e431eb823"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("telegraph_list"):
        raise RuntimeError("缺少 telegraph_list 表，请先修复并重跑基线迁移 915e431eb823")

    columns = {col["name"] for col in inspector.get_columns("telegraph_list")}
    if "type" not in columns:
        op.add_column("telegraph_list", sa.Column("type", sa.String(length=20), nullable=True))
    indexes = {idx["name"] for idx in inspector.get_indexes("telegraph_list")}
    if op.f("ix_telegraph_list_type") not in indexes:
        op.create_index(op.f("ix_telegraph_list_type"), "telegraph_list", ["type"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("telegraph_list"):
        return

    indexes = {idx["name"] for idx in inspector.get_indexes("telegraph_list")}
    if op.f("ix_telegraph_list_type") in indexes:
        op.drop_index(op.f("ix_telegraph_list_type"), table_name="telegraph_list")
    columns = {col["name"] for col in inspector.get_columns("telegraph_list")}
    if "type" in columns:
        op.drop_column("telegraph_list", "type")
