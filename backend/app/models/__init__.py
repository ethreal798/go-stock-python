"""应用模型模块，导出所有 SQLAlchemy 模型和 Base。"""

from app.core.database import Base

from .base import TimestampMixin, SoftDeleteMixin, GormBaseModel
from .user import User
from .stock import (
    FollowedStock,
    StockBasic,
    AllStockInfo,
    StockInfoHK,
    StockInfoUS,
    StockGroup,
    StockGroupItem,
    StockInfo,
    IndexBasic,
    TradingRecord,
    BKDict,
)
from .ai import (
    AIResponseResult,
    AIRecommendStocks,
    PromptTemplate,
    ChatMemory,
)
from .market import (
    Telegraph,
    TelegraphTags,
    Tags,
    MarketStatistic,
    StockChangeHistory,
    WordAnalyze,
    SentimentResultAnalyze,
    GlobalStockIndex,
    LongTigerRankData,
)
from .system import (
    Settings,
    CronTask,
    CronTaskExecutionLog,
    MCPServer,
    MCPServerTool,
    Skill,
    SkillConfig,
    AiAssistantSession,
    AIConfig,
    VersionInfo,
)
from .strategy import CustomStrategy

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "GormBaseModel",
    #user
    "User",
    # stock
    "FollowedStock",
    "StockBasic",
    "AllStockInfo",
    "StockInfoHK",
    "StockInfoUS",
    "StockGroup",
    "StockGroupItem",
    "StockInfo",
    "IndexBasic",
    "TradingRecord",
    "BKDict",
    # ai
    "AIResponseResult",
    "AIRecommendStocks",
    "PromptTemplate",
    "ChatMemory",
    # market
    "Telegraph",
    "TelegraphTags",
    "Tags",
    "MarketStatistic",
    "StockChangeHistory",
    "WordAnalyze",
    "SentimentResultAnalyze",
    "GlobalStockIndex",
    "LongTigerRankData",
    # system
    "Settings",
    "CronTask",
    "CronTaskExecutionLog",
    "MCPServer",
    "MCPServerTool",
    "Skill",
    "SkillConfig",
    "AiAssistantSession",
    "AIConfig",
    "VersionInfo",
    # strategy
    "CustomStrategy",
]
