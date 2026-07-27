import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AIModelProfile, AIProvider, AppSettings } from "@/types/settings";

interface SettingsState {
  settings: AppSettings
  loading: boolean
  saved: boolean

  // Actions
  updateSettings: (partial: Partial<AppSettings>) => void
  updateAI: (ai: Partial<AppSettings['ai']>) => void
  setAIProvider: (provider: AIProvider) => void
  upsertAIModel: (model: AIModelProfile) => void
  deleteAIModel: (id: string) => void
  setAIModelEnabled: (id: string, enabled: boolean) => void
  updateNotify: (notify: Partial<AppSettings['notify']>) => void
  updateDataSource: (ds: Partial<AppSettings['dataSource']>) => void
  setLoading: (loading: boolean) => void
  setSaved: (saved: boolean) => void
  resetSettings: () => void
}

const createModelId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`

const defaultSettings: AppSettings = {
  ai: {
    provider: 'openai',
    models: [
      {
        id: 'openai-default',
        provider: 'openai',
        displayName: 'OpenAI 默认',
        apiKey: '',
        baseUrl: 'https://api.openai.com/v1',
        model: 'gpt-4o-mini',
        maxTokens: 4096,
        temperature: 0.7,
        enabled: true,
      },
    ],
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

const normalizeProvider = (p: unknown): AIProvider => {
  if (p === 'deepseek') return 'deepseek'
  if (p === 'bailian' || p === 'aliyun_bailian' || p === 'aliyun') return 'bailian'
  return 'openai'
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

      setAIProvider: (provider) =>
        set((state) => ({
          settings: {
            ...state.settings,
            ai: { ...state.settings.ai, provider },
          },
        })),

      upsertAIModel: (model) =>
        set((state) => {
          const exists = state.settings.ai.models.some((m) => m.id === model.id)
          const nextModels = exists
            ? state.settings.ai.models.map((m) => (m.id === model.id ? model : m))
            : [model, ...state.settings.ai.models]

          return {
            settings: {
              ...state.settings,
              ai: {
                ...state.settings.ai,
                models: nextModels,
              },
            },
          }
        }),

      deleteAIModel: (id) =>
        set((state) => ({
          settings: {
            ...state.settings,
            ai: {
              ...state.settings.ai,
              models: state.settings.ai.models.filter((m) => m.id !== id),
            },
          },
        })),

      setAIModelEnabled: (id, enabled) =>
        set((state) => {
          const current = state.settings.ai.models.find((m) => m.id === id)
          if (!current) return state

          const nextModels = state.settings.ai.models.map((m) => {
            if (m.provider !== current.provider) return m
            if (m.id === id) return { ...m, enabled }
            return enabled ? { ...m, enabled: false } : m
          })

          return {
            settings: {
              ...state.settings,
              ai: {
                ...state.settings.ai,
                models: nextModels,
              },
            },
          }
        }),

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
      version: 2,
      partialize: (state) => ({ settings: state.settings }),
      migrate: (persistedState) => {
        const state = persistedState as { settings?: Partial<AppSettings> } | undefined
        const settings = state?.settings
        const ai = settings?.ai as unknown

        if (ai && typeof ai === 'object' && 'models' in (ai as Record<string, unknown>)) {
          return persistedState
        }

        if (ai && typeof ai === 'object' && 'apiKey' in (ai as Record<string, unknown>)) {
          const old = ai as {
            provider?: unknown
            apiKey?: unknown
            baseUrl?: unknown
            model?: unknown
            maxTokens?: unknown
            temperature?: unknown
          }

          const provider = normalizeProvider(old.provider)
          const modelProfile: AIModelProfile = {
            id: createModelId(),
            provider,
            displayName:
              provider === 'deepseek'
                ? 'DeepSeek 默认'
                : provider === 'bailian'
                  ? '阿里云百炼 默认'
                  : 'OpenAI 默认',
            apiKey: typeof old.apiKey === 'string' ? old.apiKey : '',
            baseUrl: typeof old.baseUrl === 'string' ? old.baseUrl : '',
            model: typeof old.model === 'string' ? old.model : '',
            maxTokens: typeof old.maxTokens === 'number' ? old.maxTokens : 4096,
            temperature: typeof old.temperature === 'number' ? old.temperature : 0.7,
            enabled: true,
          }

          return {
            settings: {
              ...defaultSettings,
              ...settings,
              ai: { provider, models: [modelProfile] },
            },
          }
        }

        return {
          settings: {
            ...defaultSettings,
            ...settings,
          },
        }
      },
    },
  ),
)
