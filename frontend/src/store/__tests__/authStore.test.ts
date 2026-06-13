import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest'

vi.mock('axios', () => ({
  default: { post: vi.fn() },
}))

vi.mock('../../services/api', () => ({
  default: { get: vi.fn() },
}))

import axios from 'axios'
import api from '../../services/api'
import { useAuthStore } from '../authStore'

describe('authStore', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ user: null, isAuthenticated: false })
    vi.clearAllMocks()
    vi.useFakeTimers()
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

  it('logout clears tokens and resets state', () => {
    localStorage.setItem('access_token', 'tok')
    localStorage.setItem('refresh_token', 'ref')
    useAuthStore.setState({
      isAuthenticated: true,
      user: { id: 1, email: 'x', nombre: 'X', apellido: 'Y', rol: 'ADMIN' },
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
    // advance past the 15-minute timeout — logout should NOT be triggered
    vi.advanceTimersByTime(16 * 60 * 1000)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })
})
