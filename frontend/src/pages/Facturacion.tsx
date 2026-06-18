import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { FileText, Search, Printer, XCircle, AlertTriangle } from 'lucide-react'
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

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface PendienteItem {
  tipo: string
  id: number
  cliente_nombre: string
  descripcion: string
  monto: number
  fecha: string
}

interface Factura {
  id: number
  nro_factura: string
  cliente: number | null
  cliente_nombre: string
  monto_total: string | number
  iva_10: string | number
  estado: string
  fecha_emision: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ESTADO_COLOR: Record<string, BadgeColor> = {
  EMITIDA: 'green',
  ANULADA: 'red',
}

const TIPO_LABEL: Record<string, string> = {
  CARGA_SALDO: 'Carga de saldo',
  ALMUERZO: 'Almuerzo',
  VENTA: 'Venta',
}

const TIPO_COLOR: Record<string, BadgeColor> = {
  CARGA_SALDO: 'blue',
  ALMUERZO: 'orange',
  VENTA: 'green',
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Facturacion() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<'pendientes' | 'emitidas'>('pendientes')

  const [pendientes, setPendientes] = useState<PendienteItem[]>([])
  const [loadingPend, setLoadingPend] = useState(false)

  const [facturas, setFacturas] = useState<Factura[]>([])
  const [loadingFact, setLoadingFact] = useState(false)
  const [searchFact, setSearchFact] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [pageFact, setPageFact] = useState(1)
  const [totalFact, setTotalFact] = useState(0)
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdRef = useRef(0)

  const [emitirModal, setEmitirModal] = useState<PendienteItem | null>(null)
  const [nroFactura, setNroFactura] = useState('')
  const [emitiendo, setEmitiendo] = useState(false)

  const [anulando, setAnulando] = useState<number | null>(null)
  const [confirmAnularId, setConfirmAnularId] = useState<Factura | null>(null)

  // ── Load pendientes ──────────────────────────────────────────────
  const loadPendientes = useCallback(async () => {
    setLoadingPend(true)
    try {
      const { data } = await api.get('/contabilidad/facturas/pendiente-facturar/')
      setPendientes(data ?? [])
    } catch {
      toast.error('Error al cargar pendientes')
    } finally {
      setLoadingPend(false)
    }
  }, [])

  // ── Load facturas ────────────────────────────────────────────────
  const loadFacturas = useCallback(async (search: string, estado: string, p: number) => {
    const requestId = ++requestIdRef.current
    setLoadingFact(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering: '-fecha_emision' }
      if (search) params.search = search
      if (estado) params.estado = estado
      const { data } = await api.get('/contabilidad/facturas/', { params })
      if (requestId !== requestIdRef.current) return
      setFacturas(data.results ?? [])
      setTotalFact(data.count ?? 0)
    } catch {
      if (requestId !== requestIdRef.current) return
      toast.error('Error al cargar facturas')
    } finally {
      if (requestId === requestIdRef.current) setLoadingFact(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (tab === 'pendientes') loadPendientes()
    else {
      setPageFact(1)
      loadFacturas(searchFact, filterEstado, 1)
    }
  }, [tab, loadPendientes, loadFacturas, searchFact, filterEstado])

  useEffect(() => {
    if (tab !== 'emitidas') return
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      setPageFact(1)
      loadFacturas(searchFact, filterEstado, 1)
    }, 350)
    return () => clearTimeout(searchTimer.current)
  }, [searchFact, filterEstado])

  // ── Emitir ───────────────────────────────────────────────────────
  const emitirFactura = useCallback(async () => {
    if (!emitirModal) return
    if (!nroFactura.trim()) { toast.error('Ingresá el número de factura'); return }
    setEmitiendo(true)
    try {
      await api.post('/contabilidad/facturas/emitir/', {
        tipo: emitirModal.tipo,
        origen_id: emitirModal.id,
        nro_factura: nroFactura.trim(),
      })
      toast.success(`Factura ${nroFactura} emitida`)
      setEmitirModal(null)
      setNroFactura('')
      loadPendientes()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setEmitiendo(false)
    }
  }, [emitirModal, nroFactura, loadPendientes])

  // ── Anular ───────────────────────────────────────────────────────
  const anularFactura = useCallback(async () => {
    if (!confirmAnularId) return
    setAnulando(confirmAnularId.id)
    try {
      await api.post(`/contabilidad/facturas/${confirmAnularId.id}/anular/`)
      toast.success('Factura anulada')
      setConfirmAnularId(null)
      loadFacturas(searchFact, filterEstado, pageFact)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAnulando(null)
    }
  }, [confirmAnularId, searchFact, filterEstado, pageFact, loadFacturas])

  // ── Columns ──────────────────────────────────────────────────────

