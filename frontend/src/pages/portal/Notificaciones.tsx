import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  Bell, AlertTriangle, CreditCard, UtensilsCrossed,
  Calendar, Info, CheckCheck, RefreshCw, Wifi, WifiOff,
} from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Spinner from '../../components/ui/Spinner'
import Button from '../../components/ui/Button'
import type { LucideIcon } from 'lucide-react'

const POLL_INTERVAL_MS = 30_000
const WS_RECONNECT_MS  = 5_000

interface Notificacion {
  id: number
  tipo: string
  titulo: string
  mensaje: string
  destino: string
  leida: boolean
  fecha_envio: string
}

const TIPO_ICON: Record<string, LucideIcon> = {
  SALDO_BAJO:  AlertTriangle,
  RECARGA:     CreditCard,
  CONSUMO:     UtensilsCrossed,
  VENCIMIENTO: Calendar,
  ALMUERZO:    UtensilsCrossed,
  SISTEMA:     Info,
  VENTA_DEUDA: AlertTriangle,
}

const TIPO_COLOR: Record<string, string> = {
  SALDO_BAJO:  'text-amber-500',
  RECARGA:     'text-blue-500',
  CONSUMO:     'text-green-500',
  VENCIMIENTO: 'text-orange-500',
  ALMUERZO:    'text-green-500',
  SISTEMA:     'text-slate-400',
  VENTA_DEUDA: 'text-red-500',
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function buildWsUrl(): string {
  const token = localStorage.getItem('access_token') ?? ''
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/notificaciones/?token=${token}`
}

export default function PortalNotificaciones() {
  const { user } = useAuthStore()
  const [notifs, setNotifs]               = useState<Notificacion[]>([])
  const [loading, setLoading]             = useState(true)
  const [marcando, setMarcando]           = useState<number | null>(null)
  const [marcandoTodas, setMarcandoTodas] = useState(false)
  const [lastUpdated, setLastUpdated]     = useState<Date | null>(null)
  const [refreshing, setRefreshing]       = useState(false)
  const [wsOnline, setWsOnline]           = useState(false)
  const isFetchingRef  = useRef(false)
  const wsRef          = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const connectWsRef   = useRef<() => void>(() => {})

  // ── REST fetch (initial load + polling fallback) ───────────────────────────

  const cargar = useCallback(async (silent = false) => {
    if (!user) return
    if (isFetchingRef.current) return
    isFetchingRef.current = true
    if (!silent) setLoading(true)
    else setRefreshing(true)
    try {
      const { data } = await api.get('/notificaciones/notificaciones/', {
        params: { usuario: user.id, ordering: '-fecha_envio', page_size: 50 },
      })
      setNotifs(prev => {
        const next: Notificacion[] = data.results || []
        const prevUnread = prev.filter(n => !n.leida).length
        const nextUnread = next.filter(n => !n.leida).length
        if (silent && nextUnread > prevUnread) {
          toast('Nueva notificación', { icon: '🔔' })
        }
        return next
      })
      setLastUpdated(new Date())
    } catch {
      if (!silent) toast.error('Error al cargar notificaciones')
    } finally {
      isFetchingRef.current = false
      if (!silent) setLoading(false)
      else setRefreshing(false)
    }
  }, [user])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargar() }, [cargar])

  // ── WebSocket ──────────────────────────────────────────────────────────────

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
        const notif: Notificacion = JSON.parse(event.data)
        setNotifs(prev => {
          if (prev.find(n => n.id === notif.id)) return prev
          toast('Nueva notificación', { icon: '🔔' })
          return [notif, ...prev]
        })
        setLastUpdated(new Date())
      } catch { /* ignore malformed frames */ }
    }

    ws.onclose = () => {
      setWsOnline(false)
      // reconnect after a short delay (use ref to avoid TDZ access)
      reconnectTimer.current = setTimeout(() => connectWsRef.current(), WS_RECONNECT_MS)
    }

    ws.onerror = () => ws.close()
  }, [])

  useEffect(() => {
    // keep ref in sync so the onclose closure can call the latest version
    connectWsRef.current = connectWs
  })

  useEffect(() => {
    connectWs()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connectWs])

  // ── Polling fallback — only runs when WS is offline ───────────────────────

  useEffect(() => {
    if (wsOnline) return
    const id = setInterval(() => cargar(true), POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [wsOnline, cargar])

  // ── Mark as read ──────────────────────────────────────────────────────────

  const marcarLeida = async (id: number) => {
    setMarcando(id)
    try {
      await api.patch(`/notificaciones/notificaciones/${id}/`, { leida: true })
      setNotifs(prev => prev.map(n => n.id === id ? { ...n, leida: true } : n))
    } catch {
      toast.error('Error al actualizar')
    } finally {
      setMarcando(null)
    }
  }

  const marcarTodas = async () => {
    const pendientes = notifs.filter(n => !n.leida)
    if (pendientes.length === 0) return
    setMarcandoTodas(true)
    try {
      await Promise.all(
        pendientes.map(n => api.patch(`/notificaciones/notificaciones/${n.id}/`, { leida: true }))
      )
      setNotifs(prev => prev.map(n => ({ ...n, leida: true })))
      toast.success('Todas marcadas como leídas')
    } catch {
      toast.error('Error al marcar algunas notificaciones')
    } finally {
      setMarcandoTodas(false)
    }
  }

  if (loading) return <Spinner className="mt-12" />

  const noLeidas = notifs.filter(n => !n.leida).length

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Notificaciones</h1>
          <div className="flex items-center gap-2 mt-0.5">
            {noLeidas > 0 && (
              <p className="text-sm text-amber-600">{noLeidas} sin leer</p>
            )}
            {lastUpdated && (
              <p className="text-xs text-slate-400">
                · actualizado {lastUpdated.toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' })}
              </p>
            )}
            <span
              title={wsOnline ? 'Tiempo real activo' : 'Sin tiempo real — actualizando cada 30s'}
              className="flex items-center"
            >
              {wsOnline
                ? <Wifi className="w-3.5 h-3.5 text-green-500" />
                : <WifiOff className="w-3.5 h-3.5 text-slate-300" />
              }
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => cargar(true)}
            disabled={refreshing}
            aria-label="Actualizar notificaciones"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer disabled:opacity-40"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          {noLeidas > 0 && (
            <Button size="sm" variant="secondary" onClick={marcarTodas} loading={marcandoTodas} disabled={marcandoTodas}>
              <CheckCheck className="w-3.5 h-3.5" />
              Marcar todas
            </Button>
          )}
        </div>
      </div>

      {notifs.length === 0 ? (
        <div className="py-16 text-center text-slate-400">
          <Bell className="w-12 h-12 mx-auto mb-4 opacity-20" />
          <p className="text-base font-medium text-slate-600">Sin notificaciones</p>
          <p className="text-sm mt-1">Te avisaremos cuando haya novedades</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifs.map(n => {
            const Icon = TIPO_ICON[n.tipo] ?? Info
            const iconColor = TIPO_COLOR[n.tipo] ?? 'text-slate-400'
            return (
              <div
                key={n.id}
                className={[
                  'bg-white rounded-xl border p-4 transition-colors',
                  n.leida ? 'border-slate-100' : 'border-amber-200 bg-amber-50',
                ].join(' ')}
              >
                <div className="flex gap-3">
                  <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${n.leida ? 'bg-slate-100' : 'bg-amber-100'}`}>
                    <Icon className={`w-4 h-4 ${iconColor}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-800 leading-snug">{n.titulo}</p>
                      {!n.leida && <span className="shrink-0 w-2 h-2 bg-amber-500 rounded-full mt-1.5" />}
                    </div>
                    <p className="text-sm text-slate-600 mt-1">{n.mensaje}</p>
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-xs text-slate-400">{formatFecha(n.fecha_envio)}</p>
                      {!n.leida && (
                        <Button
                          size="sm"
                          variant="secondary"
                          loading={marcando === n.id}
                          onClick={() => marcarLeida(n.id)}
                        >
                          Marcar leída
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
