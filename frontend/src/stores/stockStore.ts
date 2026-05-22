import { create } from 'zustand'
import type { Stock, StockPrice } from '@/types'

interface StockState {
  stocks: Stock[]
  prices: Record<string, StockPrice>
  selectedGroup: string
  loading: boolean
  lastUpdated: number | null

  // Actions
  setStocks: (stocks: Stock[]) => void
  addStock: (stock: Stock) => void
  removeStock: (code: string) => void
  updateStockPrice: (price: StockPrice) => void
  updatePrices: (prices: StockPrice[]) => void
  setSelectedGroup: (group: string) => void
  setLoading: (loading: boolean) => void
}

export const useStockStore = create<StockState>((set) => ({
  stocks: [],
  prices: {},
  selectedGroup: '全部',
  loading: false,
  lastUpdated: null,

  setStocks: (stocks) => set({ stocks }),

  addStock: (stock) =>
    set((state) => {
      const exists = state.stocks.some((s) => s.code === stock.code)
      if (exists) return state
      return { stocks: [...state.stocks, stock] }
    }),

  removeStock: (code) =>
    set((state) => ({
      stocks: state.stocks.filter((s) => s.code !== code),
    })),

  updateStockPrice: (price) =>
    set((state) => ({
      prices: { ...state.prices, [price.code]: price },
      lastUpdated: Date.now(),
    })),

  updatePrices: (prices) =>
    set((state) => {
      const newPrices = { ...state.prices }
      prices.forEach((p) => {
        newPrices[p.code] = p
      })
      return { prices: newPrices, lastUpdated: Date.now() }
    }),

  setSelectedGroup: (group) => set({ selectedGroup: group }),

  setLoading: (loading) => set({ loading }),
}))
