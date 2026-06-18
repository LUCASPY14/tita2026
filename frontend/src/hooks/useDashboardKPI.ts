import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuthStore } from '../store/authStore'

const RECONNECT_MS = 5_000

export interface DashboardKPI {
  ventasHoy: number
  montoHoy: number
  clientes: number
  productos: number
  stockBajo: number
  cajasAbiertas: number
}

function buildWsUrl(): string {
  const token = localStorage.getItem('access_token') ?? ''
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/dashboard/?token=${token}`
}

export function useDashboardKPI() {
  const { user } = useAuthStore()
  const [kpi, setKpi] = useState<DashboardKPI | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  // Ref estable para llamar connect() desde el closure de onclose sin forward-reference
  const connectRef = useRef<(() => void) | null>(null)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket(buildWsUrl())
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as { type?: string } & Partial<DashboardKPI>
        if (msg.type === 'kpi_snapshot' || msg.type === 'kpi_update') {
          setKpi({
            ventasHoy:     msg.ventasHoy     ?? 0,
            montoHoy:      msg.montoHoy      ?? 0,
            clientes:      msg.clientes      ?? 0,
            productos:     msg.productos     ?? 0,
            stockBajo:     msg.stockBajo     ?? 0,
            cajasAbiertas: msg.cajasAbiertas ?? 0,
          })
        }
      } catch { /* ignore malformed frames */ }
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = setTimeout(() => connectRef.current?.(), RECONNECT_MS)
    }

    ws.onerror = () => ws.close()
  }, [])

  // Mantener la ref sincronizada con la versión más reciente de connect
  useEffect(() => { connectRef.current = connect }, [connect])

  useEffect(() => {
    if (!user) return
    connect()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connect, user])

  return { kpi, connected }
}
