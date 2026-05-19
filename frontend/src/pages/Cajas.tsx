import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, Lock, CheckCircle, Banknote, LayoutGrid } from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Caja { id: number; nombre: string; ubicacion: string | null; activo: boolean }

interface CierreCaja {
  id: number
  caja: number
  caja_nombre: string
  empleado_nombre: string
  fecha_apertura: string
  fecha_cierre: string | null
  monto_inicial: string
  monto_contado_fisico: string | null
  diferencia_efectivo: string | null
  estado: 'ABIERTO' | 'CERRADO' | 'CONCILIADO'
  observaciones_conciliacion: string | null
}

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

function formatGs(value: string | number | null | undefined): string {
  return (Number(value) || 0).toLocaleString('es-PY') + ' Gs.'
}

function formatDatetime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const ESTADO_COLOR: Record<string, BadgeColor> = {
  ABIERTO: 'green', CERRADO: 'blue', CONCILIADO: 'purple',
}
const ESTADO_LABEL: Record<string, string> = {
  ABIERTO: 'Abierta', CERRADO: 'Cerrada', CONCILIADO: 'Conciliada',
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function CajaPage() {
  const [cierres, setCierres] = useState<CierreCaja[]>([])
  const [cajas, setCajas] = useState<Caja[]>([])
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filterEstado, setFilterEstado] = useState('')
  const [filterCaja, setFilterCaja] = useState('')

  // Abrir caja modal
  const [abrirModal, setAbrirModal] = useState(false)
  const [cajaSeleccionada, setCajaSeleccionada] = useState('')
  const [montoInicial, setMontoInicial] = useState('')
  const [abriendo, setAbriendo] = useState(false)

  // Cerrar caja modal
  const [cerrarModal, setCerrarModal] = useState<CierreCaja | null>(null)
  const [montoContado, setMontoContado] = useState('')
  const [cerrando, setCerrando] = useState(false)

  // Conciliar modal
  const [conciliarModal, setConciliarModal] = useState<CierreCaja | null>(null)
  const [obsConc, setObsConc] = useState('')
  const [conciliando, setConciliando] = useState(false)

  const filterTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  const loadCierres = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, page_size: 15 }
      if (filterEstado) params.estado = filterEstado
      if (filterCaja) params.caja = filterCaja
      const { data } = await api.get('/contabilidad/cierres-caja/', { params })
      setCierres(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      toast.error('Error al cargar cierres')
    } finally {
      setLoading(false)
    }
  }, [page, filterEstado, filterCaja])

  useEffect(() => {
    loadCierres()
  }, [loadCierres])

  useEffect(() => {
    api.get('/contabilidad/cajas/')
      .then(({ data }) => {
        const lista: Caja[] = data.results ?? data
        setCajas(lista)
        if (lista.length > 0) setCajaSeleccionada(String(lista[0].id))
      })
      .catch(() => {})
  }, [])

  // ── Handlers ────────────────────────────────────────────────────────────────

  async function abrirCaja() {
    if (!cajaSeleccionada) { toast.error('Seleccioná una caja'); return }
    setAbriendo(true)
    try {
      await api.post('/contabilidad/cierres-caja/', {
        caja: Number(cajaSeleccionada),
        monto_inicial: Number(montoInicial) || 0,
      })
      toast.success('Caja abierta')
      setAbrirModal(false)
      setMontoInicial('')
      loadCierres()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAbriendo(false)
    }
  }

  async function confirmarCierre() {
    if (!cerrarModal) return
    setCerrando(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${cerrarModal.id}/cerrar/`, {
        monto_contado_fisico: Number(montoContado) || 0,
      })
      toast.success('Caja cerrada')
      setCerrarModal(null)
      loadCierres()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setCerrando(false)
    }
  }

  async function confirmarConciliar() {
    if (!conciliarModal) return
    setConciliando(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${conciliarModal.id}/conciliar/`, {
        observaciones: obsConc,
      })
      toast.success('Cierre conciliado')
      setConciliarModal(null)
      loadCierres()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setConciliando(false)
    }
  }

  function handleFilterChange(setter: (v: string) => void) {
    return (e: React.ChangeEvent<HTMLSelectElement>) => {
      clearTimeout(filterTimerRef.current)
      filterTimerRef.current = setTimeout(() => {
        setter(e.target.value)
        setPage(1)
      }, 0)
    }
  }

  // ── Columns ──────────────────────────────────────────────────────────────────

  const columns = useMemo<Column<CierreCaja>[]>(() => [
    {
      title: 'Caja / Cajero',
      key: 'caja',
      render: (_, r) => (
        <div>
          <p className="text-sm font-semibold text-slate-800">{r.caja_nombre}</p>
          <p className="text-xs text-slate-400 mt-0.5">{r.empleado_nombre}</p>
        </div>
      ),
    },
    {
      title: 'Apertura',
      key: 'apertura',
      render: (_, r) => (
        <span className="text-sm text-slate-600">{formatDatetime(r.fecha_apertura)}</span>
      ),
    },
    {
      title: 'Cierre',
      key: 'cierre',
      render: (_, r) => (
        <span className="text-sm text-slate-600">{formatDatetime(r.fecha_cierre)}</span>
      ),
    },
    {
      title: 'Monto Inicial',
      key: 'inicial',
      render: (_, r) => (
        <span className="tabular-nums text-sm text-slate-700">{formatGs(r.monto_inicial)}</span>
      ),
    },
    {
      title: 'Diferencia',
      key: 'diferencia',
      render: (_, r) => {
        if (r.diferencia_efectivo === null) return <span className="text-slate-300">—</span>
        const n = Number(r.diferencia_efectivo) || 0
        return (
          <span className={[
            'tabular-nums text-sm font-semibold',
            n === 0 ? 'text-emerald-700' : 'text-red-600',
          ].join(' ')}>
            {n > 0 ? '+' : ''}{formatGs(n)}
          </span>
        )
      },
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => (
        <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>
          {ESTADO_LABEL[r.estado] ?? r.estado}
        </Badge>
      ),
    },
    {
      title: '',
      key: 'acciones',
      width: 140,
      render: (_, r) => (
        <div className="flex items-center gap-1.5 justify-end">
          {r.estado === 'ABIERTO' && (
            <button
              onClick={() => { setCerrarModal(r); setMontoContado('') }}
              className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
            >
              <Lock className="w-3 h-3" />
              Cerrar
            </button>
          )}
          {r.estado === 'CERRADO' && (
            <button
              onClick={() => { setConciliarModal(r); setObsConc('') }}
              className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
            >
              <CheckCircle className="w-3 h-3" />
              Conciliar
            </button>
          )}
        </div>
      ),
    },
  ], [])

  // ── Stats ────────────────────────────────────────────────────────────────────

  const stats = useMemo(() => ({
    abiertas: cierres.filter(c => c.estado === 'ABIERTO').length,
    cerradas: cierres.filter(c => c.estado === 'CERRADO').length,
    conciliadas: cierres.filter(c => c.estado === 'CONCILIADO').length,
  }), [cierres])

  const selectClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const cajaActiva = cajas.find(c => String(c.id) === cajaSeleccionada)

  return (
    <div className="p-4 md:p-6 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Caja</h1>
          <p className="text-sm text-slate-500 mt-0.5">Apertura y cierre de cajas registradoras</p>
        </div>
        <Button variant="primary" onClick={() => setAbrirModal(true)}>
          <Plus className="w-4 h-4" />
          Abrir Caja
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Abiertas', value: stats.abiertas, color: 'text-green-600', icon: Banknote },
          { label: 'Cerradas', value: stats.cerradas, color: 'text-blue-600', icon: Lock },
          { label: 'Conciliadas', value: stats.conciliadas, color: 'text-purple-600', icon: CheckCircle },
        ].map(({ label, value, color, icon: Icon }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex items-start justify-between gap-2">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
              <p className={`text-2xl font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
            </div>
            <Icon className={`w-5 h-5 mt-1 ${color} opacity-40`} />
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex flex-wrap gap-3 items-center">
        <LayoutGrid className="w-4 h-4 text-slate-400" />
        <select value={filterEstado} onChange={handleFilterChange(setFilterEstado)} className={selectClass}>
          <option value="">Todos los estados</option>
          <option value="ABIERTO">Abiertas</option>
          <option value="CERRADO">Cerradas</option>
          <option value="CONCILIADO">Conciliadas</option>
        </select>
        <select value={filterCaja} onChange={handleFilterChange(setFilterCaja)} className={selectClass}>
          <option value="">Todas las cajas</option>
          {cajas.map(c => (
            <option key={c.id} value={c.id}>{c.nombre}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden p-1">
        <Table
          columns={columns}
          dataSource={cierres}
          rowKey="id"
          loading={loading}
          pageSize={15}
          page={page}
          onPageChange={setPage}
          total={total}
        />
      </div>

      {/* ── Abrir Caja Modal ───────────────────────────────────────────────── */}
      <Modal
        open={abrirModal}
        title="Abrir Caja"
        onCancel={() => setAbrirModal(false)}
        onOk={abrirCaja}
        okText="Abrir Caja"
        confirmLoading={abriendo}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Caja
            </label>
            <select
              value={cajaSeleccionada}
              onChange={e => setCajaSeleccionada(e.target.value)}
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
            >
              <option value="">Seleccionar caja...</option>
              {cajas.filter(c => c.activo).map(c => (
                <option key={c.id} value={c.id}>
                  {c.nombre}{c.ubicacion ? ` — ${c.ubicacion}` : ''}
                </option>
              ))}
            </select>
          </div>
          {cajaActiva && (
            <div className="bg-green-50 border border-green-100 rounded-xl px-4 py-2.5">
              <p className="text-xs text-green-700 font-medium">{cajaActiva.nombre}</p>
              {cajaActiva.ubicacion && (
                <p className="text-xs text-green-600 mt-0.5">{cajaActiva.ubicacion}</p>
              )}
            </div>
          )}
          <Input
            label="Monto Inicial (Gs.)"
            type="number"
            placeholder="0"
            value={montoInicial}
            onChange={e => setMontoInicial(e.target.value)}
            min={0}
            step={10000}
          />
        </div>
      </Modal>

      {/* ── Cerrar Caja Modal ──────────────────────────────────────────────── */}
      <Modal
        open={!!cerrarModal}
        title={`Cerrar Caja — ${cerrarModal?.caja_nombre ?? ''}`}
        onCancel={() => setCerrarModal(null)}
        onOk={confirmarCierre}
        okText="Confirmar Cierre"
        confirmLoading={cerrando}
        width={420}
      >
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Apertura:</span>
              <span className="font-medium text-slate-700">{formatDatetime(cerrarModal?.fecha_apertura)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Monto inicial:</span>
              <span className="font-semibold text-slate-800 tabular-nums">{formatGs(cerrarModal?.monto_inicial)}</span>
            </div>
          </div>
          <Input
            label="Monto Contado en Efectivo (Gs.)"
            type="number"
            placeholder="0"
            value={montoContado}
            onChange={e => setMontoContado(e.target.value)}
            min={0}
            step={10000}
          />
          <p className="text-xs text-slate-400">
            La diferencia entre el monto esperado y el contado quedará registrada.
          </p>
        </div>
      </Modal>

      {/* ── Conciliar Modal ────────────────────────────────────────────────── */}
      <Modal
        open={!!conciliarModal}
        title={`Conciliar Cierre — ${conciliarModal?.caja_nombre ?? ''}`}
        onCancel={() => setConciliarModal(null)}
        onOk={confirmarConciliar}
        okText="Conciliar"
        confirmLoading={conciliando}
        width={440}
      >
        <div className="space-y-4">
          {conciliarModal && (
            <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Monto contado:</span>
                <span className="font-semibold tabular-nums text-slate-800">
                  {formatGs(conciliarModal.monto_contado_fisico)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Diferencia:</span>
                <span className={[
                  'font-semibold tabular-nums',
                  Number(conciliarModal.diferencia_efectivo) === 0 ? 'text-emerald-700' : 'text-red-600',
                ].join(' ')}>
                  {formatGs(conciliarModal.diferencia_efectivo)}
                </span>
              </div>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
              Observaciones del Contador
            </label>
            <textarea
              value={obsConc}
              onChange={e => setObsConc(e.target.value)}
              rows={3}
              placeholder="Notas de conciliación (opcional)..."
              className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors resize-none"
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}
