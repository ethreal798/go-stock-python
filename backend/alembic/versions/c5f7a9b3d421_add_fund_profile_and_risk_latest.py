"""add fund profile and risk metric latest tables

Revision ID: c5f7a9b3d421
Revises: b4e6f8a2c310
Create Date: 2026-08-09 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c5f7a9b3d421"
down_revision: Union[str, None] = "b4e6f8a2c310"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "fund_profile_latest",
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False, comment="基金代码"),
        sa.Column("fund_name", sa.String(length=200), nullable=True, comment="基金名称"),
        sa.Column("full_name", sa.String(length=300), nullable=True, comment="基金全称"),
        sa.Column("inception_date", sa.Date(), nullable=True, comment="成立时间"),
        sa.Column("latest_scale_cny", sa.Numeric(24, 2), nullable=True, comment="最新规模（元）"),
        sa.Column("fund_company", sa.String(length=200), nullable=True, comment="基金公司"),
        sa.Column("fund_manager", sa.String(length=300), nullable=True, comment="基金经理"),
        sa.Column("custodian_bank", sa.String(length=200), nullable=True, comment="托管银行"),
        sa.Column("fund_type", sa.String(length=100), nullable=True, comment="雪球基金类型"),
        sa.Column("rating_agency", sa.String(length=100), nullable=True, comment="评级机构"),
        sa.Column("fund_rating", sa.String(length=50), nullable=True, comment="基金评级"),
        sa.Column("investment_strategy", sa.Text(), nullable=True, comment="投资策略"),
        sa.Column("investment_objective", sa.Text(), nullable=True, comment="投资目标"),
        sa.Column("performance_benchmark", sa.Text(), nullable=True, comment="业绩比较基准"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fund_profile_latest_fund_id", "fund_profile_latest", ["fund_id"], unique=True)
    op.create_index("ix_fund_profile_latest_fund_code", "fund_profile_latest", ["fund_code"], unique=True)
    op.create_index("ix_fund_profile_latest_deleted_at", "fund_profile_latest", ["deleted_at"])

    op.create_table(
        "fund_risk_metric_latest",
        sa.Column("fund_id", sa.BigInteger(), nullable=False),
        sa.Column("fund_code", sa.String(length=20), nullable=False, comment="基金代码"),
        sa.Column("period", sa.String(length=20), nullable=False, comment="指标周期"),
        sa.Column("peer_risk_return_score", sa.Numeric(12, 6), nullable=True, comment="较同类风险收益比"),
        sa.Column("peer_risk_control_score", sa.Numeric(12, 6), nullable=True, comment="较同类抗风险波动"),
        sa.Column("annualized_volatility_pct", sa.Numeric(12, 6), nullable=True, comment="年化波动率(%)"),
        sa.Column("annualized_sharpe_ratio", sa.Numeric(12, 6), nullable=True, comment="年化夏普比率"),
        sa.Column("max_drawdown_pct", sa.Numeric(12, 6), nullable=True, comment="最大回撤(%)"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False, comment="抓取时间"),
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["fund_id"], ["funds.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("fund_id", "period", name="uq_fund_risk_metric_latest_fund_period"),
    )
    op.create_index("ix_fund_risk_metric_latest_fund_code", "fund_risk_metric_latest", ["fund_code"])
    op.create_index("ix_fund_risk_metric_latest_deleted_at", "fund_risk_metric_latest", ["deleted_at"])


def downgrade() -> None:
    op.drop_table("fund_risk_metric_latest")
    op.drop_table("fund_profile_latest")