  const colsPendientes: Column<PendienteItem>[] = [
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <Badge color={TIPO_COLOR[r.tipo] ?? 'default'}>{TIPO_LABEL[r.tipo] ?? r.tipo}</Badge>,
    },
    {
      title: 'Cliente',
      key: 'cliente',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.cliente_nombre}</span>,
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-sm text-slate-600">{r.descripcion}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto)}</span>,
    },
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: '',
      key: 'accion',
      width: 90,
      render: (_, r) => (
        <Button size="sm" variant="primary" onClick={() => { setEmitirModal(r); setNroFactura('') }}>
          Emitir
        </Button>
      ),
    },
  ]

  const colsFacturas: Column<Factura>[] = [
    {
      title: 'Nro. Factura',
      key: 'nro',
      render: (_, r) => <span className="font-mono text-sm font-semibold text-slate-800">{r.nro_factura}</span>,
    },
    {
      title: 'Cliente',
      key: 'cliente',
      render: (_, r) => <span className="text-sm text-slate-700">{r.cliente_nombre}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'IVA 10%',
      key: 'iva',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-500">{formatGs(r.iva_10)}</span>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha_emision)}</span>,
    },
    {
      title: '',
      key: 'acciones',
      width: 130,
      render: (_, r) => (
        <div className="flex gap-1.5">
          <Button
            size="sm"
            variant="secondary"
            onClick={async () => {
              try {
                const res = await api.get(`/contabilidad/facturas/${r.id}/pdf/`, { responseType: 'blob' })
                const url = URL.createObjectURL(new Blob([res.data], { type: 'text/html' }))
                const w = window.open(url, '_blank')
                if (w) w.onload = () => URL.revokeObjectURL(url)
              } catch {
                toast.error('Error al abrir el PDF')
              }
            }}
          >
            <Printer className="w-3.5 h-3.5" />
            PDF
          </Button>
          {r.estado === 'EMITIDA' && (
            <Button size="sm" variant="danger" loading={anulando === r.id} onClick={() => setConfirmAnularId(r)}>
              <XCircle className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      ),
    },
  ]

  // ── Styles ────────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t('facturacion.title')}</h1>
        <p className="text-base text-slate-500 mt-0.5">{t('facturacion.subtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          <button
            onClick={() => setTab('pendientes')}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              tab === 'pendientes' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Pendientes de facturar
            {pendientes.length > 0 && (
              <span className="bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">
                {pendientes.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setTab('emitidas')}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              tab === 'emitidas' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <FileText className="w-4 h-4" />
            Facturas emitidas
          </button>
        </div>
      </div>

      {/* ── Pendientes tab ───────────────────────────────────────── */}
      {tab === 'pendientes' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800">Ítems pendientes de facturar</h2>
            <span className="text-sm text-slate-400">{pendientes.length} registros</span>
          </div>
          <div className="p-1">
            <Table columns={colsPendientes} dataSource={pendientes} rowKey={r => `${r.tipo}-${r.id}`} loading={loadingPend} pageSize={20} />
          </div>
        </div>
      )}

      {/* ── Emitidas tab ─────────────────────────────────────────── */}
      {tab === 'emitidas' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px]">
              <label className={labelClass}>Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  placeholder="Nro. factura, cliente..."
                  value={searchFact}
                  onChange={e => setSearchFact(e.target.value)}
                  className={`${inputClass} pl-9`}
                />
              </div>
            </div>
            <div>
              <label className={labelClass}>Estado</label>
              <select
                value={filterEstado}
                onChange={e => { setFilterEstado(e.target.value); setPageFact(1) }}
                className={`${inputClass} w-auto`}
              >
                <option value="">Todos</option>
                <option value="EMITIDA">Emitida</option>
                <option value="ANULADA">Anulada</option>
              </select>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={colsFacturas}
                dataSource={facturas}
                rowKey="id"
                loading={loadingFact}
                pageSize={15}
                page={pageFact}
                onPageChange={p => { setPageFact(p); loadFacturas(searchFact, filterEstado, p) }}
                total={totalFact}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Emitir modal ─────────────────────────────────────────── */}
      <Modal
        open={!!emitirModal}
        title="Emitir Factura"
        onOk={emitirFactura}
        onCancel={() => setEmitirModal(null)}
        confirmLoading={emitiendo}
        okText="Emitir"
        width={460}
      >
        {emitirModal && (
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Cliente</span>
                <span className="text-slate-800 font-semibold">{emitirModal.cliente_nombre}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Concepto</span>
                <span className="text-slate-700">{emitirModal.descripcion}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Monto</span>
                <span className="text-emerald-700 font-bold tabular-nums">{formatGs(emitirModal.monto)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Tipo</span>
                <Badge color={TIPO_COLOR[emitirModal.tipo] ?? 'default'}>{TIPO_LABEL[emitirModal.tipo] ?? emitirModal.tipo}</Badge>
              </div>
            </div>

            <div>
              <label className={labelClass}>Número de Factura *</label>
              <input
                value={nroFactura}
                onChange={e => setNroFactura(e.target.value)}
                placeholder="001-001-0000001"
                className={inputClass}
                autoFocus
              />
              <p className="text-sm text-slate-400 mt-1">Formato: 001-001-0000001</p>
            </div>
          </div>
        )}
      </Modal>

      {/* ── Confirm anular modal ──────────────────────────────────── */}
      <Modal
        open={!!confirmAnularId}
        title="Anular Factura"
        onOk={anularFactura}
        onCancel={() => setConfirmAnularId(null)}
        confirmLoading={!!anulando}
        okText="Anular"
        width={400}
      >
        {confirmAnularId && (
          <div className="flex items-start gap-3 py-2">
            <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-800">
                ¿Anular factura {confirmAnularId.nro_factura}?
              </p>
              <p className="text-sm text-slate-500 mt-1">
                Esta acción no se puede deshacer. La factura quedará marcada como ANULADA.
              </p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
