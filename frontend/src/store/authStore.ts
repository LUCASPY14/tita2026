import { create } from 'zustand'
import api from '../services/api'

interface User {
  id: number
  email: string
  nombre: string
  apellido: string
  rol: string
  cliente_id?: number
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (email: string, password: string) => {
    const { data } = await api.post('/token/', { email, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    set({ isAuthenticated: true, user: data.user || null })
},

  logout: () => {
    localStorage.clear()
    set({ user: null, isAuthenticated: false })
    window.location.href = '/login'
  },

  loadUser: async () => {
    if (!localStorage.getItem('access_token')) return
    try {
      const { data } = await api.get('/usuarios/usuarios/me/')
      set({ user: data, isAuthenticated: true })
    } catch {
      localStorage.clear()
      set({ user: null, isAuthenticated: false })
    }
  },
}))