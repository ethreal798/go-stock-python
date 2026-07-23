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

// 搜索/市场基金类型
export interface SearchFund {
  code: string;
  name: string;
  type: string;
  id: number;
  is_followed?: boolean;
  nav?: number;
  acc_nav?: number;
  day_growth?: string | number;
  week_growth?: string | number;
  month_growth?: string | number;
  three_month_growth?: string | number;
  six_month_growth?: string | number;
  year_growth?: string | number;
  current_year_growth?: string | number;
  manager?: string;
  last_update?: string;
}

// 我的关注-基金详情
interface FollowFundInfo {
  id: number;
  nav: number | null;
  code: string;
  name: string;
  type: string;
  acc_nav: number | null;
  day_growth?: number | null;
  week_growth?: number | null;
  month_growth?: number | null;
  three_month_growth?: number | null;
  six_month_growth?: number | null;
  year_growth?: number | null;
  current_year_growth?: number | null;
  manager?: string;
  last_update?: string;
}

// 我的关注-完整记录
export interface FollowFund {
  id: number;
  user_id: number;
  fund_code: string;
  remark?: string;
  fund_info: FollowFundInfo;
  created_at: string;
  updated_at: string;
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
export type AIProvider = "openai" | "deepseek" | "bailian";

export interface AIModelProfile {
  id: string;
  provider: AIProvider;
  displayName: string;
  apiKey: string;
  baseUrl: string;
  model: string;
  maxTokens: number;
  temperature: number;
  enabled: boolean;
}

export interface AIConfig {
  provider: AIProvider;
  models: AIModelProfile[];
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

export interface AIModelConfigCreateRequest {
  name: string;
  provider: string;
  base_url: string;
  model: string;
  max_output_tokens: number;
  temperature: number;
  timeout_seconds: number;
  enabled: boolean;
  extra_config?: Record<string, unknown>;
  api_key: string;
}

export interface AIModelConfigResponse {
  id: number;
  name: string;
  provider: string;
  base_url: string;
  model: string;
  api_key_configured: boolean;
  api_key_hint?: string;
  max_output_tokens: number;
  temperature: number;
  timeout_seconds: number;
  enabled: boolean;
  is_default: boolean;
  extra_config?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type AIModelConfigUpdateRequest = Partial<AIModelConfigCreateRequest>;

export interface AIModelConfigTestRequest extends AIModelConfigCreateRequest {
  message?: string;
}

export interface AIModelConfigTestResponse {
  success: boolean;
  message: string;
  latency_ms: number | null;
  model: string | null;
  usage: Record<string, unknown> | null;
}

export type AIModelConfigListResponse = AIModelConfigResponse[];

export type AIModelConfigDetailResponse = AIModelConfigResponse[];

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
