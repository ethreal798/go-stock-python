export interface MarketIndex {
  code: string;
  name: string;
  price: number;
  change: number;
  changeRate: number;
}

export interface HotStock {
  rank: number;
  code: string;
  name: string;
  price: number;
  changeRate: number;
  hotValue: number;
}
