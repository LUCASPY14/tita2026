import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
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

// Umbrales de negocio para el 2do registro de almuerzo del mismo alumno:
// < 10s → reintento accidental (doble escaneo); 10-240s → todavía muy pronto
// para un ingreso real; >= 240s → 2do ingreso legítimo (repite, no cobra).
const SEGUNDOS_DOBLE_ESCANEO = 10
const SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO = 240

function horaRegistroToDate(horaStr: string): Date {
  const [h, m, s] = horaStr.split(':').map(Number)
  const d = new Date()
  d.setHours(h, m, s || 0, 0)
  return d
}

function buildRegistrosMap(results: { hijo: number; hora_registro?: string }[]): Map<number, RegistroInfo> {
  const map = new Map<number, RegistroInfo>()
  for (const r of results) {
    if (!r.hora_registro) continue
    const hora = horaRegistroToDate(r.hora_registro)
    const prev = map.get(r.hijo)
    map.set(r.hijo, {
      count: (prev?.count ?? 0) + 1,
      ultimoRegistro: prev && prev.ultimoRegistro > hora ? prev.ultimoRegistro : hora,
    })
  }
  return map
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
  saldoAlmuerzo: number | null
  esSegundo: boolean
} | {
  tipo: 'error'
  message: string
}

interface RegistroInfo {
  count: number
  ultimoRegistro: Date
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
  const { t } = useTranslation()
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
  const [registrosHoy, setRegistrosHoy] = useState<Map<number, RegistroInfo>>(new Map())
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
      setSuscriptosHoy(hijosSusc)
      setRegistrosHoy(buildRegistrosMap(consumRes.data.results ?? []))
    } catch {
      // silencioso
    } finally {
      setLoadingLista(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
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

  // Carga inicial de registrosHoy para el anti-doble-scan (siempre, no solo con panel lista)
  useEffect(() => {
    api.get('/almuerzos/registros-consumo/', { params: { fecha_consumo: todayISO(), page_size: 500 } })
      .then(r => setRegistrosHoy(buildRegistrosMap(r.data.results ?? [])))
      .catch(() => toast.error('Error al cargar registros del día'))
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

      // ── Anti-doble-scan: solo pre-bloquea el 2do intento cuando todavía no
      // pasó el umbral de tiempo. Un 3er intento (count >= 2) pasa directo al
      // backend, que es quien tiene la última palabra ("Límite alcanzado").
      const registroPrevio = registrosHoy.get(hijoId)
      if (registroPrevio && registroPrevio.count === 1) {
        const transcurridos = (Date.now() - registroPrevio.ultimoRegistro.getTime()) / 1000
        if (transcurridos < SEGUNDOS_DOBLE_ESCANEO) {
          setResult({ tipo: 'error', message: 'Escaneo duplicado — esperá unos segundos' })
          startCountdown(2)
          return
        }
        if (transcurridos < SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO) {
          const faltan = Math.ceil(SEGUNDOS_MINIMOS_SEGUNDO_REGISTRO - transcurridos)
          setResult({
            tipo: 'error',
            message: `Todavía es muy pronto para un segundo ingreso de almuerzo. Esperá ${faltan} segundos más.`,
          })
          startCountdown(3)
          return
        }
      }
      const esSegundo = registroPrevio?.count === 1

      await api.post('/almuerzos/registros-consumo/', {
        hijo: hijoId,
        fecha_consumo: todayISO(),
        nro_tarjeta: tarjeta.nro_tarjeta,
      })

      // Actualizar mapa local inmediatamente sin esperar refresh de API
      setRegistrosHoy(prev => {
        const next = new Map(prev)
        const info = next.get(hijoId as number)
        next.set(hijoId as number, { count: (info?.count ?? 0) + 1, ultimoRegistro: new Date() })
        return next
      })

      // Saldo de almuerzo (cuenta corriente, separada de la tarjeta) — solo
      // informativo, si falla no bloquea el registro ya confirmado.
      let saldoAlmuerzo: number | null = null
      try {
        const { data: saldoRes } = await api.get('/almuerzos/saldos/', { params: { hijo: hijoId } })
        const item = (saldoRes.results ?? saldoRes)[0]
        if (item) saldoAlmuerzo = Number(item.saldo_actual)
      } catch {
        // silencioso
      }

      const hora = nowTime()
      const entry: RegistroReciente = {
        id: `${nro}-${Date.now()}`,
        nombre: tarjeta.hijo_nombre,
        grado: hijoGrado,
        hora,
        tarjeta: nro,
        saldo: tarjeta.saldo_actual,
      }
      setResult({
        tipo: 'ok', nombre: tarjeta.hijo_nombre, grado: hijoGrado, tarjeta: nro,
        saldo: tarjeta.saldo_actual, saldoAlmuerzo, esSegundo,
      })
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
  }, [hijos, hijosLoading, startCountdown, registrosHoy])

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
      className="min-h-screen bg-slate-50 text-slate-900 flex flex-col select-none"
      onClick={handlePageClick}
    >
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 bg-white border-b border-slate-200 shadow-sm shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-green-50 rounded-xl p-1.5 border border-green-100">
            <img src="/logo_tita.png" alt="Cantina Tita" className="h-9 w-auto" />
          </div>
          <div>
            <p className="text-slate-800 font-black text-base tracking-tight">CANTINA TITA</p>
            <p className="text-green-600 text-sm font-bold uppercase tracking-wider">{t('comedor.title')}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-slate-500 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2">
            <Clock className="w-4 h-4" />
            <span className="text-base tabular-nums font-medium">{clock}</span>
          </div>
          {recientes.length > 0 && (
            <button
              onClick={e => { e.stopPropagation(); exportarPDF() }}
              className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl text-sm font-semibold text-slate-700 transition-colors cursor-pointer"
            >
              <Download className="w-4 h-4" />
              PDF ({recientes.length})
            </button>
          )}
          <button
            onClick={e => { e.stopPropagation(); toggleFullscreen() }}
            className="p-2 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors cursor-pointer text-slate-600"
            title={fullscreen ? 'Salir de pantalla completa' : 'Pantalla completa'}
          >
            {fullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* ── Body ───────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── Panel izquierdo: scan ─────────────────────────────── */}
        <div className="flex-1 flex flex-col items-center justify-center gap-8 p-10">

          {/* Contador de progreso */}
          {suscriptosHoy.length > 0 && (
            <div className="w-full max-w-lg bg-white rounded-2xl border border-slate-200 shadow-sm px-6 py-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-slate-500 text-sm font-bold uppercase tracking-wider">Almuerzos hoy</span>
                <span className="tabular-nums font-black text-2xl text-slate-800">
                  {registrosHoy.size}
                  <span className="text-slate-400 font-normal text-lg"> / {suscriptosHoy.length}</span>
                </span>
              </div>
              <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-3 bg-green-500 rounded-full transition-all duration-500"
                  style={{ width: `${Math.round((registrosHoy.size / suscriptosHoy.length) * 100)}%` }}
                />
              </div>
              <p className="text-slate-400 text-sm mt-1.5 text-right font-medium">
                {Math.round((registrosHoy.size / suscriptosHoy.length) * 100)}% completado
              </p>
            </div>
          )}

          {/* Área de resultado */}
          {result ? (
            result.tipo === 'ok' ? (
              <div className="w-full max-w-lg bg-green-50 border-2 border-green-400 rounded-3xl p-10 text-center animate-in fade-in zoom-in-95 duration-200 shadow-lg">
                <CheckCircle className="w-24 h-24 text-green-500 mx-auto mb-5" />
                <p className="text-green-600 text-base font-bold uppercase tracking-widest mb-2">
                  {result.esSegundo ? '2do ingreso registrado' : 'Ingreso registrado'}
                </p>
                <p className="text-slate-900 text-5xl font-black leading-tight mt-2">{result.nombre}</p>
                {result.grado && <p className="text-slate-600 text-2xl mt-2 font-medium">{result.grado}</p>}
                {result.esSegundo && (
                  <p className="text-emerald-600 text-lg font-semibold mt-2">Sin cargo adicional</p>
                )}
                <div className="mt-6 flex items-center justify-center gap-4 flex-wrap">
                  <div className="bg-white border border-green-200 rounded-2xl px-6 py-3 inline-block shadow-sm">
                    <p className="text-slate-500 text-sm">Saldo en tarjeta</p>
                    <p className="text-emerald-600 text-3xl font-black tabular-nums">{formatGs(result.saldo)}</p>
                  </div>
                  {result.saldoAlmuerzo !== null && (
                    <div className={[
                      'rounded-2xl px-6 py-3 inline-block shadow-sm border',
                      result.saldoAlmuerzo < 0 ? 'bg-red-50 border-red-200' : 'bg-white border-orange-200',
                    ].join(' ')}>
                      <p className="text-slate-500 text-sm">Saldo de almuerzo</p>
                      <p className={[
                        'text-3xl font-black tabular-nums',
                        result.saldoAlmuerzo < 0 ? 'text-red-600' : 'text-orange-600',
                      ].join(' ')}>
                        {formatGs(result.saldoAlmuerzo)}
                      </p>
                      {result.saldoAlmuerzo < 0 && (
                        <p className="text-red-500 text-xs font-semibold mt-0.5">Debe — no bloquea el ingreso</p>
                      )}
                    </div>
                  )}
                </div>
                {countdown !== null && (
                  <p className="text-slate-400 text-base mt-6 tabular-nums font-medium">
                    Próximo en {countdown}...
                  </p>
                )}
              </div>
            ) : (
              <div className="w-full max-w-lg bg-red-50 border-2 border-red-400 rounded-3xl p-10 text-center animate-in fade-in zoom-in-95 duration-200 shadow-lg">
                <XCircle className="w-24 h-24 text-red-500 mx-auto mb-5" />
                <p className="text-red-500 text-base font-bold uppercase tracking-widest mb-2">Error</p>
                <p className="text-slate-900 text-3xl font-bold">{result.message}</p>
                {countdown !== null && (
                  <p className="text-slate-400 text-base mt-6 font-medium">Reintentando en {countdown}...</p>
                )}
              </div>
            )
          ) : (
            <div className="text-center">
              <div className="w-32 h-32 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6 shadow-sm">
                <UtensilsCrossed className="w-16 h-16 text-green-500" />
              </div>
              <p className="text-slate-800 text-4xl font-black">Pasá la tarjeta</p>
              <p className="text-slate-400 text-xl mt-2">o escribí el número y presioná Enter</p>
            </div>
          )}

          {/* Input de tarjeta */}
          <div className="w-full max-w-lg" onClick={e => e.stopPropagation()}>
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
                'w-full text-center text-3xl font-black tracking-widest py-5 px-6',
                'border-2 rounded-2xl outline-none transition-all duration-150 shadow-sm',
                'placeholder:text-slate-300',
                scanning
                  ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
                  : 'bg-white border-slate-300 focus:border-green-500 focus:ring-4 focus:ring-green-500/10 text-slate-900',
              ].join(' ')}
            />
            <p className="text-center text-slate-400 text-base mt-2.5 font-medium">
              {scanning ? 'Registrando...' : 'Enter para registrar · Esc para limpiar'}
            </p>
          </div>
        </div>

        {/* ── Panel derecho ────────────────────────────────────── */}
        <div className="w-80 bg-white border-l border-slate-200 flex flex-col shrink-0">
          {/* Toggle header */}
          <div className="px-3 py-3 border-b border-slate-100 flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => setPanelMode('recientes')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-sm font-bold transition-colors cursor-pointer ${
                panelMode === 'recientes'
                  ? 'bg-green-100 text-green-700'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
              }`}
            >
              <CheckCircle className="w-4 h-4" />
              Recientes ({recientes.length})
            </button>
            <button
              type="button"
              onClick={() => setPanelMode('lista')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-sm font-bold transition-colors cursor-pointer ${
                panelMode === 'lista'
                  ? 'bg-green-100 text-green-700'
                  : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
              }`}
            >
              <List className="w-4 h-4" />
              Lista de hoy
            </button>
          </div>

          {/* Panel: recientes */}
          {panelMode === 'recientes' && (
            <div className="flex-1 overflow-y-auto">
              {recientes.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-40 gap-2 text-slate-300">
                  <CheckCircle className="w-10 h-10" />
                  <p className="text-base font-medium">Sin ingresos aún</p>
                </div>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {recientes.map((r, i) => (
                    <li key={r.id} className={`px-4 py-3.5 flex items-center gap-3 ${i === 0 ? 'bg-green-50' : ''}`}>
                      <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${i === 0 ? 'bg-green-100' : 'bg-slate-100'}`}>
                        <CheckCircle className={`w-5 h-5 ${i === 0 ? 'text-green-600' : 'text-slate-400'}`} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className={`text-base font-semibold truncate ${i === 0 ? 'text-slate-900' : 'text-slate-700'}`}>{r.nombre}</p>
                        {r.grado && <p className="text-sm text-slate-400 truncate">{r.grado}</p>}
                      </div>
                      <span className="text-sm text-slate-400 tabular-nums shrink-0 font-medium">{r.hora}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Panel: lista de hoy */}
          {panelMode === 'lista' && (
            <>
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                <p className="text-base font-medium text-slate-600">
                  <span className="text-green-600 font-black text-xl">{registrosHoy.size}</span>
                  <span className="text-slate-400"> / {suscriptosHoy.length}</span>
                  <span className="text-slate-500"> almorzaron</span>
                </p>
                <button
                  type="button"
                  onClick={e => { e.stopPropagation(); cargarListaHoy() }}
                  className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer transition-colors"
                  disabled={loadingLista}
                >
                  <RefreshCw className={`w-4 h-4 ${loadingLista ? 'animate-spin' : ''}`} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">
                {loadingLista ? (
                  <div className="flex items-center justify-center h-20">
                    <p className="text-slate-400 text-base">Cargando...</p>
                  </div>
                ) : suscriptosHoy.length === 0 ? (
                  <div className="flex items-center justify-center h-20">
                    <p className="text-slate-400 text-base text-center px-4">Sin suscripciones activas hoy</p>
                  </div>
                ) : (
                  <ul className="divide-y divide-slate-100">
                    {[...suscriptosHoy].sort((a, b) => {
                      const aCount = registrosHoy.get(a.hijoId)?.count ?? 0
                      const bCount = registrosHoy.get(b.hijoId)?.count ?? 0
                      if (aCount !== bCount) return aCount - bCount
                      return a.nombre.localeCompare(b.nombre)
                    }).map(s => {
                      const count = registrosHoy.get(s.hijoId)?.count ?? 0
                      const completo = count >= 2
                      return (
                        <li key={s.hijoId} className={`px-4 py-3 flex items-center gap-3 ${completo ? 'opacity-40' : ''}`}>
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${count > 0 ? 'bg-green-100' : 'bg-slate-100'}`}>
                            {count > 0
                              ? <CheckCircle className="w-4 h-4 text-green-600" />
                              : <XCircle className="w-4 h-4 text-slate-400" />
                            }
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className={`text-sm font-semibold truncate ${completo ? 'text-slate-400 line-through' : 'text-slate-800'}`}>{s.nombre}</p>
                            {s.grado && <p className="text-sm text-slate-400 truncate">{s.grado}</p>}
                          </div>
                          {count > 0 && (
                            <span className={`text-xs font-bold tabular-nums px-2 py-0.5 rounded-full shrink-0 ${completo ? 'bg-slate-100 text-slate-400' : 'bg-green-100 text-green-700'}`}>
                              {count}/2
                            </span>
                          )}
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
