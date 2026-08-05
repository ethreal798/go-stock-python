import request from "./index";
import type {
  FlashOverviewResponse,
  FlashUpdatesResponse,
  NewsFlashListResponse,
  NewsSourceItem,
} from "@/types/news";

export const getNewsSources = () => request.get<NewsSourceItem[]>("/news/sources");

export const getFlashOverview = (params: {
  period: "today" | "week" | "all";
  source: string;
  topic_limit: number;
}) => request.get<FlashOverviewResponse>("/news/flash/overview", { params });

export const getFlashList = (params: {
  source?: string;
  period: "today" | "week" | "all";
  important_only?: boolean;
  limit: number;
  cursor_id?: number;
  cursor_time?: string;
}) => request.get<NewsFlashListResponse>("/news/flash", { params });

export const getFlashUpdates = (params: {
  after_id: number;
  source?: string;
  period: "today" | "week" | "all";
  important_only?: boolean;
  limit: number;
}) => request.get<FlashUpdatesResponse>("/news/flash/updates", { params });
