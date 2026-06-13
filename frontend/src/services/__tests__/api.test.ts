import { beforeEach, describe, it, expect, vi } from 'vitest'

// vi.hoisted: ejecuta ANTES de vi.mock y antes de los imports estáticos.
// Permite que las variables sean accesibles dentro del factory de vi.mock.
const mocks = vi.hoisted(() => {
  let _requestFn: ((config: Record<string, unknown>) => Record<string, unknown>) | null = null
  let _responseOkFn: ((res: unknown) => unknown) | null = null
  let _responseErrFn: ((err: unknown) => Promise<unknown>) | null = null

  const mockRetry = vi.fn()  // api(originalRequest) — retry tras refresh
  const mockPost = vi.fn()   // axios.post('/api/token/refresh/', ...)
  const mockToastError = vi.fn()

  const mockInstance = Object.assign(mockRetry, {
    interceptors: {
      request: {
        use(fn: (config: Record<string, unknown>) => Record<string, unknown>) {
          _requestFn = fn
        },
      },
      response: {
        use(
          okFn: (res: unknown) => unknown,
          errFn: (err: unknown) => Promise<unknown>,
        ) {
          _responseOkFn = okFn
          _responseErrFn = errFn
        },
      },
    },
  })

  return {
    mockInstance,
    mockRetry,
    mockPost,
    mockToastError,
    get requestFn() { return _requestFn },
    get responseOkFn() { return _responseOkFn },
    get responseErrFn() { return _responseErrFn },
  }
})

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mocks.mockInstance),
    post: mocks.mockPost,
  },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: mocks.mockToastError },
}))

// Importar api DESPUÉS de los mocks para que api.ts use las versiones mockeadas
import '../api'

// ─── helpers ──────────────────────────────────────────────────────────────────

function makeError401(extra: Record<string, unknown> = {}) {
  return {
    config: { headers: {} as Record<string, string>, _retry: false, ...extra },
    response: { status: 401 },
  }
}

// ─── tests ────────────────────────────────────────────────────────────────────

beforeEach(() => {
  localStorage.clear()
  vi.clearAllMocks()
})

describe('api — request interceptor', () => {
  it('agrega Bearer token cuando existe access_token en localStorage', () => {
    localStorage.setItem('access_token', 'mi_token')
    const config = { headers: {} as Record<string, string> }
    const result = mocks.requestFn!(config) as typeof config
    expect(result.headers.Authorization).toBe('Bearer mi_token')
  })

  it('no agrega Authorization cuando no hay token', () => {
    const config = { headers: {} as Record<string, string> }
    const result = mocks.requestFn!(config) as typeof config
    expect(result.headers.Authorization).toBeUndefined()
  })
})

describe('api — response interceptor (éxito)', () => {
  it('pasa la respuesta sin modificarla', () => {
    const response = { data: { ok: true }, status: 200 }
    expect(mocks.responseOkFn!(response)).toBe(response)
  })
})

describe('api — response interceptor (401 con refresh token)', () => {
  it('llama a /api/token/refresh/ cuando recibe 401', async () => {
    localStorage.setItem('access_token', 'viejo')
    localStorage.setItem('refresh_token', 'ref123')
    mocks.mockPost.mockResolvedValueOnce({ data: { access: 'nuevo', refresh: 'nuevo_ref' } })
    mocks.mockRetry.mockResolvedValueOnce({ data: 'ok' })

    await mocks.responseErrFn!(makeError401())

    expect(mocks.mockPost).toHaveBeenCalledWith('/api/token/refresh/', { refresh: 'ref123' })
  })

  it('actualiza localStorage con el nuevo access token', async () => {
    localStorage.setItem('access_token', 'viejo')
    localStorage.setItem('refresh_token', 'ref123')
    mocks.mockPost.mockResolvedValueOnce({ data: { access: 'nuevo_tok', refresh: 'nuevo_ref' } })
    mocks.mockRetry.mockResolvedValueOnce({ data: 'ok' })

    await mocks.responseErrFn!(makeError401())

    expect(localStorage.getItem('access_token')).toBe('nuevo_tok')
  })

  it('actualiza el refresh token si el servidor devuelve uno nuevo', async () => {
    localStorage.setItem('access_token', 'viejo')
    localStorage.setItem('refresh_token', 'ref_viejo')
    mocks.mockPost.mockResolvedValueOnce({ data: { access: 'nuevo', refresh: 'ref_nuevo' } })
    mocks.mockRetry.mockResolvedValueOnce({ data: 'ok' })

    await mocks.responseErrFn!(makeError401())

    expect(localStorage.getItem('refresh_token')).toBe('ref_nuevo')
  })

  it('reintenta la request original con el nuevo token', async () => {
    localStorage.setItem('access_token', 'viejo')
    localStorage.setItem('refresh_token', 'ref')
    mocks.mockPost.mockResolvedValueOnce({ data: { access: 'nuevo', refresh: 'nuevo_ref' } })
    mocks.mockRetry.mockResolvedValueOnce({ data: 'retried' })

    const result = await mocks.responseErrFn!(makeError401())

    expect(mocks.mockRetry).toHaveBeenCalledTimes(1)
    expect(result).toEqual({ data: 'retried' })
  })
})

describe('api — response interceptor (refresh fallido)', () => {
  it('limpia tokens de localStorage', async () => {
    localStorage.setItem('access_token', 'viejo')
    localStorage.setItem('refresh_token', 'ref')
    mocks.mockPost.mockRejectedValueOnce(new Error('Refresh failed'))

    await expect(mocks.responseErrFn!(makeError401())).rejects.toThrow()

    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('despacha el evento auth:logout', async () => {
    localStorage.setItem('access_token', 'viejo')
    localStorage.setItem('refresh_token', 'ref')
    mocks.mockPost.mockRejectedValueOnce(new Error('Refresh failed'))

    const listener = vi.fn()
    window.addEventListener('auth:logout', listener)

    await expect(mocks.responseErrFn!(makeError401())).rejects.toThrow()

    expect(listener).toHaveBeenCalledTimes(1)
    window.removeEventListener('auth:logout', listener)
  })

  it('muestra toast de sesión expirada', async () => {
    localStorage.setItem('access_token', 'viejo')
    localStorage.setItem('refresh_token', 'ref')
    mocks.mockPost.mockRejectedValueOnce(new Error('Refresh failed'))

    await expect(mocks.responseErrFn!(makeError401())).rejects.toThrow()

    expect(mocks.mockToastError).toHaveBeenCalledWith('Sesión expirada. Iniciá sesión nuevamente.')
  })
})

describe('api — error de red (sin response)', () => {
  it('muestra toast de sin conexión', async () => {
    const error = { config: {}, response: undefined }

    await expect(mocks.responseErrFn!(error)).rejects.toBeDefined()

    expect(mocks.mockToastError).toHaveBeenCalledWith(
      'Sin conexión con el servidor',
      { id: 'network-error' },
    )
  })
})
