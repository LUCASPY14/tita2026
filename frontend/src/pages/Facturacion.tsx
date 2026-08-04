import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { FileText, Search, Printer, XCircle, AlertTriangle, CalendarDays, CheckSquare } from 'lucide-react'
import api from '../services/api'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import {
  formatGs, formatFecha,
  type PendienteItem, type Factura,
  ESTADO_COLOR, TIPO_LABEL, TIPO_COLOR,
} from './facturacion/shared'
import LoteModal from './facturacion/LoteModal'
import ModalEmitir from './facturacion/ModalEmitir'
import ModalAnular from './facturacion/ModalAnular'

export default function Facturacion() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<'pendientes' | 'mensual' | 'emitidas'>('pendientes')

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
  const [confirmAnularId, setConfirmAnularId] = useState<Factura | null>(null)

  // Pendientes tab multi-select
  const [selectedPend, setSelectedPend] = useState<Set<string>>(new Set())
  const [lotePendModal, setLotePendModal] = useState(false)

  // Mensual tab state
  const now = new Date()
  const [mesAnio, setMesAnio] = useState(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [loteModal, setLoteModal] = useState(false)

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
    // Carga de datos al cambiar de tab/filtro: los setLoading*(true) iniciales son intencionales.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (tab === 'pendientes' || tab === 'mensual') loadPendientes()
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
  }, [tab, searchFact, filterEstado, loadFacturas])

  // Split items by modalidad
  const itemsInmediata = useMemo(
    () => pendientes.filter(p => p.modalidad_facturacion !== 'MENSUAL'),
    [pendientes]
  )
  const itemsMensual = useMemo(
    () => pendientes.filter(p => p.modalidad_facturacion === 'MENSUAL'),
    [pendientes]
  )

  // Filter mensual items by selected month
  const itemsMensualMes = useMemo(() => {
    const [year, month] = mesAnio.split('-').map(Number)
    return itemsMensual.filter(item => {
      const d = new Date(item.fecha)
      return d.getFullYear() === year && d.getMonth() + 1 === month
    })
  }, [itemsMensual, mesAnio])

  // Group mensual items by client
  const gruposMensual = useMemo(() => {
    const map = new Map<number | null, { clienteId: number | null; clienteNombre: string; items: PendienteItem[] }>()
    for (const item of itemsMensualMes) {
      const key = item.cliente_id
      if (!map.has(key)) {
        map.set(key, { clienteId: key, clienteNombre: item.cliente_nombre, items: [] })
      }
      map.get(key)!.items.push(item)
    }
    return Array.from(map.values()).sort((a, b) => a.clienteNombre.localeCompare(b.clienteNombre))
  }, [itemsMensualMes])

  // Selected items for batch
  const selectedItems = useMemo(
    () => itemsMensualMes.filter(i => selected.has(`${i.tipo}-${i.id}`)),
    [itemsMensualMes, selected]
  )

  // All selected items must belong to a single client and same type
  const canEmitirLote = useMemo(() => {
    if (selectedItems.length === 0) return false
    const clientes = new Set(selectedItems.map(i => i.cliente_id))
    const tipos = new Set(selectedItems.map(i => i.tipo))
    return clientes.size === 1 && tipos.size === 1
  }, [selectedItems])

  const loteTotal = useMemo(
    () => selectedItems.reduce((s, i) => s + i.monto, 0),
    [selectedItems]
  )

  const toggleItem = (key: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const toggleClienteAll = (items: PendienteItem[], allChecked: boolean) => {
    setSelected(prev => {
      const next = new Set(prev)
      for (const item of items) {
        const key = `${item.tipo}-${item.id}`
        if (allChecked) next.delete(key)
        else next.add(key)
      }
      return next
    })
  }

  // Pendientes multi-select helpers
  const selectedPendItems = useMemo(
    () => itemsInmediata.filter(i => selectedPend.has(`${i.tipo}-${i.id}`)),
    [itemsInmediata, selectedPend]
  )
  const canEmitirLotePend = useMemo(() => {
    if (selectedPendItems.length < 2) return false
    const clientes = new Set(selectedPendItems.map(i => i.cliente_id))
    const tipos = new Set(selectedPendItems.map(i => i.tipo))
    return clientes.size === 1 && tipos.size === 1
  }, [selectedPendItems])
  const lotePendTotal = useMemo(
    () => selectedPendItems.reduce((s, i) => s + i.monto, 0),
    [selectedPendItems]
  )
  const togglePendItem = (key: string) => {
    setSelectedPend(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  // ── Columns ──────────────────────────────────────────────────────

  const colsPendientes: Column<PendienteItem>[] = [
    {
      title: '', key: 'check', width: 36,
      render: (_, r) => {
        const key = `${r.tipo}-${r.id}`
        return (
          <input
            type="checkbox"
            checked={selectedPend.has(key)}
            onChange={() => togglePendItem(key)}
            className="w-4 h-4 rounded accent-green-600 cursor-pointer"
          />
        )
      },
    },
    {
      title: 'Tipo', key: 'tipo',
      render: (_, r) => <Badge color={TIPO_COLOR[r.tipo] ?? 'default'}>{TIPO_LABEL[r.tipo] ?? r.tipo}</Badge>,
    },
    {
      title: 'Cliente', key: 'cliente',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.cliente_nombre}</span>,
    },
    {
      title: 'Descripción', key: 'desc',
      render: (_, r) => <span className="text-sm text-slate-600">{r.descripcion}</span>,
    },
    {
      title: 'Monto', key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto)}</span>,
    },
    {
      title: 'Fecha', key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: '', key: 'accion', width: 90,
      render: (_, r) => (
        <Button size="sm" variant="primary" onClick={() => setEmitirModal(r)}>
          Emitir
        </Button>
      ),
    },
  ]

  const colsFacturas: Column<Factura>[] = [
    {
      title: 'Nro. Factura', key: 'nro',
      render: (_, r) => <span className="font-mono text-sm font-semibold text-slate-800">{r.nro_factura}</span>,
    },
    {
      title: 'Cliente', key: 'cliente',
      render: (_, r) => <span className="text-sm text-slate-700">{r.cliente_nombre}</span>,
    },
    {
      title: 'Monto', key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'IVA 10%', key: 'iva',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-500">{formatGs(r.iva_10)}</span>,
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: 'Fecha', key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha_emision)}</span>,
    },
    {
      title: '', key: 'acciones', width: 130,
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
            <Button size="sm" variant="danger" onClick={() => setConfirmAnularId(r)}>
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

  const tabBtn = (active: boolean) => [
    'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer',
    active ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700',
  ].join(' ')

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t('facturacion.title')}</h1>
        <p className="text-base text-slate-500 mt-0.5">{t('facturacion.subtitle')}</p>
      </div>

      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          <button onClick={() => setTab('pendientes')} className={tabBtn(tab === 'pendientes')}>
            Pendientes
            {itemsInmediata.length > 0 && (
              <span className="bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">
                {itemsInmediata.length}
              </span>
            )}
          </button>
          <button onClick={() => { setTab('mensual'); setSelected(new Set()) }} className={tabBtn(tab === 'mensual')}>
            <CalendarDays className="w-4 h-4" />
            Factura Mensual
            {itemsMensual.length > 0 && (
              <span className="bg-blue-100 text-blue-700 text-xs px-1.5 py-0.5 rounded-full font-semibold">
                {itemsMensual.length}
              </span>
            )}
          </button>
          <button onClick={() => setTab('emitidas')} className={tabBtn(tab === 'emitidas')}>
            <FileText className="w-4 h-4" />
            Facturas emitidas
          </button>
        </div>
      </div>

      {/* ── Pendientes tab ───────────────────────────────────────── */}
      {tab === 'pendientes' && (
        <>
          {selectedPend.size > 0 && (
            <div className="bg-slate-800 text-white rounded-2xl px-5 py-3 flex items-center justify-between gap-4 shadow-lg">
              <div className="flex items-center gap-3 text-sm">
                <CheckSquare className="w-4 h-4 text-green-400 shrink-0" />
                <span className="font-semibold">{selectedPend.size} ítem{selectedPend.size !== 1 ? 's' : ''} seleccionado{selectedPend.size !== 1 ? 's' : ''}</span>
                {selectedPend.size >= 2 && (
                  <span className="text-slate-300">— Total: <span className="font-bold text-white tabular-nums">{formatGs(lotePendTotal)}</span></span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {!canEmitirLotePend && selectedPend.size >= 2 && (
                  <span className="text-xs text-amber-300 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Mismo cliente y tipo
                  </span>
                )}
                <button
                  onClick={() => setSelectedPend(new Set())}
                  className="text-slate-400 hover:text-white text-xs px-3 py-1.5 rounded-lg hover:bg-slate-700 transition-colors cursor-pointer"
                >
                  Limpiar
                </button>
                <Button
                  size="sm"
                  variant="primary"
                  disabled={!canEmitirLotePend}
                  onClick={() => setLotePendModal(true)}
                >
                  Emitir lote ({selectedPend.size})
                </Button>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800">Ítems pendientes de facturar</h2>
              <span className="text-sm text-slate-400">{itemsInmediata.length} registros</span>
            </div>
            <div className="p-1">
              <Table columns={colsPendientes} dataSource={itemsInmediata} rowKey={r => `${r.tipo}-${r.id}`} loading={loadingPend} pageSize={20} />
            </div>
          </div>

          <LoteModal
            open={lotePendModal}
            items={selectedPendItems}
            onClose={() => setLotePendModal(false)}
            onSuccess={() => { setSelectedPend(new Set()); loadPendientes() }}
          />
        </>
      )}

      {/* ── Mensual tab ──────────────────────────────────────────── */}
      {tab === 'mensual' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div>
              <label className={labelClass}>Mes</label>
              <input
                type="month"
                value={mesAnio}
                onChange={e => { setMesAnio(e.target.value); setSelected(new Set()) }}
                className={`${inputClass} w-auto`}
              />
            </div>
            {selectedItems.length > 0 && (
              <div className="flex items-center gap-3 ml-auto">
                <span className="text-sm text-slate-600">
                  <strong>{selectedItems.length}</strong> ítems seleccionados —{' '}
                  <strong className="text-emerald-700">{formatGs(loteTotal)}</strong>
                </span>
                {canEmitirLote ? (
                  <Button variant="primary" onClick={() => setLoteModal(true)}>
                    <CheckSquare className="w-4 h-4" />
                    Facturar seleccionados
                  </Button>
                ) : (
                  <span className="text-xs text-red-500 font-medium">
                    Solo podés facturar ítems del mismo cliente y tipo
                  </span>
                )}
              </div>
            )}
          </div>

          {loadingPend ? (
            <div className="text-center py-12 text-slate-400">Cargando...</div>
          ) : gruposMensual.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-6 py-12 text-center text-slate-400">
              No hay ítems pendientes de facturación mensual para este mes
            </div>
          ) : (
            <div className="space-y-4">
              {gruposMensual.map(grupo => {
                const itemKeys = grupo.items.map(i => `${i.tipo}-${i.id}`)
                const allChecked = itemKeys.every(k => selected.has(k))
                const someChecked = itemKeys.some(k => selected.has(k))
                const grupoTotal = grupo.items.reduce((s, i) => s + i.monto, 0)

                return (
                  <div key={grupo.clienteId ?? grupo.clienteNombre} className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 border-b border-slate-100 flex items-center gap-3 bg-slate-50">
                      <input
                        type="checkbox"
                        checked={allChecked}
                        ref={el => { if (el) el.indeterminate = someChecked && !allChecked }}
                        onChange={() => toggleClienteAll(grupo.items, allChecked)}
                        className="w-4 h-4 rounded accent-blue-600"
                      />
                      <div className="flex-1">
                        <span className="text-sm font-semibold text-slate-800">{grupo.clienteNombre}</span>
                        <span className="ml-2 text-xs text-slate-400">{grupo.items.length} ítem{grupo.items.length !== 1 ? 's' : ''}</span>
                      </div>
                      <span className="text-sm font-bold tabular-nums text-emerald-700">{formatGs(grupoTotal)}</span>
                    </div>

                    <div className="divide-y divide-slate-50">
                      {grupo.items.map(item => {
                        const key = `${item.tipo}-${item.id}`
                        const checked = selected.has(key)
                        return (
                          <div
                            key={key}
                            onClick={() => toggleItem(key)}
                            className={`flex items-center gap-3 px-5 py-3 cursor-pointer transition-colors ${checked ? 'bg-blue-50' : 'hover:bg-slate-50'}`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => toggleItem(key)}
                              onClick={e => e.stopPropagation()}
                              className="w-4 h-4 rounded accent-blue-600 shrink-0"
                            />
                            <Badge color={TIPO_COLOR[item.tipo] ?? 'default'}>
                              {TIPO_LABEL[item.tipo] ?? item.tipo}
                            </Badge>
                            <span className="text-sm text-slate-700 flex-1 truncate">{item.descripcion}</span>
                            <span className="text-sm text-slate-400 shrink-0">{formatFecha(item.fecha)}</span>
                            <span className="text-sm font-semibold tabular-nums text-slate-800 shrink-0 ml-2">{formatGs(item.monto)}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
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

      {/* ── Emitir lote modal (mensual) ───────────────────────────── */}
      <LoteModal
        open={loteModal}
        items={selectedItems}
        onClose={() => setLoteModal(false)}
        onSuccess={() => { setSelected(new Set()); loadPendientes() }}
      />

      <ModalEmitir
        item={emitirModal}
        onClose={() => setEmitirModal(null)}
        onSaved={() => { setEmitirModal(null); loadPendientes() }}
      />

      <ModalAnular
        factura={confirmAnularId}
        onClose={() => setConfirmAnularId(null)}
        onSaved={() => loadFacturas(searchFact, filterEstado, pageFact)}
      />
    </div>
  )
}
