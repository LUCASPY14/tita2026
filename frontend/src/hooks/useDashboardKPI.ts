import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuthStore } from '../store/authStore'
import api from '../services/api'

const RECONNECT_MS = 5_000
// Intervalo de polling REST cuando el WebSocket no está disponible
const POLL_MS = 30_000

export interface DashboardKPI {
  ventasHoy: number
  montoHoy: number
  clientes: number
  productos: number
  stockBajo: number
  cajasAbiertas: number
  recargasHoy: number
  montoRecargasHoy: number
  almuerzoHoy: number
  tarjetasEnAlerta: number
}

function buildWsUrl(): string {
  const token = localStorage.getItem('access_token') ?? ''
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/dashboard/?token=${token}`
}

async function fetchKpiRest(): Promise<DashboardKPI> {
  const res = await api.get<DashboardKPI>('/contabilidad/dashboard/')
  return res.data
}

export function useDashboardKPI() {
  const { user } = useAuthStore()
  const [kpi, setKpi] = useState<DashboardKPI | null>(null)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null)
  // Ref estable para llamar connect() desde el closure de onclose sin forward-reference
  const connectRef = useRef<(() => void) | null>(null)

  const stopPoll = useCallback(() => {
    if (pollTimer.current) { clearInterval(pollTimer.current); pollTimer.current = null }
  }, [])

  const startPoll = useCallback(() => {
    stopPoll()
    fetchKpiRest().then(setKpi).catch(() => {})
    pollTimer.current = setInterval(() => {
      fetchKpiRest().then(setKpi).catch(() => {})
    }, POLL_MS)
  }, [stopPoll])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    const ws = new WebSocket(buildWsUrl())
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      stopPoll()
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
            ventasHoy:        msg.ventasHoy        ?? 0,
            montoHoy:         msg.montoHoy         ?? 0,
            clientes:         msg.clientes         ?? 0,
            productos:        msg.productos        ?? 0,
            stockBajo:        msg.stockBajo        ?? 0,
            cajasAbiertas:    msg.cajasAbiertas    ?? 0,
            recargasHoy:      msg.recargasHoy      ?? 0,
            montoRecargasHoy: msg.montoRecargasHoy ?? 0,
            almuerzoHoy:      msg.almuerzoHoy      ?? 0,
            tarjetasEnAlerta: msg.tarjetasEnAlerta ?? 0,
          })
        }
      } catch { /* ignore malformed frames */ }
    }

    ws.onclose = (event) => {
      setConnected(false)
      // Fallback REST mientras el WS no esté disponible
      startPoll()
      // No reintentar: sesión rechazada (4001), socket reemplazado por uno más
      // nuevo, o ya no hay token (sesión cerrada) — evita loop infinito de
      // reconexión con token vacío/inválido.
      if (event.code === 4001) return
      if (wsRef.current !== ws) return
      if (!localStorage.getItem('access_token')) return
      reconnectTimer.current = setTimeout(() => connectRef.current?.(), RECONNECT_MS)
    }

    ws.onerror = () => ws.close()
  }, [startPoll, stopPoll])

  // Mantener la ref sincronizada con la versión más reciente de connect
  useEffect(() => { connectRef.current = connect }, [connect])

  useEffect(() => {
    if (!user) return
    connect()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
      stopPoll()
    }
  }, [connect, user, stopPoll])

  return { kpi, connected }
}
