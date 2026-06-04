import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  CheckCircle, XCircle, UtensilsCrossed, Clock,
  Download, Maximize2, Minimize2, List, RefreshCw,
} from 'lucide-react'
import api from '../services/api'
import { exportarIngresosComedorPDF } from '../utils/pdf'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function todayISO() { return new Date().toISOString().split('T')[0] }

function formatGs(n: number | string | null | undefined) {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

function nowTime() {
  return new Date().toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function nowDisplay() {
  return new Date().toLocaleString('es-PY', {
    weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    if (d.non_field_errors) return String((d.non_field_errors as string[])[0])
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Hijo {
  id: number
  nombre: string
  apellido: string
  grado: string
  nombre_completo?: string
}

interface TarjetaResult {
  nro_tarjeta: string
  hijo_nombre: string
  saldo_actual: string | number
  estado: string
  hijo?: number
}

type ResultState = {
  tipo: 'ok'
  nombre: string
  grado: string
  tarjeta: string
  saldo: string | number
} | {
  tipo: 'error'
  message: string
}

interface RegistroReciente {
  id: string
  nombre: string
  grado: string
  hora: string
  tarjeta: string
  saldo: string | number
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Comedor() {
  const inputRef = useRef<HTMLInputElement>(null)
  const countdownRef = useRef<ReturnType<typeof setInterval>>(undefined)
  const focusTimeoutRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const scanningRef = useRef(false)

  const [inputVal, setInputVal] = useState('')
  const [scanning, setScanning] = useState(false)
  const [result, setResult] = useState<ResultState | null>(null)
  const [countdown, setCountdown] = useState<number | null>(null)
  const [recientes, setRecientes] = useState<RegistroReciente[]>([])
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [hijosLoading, setHijosLoading] = useState(true)
  const [clock, setClock] = useState(nowDisplay())
  const [fullscreen, setFullscreen] = useState(false)
  const [panelMode, setPanelMode] = useState<'recientes' | 'lista'>('recientes')
  const [suscriptosHoy, setSuscriptosHoy] = useState<{ hijoId: number; nombre: string; grado: string }[]>([])
  const [consumidosHoy, setConsumidosHoy] = useState<Set<number>>(new Set())
  const [loadingLista, setLoadingLista] = useState(false)

  // reloj
  useEffect(() => {
    const t = setInterval(() => setClock(nowDisplay()), 10000)
    return () => clearInterval(t)
  }, [])

  // limpiar intervalo al desmontar
  useEffect(() => { return () => clearInterval(countdownRef.current) }, [])

  // cargar hijos al montar
  useEffect(() => {
    api.get('/clientes/hijos/', { params: { page_size: 500 } })
      .then(r => setHijos(r.data.results ?? []))
      .catch(() => toast.error('Error al cargar estudiantes'))
      .finally(() => setHijosLoading(false))
  }, [])

  // foco automático
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // cargar lista de alumnos suscritos + quiénes ya comieron hoy
  const cargarListaHoy = useCallback(async () => {
    setLoadingLista(true)
    try {
      const [suscRes, consumRes] = await Promise.all([
        api.get('/almuerzos/suscripciones/', { params: { estado: 'ACTIVA', page_size: 500 } }),
        api.get('/almuerzos/registros-consumo/', { params: { fecha_consumo: todayISO(), page_size: 500 } }),
      ])
      const hijosSusc: { hijoId: number; nombre: string; grado: string }[] = (suscRes.data.results ?? []).map(
        (s: { hijo: number; hijo_nombre?: string; hijo_grado?: string }) => ({
          hijoId: s.hijo,
          nombre: s.hijo_nombre ?? String(s.hijo),
          grado: s.hijo_grado ?? '',
        })
      )
      const consumidos = new Set<number>(
        (consumRes.data.results ?? []).map((r: { hijo: number }) => r.hijo)
      )
      setSuscriptosHoy(hijosSusc)
      setConsumidosHoy(consumidos)
    } catch {
      // silencioso
    } finally {
      setLoadingLista(false)
    }
  }, [])

  useEffect(() => {
    if (panelMode === 'lista') cargarListaHoy()
  }, [panelMode, cargarListaHoy])

  // actualizar lista cada vez que se registra un consumo
  useEffect(() => {
    const handler = () => { if (panelMode === 'lista') cargarListaHoy() }
    window.addEventListener('comedor:registro', handler)
    return () => window.removeEventListener('comedor:registro', handler)
  }, [panelMode, cargarListaHoy])

  // Auto-refresh cada 60s cuando el panel derecho está en "lista"
  useEffect(() => {
    if (panelMode !== 'lista') return
    const t = setInterval(() => cargarListaHoy(), 60_000)
    return () => clearInterval(t)
  }, [panelMode, cargarListaHoy])

  // Carga inicial del set consumidosHoy para el anti-doble-scan (siempre, no solo con panel lista)
  useEffect(() => {
    api.get('/almuerzos/registros-consumo/', { params: { fecha_consumo: todayISO(), page_size: 500 } })
      .then(r => {
        const ids = new Set<number>((r.data.results ?? []).map((x: { hijo: number }) => x.hijo))
        setConsumidosHoy(ids)
      })
      .catch(() => {})
  }, [])

  // fullscreen API
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
      setFullscreen(true)
    } else {
      document.exitFullscreen().catch(() => {})
      setFullscreen(false)
    }
  }, [])

  useEffect(() => {
    const handler = () => setFullscreen(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', handler)
    return () => document.removeEventListener('fullscreenchange', handler)
  }, [])

  const clearResult = useCallback(() => {
    clearInterval(countdownRef.current)
    clearTimeout(focusTimeoutRef.current)
    setResult(null)
    setCountdown(null)
    setInputVal('')
    focusTimeoutRef.current = setTimeout(() => inputRef.current?.focus(), 50)
  }, [])

  const startCountdown = useCallback((segundos = 4) => {
    clearInterval(countdownRef.current)
    setCountdown(segundos)
    countdownRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(countdownRef.current)
          setResult(null)
          setInputVal('')
          setTimeout(() => inputRef.current?.focus(), 50)
          return null
        }
        return prev - 1
      })
    }, 1000)
  }, [])

  const handleScan = useCallback(async (nro: string) => {
    if (scanningRef.current || !nro) return
    if (hijosLoading) {
      setResult({ tipo: 'error', message: 'Cargando datos del sistema…' })
      startCountdown(2)
      return
    }
    scanningRef.current = true
    setScanning(true)
    setInputVal('')
    clearInterval(countdownRef.current)
    setResult(null)
    setCountdown(null)
    try {
      const { data: res } = await api.get('/core/tarjetas/', { params: { search: nro } })
      const tarjeta: TarjetaResult | undefined = (res.results ?? []).find(
        (t: TarjetaResult) => t.nro_tarjeta === nro
      )
      if (!tarjeta) {
        setResult({ tipo: 'error', message: 'Tarjeta no encontrada' })
        startCountdown(3)
        return
      }
      if (tarjeta.estado !== 'ACTIVA') {
        setResult({ tipo: 'error', message: `Tarjeta ${tarjeta.estado.toLowerCase()}` })
        startCountdown(3)
        return
      }
      // Resolver hijo
      let hijoId: number | undefined = tarjeta.hijo
      let hijoGrado = ''
      if (!hijoId) {
        const match = hijos.find(
          h => h.nombre_completo === tarjeta.hijo_nombre ||
            `${h.nombre} ${h.apellido}` === tarjeta.hijo_nombre
        )
        hijoId = match?.id
        hijoGrado = match?.grado ?? ''
      } else {
        const match = hijos.find(h => h.id === hijoId)
        hijoGrado = match?.grado ?? ''
      }
      if (!hijoId) {
        setResult({ tipo: 'error', message: 'Estudiante no encontrado en sistema' })
        startCountdown(3)
        return
      }

      // ── Anti-doble-scan: verificar si ya almorzó hoy ──────────────────────
      if (consumidosHoy.has(hijoId)) {
        setResult({ tipo: 'error', message: `${tarjeta.hijo_nombre} ya registró almuerzo hoy` })
        startCountdown(4)
        return
      }

      await api.post('/almuerzos/registros-consumo/', {
        hijo: hijoId,
        fecha_consumo: todayISO(),
        nro_tarjeta: tarjeta.nro_tarjeta,
      })

      // Actualizar set local inmediatamente sin esperar refresh de API
      setConsumidosHoy(prev => new Set([...prev, hijoId as number]))

      const hora = nowTime()
      const entry: RegistroReciente = {
        id: `${nro}-${Date.now()}`,
        nombre: tarjeta.hijo_nombre,
        grado: hijoGrado,
        hora,
        tarjeta: nro,
        saldo: tarjeta.saldo_actual,
      }
      setResult({ tipo: 'ok', nombre: tarjeta.hijo_nombre, grado: hijoGrado, tarjeta: nro, saldo: tarjeta.saldo_actual })
      setRecientes(prev => [entry, ...prev].slice(0, 30))
      startCountdown(4)
      window.dispatchEvent(new CustomEvent('comedor:registro'))
    } catch (err) {
      const msg = extractErrorMessage(err)
      setResult({ tipo: 'error', message: msg })
      startCountdown(3)
    } finally {
      scanningRef.current = false
      setScanning(false)
    }
  }, [hijos, hijosLoading, startCountdown, consumidosHoy])

  // refoco al hacer click en cualquier parte
  const handlePageClick = useCallback(() => {
    if (!result) inputRef.current?.focus()
  }, [result])

  // Escape para limpiar
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') clearResult() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [clearResult])

  function exportarPDF() {
    if (!recientes.length) { toast.error('Sin ingresos registrados aún'); return }
    exportarIngresosComedorPDF(
      recientes.map(r => ({ nombre: r.nombre, hora: r.hora, grado: r.grado, tarjeta: r.tarjeta, saldo: r.saldo })),
      todayISO()
    )
    toast.success('PDF descargado')
  }

  return (
    <div
      className="min-h-screen bg-slate-900 text-white flex flex-col select-none"
      onClick={handlePageClick}
    >
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 bg-slate-950 border-b border-white/5 shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-white rounded-lg p-0.5">
            <img src="/logo_tita.png" alt="Cantina Tita" className="h-7 w-auto" />
          </div>
          <div>
            <p className="text-white font-bold text-sm tracking-tight">CANTINA TITA</p>
            <p className="text-green-400 text-xs font-medium uppercase tracking-wider">Registro de Comedor</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-slate-400">
            <Clock className="w-4 h-4" />
            <span className="text-sm tabular-nums">{clock}</span>
          </div>
          {recientes.length > 0 && (
            <button
              onClick={e => { e.stopPropagation(); exportarPDF() }}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              PDF ({recientes.length})
            </button>
          )}
          <button
            onClick={e => { e.stopPropagation(); toggleFullscreen() }}
            className="p-1.5 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors cursor-pointer"
            title={fullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}
          >
            {fullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* ── Body ───────────────────────────────────────────────── */}
      <div className="flex-1 flex gap-0 overflow-hidden">

        {/* ── Panel izquierdo: scan ─────────────────────────────── */}
        <div className="flex-1 flex flex-col items-center justify-center gap-8 p-8">

          {/* Contador de progreso */}
          {suscriptosHoy.length > 0 && (
            <div className="w-full max-w-sm">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-slate-400 text-xs font-medium uppercase tracking-wider">Almuerzos hoy</span>
                <span className="text-white text-sm font-bold tabular-nums">
                  {consumidosHoy.size}
                  <span className="text-slate-500 font-normal"> / {suscriptosHoy.length}</span>
                </span>
              </div>
              <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-2 bg-green-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.round((consumidosHoy.size / suscriptosHoy.length) * 100)}%` }}
                />
              </div>
              <p className="text-slate-600 text-xs mt-1 text-right">
                {Math.round((consumidosHoy.size / suscriptosHoy.length) * 100)}% completado
              </p>
            </div>
          )}

          {/* Área de resultado */}
          {result ? (
            result.tipo === 'ok' ? (
              <div className="w-full max-w-sm bg-green-500/10 border-2 border-green-500 rounded-3xl p-8 text-center animate-in fade-in zoom-in-95 duration-200">
                <CheckCircle className="w-20 h-20 text-green-400 mx-auto mb-4" />
                <p className="text-green-300 text-xs font-semibold uppercase tracking-widest mb-1">Ingreso registrado</p>
                <p className="text-white text-3xl font-bold leading-tight mt-2">{result.nombre}</p>
                {result.grado && <p className="text-slate-300 text-lg mt-1">{result.grado}</p>}
                <div className="mt-4 bg-slate-800/60 rounded-xl px-4 py-2 inline-block">
                  <p className="text-slate-400 text-xs">Saldo en tarjeta</p>
                  <p className="text-emerald-400 text-xl font-bold tabular-nums">{formatGs(result.saldo)}</p>
                </div>
                {countdown !== null && (
                  <p className="text-slate-500 text-sm mt-5 tabular-nums">
                    Próximo en {countdown}...
                  </p>
                )}
              </div>
            ) : (
              <div className="w-full max-w-sm bg-red-500/10 border-2 border-red-500 rounded-3xl p-8 text-center animate-in fade-in zoom-in-95 duration-200">
                <XCircle className="w-20 h-20 text-red-400 mx-auto mb-4" />
                <p className="text-red-300 text-xs font-semibold uppercase tracking-widest mb-2">Error</p>
                <p className="text-white text-2xl font-bold">{result.message}</p>
                {countdown !== null && (
                  <p className="text-slate-500 text-sm mt-5">Reintentando en {countdown}...</p>
                )}
              </div>
            )
          ) : (
            <div className="text-center">
              <UtensilsCrossed className="w-16 h-16 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-300 text-xl font-semibold">Pasá la tarjeta</p>
              <p className="text-slate-500 text-sm mt-1">o escribí el número y presioná Enter</p>
            </div>
          )}

          {/* Input de tarjeta */}
          <div className="w-full max-w-sm" onClick={e => e.stopPropagation()}>
            <input
              ref={inputRef}
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { const v = e.currentTarget.value.trim(); if (v) handleScan(v) } }}
              placeholder="Nro. de tarjeta..."
              disabled={scanning}
              autoComplete="off"
              autoFocus
              className={[
                'w-full text-center text-2xl font-bold tracking-widest py-4 px-6',
                'bg-slate-800 border-2 rounded-2xl outline-none transition-all duration-150',
                'placeholder:text-slate-600 text-white',
                scanning
                  ? 'border-slate-600 cursor-not-allowed'
                  : 'border-slate-600 focus:border-green-500 focus:ring-2 focus:ring-green-500/20',
              ].join(' ')}
            />
            <p className="text-center text-slate-600 text-xs mt-2">
              {scanning ? 'Registrando...' : 'Enter para registrar · Esc para limpiar'}
            </p>
          </div>
        </div>

        {/* ── Panel derecho ────────────────────────────────────── */}
        <div className="w-72 bg-slate-950 border-l border-white/5 flex flex-col shrink-0">
          {/* Toggle header */}
          <div className="px-3 py-2 border-b border-white/5 flex items-center gap-1">
            <button
              type="button"
              onClick={() => setPanelMode('recientes')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                panelMode === 'recientes' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <CheckCircle className="w-3.5 h-3.5" />
              Recientes ({recientes.length})
            </button>
            <button
              type="button"
              onClick={() => setPanelMode('lista')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                panelMode === 'lista' ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <List className="w-3.5 h-3.5" />
              Lista de hoy
            </button>
          </div>

          {/* Panel: recientes */}
          {panelMode === 'recientes' && (
            <div className="flex-1 overflow-y-auto">
              {recientes.length === 0 ? (
                <div className="flex items-center justify-center h-32">
                  <p className="text-slate-600 text-sm">Sin ingresos aún</p>
                </div>
              ) : (
                <ul className="divide-y divide-white/5">
                  {recientes.map((r, i) => (
                    <li key={r.id} className={`px-4 py-3 flex items-center gap-3 ${i === 0 ? 'bg-green-500/5' : ''}`}>
                      <div className="w-7 h-7 rounded-full bg-green-500/20 flex items-center justify-center shrink-0">
                        <CheckCircle className={`w-4 h-4 ${i === 0 ? 'text-green-400' : 'text-slate-500'}`} />
                      </div>
                      <div className="min-w-0">
                        <p className={`text-sm font-medium truncate ${i === 0 ? 'text-white' : 'text-slate-300'}`}>{r.nombre}</p>
                        {r.grado && <p className="text-xs text-slate-500 truncate">{r.grado}</p>}
                      </div>
                      <span className="text-xs text-slate-500 tabular-nums shrink-0 ml-auto">{r.hora}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Panel: lista de hoy */}
          {panelMode === 'lista' && (
            <>
              <div className="px-3 py-2 border-b border-white/5 flex items-center justify-between">
                <p className="text-xs text-slate-500">
                  <span className="text-green-400 font-semibold">{consumidosHoy.size}</span>
                  {' / '}
                  <span className="text-slate-400 font-semibold">{suscriptosHoy.length}</span>
                  {' almorzaron'}
                </p>
                <button
                  type="button"
                  onClick={e => { e.stopPropagation(); cargarListaHoy() }}
                  className="p-1 text-slate-500 hover:text-slate-300 cursor-pointer"
                  disabled={loadingLista}
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingLista ? 'animate-spin' : ''}`} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">
                {loadingLista ? (
                  <div className="flex items-center justify-center h-20">
                    <p className="text-slate-600 text-xs">Cargando...</p>
                  </div>
                ) : suscriptosHoy.length === 0 ? (
                  <div className="flex items-center justify-center h-20">
                    <p className="text-slate-600 text-xs">Sin suscripciones activas hoy</p>
                  </div>
                ) : (
                  <ul className="divide-y divide-white/5">
                    {[...suscriptosHoy].sort((a, b) => {
                      const aOk = consumidosHoy.has(a.hijoId)
                      const bOk = consumidosHoy.has(b.hijoId)
                      if (aOk !== bOk) return aOk ? 1 : -1
                      return a.nombre.localeCompare(b.nombre)
                    }).map(s => {
                      const comio = consumidosHoy.has(s.hijoId)
                      return (
                        <li key={s.hijoId} className="px-3 py-2.5 flex items-center gap-2.5">
                          <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${comio ? 'bg-green-500/20' : 'bg-slate-800'}`}>
                            {comio
                              ? <CheckCircle className="w-3.5 h-3.5 text-green-400" />
                              : <XCircle className="w-3.5 h-3.5 text-slate-600" />
                            }
                          </div>
                          <div className="min-w-0">
                            <p className={`text-xs font-medium truncate ${comio ? 'text-slate-400' : 'text-slate-200'}`}>{s.nombre}</p>
                            {s.grado && <p className="text-xs text-slate-600 truncate">{s.grado}</p>}
                          </div>
                        </li>
                      )
                    })}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
