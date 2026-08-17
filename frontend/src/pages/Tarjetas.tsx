import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { CreditCard, Search, Plus, Lock, Unlock, History, Edit2 } from 'lucide-react'
import tarjetasService from '../services/tarjetas'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import { extractErrorMessage, formatGs, formatFechaCorta, type Tarjeta, ESTADO_COLOR } from './tarjetas/shared'
import ModalDetalle from './tarjetas/ModalDetalle'
import ModalCrear from './tarjetas/ModalCrear'
import ModalEditar from './tarjetas/ModalEditar'

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
  const [toggling, setToggling] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editTarjeta, setEditTarjeta] = useState<Tarjeta | null>(null)

  // ── Data loading ─────────────────────────────────────────────────

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

  // ── Actions ──────────────────────────────────────────────────────

  const toggleEstado = useCallback(async (t: Tarjeta) => {
    const nuevoEstado = t.estado === 'ACTIVA' ? 'BLOQUEADA' : 'ACTIVA'
    setToggling(t.nro_tarjeta)
    try {
      await (t.estado === 'ACTIVA' ? tarjetasService.bloquear(t.nro_tarjeta) : tarjetasService.activar(t.nro_tarjeta))
      toast.success(nuevoEstado === 'BLOQUEADA' ? 'Tarjeta bloqueada' : 'Tarjeta activada')
      setDetailTarjeta(prev => prev?.nro_tarjeta === t.nro_tarjeta ? { ...prev, estado: nuevoEstado } : prev)
      loadTarjetas(search, estadoFilter, page)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setToggling(null)
    }
  }, [search, estadoFilter, page, loadTarjetas])

  // ── Styles / columns ─────────────────────────────────────────────

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const columnsMain: Column<Tarjeta>[] = [
    {
      title: 'Nro. Tarjeta', key: 'nro',
      render: (_, r) => (
        <div>
          <p className="font-mono text-base font-semibold text-slate-800">{r.nro_tarjeta}</p>
          <p className="text-sm text-slate-400">{r.codigo_barras || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Titular', key: 'titular',
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
      title: 'Cliente', key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-base text-slate-700">{r.cliente_nombre}</p>
          <p className="text-sm text-slate-400">{r.cliente_ruc}</p>
        </div>
      ),
    },
    {
      title: 'Saldo', key: 'saldo',
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
      title: 'Límite', key: 'limite',
      render: (_, r) => (
        <span className="tabular-nums text-base text-slate-500">{formatGs(r.limite_credito)}</span>
      ),
    },
    {
      title: 'Vencimiento', key: 'vto',
      render: (_, r) => (
        <span className="text-base text-slate-600">{formatFechaCorta(r.fecha_vencimiento)}</span>
      ),
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: '', key: 'acciones', width: 160,
      render: (_, r) => (
        <div className="flex items-center gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => setDetailTarjeta(r)}>
            <History className="w-3.5 h-3.5" />
            Ver
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setEditTarjeta(r)}>
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

  // ── Render ───────────────────────────────────────────────────────

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('tarjetas.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('tarjetas.subtitle')}</p>
        </div>
        <Button variant="primary" onClick={() => setCreateOpen(true)}>
          <Plus className="w-4 h-4" />
          {t('tarjetas.newTarjeta')}
        </Button>
      </div>

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

      <ModalDetalle
        tarjeta={detailTarjeta}
        toggling={toggling}
        onToggleEstado={toggleEstado}
        onClose={() => setDetailTarjeta(null)}
        onTarjetaUpdated={t => setDetailTarjeta(t)}
        onListReload={() => loadTarjetas(search, estadoFilter, page)}
      />

      <ModalCrear
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onSaved={() => { setPage(1); loadTarjetas(search, estadoFilter, 1) }}
      />

      <ModalEditar
        tarjeta={editTarjeta}
        onClose={() => setEditTarjeta(null)}
        onSaved={updates => {
          loadTarjetas(search, estadoFilter, page)
          setDetailTarjeta(prev =>
            prev?.nro_tarjeta === editTarjeta?.nro_tarjeta ? { ...prev!, ...updates } : prev,
          )
        }}
      />
    </div>
  )
}
