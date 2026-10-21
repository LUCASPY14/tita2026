import axios from 'axios'
import { create } from 'zustand'
import api from '../services/api'

const INACTIVITY_MS = 60 * 60 * 1000 // 60 minutes

interface User {
  id_usuario: number
  email: string
  nombre: string
  apellido: string
  rol: string
  cliente_id?: number
  debe_cambiar_contrasena: boolean
  tiene_2fa_activo?: boolean
  tiene_webauthn?: boolean
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  /** pre_auth_token when the server requires 2FA to complete login */
  pending2FA: string | null
  /** true si la cuenta con pending2FA también tiene huella/Face ID configurada */
  pendingTieneWebauthn: boolean
  /** método de 2FA configurado para la cuenta con pending2FA ('TOTP' | 'WHATSAPP' | null) */
  pendingMetodo2FA: string | null
  /** true → full login done; false → 2FA step required (pending2FA is set) */
  login: (email: string, password: string) => Promise<boolean>
  verify2FA: (codigo: string) => Promise<void>
  verifyWebAuthn: (credential: unknown) => Promise<void>
  /** reenvía el código de 2FA por WhatsApp durante el login; devuelve el teléfono enmascarado */
  enviarCodigoWhatsapp2FA: () => Promise<string>
  cancelPending2FA: () => void
  logout: () => void
  loadUser: () => Promise<void>
  resetInactivityTimer: () => void
}

let inactivityTimer: ReturnType<typeof setTimeout> | undefined
// Reentrancy guard: dispatchEvent('auth:logout') es síncrono y AuthMonitor
// reacciona llamando a logout() de nuevo — sin esto, cada logout() vuelve a
// dispatchear y dispara una recursión infinita síncrona.
let loggingOut = false

function clearInactivityTimer() {
  if (inactivityTimer !== undefined) {
    clearTimeout(inactivityTimer)
    inactivityTimer = undefined
  }
}

function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('session_key')
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  pending2FA: null,
  pendingTieneWebauthn: false,
  pendingMetodo2FA: null,

  login: async (email: string, password: string): Promise<boolean> => {
    const { data } = await axios.post('/api/token/', { email, password })
    if (data.requires_2fa) {
      set({
        pending2FA: data.pre_auth_token,
        pendingTieneWebauthn: !!data.tiene_webauthn,
        pendingMetodo2FA: data.metodo_2fa ?? null,
      })
      return false
    }
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    if (data.session_key) localStorage.setItem('session_key', data.session_key)
    set({ isAuthenticated: true, user: data.user || null, pending2FA: null, pendingTieneWebauthn: false, pendingMetodo2FA: null })
    get().resetInactivityTimer()
    return true
  },

  verify2FA: async (codigo: string): Promise<void> => {
    const preAuthToken = get().pending2FA
    if (!preAuthToken) throw new Error('No hay 2FA pendiente')
    const { data } = await api.post('/usuarios/2fa/login/', {
      pre_auth_token: preAuthToken,
      codigo,
    })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    if (data.session_key) localStorage.setItem('session_key', data.session_key)
    set({ isAuthenticated: true, user: data.user || null, pending2FA: null, pendingTieneWebauthn: false, pendingMetodo2FA: null })
    get().resetInactivityTimer()
  },

  verifyWebAuthn: async (credential: unknown): Promise<void> => {
    const preAuthToken = get().pending2FA
    if (!preAuthToken) throw new Error('No hay 2FA pendiente')
    const { data } = await api.post('/usuarios/webauthn/login-verificar/', {
      pre_auth_token: preAuthToken,
      credential,
    })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    if (data.session_key) localStorage.setItem('session_key', data.session_key)
    set({ isAuthenticated: true, user: data.user || null, pending2FA: null, pendingTieneWebauthn: false, pendingMetodo2FA: null })
    get().resetInactivityTimer()
  },

  enviarCodigoWhatsapp2FA: async (): Promise<string> => {
    const preAuthToken = get().pending2FA
    if (!preAuthToken) throw new Error('No hay 2FA pendiente')
    const { data } = await api.post('/usuarios/2fa/login/whatsapp/enviar/', {
      pre_auth_token: preAuthToken,
    })
    return data.telefono ?? ''
  },

  cancelPending2FA: () => {
    set({ pending2FA: null, pendingTieneWebauthn: false, pendingMetodo2FA: null })
  },

  logout: () => {
    if (loggingOut) return
    loggingOut = true
    try {
      clearInactivityTimer()
      // Fire-and-forget: mark session inactive on the server
      const sessionKey = localStorage.getItem('session_key')
      const refreshToken = localStorage.getItem('refresh_token')
      if (sessionKey) {
        api.post('/usuarios/logout/', {
          session_key: sessionKey,
          refresh_token: refreshToken,
        }).catch(() => {})
      }
      clearTokens()
      set({ user: null, isAuthenticated: false, pending2FA: null })
      window.dispatchEvent(new Event('auth:logout'))
    } finally {
      loggingOut = false
    }
  },

  loadUser: async () => {
    if (!localStorage.getItem('access_token')) return
    try {
      const { data } = await api.get('/usuarios/usuarios/me/')
      set({ user: data, isAuthenticated: true })
      get().resetInactivityTimer()
    } catch {
      clearInactivityTimer()
      clearTokens()
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

  // Pausar el timer de inactividad mientras la pestaña está en segundo plano:
  // si no, un trámite externo (ej. catastro de tarjeta en Bancard, con OTP del
  // banco de por medio) puede dejar el timer de 60 min corriendo mientras el
  // navegador suspende el JS en background, y disparar un logout() apenas se
  // reanuda — justo al volver del banco, sin que el usuario estuviera inactivo
  // en la app en ningún momento real.
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      clearInactivityTimer()
    } else if (useAuthStore.getState().isAuthenticated) {
      useAuthStore.getState().resetInactivityTimer()
    }
  })

  // Start inactivity timer immediately on page reload if already authenticated
  if (useAuthStore.getState().isAuthenticated) {
    useAuthStore.getState().resetInactivityTimer()
  }
}
