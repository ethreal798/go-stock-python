import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'


interface AuthState {
  token_type: string | null
  access_token: string | null
  isAuthenticated: boolean
  isGuestMode: boolean // 游客模式：点击了“暂不登录”
  // Actions
  login: (access_token: string, token_type: string) => void
  logout: () => void
  setGuestMode: (isGuest: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token_type: null, 
      access_token: null,
      isAuthenticated: false,
      isGuestMode: false,

      login: (access_token, token_type) => set({ 
        access_token,   
        token_type,   
        isAuthenticated: true, 
        isGuestMode: false 
      }),
      
      logout: () => set({ 
        access_token: null, 
        token_type: null, 
        isAuthenticated: false,
        isGuestMode: false
      }),

      setGuestMode: (isGuest) => set({ isGuestMode: isGuest }),
    }),
    {
      name: 'auth-storage',
      // 将数据存储在 localStorage 中
      storage: createJSONStorage(() => localStorage), 
      // 只持久化 token 和 user，不持久化游客状态，保证刷新页面重新提示
        partialize: (state) => ({ 
        access_token: state.access_token, 
        token_type: state.token_type || null , 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)
