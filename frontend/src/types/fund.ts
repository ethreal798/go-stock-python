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
