import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  CreditCard, Search, Plus, Lock, Unlock, History,
  ArrowUp, ArrowDown, Edit2,
} from 'lucide-react'
import tarjetasService from '../services/tarjetas'
import clientesService from '../services/clientes'
import api from '../services/api'
import { METODO_PAGO_LABEL } from '../constants/mediosPago'
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
  es_alumno: boolean
  hijo_nombre: string | null
  hijo_grado: string | null
  cliente_nombre: string | null
  cliente_ruc: string | null
  saldo_actual: string | number
  saldo_disponible: string | number
  limite_credito: string | number
  estado: string
  fecha_vencimiento: string | null
  permite_saldo_negativo: boolean
}

interface ClienteBasico {
  id: number
  nombre_completo: string
  ruc_ci: string
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
  fecha_carga: string
  usuario_nombre?: string
}

type TipoTitular = 'alumno' | 'funcionario'

interface TarjetaForm {
  nro_tarjeta: string
  codigo_barras: string
  tipoTitular: TipoTitular
  hijo: number | ''
  cliente_directo: number | ''
  limite_credito: string
  permite_saldo_negativo: boolean
  estado: string
  fecha_vencimiento: string
}

interface TarjetaEditForm {
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
  CONFIRMADA: 'green',
  PENDIENTE: 'yellow',
  RECHAZADA: 'red',
}

