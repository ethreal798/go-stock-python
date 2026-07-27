import request from './index'
import type { PageResult } from "@/types/common";
import type { KLineData, Stock, StockPrice } from "@/types/stock";

// 获取自选股列表
export const getStockList = () =>
  request.get<{ data: Stock[] }>('/stocks')

// 添加自选股
export const addStock = (data: { code: string; name: string; group?: string }) =>
  request.post('/stocks', data)

// 删除自选股
export const deleteStock = (code: string) =>
  request.delete(`/stocks/${code}`)

// 修改自选股备注/分组
export const updateStock = (code: string, data: Partial<Stock>) =>
  request.put(`/stocks/${code}`, data)

// 获取股票实时价格（批量）
export const getStockPrices = (codes: string[]) =>
  request.post<{ data: StockPrice[] }>('/stocks/prices', { codes })

// 获取单支股票实时价格
export const getStockPrice = (code: string) =>
  request.get<{ data: StockPrice }>(`/stocks/${code}/price`)

// 搜索股票
export const searchStock = (keyword: string) =>
  request.get<{ data: Stock[] }>('/stocks/search', { params: { keyword } })

// 获取K线数据
export const getKLineData = (
  code: string,
  params: { period: string; count?: number; startDate?: string; endDate?: string },
) => request.get<{ data: KLineData[] }>(`/stocks/${code}/kline`, { params })

// 获取股票基本信息
export const getStockInfo = (code: string) =>
  request.get(`/stocks/${code}/info`)

// 获取股票分组列表
export const getStockGroups = () =>
  request.get<{ data: string[] }>('/stocks/groups')

// 获取资金流向
export const getMoneyFlow = (code: string) =>
  request.get(`/stocks/${code}/money-flow`)

// 获取龙虎榜
export const getDragonTiger = (params?: { date?: string; page?: number; pageSize?: number }) =>
  request.get<{ data: PageResult<unknown> }>('/market/dragon-tiger', { params })
