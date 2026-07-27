"""add prompt templates table

Revision ID: 8a1f4c2e7b90
Revises: 6986dd037381
Create Date: 2026-07-27 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8a1f4c2e7b90"
down_revision: Union[str, None] = "6986dd037381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prompt_templates_name"), "prompt_templates", ["name"], unique=False)
    op.create_index(op.f("ix_prompt_templates_type"), "prompt_templates", ["type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_prompt_templates_type"), table_name="prompt_templates")
    op.drop_index(op.f("ix_prompt_templates_name"), table_name="prompt_templates")
    op.drop_table("prompt_templates")
