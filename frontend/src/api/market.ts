import request from "./index";
import type { MarketIndex, HotStock, NewsItem } from "@/types";

// 获取龙虎榜数据
export const getDragonTiger = () => request.get("/market/dragon-tiger");
// 获取市场主要指数
export const getMarketIndexes = () =>
  request.get<{ data: MarketIndex[] }>("/market/indexes");

// 获取热股榜
export const getHotStocks = (params?: { market?: string; count?: number }) =>
  request.get<{ data: HotStock[] }>("/market/hot-stocks", { params });

// 获取涨停股
export const getLimitUpStocks = (params?: { date?: string }) =>
  request.get("/market/limit-up", { params });

// 获取跌停股
export const getLimitDownStocks = (params?: { date?: string }) =>
  request.get("/market/limit-down", { params });

// 获取异动股
export const getAbnormalStocks = () => request.get("/market/abnormal");

// 获取行业板块行情
export const getSectorData = (params?: {
  type?: "industry" | "concept" | "area";
}) => request.get("/market/sectors", { params });

// 获取市场资金流向
export const getMarketMoneyFlow = () => request.get("/market/money-flow");

// 获取融资融券数据
export const getMarginData = (params?: { page?: number; pageSize?: number }) =>
  request.get("/market/margin", { params });

// 获取新闻列表
export const getNewsList = (params?: {
  count:number;
  page?: number;
  relevant_only?:boolean;
}) => request.get<NewsItem[]>("/news/market", { params });

// 获取快讯/电报
export const getFlashNews = (params?: {
  count: number;
  page: number;
  source: string;
}) => request.get<NewsItem[]>("/news/telegraph", { params });

// 获取全球市场数据
export const getGlobalMarket = () => request.get("/market/global");

// 获取A股市场统计
export const getMarketStatistic = () => request.get("/market/statistic");
