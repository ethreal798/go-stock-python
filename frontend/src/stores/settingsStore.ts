import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AppSettings } from '@/types'

interface SettingsState {
  settings: AppSettings
  loading: boolean
  saved: boolean

  // Actions
  updateSettings: (partial: Partial<AppSettings>) => void
  updateAI: (ai: Partial<AppSettings['ai']>) => void
  updateNotify: (notify: Partial<AppSettings['notify']>) => void
  updateDataSource: (ds: Partial<AppSettings['dataSource']>) => void
  setLoading: (loading: boolean) => void
  setSaved: (saved: boolean) => void
  resetSettings: () => void
}

const defaultSettings: AppSettings = {
  ai: {
    provider: 'openai',
    apiKey: '',
    baseUrl: 'https://api.openai.com/v1',
    model: 'gpt-4o-mini',
    maxTokens: 4096,
    temperature: 0.7,
  },
  notify: {
    dingdingEnabled: false,
    dingdingToken: '',
    dingdingSecret: '',
    emailEnabled: false,
    emailSmtp: '',
    emailFrom: '',
    emailTo: '',
  },
  dataSource: {
    tushareToken: '',
    iwencaiEnabled: false,
  },
  theme: 'light',
  language: 'zh-CN',
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      loading: false,
      saved: false,

      updateSettings: (partial) =>
        set((state) => ({
          settings: { ...state.settings, ...partial },
        })),

      updateAI: (ai) =>
        set((state) => ({
          settings: {
            ...state.settings,
            ai: { ...state.settings.ai, ...ai },
          },
        })),

      updateNotify: (notify) =>
        set((state) => ({
          settings: {
            ...state.settings,
            notify: { ...state.settings.notify, ...notify },
          },
        })),

      updateDataSource: (ds) =>
        set((state) => ({
          settings: {
            ...state.settings,
            dataSource: { ...state.settings.dataSource, ...ds },
          },
        })),

      setLoading: (loading) => set({ loading }),

      setSaved: (saved) => set({ saved }),

      resetSettings: () => set({ settings: defaultSettings }),
    }),
    {
      name: 'go-stock-settings',
      partialize: (state) => ({ settings: state.settings }),
    },
  ),
)
