import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  CreditCard, Search, Plus, Lock, Unlock, History,
  RefreshCw, ArrowUp, ArrowDown,
} from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import Modal from '../components/ui/Modal'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

function formatGs(n: number | string | null | undefined): string {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

function formatFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function formatFechaCorta(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string
  hijo_nombre: string
  hijo_grado: string
  cliente_nombre: string
  cliente_ruc: string
  saldo_actual: string | number
  saldo_disponible: string | number
  limite_credito: string | number
  estado: string
  fecha_vencimiento: string | null
  permite_saldo_negativo: boolean
}

interface Hijo {
  id: number
  nombre: string
  apellido: string
  grado: string
  activo: boolean
}

interface MovimientoTarjeta {
  id: number
  tarjeta: string
  tipo: string
  monto: string | number
  saldo_anterior: string | number
  saldo_resultante: string | number
  descripcion: string
  fecha: string
}

interface CargaSaldo {
  id: number
  tarjeta: string
  monto_cargado: string | number
  metodo_pago: string
  estado: string
  fecha: string
  usuario_nombre?: string
}

interface TarjetaForm {
  nro_tarjeta: string
  codigo_barras: string
  hijo: number | ''
  limite_credito: string
  permite_saldo_negativo: boolean
  estado: string
  fecha_vencimiento: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ESTADO_COLOR: Record<string, BadgeColor> = {
  ACTIVA: 'green',
  BLOQUEADA: 'orange',
  VENCIDA: 'red',
  CANCELADA: 'default',
}

const TIPO_MOV_LABEL: Record<string, string> = {
  RECARGA: 'Recarga',
  CONSUMO: 'Consumo',
  AJUSTE: 'Ajuste',
  REVERSO: 'Reverso',
}

const TIPO_MOV_COLOR: Record<string, BadgeColor> = {
  RECARGA: 'green',
  CONSUMO: 'blue',
  AJUSTE: 'orange',
  REVERSO: 'purple',
}

const ESTADO_CARGA_COLOR: Record<string, BadgeColor> = {
  APROBADA: 'green',
  PENDIENTE: 'yellow',
  RECHAZADA: 'red',
  ANULADA: 'default',
}

const METODO_PAGO_LABEL: Record<string, string> = {
  EFECTIVO: 'Efectivo',
  TRANSFERENCIA: 'Transferencia',
  TARJETA: 'Tarjeta',
}

const FORM_INITIAL: TarjetaForm = {
  nro_tarjeta: '', codigo_barras: '', hijo: '',
  limite_credito: '', permite_saldo_negativo: false,
  estado: 'ACTIVA', fecha_vencimiento: '',
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Tarjetas() {
  const [tarjetas, setTarjetas] = useState<Tarjeta[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const [detailTarjeta, setDetailTarjeta] = useState<Tarjeta | null>(null)
  const [detailTab, setDetailTab] = useState<'movimientos' | 'cargas'>('movimientos')
  const [movimientos, setMovimientos] = useState<MovimientoTarjeta[]>([])
  const [cargas, setCargas] = useState<CargaSaldo[]>([])
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [tipoMovFilter, setTipoMovFilter] = useState('')

  const [createOpen, setCreateOpen] = useState(false)
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [form, setForm] = useState<TarjetaForm>(FORM_INITIAL)
  const [saving, setSaving] = useState(false)

  const [recargaOpen, setRecargaOpen] = useState(false)
  const [recargaTarjeta, setRecargaTarjeta] = useState<Tarjeta | null>(null)
  const [montoRecarga, setMontoRecarga] = useState('')
  const [metodoPago, setMetodoPago] = useState('EFECTIVO')
  const [recargando, setRecargando] = useState(false)

  const [toggling, setToggling] = useState<string | null>(null)

  // ── Data loading ────────────────────────────────────────────────

  const loadTarjetas = useCallback(async (q: string, estado: string, p: number) => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15 }
      if (q) params.search = q
      if (estado) params.estado = estado
      const { data } = await api.get('/core/tarjetas/', { params })
      setTarjetas(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      toast.error('Error al cargar tarjetas')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      setPage(1)
      loadTarjetas(search, estadoFilter, 1)
    }, 350)
    return () => clearTimeout(searchTimer.current)
  }, [search, estadoFilter, loadTarjetas])

  useEffect(() => {
    loadTarjetas(search, estadoFilter, page)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const openDetail = useCallback(async (t: Tarjeta) => {
    setDetailTarjeta(t)
    setDetailTab('movimientos')
    setTipoMovFilter('')
    setLoadingDetail(true)
    try {
      const [movRes, cargaRes] = await Promise.all([
        api.get('/core/movimientos-tarjeta/', { params: { tarjeta: t.nro_tarjeta, page_size: 200 } }),
        api.get('/core/cargas-saldo/', { params: { tarjeta: t.nro_tarjeta, page_size: 200 } }),
      ])
      setMovimientos(movRes.data.results ?? movRes.data ?? [])
      setCargas(cargaRes.data.results ?? cargaRes.data ?? [])
    } catch {
      toast.error('Error al cargar historial')
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  useEffect(() => {
    if (createOpen && hijos.length === 0) {
      api.get('/clientes/hijos/', { params: { activo: true, page_size: 500 } })
        .then(({ data }) => setHijos(data.results ?? []))
        .catch(() => {})
    }
  }, [createOpen, hijos.length])

  // ── Actions ─────────────────────────────────────────────────────

  const toggleEstado = useCallback(async (t: Tarjeta) => {
    const nuevoEstado = t.estado === 'ACTIVA' ? 'BLOQUEADA' : 'ACTIVA'
    setToggling(t.nro_tarjeta)
    try {
      await api.patch(`/core/tarjetas/${t.nro_tarjeta}/`, { estado: nuevoEstado })
      toast.success(nuevoEstado === 'BLOQUEADA' ? 'Tarjeta bloqueada' : 'Tarjeta activada')
      setDetailTarjeta(prev => prev?.nro_tarjeta === t.nro_tarjeta ? { ...prev, estado: nuevoEstado } : prev)
      loadTarjetas(search, estadoFilter, page)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setToggling(null)
    }
  }, [search, estadoFilter, page, loadTarjetas])

  const handleCreate = useCallback(async () => {
    if (!form.nro_tarjeta || !form.hijo) { toast.error('Completá los campos obligatorios'); return }
    setSaving(true)
    try {
      await api.post('/core/tarjetas/', {
        ...form,
        limite_credito: Number(form.limite_credito) || 0,
      })
      toast.success('Tarjeta creada')
      setCreateOpen(false)
      setForm(FORM_INITIAL)
      setPage(1)
      loadTarjetas(search, estadoFilter, 1)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }, [form, search, estadoFilter, loadTarjetas])

  const openRecarga = useCallback((t: Tarjeta) => {
    setRecargaTarjeta(t)
    setMontoRecarga('')
    setMetodoPago('EFECTIVO')
    setRecargaOpen(true)
  }, [])

  const handleRecarga = useCallback(async () => {
    const montoNum = Number(montoRecarga) || 0
    if (montoNum <= 0) { toast.error('Ingresá un monto válido'); return }
    setRecargando(true)
    try {
      await api.post('/core/cargas-saldo/', {
        tarjeta: recargaTarjeta?.nro_tarjeta,
        monto_cargado: montoNum,
        metodo_pago: metodoPago,
      })
      toast.success('Recarga realizada')
      setRecargaOpen(false)
      loadTarjetas(search, estadoFilter, page)
      if (detailTarjeta && recargaTarjeta && detailTarjeta.nro_tarjeta === recargaTarjeta.nro_tarjeta) {
        openDetail(detailTarjeta)
      }
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setRecargando(false)
    }
  }, [montoRecarga, metodoPago, recargaTarjeta, search, estadoFilter, page, loadTarjetas, detailTarjeta, openDetail])

  // ── Derived ─────────────────────────────────────────────────────

  const movimientosFiltrados = useMemo(
    () => tipoMovFilter ? movimientos.filter(m => m.tipo === tipoMovFilter) : movimientos,
    [movimientos, tipoMovFilter],
  )

  // ── Columns ─────────────────────────────────────────────────────

  const columnsMain: Column<Tarjeta>[] = [
    {
      title: 'Nro. Tarjeta',
      key: 'nro',
      render: (_, r) => (
        <div>
          <p className="font-mono text-sm font-semibold text-slate-800">{r.nro_tarjeta}</p>
          <p className="text-xs text-slate-400">{r.codigo_barras || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Estudiante',
      key: 'hijo',
      render: (_, r) => (
        <div>
          <p className="text-sm font-medium text-slate-800">{r.hijo_nombre}</p>
          <p className="text-xs text-slate-400">{r.hijo_grado}</p>
        </div>
      ),
    },
    {
      title: 'Cliente',
      key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-sm text-slate-700">{r.cliente_nombre}</p>
          <p className="text-xs text-slate-400">{r.cliente_ruc}</p>
        </div>
      ),
    },
    {
      title: 'Saldo',
      key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_actual) || 0
        return (
          <span className={`tabular-nums font-semibold text-sm ${n < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
            {formatGs(n)}
          </span>
        )
      },
    },
    {
      title: 'Límite',
      key: 'limite',
      render: (_, r) => (
        <span className="tabular-nums text-sm text-slate-500">{formatGs(r.limite_credito)}</span>
      ),
    },
    {
      title: 'Vencimiento',
      key: 'vto',
      render: (_, r) => (
        <span className="text-sm text-slate-600">{formatFechaCorta(r.fecha_vencimiento)}</span>
      ),
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 210,
      render: (_, r) => (
        <div className="flex items-center gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => openDetail(r)}>
            <History className="w-3.5 h-3.5" />
            Ver
          </Button>
          <Button size="sm" variant="secondary" onClick={() => openRecarga(r)} disabled={r.estado !== 'ACTIVA'}>
            <RefreshCw className="w-3.5 h-3.5" />
            Recargar
          </Button>
          <Button
            size="sm"
            variant={r.estado === 'ACTIVA' ? 'danger' : 'primary'}
            onClick={() => toggleEstado(r)}
            loading={toggling === r.nro_tarjeta}
            disabled={r.estado === 'VENCIDA' || r.estado === 'CANCELADA'}
          >
            {r.estado === 'ACTIVA'
              ? <Lock className="w-3.5 h-3.5" />
              : <Unlock className="w-3.5 h-3.5" />}
          </Button>
        </div>
      ),
    },
  ]

  const colsMovimientos: Column<MovimientoTarjeta>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-xs text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => (
        <Badge color={TIPO_MOV_COLOR[r.tipo] ?? 'default'}>{TIPO_MOV_LABEL[r.tipo] ?? r.tipo}</Badge>
      ),
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => {
        const isEntry = r.tipo === 'RECARGA' || r.tipo === 'REVERSO'
        return (
          <span className={`tabular-nums font-semibold text-sm flex items-center gap-0.5 ${isEntry ? 'text-emerald-700' : 'text-slate-700'}`}>
            {isEntry ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {formatGs(r.monto)}
          </span>
        )
      },
    },
    {
      title: 'Saldo ant.',
      key: 'saldo_ant',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-400">{formatGs(r.saldo_anterior)}</span>,
    },
    {
      title: 'Saldo result.',
      key: 'saldo_res',
      render: (_, r) => (
        <span className={`tabular-nums text-sm font-medium ${Number(r.saldo_resultante) < 0 ? 'text-red-600' : 'text-slate-700'}`}>
          {formatGs(r.saldo_resultante)}
        </span>
      ),
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-sm text-slate-400">{r.descripcion || '—'}</span>,
    },
  ]

  const colsCargas: Column<CargaSaldo>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-xs text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => (
        <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto_cargado)}</span>
      ),
    },
    {
      title: 'Método',
      key: 'metodo',
      render: (_, r) => (
        <span className="text-sm text-slate-600">{METODO_PAGO_LABEL[r.metodo_pago] ?? r.metodo_pago}</span>
      ),
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_CARGA_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: 'Usuario',
      key: 'usuario',
      render: (_, r) => <span className="text-sm text-slate-400">{r.usuario_nombre ?? '—'}</span>,
    },
  ]

  // ── Styles ──────────────────────────────────────────────────────

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  // ── Render ──────────────────────────────────────────────────────

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tarjetas</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de tarjetas prepago de estudiantes</p>
        </div>
        <Button variant="primary" onClick={() => { setForm(FORM_INITIAL); setCreateOpen(true) }}>
          <Plus className="w-4 h-4" />
          Nueva Tarjeta
        </Button>
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[200px]">
          <label className={labelClass}>Buscar</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            <input
              placeholder="Nro. tarjeta, estudiante..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className={`${inputClass} pl-9`}
            />
          </div>
        </div>
        <div>
          <label className={labelClass}>Estado</label>
          <select
            value={estadoFilter}
            onChange={e => { setEstadoFilter(e.target.value); setPage(1) }}
            className={`${inputClass} w-auto`}
          >
            <option value="">Todos</option>
            <option value="ACTIVA">Activa</option>
            <option value="BLOQUEADA">Bloqueada</option>
            <option value="VENCIDA">Vencida</option>
            <option value="CANCELADA">Cancelada</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-slate-400" />
            Tarjetas
          </h2>
          <span className="text-xs text-slate-400">{total} registros</span>
        </div>
        <div className="p-1">
          <Table
            columns={columnsMain}
            dataSource={tarjetas}
            rowKey="nro_tarjeta"
            loading={loading}
            pageSize={15}
            page={page}
            onPageChange={setPage}
            total={total}
          />
        </div>
      </div>

      {/* ── Detail Modal ─────────────────────────────────────────── */}
      {detailTarjeta && (
        <Modal
          open
          title={`Tarjeta ${detailTarjeta.nro_tarjeta} — ${detailTarjeta.hijo_nombre}`}
          onCancel={() => setDetailTarjeta(null)}
          width={820}
          footer={null}
        >
          {/* Summary cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {[
              { label: 'Saldo Actual', value: formatGs(detailTarjeta.saldo_actual), warn: Number(detailTarjeta.saldo_actual) < 0 },
              { label: 'Saldo Disponible', value: formatGs(detailTarjeta.saldo_disponible) },
              { label: 'Límite Crédito', value: formatGs(detailTarjeta.limite_credito) },
              { label: 'Vencimiento', value: formatFechaCorta(detailTarjeta.fecha_vencimiento) },
            ].map(({ label, value, warn }) => (
              <div key={label} className="bg-slate-50 rounded-xl px-3 py-3">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className={`text-base font-bold mt-0.5 tabular-nums ${warn ? 'text-red-600' : 'text-slate-800'}`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Status + actions */}
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <div className="flex items-center gap-2">
              <Badge color={ESTADO_COLOR[detailTarjeta.estado] ?? 'default'}>{detailTarjeta.estado}</Badge>
              {detailTarjeta.permite_saldo_negativo && <Badge color="yellow">Permite saldo negativo</Badge>}
              <span className="text-xs text-slate-400">Cliente: {detailTarjeta.cliente_nombre}</span>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={() => openRecarga(detailTarjeta)} disabled={detailTarjeta.estado !== 'ACTIVA'}>
                <RefreshCw className="w-3.5 h-3.5" />
                Recargar
              </Button>
              <Button
                size="sm"
                variant={detailTarjeta.estado === 'ACTIVA' ? 'danger' : 'primary'}
                onClick={() => toggleEstado(detailTarjeta)}
                loading={toggling === detailTarjeta.nro_tarjeta}
                disabled={detailTarjeta.estado === 'VENCIDA' || detailTarjeta.estado === 'CANCELADA'}
              >
                {detailTarjeta.estado === 'ACTIVA' ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                {detailTarjeta.estado === 'ACTIVA' ? 'Bloquear' : 'Activar'}
              </Button>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-slate-200 mb-4">
            <div className="flex">
              {(['movimientos', 'cargas'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setDetailTab(tab)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                    detailTab === tab
                      ? 'border-green-600 text-green-700'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  {tab === 'movimientos' ? 'Movimientos' : 'Cargas de Saldo'}
                </button>
              ))}
            </div>
          </div>

          {loadingDetail ? (
            <div className="py-10 text-center text-slate-400 text-sm">Cargando historial...</div>
          ) : detailTab === 'movimientos' ? (
            <>
              <div className="mb-3">
                <select
                  value={tipoMovFilter}
                  onChange={e => setTipoMovFilter(e.target.value)}
                  className="border border-slate-200 rounded-xl px-3 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                >
                  <option value="">Todos los tipos</option>
                  <option value="RECARGA">Recarga</option>
                  <option value="CONSUMO">Consumo</option>
                  <option value="AJUSTE">Ajuste</option>
                  <option value="REVERSO">Reverso</option>
                </select>
              </div>
              <Table columns={colsMovimientos} dataSource={movimientosFiltrados} rowKey="id" pageSize={8} />
            </>
          ) : (
            <Table columns={colsCargas} dataSource={cargas} rowKey="id" pageSize={8} />
          )}

          <div className="flex justify-end mt-5">
            <Button variant="secondary" onClick={() => setDetailTarjeta(null)}>Cerrar</Button>
          </div>
        </Modal>
      )}

      {/* ── Create Modal ──────────────────────────────────────────── */}
      <Modal
        open={createOpen}
        title="Nueva Tarjeta"
        onOk={handleCreate}
        onCancel={() => setCreateOpen(false)}
        okText="Crear Tarjeta"
        confirmLoading={saving}
        width={540}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nro. Tarjeta *</label>
              <input
                value={form.nro_tarjeta}
                onChange={e => setForm(f => ({ ...f, nro_tarjeta: e.target.value }))}
                placeholder="0001234"
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Código de Barras</label>
              <input
                value={form.codigo_barras}
                onChange={e => setForm(f => ({ ...f, codigo_barras: e.target.value }))}
                placeholder="1234567890"
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className={labelClass}>Estudiante *</label>
            <select
              value={form.hijo}
              onChange={e => setForm(f => ({ ...f, hijo: Number(e.target.value) || '' }))}
              className={inputClass}
            >
              <option value="">Seleccionar estudiante...</option>
              {hijos.map(h => (
                <option key={h.id} value={h.id}>{h.nombre} {h.apellido} — {h.grado}</option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Límite de Crédito (Gs.)</label>
              <input
                type="number"
                value={form.limite_credito}
                onChange={e => setForm(f => ({ ...f, limite_credito: e.target.value }))}
                placeholder="0"
                min={0}
                step={1000}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Estado inicial</label>
              <select
                value={form.estado}
                onChange={e => setForm(f => ({ ...f, estado: e.target.value }))}
                className={inputClass}
              >
                <option value="ACTIVA">Activa</option>
                <option value="BLOQUEADA">Bloqueada</option>
              </select>
            </div>
          </div>

          <div>
            <label className={labelClass}>Fecha de Vencimiento</label>
            <input
              type="date"
              value={form.fecha_vencimiento}
              onChange={e => setForm(f => ({ ...f, fecha_vencimiento: e.target.value }))}
              className={inputClass}
            />
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative shrink-0">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={form.permite_saldo_negativo}
                onChange={e => setForm(f => ({ ...f, permite_saldo_negativo: e.target.checked }))}
              />
              <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
            </div>
            <span className="text-sm text-slate-700">Permite saldo negativo</span>
          </label>
        </div>
      </Modal>

      {/* ── Recarga Modal ─────────────────────────────────────────── */}
      <Modal
        open={recargaOpen}
        title={`Recargar — ${recargaTarjeta?.hijo_nombre ?? ''}`}
        onOk={handleRecarga}
        onCancel={() => setRecargaOpen(false)}
        okText="Recargar"
        confirmLoading={recargando}
        width={400}
      >
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl px-4 py-3 flex justify-between items-center">
            <div>
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">Saldo actual</p>
              <p className="text-xl font-bold tabular-nums text-slate-800">
                {formatGs(recargaTarjeta?.saldo_actual)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">Nro. tarjeta</p>
              <p className="text-sm font-mono font-semibold text-slate-700">{recargaTarjeta?.nro_tarjeta}</p>
            </div>
          </div>

          <div>
            <label className={labelClass}>Monto a recargar *</label>
            <input
              type="number"
              value={montoRecarga}
              onChange={e => setMontoRecarga(e.target.value)}
              placeholder="Guaraníes"
              min={1000}
              step={1000}
              className={inputClass}
              autoFocus
            />
          </div>

          <div>
            <label className={labelClass}>Método de pago</label>
            <select
              value={metodoPago}
              onChange={e => setMetodoPago(e.target.value)}
              className={inputClass}
            >
              <option value="EFECTIVO">Efectivo</option>
              <option value="TRANSFERENCIA">Transferencia</option>
              <option value="TARJETA">Tarjeta</option>
            </select>
          </div>
        </div>
      </Modal>
    </div>
  )
}
