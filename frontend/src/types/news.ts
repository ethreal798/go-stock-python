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
