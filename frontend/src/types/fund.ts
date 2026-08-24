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
  two_year_growth?: string | number;
  three_year_growth?: string | number;
  five_year_growth?: string | number;
  current_year_growth?: string | number;
  manager?: string;
  last_update?: string;
  latest_nav?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
}

/**
 * 基金排行榜条目 - 由 GET /api/v1/funds/ 返回
 */
export interface FundRankingItem {
  code: string;
  name: string;
  type: string;
  category: "open" | "money" | "exchange";
  data_date: string;
  latest: FundRankingLatestMetrics;
  is_in_watchlist: boolean;
}

/**
 * 排行榜 latest 指标（开放基金与货币基金字段有差异）
 * 所有字段均为可选，按 category 取用
 */
export interface FundRankingLatestMetrics {
  unit_nav?: number;
  accumulated_nav?: number;
  daily_growth_pct?: number;
  return_1w_pct?: number;
  return_1m_pct?: number;
  return_3m_pct?: number;
  return_6m_pct?: number;
  return_1y_pct?: number;
  return_2y_pct?: number;
  return_3y_pct?: number;
  return_5y_pct?: number;
  return_ytd_pct?: number;
  return_since_inception_pct?: number;
  income_per_10k?: number;
  annualized_7d_pct?: number;
  annualized_14d_pct?: number;
  annualized_28d_pct?: number;
  data_date?: string;
}

/**
 * GET /api/v1/funds/ 响应
 */
export interface FundRankingResponse {
  items: FundRankingItem[];
  total: number;
  page: number;
  limit: number;
  category: "open" | "money" | "exchange";
  sort: FundSortKey;
  period: string;
  order: "asc" | "desc";
}

/**
 * 排行榜 sort 键
 * 周期维度用于"涨跌幅"列排序；净值维度用于"累计净值/最新净值"列排序
 */
export type FundSortKey =
  | "1w"
  | "1m"
  | "3m"
  | "6m"
  | "1y"
  | "2y"
  | "3y"
  | "5y"
  | "ytd"
  | "since_inception"
  | "accumulated_nav"
  | "unit_nav"
  | "annualized_7d_pct"
  | "income_per_10k";

/**
 * 周期维度 sort 键（仅涨跌幅/时间分段 Tab 使用）
 */
export type FundPeriodSortKey = Exclude<
  FundSortKey,
  "accumulated_nav" | "unit_nav"
>;

/**
 * 排行榜 category（当前 UI 仅开放/货币）
 */
export type FundCategoryKey = "open" | "money" | "exchange";

/**
 * 基金表格行数据 - 用于 FundTable 组件
 * 统一了搜索结果和关注列表的数据结构
 */
export interface FundTableRow {
  id: number;
  code: string;
  name: string;
  type: string;
  remark?: string;
  is_followed: boolean;
  latest?: FundLatestMetrics;
  last_seen_data_date?: string;
  category?: "open" | "money" | "exchange";
  is_in_watchlist?: boolean;
}

export interface FundLatestMetrics {
  metric_kind: string;
  data_date: string;
  unit_nav: number;
  accumulated_nav: number;
  daily_growth_pct: number;
  return_1w_pct: number;
  return_1m_pct: number;
  return_3m_pct: number;
  return_6m_pct: number;
  return_1y_pct: number;
  return_2y_pct: number;
  return_3y_pct: number;
  return_ytd_pct: number;
  return_since_inception_pct: number;
  income_per_10k?: number;
  annualized_7d_pct?: number;
  annualized_14d_pct?: number;
  annualized_28d_pct?: number;
}

export interface FollowFundInfo {
  id: number;
  code: string;
  name: string;
  type: string;
  category?: string;
  status?: string;
  last_seen_data_date?: string;
  last_seen_at?: string;
  latest?: FundLatestMetrics;
  is_in_watchlist?: boolean;
}

export interface FollowFund {
  id: number;
  user_id: number;
  fund_code: string;
  remark?: string;
  fund_info: FollowFundInfo;
  created_at: string;
  updated_at: string;
}

// ============================================================
// 基金业绩走势
// ============================================================

export type PerformancePoint = [string, number];

export interface PerformanceSeries {
  key: string;
  name: string;
  latest_return_pct: number;
  points: PerformancePoint[];
}

export interface PerformanceTrendResponse {
  fund_code: string;
  period: string;
  start_date: string;
  end_date: string;
  is_hb: boolean;
  fetched_at: string;
  is_stale: boolean;
  series: PerformanceSeries[];
}

// ============================================================
// 基金详情
// ============================================================

export interface FundDetailLatest {
  data_date: string;
  unit_nav?: number;
  accumulated_nav?: number;
  daily_growth_pct?: number;
  return_1w_pct?: number | null;
  return_1m_pct?: number | null;
  return_3m_pct?: number | null;
  return_6m_pct?: number | null;
  return_1y_pct?: number | null;
  return_2y_pct?: number | null;
  return_3y_pct?: number | null;
  return_5y_pct?: number | null;
  return_ytd_pct?: number | null;
  return_since_inception_pct?: number | null;
  income_per_10k?: number;
  annualized_7d_pct?: number;
  annualized_14d_pct?: number;
  annualized_28d_pct?: number;
}

export interface FundDetailResponse {
  id: number;
  code: string;
  name: string;
  fund_type: string;
  is_hb: boolean;
  is_exchange: boolean;
  latest: FundDetailLatest | null;
  is_in_watchlist: boolean;
}
