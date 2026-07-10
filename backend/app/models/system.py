"""系统配置模型"""

from sqlalchemy import Column, BigInteger, String, Integer, Boolean, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from .base import Base, GormBaseModel, TimestampMixin


class Settings(GormBaseModel):
    """系统设置"""

    __tablename__ = "settings"

    tushare_token = Column(String(255), name="tushare_token")
    local_push_enable = Column(Boolean, default=False, name="local_push_enable")
    ding_push_enable = Column(Boolean, default=False, name="ding_push_enable")
    ding_robot = Column(String(500), name="ding_robot")
    update_basic_info_on_start = Column(Boolean, default=False, name="update_basic_info_on_start")
    refresh_interval = Column(BigInteger, name="refresh_interval")
    open_ai_enable = Column(Boolean, default=False, name="open_ai_enable")
    prompt = Column(Text)
    check_update = Column(Boolean, default=False, name="check_update")
    update_channel = Column(String(50), name="update_channel")
    question_template = Column(Text, name="question_template")
    crawl_time_out = Column(BigInteger, name="crawl_time_out")
    k_days = Column(BigInteger, name="k_days")
    enable_danmu = Column(Boolean, default=False, name="enable_danmu")
    browser_path = Column(String(500), name="browser_path")
    enable_news = Column(Boolean, default=False, name="enable_news")
    dark_theme = Column(Boolean, default=False, name="dark_theme")
    browser_pool_size = Column(Integer, default=5, name="browser_pool_size")
    enable_fund = Column(Boolean, default=False, name="enable_fund")
    enable_push_news = Column(Boolean, default=False, name="enable_push_news")
    enable_only_push_red_news = Column(Boolean, default=False, name="enable_only_push_red_news")
    sponsor_code = Column(String(100), name="sponsor_code")
    http_proxy = Column(String(500), name="http_proxy")
    http_proxy_enabled = Column(Boolean, default=False, name="http_proxy_enabled")
    enable_agent = Column(Boolean, default=False, name="enable_agent")
    qgqp_b_id = Column(String(100), name="qgqp_b_id")
    iwencai_api_key = Column(String(255), name="iwencai_api_key")
    em_api_key = Column(String(255), name="em_api_key")
    window_width = Column(Integer, name="window_width")
    window_height = Column(Integer, name="window_height")
    prompt_plaza_api_base = Column(String(500), name="prompt_plaza_api_base")


class CronTask(Base, TimestampMixin):
    """定时任务"""

    __tablename__ = "cron_tasks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    cron_expr = Column(String(100), nullable=False, name="cron_expr")
    task_type = Column(String(50), nullable=False, name="task_type")
    target = Column(String(255))
    params = Column(Text)
    enable = Column(Boolean, default=True, server_default="1")
    last_run_at = Column(DateTime, nullable=True, name="last_run_at")
    next_run_at = Column(DateTime, nullable=True, name="next_run_at")
    run_count = Column(BigInteger, default=0, server_default="0", name="run_count")
    status = Column(String(20), default="active", server_default="'active'", name="status")
    description = Column(String(500))
    last_run_result = Column(String(500), name="last_run_result")

    execution_logs = relationship("CronTaskExecutionLog", back_populates="task", cascade="all, delete-orphan")


class CronTaskExecutionLog(Base):
    """定时任务执行日志"""

    __tablename__ = "cron_task_execution_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_id = Column(BigInteger, ForeignKey("cron_tasks.id"), nullable=False, name="task_id")
    status = Column(String(20), default="running", server_default="'running'")
    result = Column(Text)
    started_at = Column(DateTime, default=func.now(), name="started_at")
    finished_at = Column(DateTime, nullable=True, name="finished_at")
    error_message = Column(Text, name="error_message")
    created_at = Column(DateTime, default=func.now(), name="created_at")

    task = relationship("CronTask", back_populates="execution_logs")


class MCPServer(Base, TimestampMixin):
    """MCP 服务器配置"""

    __tablename__ = "mcp_servers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    url = Column(String(500))
    command = Column(String(500))
    args = Column(Text)
    env = Column(Text)
    enable = Column(Boolean, default=True, server_default="1")
    status = Column(String(20), default="stopped", server_default="'stopped'")
    test_result = Column(String(500), name="test_result")

    tools = relationship("MCPServerTool", back_populates="server", cascade="all, delete-orphan")


class MCPServerTool(Base, TimestampMixin):
    """MCP 服务器工具"""

    __tablename__ = "mcp_server_tools"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    mcp_server_id = Column(BigInteger, ForeignKey("mcp_servers.id"), nullable=False, index=True, name="mcp_server_id")
    tool_name = Column(String(255), nullable=False, name="tool_name")
    description = Column(Text)
    params_schema = Column(Text, name="params_schema")

    server = relationship("MCPServer", back_populates="tools")


class Skill(Base, TimestampMixin):
    """技能配置"""

    __tablename__ = "skills"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    category = Column(String(50))
    system_prompt = Column(Text, name="system_prompt")
    examples = Column(Text)
    trigger_keywords = Column(String(500), name="trigger_keywords")
    mcp_server_ids = Column(String(500), name="mcp_server_ids")
    enable = Column(Boolean, default=True, server_default="1")
    sort_order = Column(Integer, default=0, server_default="0", name="sort_order")

    configs = relationship("SkillConfig", back_populates="skill", cascade="all, delete-orphan")


class SkillConfig(Base, TimestampMixin):
    """技能扩展配置"""

    __tablename__ = "skill_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    skill_id = Column(BigInteger, ForeignKey("skills.id"), nullable=False, name="skill_id")
    config_key = Column(String(100), nullable=False, name="config_key")
    config_value = Column(Text, name="config_value")

    skill = relationship("Skill", back_populates="configs")


class AiAssistantSession(Base, TimestampMixin):
    """AI 助手会话"""

    __tablename__ = "ai_assistant_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True, name="session_id")
    messages = Column(Text)


class AIConfig(Base, TimestampMixin):
    """AI 配置"""

    __tablename__ = "ai_config"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100))
    base_url = Column(String(500), name="base_url")
    api_key = Column(String(500), name="api_key")
    model_name = Column(String(100), name="model_name")
    max_tokens = Column(Integer, name="max_tokens")
    temperature = Column(Float)
    time_out = Column(Integer, name="time_out")
    http_proxy = Column(String(500), name="http_proxy")
    http_proxy_enabled = Column(Boolean, default=False, name="http_proxy_enabled")
    session_id = Column(String(64), index=True, name="session_id")
    thinking = Column(Boolean, default=False)


class VersionInfo(GormBaseModel):
    """版本信息"""

    __tablename__ = "version_info"

    version = Column(String(50))
    content = Column(Text)
    icon = Column(String(500))
    alipay = Column(String(500))
    wxpay = Column(String(500))
    wxgzh = Column(String(500))
    build_time_stamp = Column(BigInteger, name="build_time_stamp")
    official_statement = Column(Text, name="official_statement")
    is_del = Column(DateTime, nullable=True, index=True, name="is_del")
