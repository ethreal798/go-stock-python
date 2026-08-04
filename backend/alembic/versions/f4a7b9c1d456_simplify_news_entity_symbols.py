"""simplify news entity symbols and supported markets

Revision ID: f4a7b9c1d456
Revises: e2f6a8b0c345
Create Date: 2026-08-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f4a7b9c1d456"
down_revision: Union[str, None] = "e2f6a8b0c345"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("news_item_entities", sa.Column("symbol", sa.String(length=100), nullable=True))
    op.execute("""
        UPDATE news_item_entities
        SET entity_type = CASE
                WHEN lower(coalesce(market, '')) = 'fund' THEN 'fund'
                ELSE entity_type
            END,
            symbol = CASE
                WHEN entity_type = 'fund' OR lower(coalesce(market, '')) = 'fund'
                    THEN nullif(btrim(source_symbol), '')
                WHEN normalized_symbol ~ '^[0-9]{6}[.](SH|SZ|BJ)$'
                    THEN normalized_symbol
                WHEN normalized_symbol ~ '^[0-9]{1,5}[.]HK$'
                    THEN lpad(split_part(normalized_symbol, '.', 1), 5, '0') || '.HK'
                WHEN lower(coalesce(market, '')) = 'hk' AND source_symbol ~ '^[0-9]{1,5}$'
                    THEN lpad(source_symbol, 5, '0') || '.HK'
                WHEN source_symbol ~* '^hk[0-9]{1,5}$'
                    THEN lpad(substring(source_symbol from 3), 5, '0') || '.HK'
                ELSE NULL
            END
        """)
    op.execute("""
        DELETE FROM news_item_entities
        WHERE entity_type NOT IN ('stock', 'fund')
           OR symbol IS NULL
           OR btrim(symbol) = ''
        """)
    op.execute("""
        DELETE FROM news_item_entities AS entity
        USING news_item_entities AS duplicate
        WHERE entity.news_item_id = duplicate.news_item_id
          AND entity.entity_type = duplicate.entity_type
          AND entity.symbol = duplicate.symbol
          AND entity.id > duplicate.id
        """)

    op.drop_index("ix_news_entities_normalized_type", table_name="news_item_entities")
    op.drop_index("ix_news_item_entities_normalized_symbol", table_name="news_item_entities")
    op.drop_index("ix_news_item_entities_market", table_name="news_item_entities")
    op.drop_constraint("uq_news_item_entity", "news_item_entities", type_="unique")

    op.alter_column("news_item_entities", "symbol", existing_type=sa.String(length=100), nullable=False)
    op.create_unique_constraint(
        "uq_news_item_entity",
        "news_item_entities",
        ["news_item_id", "entity_type", "symbol"],
    )
    op.create_index("ix_news_item_entities_symbol", "news_item_entities", ["symbol"])
    op.create_index("ix_news_entities_symbol_type", "news_item_entities", ["symbol", "entity_type"])

    op.drop_column("news_item_entities", "market")
    op.drop_column("news_item_entities", "source_symbol")
    op.drop_column("news_item_entities", "normalized_symbol")


def downgrade() -> None:
    op.add_column("news_item_entities", sa.Column("market", sa.String(length=32), nullable=True))
    op.add_column("news_item_entities", sa.Column("source_symbol", sa.String(length=100), nullable=True))
    op.add_column("news_item_entities", sa.Column("normalized_symbol", sa.String(length=100), nullable=True))
    op.execute("""
        UPDATE news_item_entities
        SET source_symbol = symbol,
            normalized_symbol = symbol
        """)

    op.drop_index("ix_news_entities_symbol_type", table_name="news_item_entities")
    op.drop_index("ix_news_item_entities_symbol", table_name="news_item_entities")
    op.drop_constraint("uq_news_item_entity", "news_item_entities", type_="unique")
    op.create_unique_constraint(
        "uq_news_item_entity",
        "news_item_entities",
        ["news_item_id", "entity_type", "source_symbol"],
    )
    op.create_index("ix_news_item_entities_market", "news_item_entities", ["market"])
    op.create_index("ix_news_item_entities_normalized_symbol", "news_item_entities", ["normalized_symbol"])
    op.create_index(
        "ix_news_entities_normalized_type",
        "news_item_entities",
        ["normalized_symbol", "entity_type"],
    )
    op.drop_column("news_item_entities", "symbol")
