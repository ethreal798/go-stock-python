// 股票基础信息
export interface Stock {
  code: string;
  name: string;
  market: string; // SH | SZ | BJ
  group?: string;
  remark?: string;
}

// 股票实时价格
export interface StockPrice {
  code: string;
  name: string;
  price: number;
  change: number; // 涨跌额
  changeRate: number; // 涨跌幅 (%)
  open: number;
  high: number;
  low: number;
  preClose: number;
  volume: number; // 成交量 (手)
  amount: number; // 成交额 (元)
  turnover?: number; // 换手率 (%)
  pe?: number; // 市盈率
  pb?: number; // 市净率
  mktCap?: number; // 市值
  timestamp: string;
}

// K线数据
export interface KLineData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// AI聊天消息
export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  loading?: boolean;
  error?: boolean;
}

// 聊天会话
export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

// 新闻资讯
export interface NewsItem {
  id: number;
  time: string;
  data_time: string;
  title: string;
  content?: string;
  is_red: boolean;
  source: string;
  url?: string;
  sentiment_result: string;
  subjects: string[];
  stocks: string[];
  is_relevant: boolean;
  relevant_score?: number;
  category?: string;
}

// 基金
export interface Fund {
  code: string;
  name: string;
  type: string;
  nav: number; // 净值
  accNav: number; // 累计净值
  dayGrowth: number; // 日增长率
  weekGrowth?: number;
  monthGrowth?: number;
}

// 定时任务
export interface CronTask {
  id: number;
  name: string;
  cronExpr: string;
  taskType: string;
  params?: Record<string, unknown>;
  enabled: boolean;
  lastRun?: string;
  nextRun?: string;
  status?: "running" | "idle" | "error";
  remark?: string;
}

// 设置 - AI配置
export interface AIConfig {
  provider: string; // openai | ollama | zhipu | ...
  apiKey: string;
  baseUrl: string;
  model: string;
  maxTokens: number;
  temperature: number;
}

// 设置 - 通知配置
export interface NotifyConfig {
  dingdingEnabled: boolean;
  dingdingToken?: string;
  dingdingSecret?: string;
  emailEnabled: boolean;
  emailSmtp?: string;
  emailFrom?: string;
  emailTo?: string;
}

// 设置 - 数据源配置
export interface DataSourceConfig {
  tushareToken?: string;
  iwencaiEnabled: boolean;
}

// 全局设置
export interface AppSettings {
  ai: AIConfig;
  notify: NotifyConfig;
  dataSource: DataSourceConfig;
  theme: "light" | "dark";
  language: string;
}

// API分页响应
export interface PageResult<T> {
  list: T[];
  total: number;
  page: number;
  pageSize: number;
}

// 通用API响应
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

// 市场指数
export interface MarketIndex {
  code: string;
  name: string;
  price: number;
  change: number;
  changeRate: number;
}

// 热股榜
export interface HotStock {
  rank: number;
  code: string;
  name: string;
  price: number;
  changeRate: number;
  hotValue: number;
}

// WebSocket消息
export interface WSMessage {
  channel: string;
  type: string;
  data: unknown;
  timestamp: number;
}
