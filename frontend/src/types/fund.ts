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

export interface FollowFundInfo {
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

export interface FollowFund {
  id: number;
  user_id: number;
  fund_code: string;
  remark?: string;
  fund_info: FollowFundInfo;
  created_at: string;
  updated_at: string;
}
