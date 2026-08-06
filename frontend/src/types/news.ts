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

export interface NewsSourceItem {
  code: string;
  name: string;
}

export interface FlashOverviewTopic {
  name: string;
  news_count: number;
}

export interface FlashOverviewResponse {
  total_count: number;
  important_count: number;
  top_topics: FlashOverviewTopic[];
}

export interface NewsFlashSource {
  code: string;
  name: string;
}

export interface NewsFlashTopic {
  name: string;
}

export interface NewsFlashEntity {
  type: string;
  name: string;
  symbol?: string;
}

export interface NewsFlashItem {
  id: number;
  source: NewsFlashSource;
  content_type: string;
  title?: string | null;
  content: string;
  is_source_important: boolean;
  published_at: string;
  topics: NewsFlashTopic[];
  entities: NewsFlashEntity[];
  relations: unknown[];
}

export interface NewsFlashCursor {
  cursor_id: number;
  cursor_time: string;
}

export interface NewsFlashListResponse {
  items: NewsFlashItem[];
  next_cursor: NewsFlashCursor | null;
  has_more: boolean;
}

export interface FlashUpdatesResponse {
  items: NewsFlashItem[];
  sync_id: number;
  has_more: boolean;
  cursortime?: string;
}
