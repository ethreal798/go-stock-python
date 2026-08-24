import request from "./index";
import type {
  FollowFund,
  FollowFundInfo,
  FundRankingResponse,
  FundSortKey,
  FundCategoryKey,
  PerformanceTrendResponse,
  FundDetailResponse,
} from "@/types/fund";

export type FundRangeKey =
  | "day"
  | "week"
  | "month"
  | "three_month"
  | "six_month"
  | "year"
  | "two_year"
  | "three_year"
  | "five_year";

// 获取关注的基金列表（watchlist）
export const getFollowedFunds = () =>
  request.get<FollowFund[]>("/funds/watchlist");

// 添加关注基金
export const followFund = (data: { fund_code: string; remark?: string }) =>
  request.post("/funds/watchlist", data);

// 取消关注基金（可选，您没提但一般会有，先加上）
export const unfollowFund = (fund_code: string) =>
  request.delete(`/funds/watchlist/${fund_code}`);

// 搜索基金 - 返回基金信息列表（含净值、增长率等详细数据）
export const searchFund = (params: {
  keyword: string;
  page?: number;
  limit?: number;
  range?: FundRangeKey;
  fund_type?: string;
}) => request.get<FollowFundInfo[]>("/funds/search", { params });

// 基金排行榜（FundMarket 页面主接口）
export const getFundRanking = (params: {
  category: FundCategoryKey;
  sort?: FundSortKey;
  order?: "asc" | "desc";
  page?: number;
  limit?: number;
}) => request.get<FundRankingResponse>("/funds/", { params });

// 获取基金详情
export const getFundDetail = (code: string) =>
  request.get<FundDetailResponse>(`/funds/${code}`);

// 获取基金业绩走势
export const getFundPerformanceTrend = (code: string, period: string) =>
  request.get<PerformanceTrendResponse>(`/funds/${code}/performance-trend`, {
    params: { period },
  });
