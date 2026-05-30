import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  CreditCard, Search, CheckCircle, RefreshCw, History,
  ArrowUp, ArrowDown, X, Wallet,
} from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Table, { type Column } from '../components/ui/Table'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    if (d.error) return String(d.error)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

function formatGs(n: number | string | null | undefined): string {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

function formatFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string | null
  hijo_nombre: string
  hijo_grado: string
  cliente_nombre: string
  saldo_actual: string | number
  saldo_disponible: string | number
  estado: string
}

interface Movimiento {
  id: number
  tipo: string
  monto: string | number
  saldo_anterior: string | number
  saldo_resultante: string | number
  descripcion: string
  fecha: string
}

interface CargaReciente {
  id: number
  monto_cargado: string | number
  metodo_pago: string
  estado: string
  fecha_carga: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const METODOS = [
  { value: 'EFECTIVO',    label: 'Efectivo',             autoconfirma: true  },
  { value: 'POS DEBITO',  label: 'POS Débito',           autoconfirma: true  },
  { value: 'POS CREDITO', label: 'POS Crédito',          autoconfirma: true  },
  { value: 'TRANSFERENCIA', label: 'Transferencia bancaria', autoconfirma: false },
]

const MONTOS_RAPIDOS = [10000, 20000, 50000, 100000, 200000]

const TIPO_COLOR: Record<string, BadgeColor> = {
  RECARGA: 'green', CONSUMO: 'blue', AJUSTE: 'orange', REVERSO: 'purple',
}
const ESTADO_COLOR: Record<string, BadgeColor> = {
  CONFIRMADA: 'green', PENDIENTE: 'yellow', RECHAZADA: 'red',
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function CargaSaldo() {
  // ── Búsqueda de tarjeta ──────────────────────────────────────────
  const [busqueda, setBusqueda] = useState('')
  const [tarjeta, setTarjeta] = useState<Tarjeta | null>(null)
  const [buscando, setBuscando] = useState(false)
  const inputBusquedaRef = useRef<HTMLInputElement>(null)
  const limpiarTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  // ── Formulario de carga ──────────────────────────────────────────
  const [monto, setMonto] = useState('')
  const [metodo, setMetodo] = useState('EFECTIVO')
  const [referencia, setReferencia] = useState('')
  const [cargando, setCargando] = useState(false)

  // ── Historial ────────────────────────────────────────────────────
  const [movimientos, setMovimientos] = useState<Movimiento[]>([])
  const [cargas, setCargas] = useState<CargaReciente[]>([])
  const [loadingHistorial, setLoadingHistorial] = useState(false)
  const [historialTab, setHistorialTab] = useState<'movimientos' | 'cargas'>('movimientos')

  // ── Última operación exitosa ─────────────────────────────────────
  const [ultimaCarga, setUltimaCarga] = useState<{ monto: number; metodo: string; estado: string } | null>(null)

  // ── Auto-focus al inicio ──────────────────────────────────────────
  useEffect(() => {
    inputBusquedaRef.current?.focus()
    return () => clearTimeout(limpiarTimerRef.current)
  }, [])

  // ── Buscar tarjeta ────────────────────────────────────────────────
  const buscarTarjeta = useCallback(async () => {
    const q = busqueda.trim()
    if (!q) { toast.error('Ingresá el número de tarjeta'); return }
    setBuscando(true)
    setTarjeta(null)
    setMovimientos([])
    setCargas([])
    setUltimaCarga(null)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: q } })
      const found: Tarjeta | undefined = (data.results ?? []).find(
        (t: Tarjeta) => t.nro_tarjeta === q || t.codigo_barras === q
      )
      if (!found) { toast.error('Tarjeta no encontrada'); return }
      if (found.estado !== 'ACTIVA') {
        toast.error(`Tarjeta ${found.estado.toLowerCase()} — no se puede recargar`)
        return
      }
      setTarjeta(found)
      cargarHistorial(found.nro_tarjeta)
    } catch {
      toast.error('Error al buscar tarjeta')
    } finally {
      setBuscando(false)
    }
  }, [busqueda])

  const cargarHistorial = useCallback(async (nro: string) => {
    setLoadingHistorial(true)
    try {
      const [movRes, cargaRes] = await Promise.all([
        api.get('/core/movimientos-tarjeta/', { params: { tarjeta: nro, page_size: 20 } }),
        api.get('/core/cargas-saldo/', { params: { tarjeta: nro, page_size: 20 } }),
      ])
      setMovimientos(movRes.data.results ?? movRes.data ?? [])
      setCargas(cargaRes.data.results ?? cargaRes.data ?? [])
    } catch {
      // historial es secundario, no bloquear
    } finally {
      setLoadingHistorial(false)
    }
  }, [])

  // ── Confirmar carga pendiente ─────────────────────────────────────
  const confirmarCarga = useCallback(async (id: number) => {
    try {
      await api.post(`/core/cargas-saldo/${id}/confirmar/`)
      toast.success('Carga confirmada')
      if (tarjeta) {
        const { data } = await api.get(`/core/tarjetas/${tarjeta.nro_tarjeta}/`)
        setTarjeta(data)
        cargarHistorial(tarjeta.nro_tarjeta)
      }
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [tarjeta, cargarHistorial])

  // ── Realizar carga ────────────────────────────────────────────────
  const handleCargar = useCallback(async () => {
    const montoNum = Number(monto)
    if (!tarjeta) { toast.error('Buscá primero la tarjeta'); return }
    if (!montoNum || montoNum <= 0) { toast.error('Ingresá un monto válido'); return }

    setCargando(true)
    try {
      const payload: Record<string, unknown> = {
        tarjeta: tarjeta.nro_tarjeta,
        monto_cargado: montoNum,
        metodo_pago: metodo,
      }
      if (referencia.trim()) payload.referencia = referencia.trim()

      const { data } = await api.post('/core/cargas-saldo/', payload)

      const metodoInfo = METODOS.find(m => m.value === metodo)
      setUltimaCarga({ monto: montoNum, metodo, estado: data.estado ?? 'CONFIRMADA' })

      if (metodoInfo?.autoconfirma) {
        toast.success(`Recarga de ${formatGs(montoNum)} confirmada`)
      } else {
        toast.success(`Carga de ${formatGs(montoNum)} registrada — pendiente de confirmación`)
      }

      // Actualizar saldo de la tarjeta y recargar historial
      const { data: tarjetaActualizada } = await api.get(`/core/tarjetas/${tarjeta.nro_tarjeta}/`)
      setTarjeta(tarjetaActualizada)
      cargarHistorial(tarjeta.nro_tarjeta)

      // Limpiar formulario para la próxima operación
      setMonto('')
      setReferencia('')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setCargando(false)
    }
  }, [tarjeta, monto, metodo, referencia, cargarHistorial])

  // ── Limpiar y nueva operación ─────────────────────────────────────
  const limpiar = useCallback(() => {
    setTarjeta(null)
    setBusqueda('')
    setMonto('')
    setReferencia('')
    setMetodo('EFECTIVO')
    setMovimientos([])
    setCargas([])
    setUltimaCarga(null)
    limpiarTimerRef.current = setTimeout(() => inputBusquedaRef.current?.focus(), 50)
  }, [])

  const metodoSeleccionado = METODOS.find(m => m.value === metodo)

  // ── Columnas historial ────────────────────────────────────────────
  const colsMovimientos: Column<Movimiento>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-xs text-slate-400">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <Badge color={TIPO_COLOR[r.tipo] ?? 'default'}>{r.tipo}</Badge>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => {
        const entrada = r.tipo === 'RECARGA' || r.tipo === 'REVERSO'
        return (
          <span className={`tabular-nums font-semibold text-sm flex items-center gap-0.5 ${entrada ? 'text-emerald-700' : 'text-slate-600'}`}>
            {entrada ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {formatGs(r.monto)}
          </span>
        )
      },
    },
    {
      title: 'Saldo resultante',
      key: 'saldo',
      render: (_, r) => (
        <span className={`tabular-nums text-sm font-medium ${Number(r.saldo_resultante) < 0 ? 'text-red-600' : 'text-slate-700'}`}>
          {formatGs(r.saldo_resultante)}
        </span>
      ),
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-xs text-slate-400">{r.descripcion || '—'}</span>,
    },
  ]

  const colsCargas: Column<CargaReciente>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-xs text-slate-400">{formatFecha(r.fecha_carga)}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto_cargado)}</span>,
    },
    {
      title: 'Método',
      key: 'metodo',
      render: (_, r) => <span className="text-sm text-slate-600">{METODOS.find(m => m.value === r.metodo_pago)?.label ?? r.metodo_pago}</span>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: '',
      key: 'accion',
      width: 110,
      render: (_, r) => r.estado === 'PENDIENTE' ? (
        <Button size="sm" variant="primary" onClick={() => confirmarCarga(r.id)}>
          Confirmar
        </Button>
      ) : null,
    },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Wallet className="w-6 h-6 text-green-600" />
          Carga de Saldo
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">Recarga de saldo en tarjetas de estudiantes</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* ── Panel izquierdo: operación ─────────────────────────── */}
        <div className="lg:col-span-2 space-y-4">

          {/* Búsqueda */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-3">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1.5">
              <CreditCard className="w-3.5 h-3.5" />
              Tarjeta
            </p>
            <div className="flex gap-2">
              <Input
                ref={inputBusquedaRef}
                placeholder="Escanear o escribir nro. tarjeta..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && buscarTarjeta()}
              />
              <Button variant="secondary" loading={buscando} onClick={buscarTarjeta}>
                <Search className="w-4 h-4" />
              </Button>
            </div>

            {/* Datos de la tarjeta encontrada */}
            {tarjeta && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-2">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-base font-bold text-slate-800">{tarjeta.hijo_nombre}</p>
                    <p className="text-xs text-slate-500">{tarjeta.hijo_grado} · {tarjeta.cliente_nombre}</p>
                    <p className="text-xs text-slate-400 font-mono mt-0.5">{tarjeta.nro_tarjeta}</p>
                  </div>
                  <button onClick={limpiar} className="text-slate-300 hover:text-red-400 transition-colors cursor-pointer">
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="border-t border-emerald-200 pt-2 flex items-baseline gap-2">
                  <span className="text-xs text-slate-500">Saldo disponible:</span>
                  <span className={`text-xl font-extrabold tabular-nums ${Number(tarjeta.saldo_disponible) < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                    {formatGs(tarjeta.saldo_disponible)}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Formulario de carga */}
          {tarjeta && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5" />
                Nueva carga
              </p>

              {/* Montos rápidos */}
              <div>
                <p className="text-xs text-slate-400 mb-2">Montos rápidos</p>
                <div className="flex flex-wrap gap-2">
                  {MONTOS_RAPIDOS.map(m => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMonto(String(m))}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                        monto === String(m)
                          ? 'bg-green-600 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {(m).toLocaleString('es-PY')}
                    </button>
                  ))}
                </div>
              </div>

              <Input
                label="Monto (Gs.) *"
                type="number"
                min={1000}
                step={1000}
                value={monto}
                onChange={e => setMonto(e.target.value)}
                placeholder="0"
              />

              <div>
                <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
                  Método de pago
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {METODOS.map(m => (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => setMetodo(m.value)}
                      className={`px-3 py-2 rounded-xl text-xs font-semibold text-left transition-colors cursor-pointer border ${
                        metodo === m.value
                          ? 'bg-green-600 text-white border-green-600'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-green-400'
                      }`}
                    >
                      {m.label}
                      {!m.autoconfirma && (
                        <span className={`block text-[10px] mt-0.5 font-normal ${metodo === m.value ? 'text-green-100' : 'text-slate-400'}`}>
                          queda pendiente
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {!metodoSeleccionado?.autoconfirma && (
                <Input
                  label="Referencia / Comprobante"
                  value={referencia}
                  onChange={e => setReferencia(e.target.value)}
                  placeholder="Nro. de transferencia..."
                />
              )}

              <Button
                variant="primary"
                className="w-full"
                loading={cargando}
                onClick={handleCargar}
              >
                <RefreshCw className="w-4 h-4" />
                {metodoSeleccionado?.autoconfirma ? 'Cargar saldo' : 'Registrar carga pendiente'}
              </Button>
            </div>
          )}

          {/* Resultado de última operación */}
          {ultimaCarga && (
            <div className={`rounded-2xl border p-4 ${ultimaCarga.estado === 'CONFIRMADA' ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle className={`w-4 h-4 ${ultimaCarga.estado === 'CONFIRMADA' ? 'text-emerald-600' : 'text-amber-600'}`} />
                <span className={`text-sm font-semibold ${ultimaCarga.estado === 'CONFIRMADA' ? 'text-emerald-700' : 'text-amber-700'}`}>
                  {ultimaCarga.estado === 'CONFIRMADA' ? 'Carga realizada' : 'Carga registrada — pendiente'}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {formatGs(ultimaCarga.monto)} · {METODOS.find(m => m.value === ultimaCarga.metodo)?.label}
              </p>
              <button
                onClick={limpiar}
                className="mt-3 w-full text-xs text-slate-500 hover:text-slate-700 underline cursor-pointer"
              >
                Nueva operación
              </button>
            </div>
          )}
        </div>

        {/* ── Panel derecho: historial ───────────────────────────── */}
        <div className="lg:col-span-3">
          {tarjeta ? (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-slate-100 flex items-center gap-2">
                <History className="w-4 h-4 text-slate-400" />
                <span className="text-sm font-semibold text-slate-700">Historial — {tarjeta.hijo_nombre}</span>
              </div>

              <div className="border-b border-slate-100">
                <div className="flex">
                  {(['movimientos', 'cargas'] as const).map(tab => (
                    <button
                      key={tab}
                      onClick={() => setHistorialTab(tab)}
                      className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                        historialTab === tab
                          ? 'border-green-600 text-green-700'
                          : 'border-transparent text-slate-500 hover:text-slate-700'
                      }`}
                    >
                      {tab === 'movimientos' ? 'Movimientos' : 'Cargas de saldo'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="p-1">
                {loadingHistorial ? (
                  <div className="py-10 text-center text-slate-400 text-sm">Cargando historial...</div>
                ) : historialTab === 'movimientos' ? (
                  <Table columns={colsMovimientos} dataSource={movimientos} rowKey="id" pageSize={8} />
                ) : (
                  <Table columns={colsCargas} dataSource={cargas} rowKey="id" pageSize={8} />
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm flex flex-col items-center justify-center py-20 text-center px-8">
              <CreditCard className="w-12 h-12 text-slate-200 mb-4" />
              <p className="text-slate-400 text-sm">Buscá una tarjeta para ver el historial de movimientos y cargas</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
