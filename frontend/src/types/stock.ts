export interface Stock {
  code: string;
  name: string;
  market: string;
  group?: string;
  remark?: string;
}

export interface StockPrice {
  code: string;
  name: string;
  price: number;
  change: number;
  changeRate: number;
  open: number;
  high: number;
  low: number;
  preClose: number;
  volume: number;
  amount: number;
  turnover?: number;
  pe?: number;
  pb?: number;
  mktCap?: number;
  timestamp: string;
}

export interface KLineData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