const FORM_INITIAL: TarjetaForm = {
  nro_tarjeta: '', codigo_barras: '',
  tipoTitular: 'alumno', hijo: '', cliente_directo: '',
  limite_credito: '', permite_saldo_negativo: false,
  estado: 'ACTIVA', fecha_vencimiento: '',
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Tarjetas() {
  const { t } = useTranslation()
  const [tarjetas, setTarjetas] = useState<Tarjeta[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [estadoFilter, setEstadoFilter] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdRef = useRef(0)

  const [detailTarjeta, setDetailTarjeta] = useState<Tarjeta | null>(null)
  const [detailTab, setDetailTab] = useState<'movimientos' | 'cargas'>('movimientos')
  const [movimientos, setMovimientos] = useState<MovimientoTarjeta[]>([])
  const [cargas, setCargas] = useState<CargaSaldo[]>([])
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [tipoMovFilter, setTipoMovFilter] = useState('')

  const [createOpen, setCreateOpen] = useState(false)
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [clientesSearch, setClientesSearch] = useState('')
  const [clientes, setClientes] = useState<ClienteBasico[]>([])
  const [loadingClientes, setLoadingClientes] = useState(false)
  const clientesTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const [form, setForm] = useState<TarjetaForm>(FORM_INITIAL)
  const [saving, setSaving] = useState(false)

  const [toggling, setToggling] = useState<string | null>(null)

  const [editTarjeta, setEditTarjeta] = useState<Tarjeta | null>(null)
  const [editForm, setEditForm] = useState<TarjetaEditForm>({
    limite_credito: '', permite_saldo_negativo: false, estado: 'ACTIVA', fecha_vencimiento: '',
  })
  const [editSaving, setEditSaving] = useState(false)

  // ── Confirmar carga modal ───────────────────────────────────────
  const [confirmCargaId, setConfirmCargaId] = useState<number | null>(null)
  const [confirmFactura, setConfirmFactura] = useState({ emitir: false, nro: '' })
  const [confirmando, setConfirmando] = useState(false)

  // ── Data loading ────────────────────────────────────────────────

  const loadTarjetas = useCallback(async (q: string, estado: string, p: number) => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15 }
      if (q) params.search = q
      if (estado) params.estado = estado
      const { data } = await tarjetasService.listar<Tarjeta>(params)
      if (requestId !== requestIdRef.current) return
      setTarjetas(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (requestId !== requestIdRef.current) return
      toast.error('Error al cargar tarjetas')
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
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

  const openDetail = useCallback(async (t: Tarjeta) => {
    setDetailTarjeta(t)
    setDetailTab('movimientos')
    setTipoMovFilter('')
    setLoadingDetail(true)
    try {
      const [movRes, cargaRes] = await Promise.all([
        tarjetasService.getMovimientos<MovimientoTarjeta>(t.nro_tarjeta, 200),
        tarjetasService.getCargas<CargaSaldo>(t.nro_tarjeta, 200),
      ])
      setMovimientos(movRes.data.results ?? [])
      setCargas(cargaRes.data.results ?? [])
    } catch {
      toast.error('Error al cargar historial')
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  useEffect(() => {
    if (createOpen && hijos.length === 0) {
      clientesService.getHijos<Hijo>({ activo: true, page_size: 500 })
        .then(({ data }) => setHijos(data.results ?? []))
        .catch(() => {})
    }
  }, [createOpen, hijos.length])

  // Búsqueda debounced de clientes (docentes/funcionarios) para el modal de creación
  useEffect(() => {
    if (!createOpen || form.tipoTitular !== 'funcionario') return
    clearTimeout(clientesTimer.current)
    if (!clientesSearch.trim()) { setClientes([]); return }
    clientesTimer.current = setTimeout(() => {
      setLoadingClientes(true)
      api.get<{ results?: ClienteBasico[]; count?: number }>('/clientes/clientes/', {
        params: { search: clientesSearch, activo: true, page_size: 8 },
      })
        .then(({ data }) => setClientes(data.results ?? []))
        .catch(() => setClientes([]))
        .finally(() => setLoadingClientes(false))
    }, 350)
    return () => clearTimeout(clientesTimer.current)
  }, [clientesSearch, createOpen, form.tipoTitular])

  // ── Actions ─────────────────────────────────────────────────────

  const toggleEstado = useCallback(async (t: Tarjeta) => {
    const nuevoEstado = t.estado === 'ACTIVA' ? 'BLOQUEADA' : 'ACTIVA'
    setToggling(t.nro_tarjeta)
    try {
      await tarjetasService.actualizar(t.nro_tarjeta, { estado: nuevoEstado })
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
    if (!form.nro_tarjeta) { toast.error('Ingresá el número de tarjeta'); return }
    if (form.tipoTitular === 'alumno' && !form.hijo) {
      toast.error('Seleccioná el estudiante'); return
    }
    if (form.tipoTitular === 'funcionario' && !form.cliente_directo) {
      toast.error('Seleccioná el cliente (docente/funcionario)'); return
    }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        nro_tarjeta: form.nro_tarjeta,
        codigo_barras: form.codigo_barras || null,
        limite_credito: Number(form.limite_credito) || 0,
        permite_saldo_negativo: form.permite_saldo_negativo,
        estado: form.estado,
        fecha_vencimiento: form.fecha_vencimiento || null,
      }
      if (form.tipoTitular === 'alumno') {
        payload.hijo = form.hijo
        payload.cliente_directo = null
      } else {
        payload.hijo = null
        payload.cliente_directo = form.cliente_directo
      }
      await tarjetasService.crear(payload)
      toast.success('Tarjeta creada')
      setCreateOpen(false)
      setForm(FORM_INITIAL)
      setClientesSearch('')
      setClientes([])
      setPage(1)
      loadTarjetas(search, estadoFilter, 1)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }, [form, search, estadoFilter, loadTarjetas])

  const openEdit = useCallback((t: Tarjeta) => {
    setEditTarjeta(t)
    setEditForm({
      limite_credito: String(Number(t.limite_credito) || 0),
      permite_saldo_negativo: t.permite_saldo_negativo,
      estado: t.estado,
      fecha_vencimiento: t.fecha_vencimiento ?? '',
    })
  }, [])

  const handleEditSave = useCallback(async () => {
    if (!editTarjeta) return
    setEditSaving(true)
    try {
      await tarjetasService.actualizar(editTarjeta.nro_tarjeta, {
        limite_credito: Number(editForm.limite_credito) || 0,
        permite_saldo_negativo: editForm.permite_saldo_negativo,
        estado: editForm.estado,
        fecha_vencimiento: editForm.fecha_vencimiento || null,
      })
      toast.success('Tarjeta actualizada')
      setEditTarjeta(null)
      loadTarjetas(search, estadoFilter, page)
      if (detailTarjeta?.nro_tarjeta === editTarjeta.nro_tarjeta) {
        setDetailTarjeta(prev => prev ? {
          ...prev,
          limite_credito: editForm.limite_credito,
          permite_saldo_negativo: editForm.permite_saldo_negativo,
          estado: editForm.estado,
          fecha_vencimiento: editForm.fecha_vencimiento || null,
        } : prev)
      }
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setEditSaving(false)
    }
  }, [editTarjeta, editForm, search, estadoFilter, page, loadTarjetas, detailTarjeta])

  const openConfirmarCarga = useCallback((cargaId: number) => {
    setConfirmCargaId(cargaId)
    setConfirmFactura({ emitir: false, nro: '' })
  }, [])

  const handleConfirmarCarga = useCallback(async () => {
    if (!confirmCargaId || !detailTarjeta) return
    if (confirmFactura.emitir && !confirmFactura.nro.trim()) { toast.error('Ingresá el número de factura'); return }
    setConfirmando(true)
    try {
      await tarjetasService.confirmarCarga(
        confirmCargaId,
        confirmFactura.emitir ? confirmFactura.nro.trim() : undefined,
      )
      toast.success('Carga confirmada')
      setConfirmCargaId(null)
      const [tarjetaRes, movRes, cargaRes] = await Promise.all([
        tarjetasService.getByNro<Tarjeta>(detailTarjeta.nro_tarjeta),
        tarjetasService.getMovimientos<MovimientoTarjeta>(detailTarjeta.nro_tarjeta, 200),
        tarjetasService.getCargas<CargaSaldo>(detailTarjeta.nro_tarjeta, 200),
      ])
      setDetailTarjeta(tarjetaRes.data)
      setMovimientos(movRes.data.results ?? [])
      setCargas(cargaRes.data.results ?? [])
      loadTarjetas(search, estadoFilter, page)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setConfirmando(false)
    }
  }, [confirmCargaId, confirmFactura, detailTarjeta, search, estadoFilter, page, loadTarjetas])

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
          <p className="font-mono text-base font-semibold text-slate-800">{r.nro_tarjeta}</p>
          <p className="text-sm text-slate-400">{r.codigo_barras || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Titular',
      key: 'titular',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.hijo_nombre ?? '—'}</p>
          <p className="text-sm text-slate-400">
            {r.es_alumno ? (r.hijo_grado ?? '') : 'Docente / Funcionario'}
          </p>
        </div>
      ),
    },
    {
      title: 'Cliente',
      key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-base text-slate-700">{r.cliente_nombre}</p>
          <p className="text-sm text-slate-400">{r.cliente_ruc}</p>
        </div>
      ),
    },
    {
      title: 'Saldo',
      key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_actual) || 0
        return (
          <span className={`tabular-nums font-semibold text-base ${n < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
            {formatGs(n)}
          </span>
        )
      },
    },
    {
      title: 'Límite',
      key: 'limite',
      render: (_, r) => (
        <span className="tabular-nums text-base text-slate-500">{formatGs(r.limite_credito)}</span>
      ),
    },
    {
      title: 'Vencimiento',
      key: 'vto',
      render: (_, r) => (
        <span className="text-base text-slate-600">{formatFechaCorta(r.fecha_vencimiento)}</span>
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
      width: 160,
      render: (_, r) => (
        <div className="flex items-center gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => openDetail(r)}>
            <History className="w-3.5 h-3.5" />
            Ver
          </Button>
          <Button size="sm" variant="secondary" onClick={() => openEdit(r)}>
            <Edit2 className="w-3.5 h-3.5" />
            Editar
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
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha)}</span>,
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
          <span className={`tabular-nums font-semibold text-base flex items-center gap-0.5 ${isEntry ? 'text-emerald-700' : 'text-slate-700'}`}>
            {isEntry ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {formatGs(r.monto)}
          </span>
        )
      },
    },
    {
      title: 'Saldo ant.',
      key: 'saldo_ant',
      render: (_, r) => <span className="tabular-nums text-base text-slate-400">{formatGs(r.saldo_anterior)}</span>,
    },
    {
      title: 'Saldo result.',
      key: 'saldo_res',
      render: (_, r) => (
        <span className={`tabular-nums text-base font-medium ${Number(r.saldo_resultante) < 0 ? 'text-red-600' : 'text-slate-700'}`}>
          {formatGs(r.saldo_resultante)}
        </span>
      ),
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-base text-slate-400">{r.descripcion || '—'}</span>,
    },
  ]

  const colsCargas: Column<CargaSaldo>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-xs text-slate-500">{formatFecha(r.fecha_carga ?? r.fecha)}</span>,
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
        <span className="text-base text-slate-600">{METODO_PAGO_LABEL[r.metodo_pago] ?? r.metodo_pago}</span>
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
      render: (_, r) => <span className="text-base text-slate-400">{r.usuario_nombre ?? '—'}</span>,
    },
    {
      title: '',
      key: 'accion',
      width: 110,
      render: (_, r) => r.estado === 'PENDIENTE' ? (
        <Button size="sm" variant="primary" onClick={() => openConfirmarCarga(r.id)}>
          Confirmar
        </Button>
      ) : null,
    },
  ]

  // ── Styles ──────────────────────────────────────────────────────

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  // ── Render ──────────────────────────────────────────────────────

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('tarjetas.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('tarjetas.subtitle')}</p>
        </div>
        <Button variant="primary" onClick={() => { setForm(FORM_INITIAL); setCreateOpen(true) }}>
          <Plus className="w-4 h-4" />
          {t('tarjetas.newTarjeta')}
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
          <h2 className="text-base font-semibold text-slate-800 flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-slate-400" />
            Tarjetas
          </h2>
          <span className="text-sm text-slate-400">{total} registros</span>
        </div>
        <div className="p-1">
          <Table
            columns={columnsMain}
            dataSource={tarjetas}
            rowKey="nro_tarjeta"
            loading={loading}
            pageSize={15}
            page={page}
            onPageChange={p => { setPage(p); loadTarjetas(search, estadoFilter, p) }}
            total={total}
          />
        </div>
      </div>

      {/* ── Detail Modal ─────────────────────────────────────────── */}
      {detailTarjeta && (
        <Modal
          open
          title={`Tarjeta ${detailTarjeta.nro_tarjeta} — ${detailTarjeta.hijo_nombre ?? '—'}`}
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
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className={`text-base font-bold mt-0.5 tabular-nums ${warn ? 'text-red-600' : 'text-slate-800'}`}>{value}</p>
              </div>
            ))}
          </div>

          {/* Status + actions */}
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <div className="flex items-center gap-2">
              <Badge color={ESTADO_COLOR[detailTarjeta.estado] ?? 'default'}>{detailTarjeta.estado}</Badge>
              {detailTarjeta.permite_saldo_negativo && <Badge color="yellow">Permite saldo negativo</Badge>}
              <span className="text-sm text-slate-400">Cliente: {detailTarjeta.cliente_nombre}</span>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={detailTarjeta.estado === 'ACTIVA' ? 'danger' : 'primary'}
                onClick={() => toggleEstado(detailTarjeta)}
                loading={toggling === detailTarjeta.nro_tarjeta}
                disabled={!!toggling || detailTarjeta.estado === 'VENCIDA' || detailTarjeta.estado === 'CANCELADA'}
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
        onCancel={() => { setCreateOpen(false); setClientesSearch(''); setClientes([]) }}
        okText="Crear Tarjeta"
        confirmLoading={saving}
        width={560}
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

          {/* Tipo de titular */}
          <div>
            <label className={labelClass}>Tipo de titular *</label>
            <div className="flex gap-3">
              {(['alumno', 'funcionario'] as TipoTitular[]).map(tipo => (
                <button
                  key={tipo}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, tipoTitular: tipo, hijo: '', cliente_directo: '' }))}
                  className={[
                    'flex-1 py-2.5 rounded-xl border-2 text-sm font-bold transition-colors cursor-pointer',
                    form.tipoTitular === tipo
                      ? 'bg-green-600 border-green-600 text-white'
                      : 'bg-white border-slate-300 text-slate-600 hover:border-green-400',
                  ].join(' ')}
                >
                  {tipo === 'alumno' ? '🎓 Estudiante' : '👤 Docente / Funcionario'}
                </button>
              ))}
            </div>
          </div>

          {/* Selector condicional según tipo */}
          {form.tipoTitular === 'alumno' ? (
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
          ) : (
            <div>
              <label className={labelClass}>Docente / Funcionario *</label>
              <input
                value={clientesSearch}
                onChange={e => { setClientesSearch(e.target.value); setForm(f => ({ ...f, cliente_directo: '' })) }}
                placeholder="Buscar por nombre o cédula..."
                className={inputClass}
              />
              {loadingClientes && (
                <p className="text-xs text-slate-400 mt-1">Buscando...</p>
              )}
              {clientes.length > 0 && !form.cliente_directo && (
                <ul className="border border-slate-200 rounded-xl mt-1 max-h-40 overflow-y-auto">
                  {clientes.map(c => (
                    <li key={c.id}>
                      <button
                        type="button"
                        onClick={() => { setForm(f => ({ ...f, cliente_directo: c.id })); setClientesSearch(c.nombre_completo) }}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-green-50 cursor-pointer"
                      >
                        <span className="font-semibold text-slate-800">{c.nombre_completo}</span>
                        <span className="text-slate-400 ml-2 text-xs">{c.ruc_ci}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {form.cliente_directo !== '' && (
                <div className="mt-1 flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-1.5">
                  <span className="text-green-700 text-sm font-semibold">{clientesSearch}</span>
                  <button
                    type="button"
                    onClick={() => { setForm(f => ({ ...f, cliente_directo: '' })); setClientesSearch('') }}
                    className="ml-auto text-slate-400 hover:text-red-500 text-xs cursor-pointer"
                  >
                    ✕
                  </button>
                </div>
              )}
            </div>
          )}

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

      {/* ── Edit Modal ────────────────────────────────────────────── */}
      <Modal
        open={!!editTarjeta}
        title={editTarjeta ? `Editar Tarjeta — ${editTarjeta.nro_tarjeta}` : ''}
        onOk={handleEditSave}
        onCancel={() => setEditTarjeta(null)}
        okText="Guardar Cambios"
        confirmLoading={editSaving}
        width={480}
      >
        {editTarjeta && (
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-xl px-4 py-3 text-sm text-slate-500">
              {editTarjeta.es_alumno ? 'Estudiante' : 'Docente / Funcionario'}:{' '}
              <span className="font-semibold text-slate-800">{editTarjeta.hijo_nombre ?? '—'}</span>
              {editTarjeta.es_alumno && (
                <>{' · '} Responsable: <span className="font-semibold text-slate-800">{editTarjeta.cliente_nombre ?? '—'}</span></>
              )}
            </div>

            <div>
              <label className={labelClass}>Límite de Crédito (Gs.)</label>
              <p className="text-xs text-slate-400 mb-1.5">
                Monto máximo que puede gastar con saldo negativo, autorizado con PIN del padre
              </p>
              <input
                type="number"
                value={editForm.limite_credito}
                onChange={e => setEditForm(f => ({ ...f, limite_credito: e.target.value }))}
                placeholder="0"
                min={0}
                step={1000}
                className={inputClass}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Estado</label>
                <select
                  value={editForm.estado}
                  onChange={e => setEditForm(f => ({ ...f, estado: e.target.value }))}
                  className={inputClass}
                >
                  <option value="ACTIVA">Activa</option>
                  <option value="BLOQUEADA">Bloqueada</option>
                  <option value="CANCELADA">Cancelada</option>
                </select>
              </div>
              <div>
                <label className={labelClass}>Fecha de Vencimiento</label>
                <input
                  type="date"
                  value={editForm.fecha_vencimiento}
                  onChange={e => setEditForm(f => ({ ...f, fecha_vencimiento: e.target.value }))}
                  className={inputClass}
                />
              </div>
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <div className="relative shrink-0">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={editForm.permite_saldo_negativo}
                  onChange={e => setEditForm(f => ({ ...f, permite_saldo_negativo: e.target.checked }))}
                />
                <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
                <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
              </div>
              <div>
                <span className="text-sm font-medium text-slate-700">Permite saldo negativo</span>
                <p className="text-xs text-slate-400">Activa la solicitud de PIN del padre cuando se excede el saldo</p>
              </div>
            </label>
          </div>
        )}
      </Modal>

      {/* ── Confirmar carga modal ──────────────────────────────────── */}
      <Modal
        open={confirmCargaId !== null}
        title="Confirmar Carga de Saldo"
        onOk={handleConfirmarCarga}
        onCancel={() => setConfirmCargaId(null)}
        okText="Confirmar"
        confirmLoading={confirmando}
        width={400}
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">¿Confirmás esta carga de saldo?</p>
          <div className="pt-1">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={confirmFactura.emitir}
                onChange={e => setConfirmFactura(f => ({ ...f, emitir: e.target.checked, nro: '' }))}
                className="w-4 h-4 rounded accent-green-600"
              />
              <span className="text-sm font-semibold text-slate-700">Emitir factura ahora</span>
            </label>
            {confirmFactura.emitir && (
              <div className="mt-2">
                <label className={labelClass}>Nro. Factura *</label>
                <input
                  value={confirmFactura.nro}
                  onChange={e => setConfirmFactura(f => ({ ...f, nro: e.target.value }))}
                  placeholder="001-001-0001234"
                  className={inputClass}
                  autoFocus
                />
              </div>
            )}
          </div>
        </div>
      </Modal>

    </div>
  )
}
