import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest'

vi.mock('axios', () => ({
  default: { post: vi.fn() },
}))

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

import axios from 'axios'
import api from '../../services/api'
import { useAuthStore } from '../authStore'

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ user: null, isAuthenticated: false, pending2FA: null })
    vi.clearAllMocks()
    vi.useFakeTimers()
    // api.post returns a Promise by default so .catch() in logout doesn't throw
    vi.mocked(api.post).mockResolvedValue({ data: {} })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('initial isAuthenticated is false when no token', () => {
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('login stores tokens in localStorage and sets state', async () => {
    const mockData = {
      access: 'acc_tok',
      refresh: 'ref_tok',
      user: { id: 1, email: 'ana@test.com', nombre: 'Ana', apellido: 'L', rol: 'ADMIN' },
    }
    vi.mocked(axios.post).mockResolvedValueOnce({ data: mockData })

    await useAuthStore.getState().login('ana@test.com', 'pass123')

    expect(localStorage.getItem('access_token')).toBe('acc_tok')
    expect(localStorage.getItem('refresh_token')).toBe('ref_tok')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().user?.email).toBe('ana@test.com')
  })

  it('login calls the correct endpoint', async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({
      data: { access: 'a', refresh: 'r', user: null },
    })
    await useAuthStore.getState().login('x@y.com', 'pwd')
    expect(vi.mocked(axios.post)).toHaveBeenCalledWith('/api/token/', {
      email: 'x@y.com',
      password: 'pwd',
    })
  })

  it('login propagates errors', async () => {
    vi.mocked(axios.post).mockRejectedValueOnce(new Error('Invalid credentials'))
    await expect(
      useAuthStore.getState().login('bad@test.com', 'wrong')
    ).rejects.toThrow('Invalid credentials')
  })

  it('login sets pending2FA and returns false when server requires 2FA', async () => {
    vi.mocked(axios.post).mockResolvedValueOnce({
      data: { requires_2fa: true, pre_auth_token: 'pre_tok_123' },
    })
    const result = await useAuthStore.getState().login('user@test.com', 'pass')
    expect(result).toBe(false)
    expect(useAuthStore.getState().pending2FA).toBe('pre_tok_123')
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('verify2FA completes login using pre_auth_token', async () => {
    useAuthStore.setState({ pending2FA: 'pre_tok_123' })
    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        access: 'acc_2fa',
        refresh: 'ref_2fa',
        session_key: 'sess_2fa',
        user: { id: 3, email: 'u@test.com', nombre: 'U', apellido: 'V', rol: 'CAJERO' },
      },
    })
    await useAuthStore.getState().verify2FA('123456')
    expect(localStorage.getItem('access_token')).toBe('acc_2fa')
    expect(localStorage.getItem('session_key')).toBe('sess_2fa')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().pending2FA).toBeNull()
  })

  it('verify2FA throws when no pending2FA token', async () => {
    useAuthStore.setState({ pending2FA: null })
    await expect(useAuthStore.getState().verify2FA('123456')).rejects.toThrow('No hay 2FA pendiente')
  })

  it('cancelPending2FA clears pending2FA state', () => {
    useAuthStore.setState({ pending2FA: 'some_token' })
    useAuthStore.getState().cancelPending2FA()
    expect(useAuthStore.getState().pending2FA).toBeNull()
  })

  it('logout clears tokens and resets state', () => {
    localStorage.setItem('access_token', 'tok')
    localStorage.setItem('refresh_token', 'ref')
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 1, email: 'x', nombre: 'X', apellido: 'Y', rol: 'ADMIN', debe_cambiar_contrasena: false },
    })

    useAuthStore.getState().logout()

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('logout dispatches auth:logout event', () => {
    const listener = vi.fn()
    window.addEventListener('auth:logout', listener)
    useAuthStore.getState().logout()
    expect(listener).toHaveBeenCalledTimes(1)
    window.removeEventListener('auth:logout', listener)
  })

  it('logout fires server request when session_key is stored', () => {
    localStorage.setItem('session_key', 'sess_abc')
    localStorage.setItem('refresh_token', 'ref_tok')
    useAuthStore.setState({ isAuthenticated: true })

    useAuthStore.getState().logout()

    expect(vi.mocked(api.post)).toHaveBeenCalledWith('/usuarios/logout/', {
      session_key: 'sess_abc',
      refresh_token: 'ref_tok',
    })
  })

  it('loadUser does nothing when no access_token in localStorage', async () => {
    await useAuthStore.getState().loadUser()
    expect(vi.mocked(api.get)).not.toHaveBeenCalled()
  })

  it('loadUser sets user and isAuthenticated on success', async () => {
    localStorage.setItem('access_token', 'valid_tok')
    const mockUser = {
      id: 2, email: 'bob@test.com', nombre: 'Bob', apellido: 'S', rol: 'CAJERO',
    }
    vi.mocked(api.get).mockResolvedValueOnce({ data: mockUser })

    await useAuthStore.getState().loadUser()

    expect(useAuthStore.getState().user?.email).toBe('bob@test.com')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('loadUser clears tokens and state on API failure', async () => {
    localStorage.setItem('access_token', 'expired_tok')
    localStorage.setItem('refresh_token', 'ref')
    vi.mocked(api.get).mockRejectedValueOnce(new Error('401'))

    await useAuthStore.getState().loadUser()

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('resetInactivityTimer is a no-op when not authenticated', () => {
    useAuthStore.setState({ isAuthenticated: false })
    useAuthStore.getState().resetInactivityTimer()
    vi.advanceTimersByTime(16 * 60 * 1000)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('resetInactivityTimer schedules auto-logout after 15 minutes', () => {
    useAuthStore.setState({ isAuthenticated: true })
    useAuthStore.getState().resetInactivityTimer()

    vi.advanceTimersByTime(14 * 60 * 1000 + 59_000)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    vi.advanceTimersByTime(1001)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('global activity events reset inactivity timer when authenticated', () => {
    useAuthStore.setState({ isAuthenticated: true })
    useAuthStore.getState().resetInactivityTimer()

    // Advance 14 minutes without triggering logout yet
    vi.advanceTimersByTime(14 * 60 * 1000)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    // User activity resets the 15-minute window
    window.dispatchEvent(new MouseEvent('mousemove'))

    // Another 14 minutes — still authenticated because timer was reset
    vi.advanceTimersByTime(14 * 60 * 1000)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })
})

describe('authStore — inicialización del módulo con sesión previa', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.useFakeTimers()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('inicia el timer de inactividad si access_token ya existe al cargar el módulo', async () => {
    // access_token en localStorage hace que isAuthenticated initialice en true
    localStorage.setItem('access_token', 'tok')

    // vi.resetModules limpia la caché de módulos; el próximo import() crea
    // una instancia fresca de authStore que ejecuta el bloque de init
    vi.resetModules()
    const { useAuthStore: freshStore } = await import('../authStore')

    expect(freshStore.getState().isAuthenticated).toBe(true)

    // Si resetInactivityTimer fue invocado durante la inicialización,
    // avanzar 15 min + 1 s debe disparar el auto-logout
    vi.advanceTimersByTime(15 * 60 * 1000 + 1_000)
    expect(freshStore.getState().isAuthenticated).toBe(false)
  })
})
