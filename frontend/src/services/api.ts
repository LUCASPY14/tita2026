import axios from 'axios'
import toast from 'react-hot-toast'

const api = axios.create({
  baseURL: '/api/v1',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ` + token
  }
  return config
})

// Queue for requests that arrive while a token refresh is already in flight
let isRefreshing = false
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token!)
  })
  failedQueue = []
}

const SESION_CODES_SIN_RETRY = new Set(['sesion_reemplazada', 'sesion_expirada', 'sesion_no_encontrada'])

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const code = error.response?.data?.code

    // La sesión de este dispositivo ya no existe (se cerró al loguearse en
    // otro, o expiró por inactividad) — reintentar con refresh no sirve,
    // porque el refresh token también lleva la sesión vieja: se saca al
    // usuario directo en vez de reintentar en loop silencioso.
    if (error.response?.status === 401 && SESION_CODES_SIN_RETRY.has(code)) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      toast.error(error.response.data.detail || 'Tu sesión ya no está activa. Iniciá sesión nuevamente.')
      window.dispatchEvent(new Event('auth:logout'))
      return Promise.reject(error)
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // Park this request until the in-flight refresh completes
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ` + token
          return api(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/token/refresh/', { refresh: refreshToken })
          localStorage.setItem('access_token', data.access)
          if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
          processQueue(null, data.access)
          originalRequest.headers.Authorization = `Bearer ` + data.access
          return api(originalRequest)
        } catch (refreshError) {
          processQueue(refreshError, null)
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          toast.error('Sesión expirada. Iniciá sesión nuevamente.')
          window.dispatchEvent(new Event('auth:logout'))
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }
    }

    if (!error.response) {
      toast.error('Sin conexión con el servidor', { id: 'network-error' })
    }
    return Promise.reject(error)
  }
)

export default api
