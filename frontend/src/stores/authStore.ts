import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isGuestMode: boolean // 游客模式：点击了“暂不登录”
  
  // Actions
  login: (token: string, user: User) => void
  logout: () => void
  setGuestMode: (isGuest: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isGuestMode: false,

      login: (token, user) => set({ 
        token, 
        user, 
        isAuthenticated: true, 
        isGuestMode: false 
      }),
      
      logout: () => set({ 
        token: null, 
        user: null, 
        isAuthenticated: false,
        isGuestMode: false
      }),

      setGuestMode: (isGuest) => set({ isGuestMode: isGuest }),
    }),
    {
      name: 'auth-storage',
      // 只持久化 token 和 user，不持久化游客状态，保证刷新页面重新提示
      partialize: (state) => ({ 
        token: state.token, 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)
