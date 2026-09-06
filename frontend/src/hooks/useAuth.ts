import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AuthUser } from '@/types'
import { api } from '@/lib/api'

interface AuthState {
  user: AuthUser | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuth = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,

      login: async (email, password) => {
        const { data } = await api.post('/auth/login', { email, password })
        localStorage.setItem('classos_token', data.access_token)
        const { data: me } = await api.get('/auth/me')
        set({ user: me, token: data.access_token })
      },

      logout: () => {
        localStorage.removeItem('classos_token')
        set({ user: null, token: null })
      },
    }),
    { name: 'classos-auth', partialize: (s) => ({ user: s.user, token: s.token }) }
  )
)
