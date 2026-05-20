import axios from 'axios'
import { create } from 'zustand'
import api from '../services/api'

const INACTIVITY_MS = 15 * 60 * 1000 // 15 minutes

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
  resetInactivityTimer: () => void
}

let inactivityTimer: ReturnType<typeof setTimeout> | undefined

function clearInactivityTimer() {
  if (inactivityTimer !== undefined) {
    clearTimeout(inactivityTimer)
    inactivityTimer = undefined
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),

  login: async (email: string, password: string) => {
    const { data } = await axios.post('/api/token/', { email, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    set({ isAuthenticated: true, user: data.user || null })
    get().resetInactivityTimer()
  },

  logout: () => {
    clearInactivityTimer()
    localStorage.clear()
    set({ user: null, isAuthenticated: false })
    window.location.href = '/login'
  },

  loadUser: async () => {
    if (!localStorage.getItem('access_token')) return
    try {
      const { data } = await api.get('/usuarios/usuarios/me/')
      set({ user: data, isAuthenticated: true })
      get().resetInactivityTimer()
    } catch {
      clearInactivityTimer()
      localStorage.clear()
      set({ user: null, isAuthenticated: false })
    }
  },

  resetInactivityTimer: () => {
    if (!get().isAuthenticated) return
    clearInactivityTimer()
    inactivityTimer = setTimeout(() => {
      get().logout()
    }, INACTIVITY_MS)
  },
}))

// Track user activity globally and reset inactivity timer
if (typeof window !== 'undefined') {
  const ACTIVITY_EVENTS = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']
  const handleActivity = () => {
    const store = useAuthStore.getState()
    if (store.isAuthenticated) store.resetInactivityTimer()
  }
  ACTIVITY_EVENTS.forEach((event) =>
    window.addEventListener(event, handleActivity, { passive: true })
  )
}
