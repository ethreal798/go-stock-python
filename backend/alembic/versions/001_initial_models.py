"""初始模型创建

Revision ID: 001
Revises: 
Create Date: 2026-05-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== stock.py ====================
    op.create_table(
        'followed_stock',
        sa.Column('stock_code', sa.String(20), primary_key=True),
        sa.Column('name', sa.String(50)),
        sa.Column('volume', sa.BigInteger),
        sa.Column('cost_price', sa.Float),
        sa.Column('price', sa.Float),
        sa.Column('price_change', sa.Float),
        sa.Column('change_percent', sa.Float),
        sa.Column('alarm_change_percent', sa.Float),
        sa.Column('alarm_price', sa.Float),
        sa.Column('time', sa.DateTime),
        sa.Column('sort', sa.BigInteger),
        sa.Column('cron', sa.String(255), nullable=True),
        sa.Column('is_del', sa.DateTime, nullable=True, index=True),
        sa.Column('ai_config_id', sa.Integer),
        sa.Column('entry_price', sa.Float),
        sa.Column('take_profit_price', sa.Float),
        sa.Column('stop_loss_price', sa.Float),
    )

    op.create_table(
        'stock_basics',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('ts_code', sa.String(50), index=True),
        sa.Column('symbol', sa.String(20), index=True),
        sa.Column('name', sa.String(50), index=True),
        sa.Column('area', sa.String(50)),
        sa.Column('industry', sa.String(50), index=True),
        sa.Column('fullname', sa.String(100)),
        sa.Column('ename', sa.String(100)),
        sa.Column('cnspell', sa.String(50)),
        sa.Column('market', sa.String(20)),
        sa.Column('exchange', sa.String(20)),
        sa.Column('curr_type', sa.String(20)),
        sa.Column('list_status', sa.String(10)),
        sa.Column('list_date', sa.String(20)),
        sa.Column('delist_date', sa.String(20)),
        sa.Column('is_hs', sa.String(10)),
        sa.Column('act_name', sa.String(100)),
        sa.Column('act_ent_type', sa.String(50)),
        sa.Column('bk_name', sa.String(100)),
        sa.Column('bk_code', sa.String(50)),
    )

    op.create_table(
        'all_stock_info',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('secucode', sa.String(50), index=True),
        sa.Column('securitycode', sa.String(20), index=True),
        sa.Column('securitynameabbr', sa.String(50), index=True),
        sa.Column('newprice', sa.String(20)),
        sa.Column('changerate', sa.String(20)),
        sa.Column('volumeratio', sa.String(20)),
        sa.Column('highprice', sa.String(20)),
        sa.Column('lowprice', sa.String(20)),
        sa.Column('precloseprice', sa.String(20)),
        sa.Column('volume', sa.String(30)),
        sa.Column('dealamount', sa.String(30)),
        sa.Column('turnoverrate', sa.String(20)),
        sa.Column('market', sa.String(20), index=True),
        sa.Column('concept', sa.String(500), index=True),
        sa.Column('industry', sa.String(100), index=True),
        sa.Column('maxtradedate', sa.String(20), index=True),
    )

    op.create_table(
        'stock_base_info_hk',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('code', sa.String(20), index=True),
        sa.Column('name', sa.String(50)),
        sa.Column('full_name', sa.String(100)),
        sa.Column('e_name', sa.String(100)),
        sa.Column('is_del', sa.DateTime, nullable=True, index=True),
        sa.Column('bk_name', sa.String(100)),
        sa.Column('bk_code', sa.String(50)),
    )

    op.create_table(
        'stock_base_info_us',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('code', sa.String(20), index=True),
        sa.Column('name', sa.String(50)),
        sa.Column('full_name', sa.String(100)),
        sa.Column('e_name', sa.String(100)),
        sa.Column('exchange', sa.String(20)),
        sa.Column('type', sa.String(20)),
        sa.Column('is_del', sa.DateTime, nullable=True, index=True),
        sa.Column('bk_name', sa.String(100)),
        sa.Column('bk_code', sa.String(50)),
    )

    op.create_table(
        'stock_groups',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('name', sa.String(100), index=True),
        sa.Column('sort', sa.Integer, server_default='0'),
    )

    op.create_table(
        'group_stock_info',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('stock_code', sa.String(20), index=True),
        sa.Column('group_id', sa.BigInteger, sa.ForeignKey('stock_groups.id'), index=True),
    )

    op.create_table(
        'stock_infos',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('date', sa.String(20), index=True),
        sa.Column('time', sa.String(20), index=True),
        sa.Column('code', sa.String(20), index=True),
        sa.Column('name', sa.String(50), index=True),
        sa.Column('pre_price', sa.Float),
        sa.Column('price', sa.String(20)),
        sa.Column('volume', sa.String(30)),
        sa.Column('amount', sa.String(30)),
        sa.Column('open', sa.String(20)),
        sa.Column('pre_close', sa.String(20)),
        sa.Column('high', sa.String(20)),
        sa.Column('low', sa.String(20)),
        sa.Column('bid', sa.String(20)),
        sa.Column('ask', sa.String(20)),
        sa.Column('b1p', sa.String(20)),
        sa.Column('b1v', sa.String(20)),
        sa.Column('b2p', sa.String(20)),
        sa.Column('b2v', sa.String(20)),
        sa.Column('b3p', sa.String(20)),
        sa.Column('b3v', sa.String(20)),
        sa.Column('b4p', sa.String(20)),
        sa.Column('b4v', sa.String(20)),
        sa.Column('b5p', sa.String(20)),
        sa.Column('b5v', sa.String(20)),
        sa.Column('a1p', sa.String(20)),
        sa.Column('a1v', sa.String(20)),
        sa.Column('a2p', sa.String(20)),
        sa.Column('a2v', sa.String(20)),
        sa.Column('a3p', sa.String(20)),
        sa.Column('a3v', sa.String(20)),
        sa.Column('a4p', sa.String(20)),
        sa.Column('a4v', sa.String(20)),
        sa.Column('a5p', sa.String(20)),
        sa.Column('a5v', sa.String(20)),
    )

    op.create_table(
        'tushare_index_basic',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('ts_code', sa.String(50), index=True),
        sa.Column('symbol', sa.String(20), index=True),
        sa.Column('name', sa.String(50), index=True),
        sa.Column('full_name', sa.String(100)),
        sa.Column('index_type', sa.String(50)),
        sa.Column('category', sa.String(50)),
        sa.Column('market', sa.String(20)),
        sa.Column('list_date', sa.String(20)),
        sa.Column('base_date', sa.String(20)),
        sa.Column('base_point', sa.Float),
        sa.Column('publisher', sa.String(100)),
        sa.Column('weight_rule', sa.String(50)),
        sa.Column('desc', sa.Text),
    )

    op.create_table(
        'trading_records',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('stock_code', sa.String(20), index=True),
        sa.Column('stock_name', sa.String(50)),
        sa.Column('direction', sa.String(10), index=True),
        sa.Column('price', sa.Float),
        sa.Column('volume', sa.BigInteger),
        sa.Column('reason', sa.Text),
        sa.Column('stop_loss_price', sa.Float),
        sa.Column('take_profit_price', sa.Float),
        sa.Column('fee', sa.Float),
        sa.Column('market_value', sa.Float),
        sa.Column('mindset', sa.Text),
        sa.Column('recorded_close_price', sa.Float),
        sa.Column('trading_time', sa.DateTime, index=True),
    )

    op.create_table(
        'bk_dict',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('bk_code', sa.String(50)),
        sa.Column('bk_name', sa.String(100)),
        sa.Column('first_letter', sa.String(50)),
        sa.Column('fubk_code', sa.String(50)),
        sa.Column('publish_code', sa.String(50)),
    )

    # ==================== ai.py ====================
    op.create_table(
        'ai_response_result',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('chat_id', sa.String(100)),
        sa.Column('model_name', sa.String(100)),
        sa.Column('stock_code', sa.String(20)),
        sa.Column('stock_name', sa.String(50)),
        sa.Column('question', sa.Text),
        sa.Column('content', sa.Text),
        sa.Column('is_del', sa.DateTime, nullable=True, index=True),
    )

    op.create_table(
        'ai_recommend_stocks',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('data_time', sa.DateTime, index=True),
        sa.Column('model_name', sa.String(100)),
        sa.Column('rating', sa.String(20)),
        sa.Column('stock_code', sa.String(20)),
        sa.Column('stock_name', sa.String(50)),
        sa.Column('bk_code', sa.String(50)),
        sa.Column('bk_name', sa.String(100)),
        sa.Column('stock_price', sa.String(20)),
        sa.Column('stock_current_price', sa.String(20)),
        sa.Column('stock_current_price_time', sa.String(50)),
        sa.Column('stock_close_price', sa.String(20)),
        sa.Column('stock_pre_price', sa.String(20)),
        sa.Column('recommend_reason', sa.Text),
        sa.Column('recommend_buy_price', sa.String(50)),
        sa.Column('recommend_buy_price_min', sa.Float),
        sa.Column('recommend_buy_price_max', sa.Float),
        sa.Column('recommend_stop_profit_price', sa.String(50)),
        sa.Column('recommend_stop_profit_price_min', sa.Float),
        sa.Column('recommend_stop_profit_price_max', sa.Float),
        sa.Column('recommend_stop_loss_price', sa.String(50)),
        sa.Column('risk_remarks', sa.Text),
        sa.Column('remarks', sa.Text),
        sa.Column('enable_alert', sa.Boolean, server_default='0'),
    )

    op.create_table(
        'prompt_templates',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(100)),
        sa.Column('content', sa.Text),
        sa.Column('type', sa.String(50)),
    )

    op.create_table(
        'chat_memory',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('session_id', sa.String(64), index=True),
        sa.Column('role', sa.String(20)),
        sa.Column('content', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==================== market.py ====================
    op.create_table(
        'telegraph_list',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('time', sa.String(50)),
        sa.Column('data_time', sa.DateTime, nullable=True, index=True),
        sa.Column('title', sa.String(500), index=True),
        sa.Column('content', sa.Text, index=True),
        sa.Column('is_red', sa.Boolean, server_default='0', index=True),
        sa.Column('url', sa.String(500)),
        sa.Column('source', sa.String(100), index=True),
        sa.Column('sentiment_result', sa.String(50), index=True),
    )

    op.create_table(
        'tags',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('name', sa.String(100)),
        sa.Column('type', sa.String(50)),
    )

    op.create_table(
        'telegraph_tags',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('tag_id', sa.BigInteger, sa.ForeignKey('tags.id')),
        sa.Column('telegraph_id', sa.BigInteger, sa.ForeignKey('telegraph_list.id')),
    )

    op.create_table(
        'market_statistic',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('data_date', sa.String(10), index=True),
        sa.Column('data_time', sa.String(8), index=True),
        sa.Column('up_count', sa.Integer),
        sa.Column('down_count', sa.Integer),
        sa.Column('up_ratio', sa.Float),
        sa.Column('up_down_ratio', sa.Float),
        sa.Column('sentiment_desc', sa.String(20)),
        sa.Column('limit_up', sa.Integer),
        sa.Column('limit_down', sa.Integer),
        sa.Column('limit_ratio', sa.Float),
        sa.Column('sh_up_count', sa.Integer),
        sa.Column('sh_down_count', sa.Integer),
        sa.Column('sz_up_count', sa.Integer),
        sa.Column('sz_down_count', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'stock_change_history',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('change_time', sa.String(10)),
        sa.Column('change_date', sa.String(10), index=True),
        sa.Column('stock_code', sa.String(20), index=True),
        sa.Column('stock_name', sa.String(50)),
        sa.Column('market', sa.Integer),
        sa.Column('change_type', sa.Integer, index=True),
        sa.Column('type_name', sa.String(20)),
        sa.Column('volume', sa.BigInteger),
        sa.Column('price', sa.Float),
        sa.Column('change_rate', sa.Float),
        sa.Column('amount', sa.Float),
        sa.Column('industry', sa.String(100)),
        sa.Column('concept', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('change_time', 'change_date', 'stock_code', 'change_type',
                            'volume', 'price', 'change_rate', 'amount',
                            name='idx_unique_change'),
    )

    op.create_table(
        'word_analyzes',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('data_time', sa.DateTime, index=True, server_default=sa.func.now()),
        sa.Column('word', sa.String(100)),
        sa.Column('frequency', sa.Integer),
        sa.Column('weight', sa.Float),
        sa.Column('score', sa.Float),
    )

    op.create_table(
        'sentiment_result_analyzes',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('data_time', sa.DateTime, index=True, server_default=sa.func.now()),
        sa.Column('score', sa.Float),
        sa.Column('category', sa.Integer),
        sa.Column('positive_count', sa.Integer),
        sa.Column('negative_count', sa.Integer),
        sa.Column('description', sa.Text),
    )

    op.create_table(
        'global_stock_index',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('code', sa.String(20), index=True),
        sa.Column('name', sa.String(50)),
        sa.Column('location', sa.String(50)),
        sa.Column('qtcode', sa.String(50), index=True),
        sa.Column('state', sa.String(20)),
        sa.Column('zdf', sa.String(20)),
        sa.Column('zxj', sa.String(20)),
        sa.Column('img', sa.String(500)),
        sa.Column('region', sa.String(50), index=True),
        sa.Column('region_name', sa.String(50)),
    )

    op.create_table(
        'long_tiger_rank',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('accum_amount', sa.Float),
        sa.Column('billboard_buy_amt', sa.Float),
        sa.Column('billboard_deal_amt', sa.Float),
        sa.Column('billboard_net_amt', sa.Float),
        sa.Column('billboard_sell_amt', sa.Float),
        sa.Column('change_rate', sa.Float),
        sa.Column('close_price', sa.Float),
        sa.Column('deal_amount_ratio', sa.Float),
        sa.Column('deal_net_ratio', sa.Float),
        sa.Column('explain', sa.Text),
        sa.Column('explanation', sa.Text),
        sa.Column('free_market_cap', sa.Float),
        sa.Column('secucode', sa.String(50), index=True),
        sa.Column('security_code', sa.String(20)),
        sa.Column('security_name_abbr', sa.String(50)),
        sa.Column('security_type_code', sa.String(20)),
        sa.Column('trade_date', sa.String(20), index=True),
        sa.Column('turnoverrate', sa.Float),
    )

    # ==================== system.py ====================
    op.create_table(
        'settings',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('tushare_token', sa.String(255)),
        sa.Column('local_push_enable', sa.Boolean, server_default='0'),
        sa.Column('ding_push_enable', sa.Boolean, server_default='0'),
        sa.Column('ding_robot', sa.String(500)),
        sa.Column('update_basic_info_on_start', sa.Boolean, server_default='0'),
        sa.Column('refresh_interval', sa.BigInteger),
        sa.Column('open_ai_enable', sa.Boolean, server_default='0'),
        sa.Column('prompt', sa.Text),
        sa.Column('check_update', sa.Boolean, server_default='0'),
        sa.Column('update_channel', sa.String(50)),
        sa.Column('question_template', sa.Text),
        sa.Column('crawl_time_out', sa.BigInteger),
        sa.Column('k_days', sa.BigInteger),
        sa.Column('enable_danmu', sa.Boolean, server_default='0'),
        sa.Column('browser_path', sa.String(500)),
        sa.Column('enable_news', sa.Boolean, server_default='0'),
        sa.Column('dark_theme', sa.Boolean, server_default='0'),
        sa.Column('browser_pool_size', sa.Integer, server_default='5'),
        sa.Column('enable_fund', sa.Boolean, server_default='0'),
        sa.Column('enable_push_news', sa.Boolean, server_default='0'),
        sa.Column('enable_only_push_red_news', sa.Boolean, server_default='0'),
        sa.Column('sponsor_code', sa.String(100)),
        sa.Column('http_proxy', sa.String(500)),
        sa.Column('http_proxy_enabled', sa.Boolean, server_default='0'),
        sa.Column('enable_agent', sa.Boolean, server_default='0'),
        sa.Column('qgqp_b_id', sa.String(100)),
        sa.Column('iwencai_api_key', sa.String(255)),
        sa.Column('em_api_key', sa.String(255)),
        sa.Column('window_width', sa.Integer),
        sa.Column('window_height', sa.Integer),
        sa.Column('prompt_plaza_api_base', sa.String(500)),
    )

    op.create_table(
        'cron_tasks',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('cron_expr', sa.String(100), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('target', sa.String(255)),
        sa.Column('params', sa.Text),
        sa.Column('enable', sa.Boolean, server_default='1'),
        sa.Column('last_run_at', sa.DateTime, nullable=True),
        sa.Column('next_run_at', sa.DateTime, nullable=True),
        sa.Column('run_count', sa.BigInteger, server_default='0'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('description', sa.String(500)),
        sa.Column('last_run_result', sa.String(500)),
    )

    op.create_table(
        'cron_task_execution_logs',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.BigInteger, sa.ForeignKey('cron_tasks.id'), nullable=False),
        sa.Column('status', sa.String(20), server_default='running'),
        sa.Column('result', sa.Text),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('finished_at', sa.DateTime, nullable=True),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'mcp_servers',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('url', sa.String(500)),
        sa.Column('command', sa.String(500)),
        sa.Column('args', sa.Text),
        sa.Column('env', sa.Text),
        sa.Column('enable', sa.Boolean, server_default='1'),
        sa.Column('status', sa.String(20), server_default='stopped'),
        sa.Column('test_result', sa.String(500)),
    )

    op.create_table(
        'mcp_server_tools',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('mcp_server_id', sa.BigInteger, sa.ForeignKey('mcp_servers.id'), nullable=False, index=True),
        sa.Column('tool_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('params_schema', sa.Text),
    )

    op.create_table(
        'skills',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('category', sa.String(50)),
        sa.Column('system_prompt', sa.Text),
        sa.Column('examples', sa.Text),
        sa.Column('trigger_keywords', sa.String(500)),
        sa.Column('mcp_server_ids', sa.String(500)),
        sa.Column('enable', sa.Boolean, server_default='1'),
        sa.Column('sort_order', sa.Integer, server_default='0'),
    )

    op.create_table(
        'skill_configs',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('skill_id', sa.BigInteger, sa.ForeignKey('skills.id'), nullable=False),
        sa.Column('config_key', sa.String(100), nullable=False),
        sa.Column('config_value', sa.Text),
    )

    op.create_table(
        'ai_assistant_sessions',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('session_id', sa.String(64), index=True),
        sa.Column('messages', sa.Text),
    )

    op.create_table(
        'ai_config',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(100)),
        sa.Column('base_url', sa.String(500)),
        sa.Column('api_key', sa.String(500)),
        sa.Column('model_name', sa.String(100)),
        sa.Column('max_tokens', sa.Integer),
        sa.Column('temperature', sa.Float),
        sa.Column('time_out', sa.Integer),
        sa.Column('http_proxy', sa.String(500)),
        sa.Column('http_proxy_enabled', sa.Boolean, server_default='0'),
        sa.Column('session_id', sa.String(64), index=True),
        sa.Column('thinking', sa.Boolean, server_default='0'),
    )

    op.create_table(
        'version_info',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime, nullable=True, index=True),
        sa.Column('version', sa.String(50)),
        sa.Column('content', sa.Text),
        sa.Column('icon', sa.String(500)),
        sa.Column('alipay', sa.String(500)),
        sa.Column('wxpay', sa.String(500)),
        sa.Column('wxgzh', sa.String(500)),
        sa.Column('build_time_stamp', sa.BigInteger),
        sa.Column('official_statement', sa.Text),
        sa.Column('is_del', sa.DateTime, nullable=True, index=True),
    )

    # ==================== strategy.py ====================
    op.create_table(
        'custom_strategies',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('query', sa.Text, nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('sort_order', sa.Integer, server_default='0'),
    )


def downgrade() -> None:
    op.drop_table('custom_strategies')
    op.drop_table('version_info')
    op.drop_table('ai_config')
    op.drop_table('ai_assistant_sessions')
    op.drop_table('skill_configs')
    op.drop_table('skills')
    op.drop_table('mcp_server_tools')
    op.drop_table('mcp_servers')
    op.drop_table('cron_task_execution_logs')
    op.drop_table('cron_tasks')
    op.drop_table('settings')
    op.drop_table('long_tiger_rank')
    op.drop_table('global_stock_index')
    op.drop_table('sentiment_result_analyzes')
    op.drop_table('word_analyzes')
    op.drop_table('stock_change_history')
    op.drop_table('market_statistic')
    op.drop_table('tags')
    op.drop_table('telegraph_tags')
    op.drop_table('telegraph_list')
    op.drop_table('chat_memory')
    op.drop_table('prompt_templates')
    op.drop_table('ai_recommend_stocks')
    op.drop_table('ai_response_result')
    op.drop_table('bk_dict')
    op.drop_table('trading_records')
    op.drop_table('tushare_index_basic')
    op.drop_table('stock_infos')
    op.drop_table('group_stock_info')
    op.drop_table('stock_groups')
    op.drop_table('stock_base_info_us')
    op.drop_table('stock_base_info_hk')
    op.drop_table('all_stock_info')
    op.drop_table('stock_basics')
    op.drop_table('followed_stock')
