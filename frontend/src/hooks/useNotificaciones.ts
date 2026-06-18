import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'

const POLL_MS = 30_000
const RECONNECT_MS = 5_000

function buildWsUrl(): string {
  const token = localStorage.getItem('access_token') ?? ''
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/notificaciones/?token=${token}`
}

/**
 * Global WebSocket hook for the parents portal.
 * Opens a single connection while the layout is mounted, shows a toast
 * on each incoming notification, and exposes the unread count for the badge.
 *
 * Falls back to 30-second REST polling when the socket is offline.
 * `clearUnread()` should be called when the user opens the notifications page.
 */
export function useNotificaciones() {
  const { user } = useAuthStore()
  const [unreadCount, setUnreadCount] = useState(0)
  const [wsOnline, setWsOnline] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const connectWsRef = useRef<(() => void) | null>(null)

  const fetchCount = useCallback(async () => {
    if (!user) return
    try {
      const { data } = await api.get('/notificaciones/notificaciones/', {
        params: { leida: false, page_size: 1 },
      })
      setUnreadCount(data.count ?? 0)
    } catch { /* ignore network errors silently */ }
  }, [user])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { fetchCount() }, [fetchCount])

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket(buildWsUrl())
    wsRef.current = ws

    ws.onopen = () => {
      setWsOnline(true)
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const notif: { titulo?: string } = JSON.parse(event.data)
        setUnreadCount(prev => prev + 1)
        toast(notif.titulo ?? 'Nueva notificación', { icon: '🔔' })
      } catch { /* ignore malformed frames */ }
    }

    ws.onclose = () => {
      setWsOnline(false)
      reconnectTimer.current = setTimeout(() => connectWsRef.current?.(), RECONNECT_MS)
    }

    ws.onerror = () => ws.close()
  }, [])

  useEffect(() => { connectWsRef.current = connectWs }, [connectWs])

  useEffect(() => {
    if (!user) return
    connectWs()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connectWs, user])

  // Polling fallback when WS is offline
  useEffect(() => {
    if (wsOnline) return
    const id = setInterval(fetchCount, POLL_MS)
    return () => clearInterval(id)
  }, [wsOnline, fetchCount])

  const clearUnread = useCallback(() => setUnreadCount(0), [])

  return { unreadCount, clearUnread }
}
