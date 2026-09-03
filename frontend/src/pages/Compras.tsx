import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  AlertTriangle, ArrowRightCircle, Building2, CheckCircle, ClipboardList,
  CreditCard, DollarSign, Eye, FileText, PackageCheck,
  Plus, Search, Send, Truck, Undo2, XCircle,
} from 'lucide-react'
import api from '../services/api'
import { useCatalogoStore } from '../store/catalogoStore'
import { useAuthStore } from '../store/authStore'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'
import ModalProveedor from './compras/ModalProveedor'
import ModalCuentaCorriente from './compras/ModalCuentaCorriente'
import ModalCompra from './compras/ModalCompra'
import ModalCompraDetail from './compras/ModalCompraDetail'
import ModalPago from './compras/ModalPago'
import ModalOC from './compras/ModalOC'
import ModalOCDetail from './compras/ModalOCDetail'
import ModalRechazarOC from './compras/ModalRechazarOC'
import ModalNC from './compras/ModalNC'
import ModalNCDetail from './compras/ModalNCDetail'
import {
  extractErrorMessage, formatGs, formatFecha,
  ESTADO_PAGO_COLOR, TIPO_PAGO_COLOR, ESTADO_ENTREGA_COLOR, NC_ESTADO_COLOR, OC_ESTADO_COLOR, OC_ESTADO_LABEL,
  type Compra, type NotaCredito, type OrdenCompra, type PagoProveedor, type Producto, type Proveedor,
} from './compras/shared'

type TabKey = 'compras' | 'proveedores' | 'pagos' | 'ordenes' | 'notas'

const PAGE_SIZE = 15

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: 'ordenes',     label: 'Órdenes',     icon: ClipboardList },
  { key: 'compras',     label: 'Compras',     icon: Truck },
  { key: 'proveedores', label: 'Proveedores', icon: Building2 },
  { key: 'pagos',       label: 'Pagos',       icon: CreditCard },
  { key: 'notas',       label: 'Notas C/C',   icon: FileText },
]

export default function Compras() {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const canApprove = user?.rol === 'ADMIN' || user?.rol === 'SUPERVISOR'
  const [tab, setTab] = useState<TabKey>('compras')
  const getProductos = useCatalogoStore(state => state.getProductos)
  const getMediosPago = useCatalogoStore(state => state.getMediosPago)

  // ── Catalog data ────────────────────────────────────────────────
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [productos, setProductos] = useState<Producto[]>([])
  const [mediosPago, setMediosPago] = useState<{ id: number; descripcion: string }[]>([])

  // ── Compras list ────────────────────────────────────────────────
  const [compras, setCompras] = useState<Compra[]>([])
  const [loadingCompras, setLoadingCompras] = useState(false)
  const [searchCompras, setSearchCompras] = useState('')
  const [filterEstado, setFilterEstado] = useState('')
  const [filterTipo, setFilterTipo] = useState('')
  const [filterProveedor, setFilterProveedor] = useState('')
  const [filterEntrega, setFilterEntrega] = useState('')
  const [pageCompras, setPageCompras] = useState(1)
  const [totalCompras, setTotalCompras] = useState(0)
  const searchTimerCompras = useRef<ReturnType<typeof setTimeout>>(undefined)
  const reqComprasRef = useRef(0)

  // ── Proveedores list ────────────────────────────────────────────
  const [pageProveedores, setPageProveedores] = useState(1)
  const [totalProveedores, setTotalProveedores] = useState(0)
  const [loadingProv, setLoadingProv] = useState(false)
  const [searchProv, setSearchProv] = useState('')
  const searchTimerProv = useRef<ReturnType<typeof setTimeout>>(undefined)
  const reqProvRef = useRef(0)

  // ── Pagos list ──────────────────────────────────────────────────
  const [pagos, setPagos] = useState<PagoProveedor[]>([])
  const [loadingPagos, setLoadingPagos] = useState(false)
  const [pagePagos, setPagePagos] = useState(1)
  const [totalPagos, setTotalPagos] = useState(0)
  const reqPagosRef = useRef(0)

  // ── Notas list ──────────────────────────────────────────────────
  const [notas, setNotas] = useState<NotaCredito[]>([])
  const [loadingNotas, setLoadingNotas] = useState(false)
  const [pageNotas, setPageNotas] = useState(1)
  const [totalNotas, setTotalNotas] = useState(0)
  const reqNotasRef = useRef(0)

  // ── Ordenes list ────────────────────────────────────────────────
  const [ordenes, setOrdenes] = useState<OrdenCompra[]>([])
  const [loadingOrdenes, setLoadingOrdenes] = useState(false)
  const [pageOrdenes, setPageOrdenes] = useState(1)
  const [totalOrdenes, setTotalOrdenes] = useState(0)
  const [filterEstadoOC, setFilterEstadoOC] = useState('')
  const reqOCRef = useRef(0)
  const [accionOCLoading, setAccionOCLoading] = useState<number | null>(null)
  const [confirmandoEntrega, setConfirmandoEntrega] = useState<number | null>(null)
  const [confirmAnularCompra, setConfirmAnularCompra] = useState<Compra | null>(null)
  const [anulandoCompra, setAnulandoCompra] = useState(false)

  // ── Modal state ─────────────────────────────────────────────────
  const [provModal, setProvModal] = useState<{ open: boolean; prov: Proveedor | null }>({ open: false, prov: null })
  const [ccProveedor, setCcProveedor] = useState<Proveedor | null>(null)
  const [compraModal, setCompraModal] = useState<{ open: boolean; compra: Compra | null }>({ open: false, compra: null })
  const [detailCompra, setDetailCompra] = useState<Compra | null>(null)
  const [pagoModal, setPagoModal] = useState<{ open: boolean; compra: Compra | null }>({ open: false, compra: null })
  const [ocModal, setOcModal] = useState<{ open: boolean; oc: OrdenCompra | null }>({ open: false, oc: null })
  const [detailOC, setDetailOC] = useState<OrdenCompra | null>(null)
  const [rechazarOC, setRechazarOC] = useState<OrdenCompra | null>(null)
  const [ncModalOpen, setNcModalOpen] = useState(false)
  const [detailNC, setDetailNC] = useState<NotaCredito | null>(null)

  // ── Load catalogs ────────────────────────────────────────────────
  useEffect(() => {
    api.get('/compras/proveedores/', { params: { activo: true, page_size: 500 } })
      .then(res => setProveedores(res.data.results ?? []))
      .catch(() => toast.error('Error al cargar proveedores'))
    getProductos().then(prods => setProductos(prods as Producto[])).catch(() => toast.error('Error al cargar productos'))
    getMediosPago().then(mp => setMediosPago(mp as { id: number; descripcion: string }[])).catch(() => toast.error('Error al cargar medios de pago'))
  }, [getProductos, getMediosPago])

  // ── Load functions ───────────────────────────────────────────────
  const loadCompras = useCallback(async (search: string, estado: string, tipo: string, prov: string, entrega: string, p: number) => {
    const id = ++reqComprasRef.current
    setLoadingCompras(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: PAGE_SIZE }
      if (search) params.search = search
      if (estado) params.estado_pago = estado
      if (tipo) params.tipo_pago = tipo
      if (prov) params.proveedor = prov
      if (entrega) params.estado_entrega = entrega
      const { data } = await api.get('/compras/compras/', { params })
      if (id !== reqComprasRef.current) return
      setCompras(data.results ?? [])
      setTotalCompras(data.count ?? 0)
    } catch {
      if (id !== reqComprasRef.current) return
      toast.error('Error al cargar compras')
    } finally {
      if (id === reqComprasRef.current) setLoadingCompras(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(searchTimerCompras.current)
    searchTimerCompras.current = setTimeout(() => {
      setPageCompras(1)
      loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, 1)
    }, 350)
    return () => clearTimeout(searchTimerCompras.current)
  }, [searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, loadCompras])

  const loadProveedores = useCallback(async (search: string, p: number) => {
    const id = ++reqProvRef.current
    setLoadingProv(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: PAGE_SIZE }
      if (search) params.search = search
      const { data } = await api.get('/compras/proveedores/', { params })
      if (id !== reqProvRef.current) return
      setProveedores(data.results ?? [])
      setTotalProveedores(data.count ?? 0)
    } catch {
      if (id !== reqProvRef.current) return
      toast.error('Error al cargar proveedores')
    } finally {
      if (id === reqProvRef.current) setLoadingProv(false)
    }
  }, [])

  useEffect(() => {
    if (tab !== 'proveedores') return
    clearTimeout(searchTimerProv.current)
    searchTimerProv.current = setTimeout(() => { setPageProveedores(1); loadProveedores(searchProv, 1) }, 350)
    return () => clearTimeout(searchTimerProv.current)
  }, [searchProv, tab, loadProveedores])

  const loadPagos = useCallback(async (p: number) => {
    const id = ++reqPagosRef.current
    setLoadingPagos(true)
    try {
      const { data } = await api.get('/compras/pagos/', { params: { page: p, page_size: PAGE_SIZE } })
      if (id !== reqPagosRef.current) return
      setPagos(data.results ?? [])
      setTotalPagos(data.count ?? 0)
    } catch {
      if (id !== reqPagosRef.current) return
      toast.error('Error al cargar pagos')
    } finally {
      if (id === reqPagosRef.current) setLoadingPagos(false)
    }
  }, [])

  // Carga de datos al cambiar de tab/página: el setLoadingPagos(true) inicial es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (tab === 'pagos') loadPagos(pagePagos) }, [tab, pagePagos, loadPagos])

  const loadNotas = useCallback(async (p: number) => {
    const id = ++reqNotasRef.current
    setLoadingNotas(true)
    try {
      const { data } = await api.get('/compras/notas-credito/', { params: { page: p, page_size: PAGE_SIZE } })
      if (id !== reqNotasRef.current) return
      setNotas(data.results ?? [])
      setTotalNotas(data.count ?? 0)
    } catch {
      if (id !== reqNotasRef.current) return
      toast.error('Error al cargar notas de crédito')
    } finally {
      if (id === reqNotasRef.current) setLoadingNotas(false)
    }
  }, [])

  // Carga de datos al cambiar de tab/página: el setLoadingNotas(true) inicial es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (tab === 'notas') loadNotas(pageNotas) }, [tab, pageNotas, loadNotas])

  const loadOrdenes = useCallback(async (estado: string, p: number) => {
    const id = ++reqOCRef.current
    setLoadingOrdenes(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: PAGE_SIZE }
      if (estado) params.estado = estado
      const { data } = await api.get('/compras/ordenes/', { params })
      if (id !== reqOCRef.current) return
      setOrdenes(data.results ?? [])
      setTotalOrdenes(data.count ?? 0)
    } catch {
      if (id !== reqOCRef.current) return
      toast.error('Error al cargar órdenes de compra')
    } finally {
      if (id === reqOCRef.current) setLoadingOrdenes(false)
    }
  }, [])

  // Carga de datos al cambiar de tab/filtro/página: el setLoadingOrdenes(true) inicial es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { if (tab === 'ordenes') loadOrdenes(filterEstadoOC, pageOrdenes) }, [tab, filterEstadoOC, pageOrdenes, loadOrdenes])

  // ── Actions ──────────────────────────────────────────────────────
  const handleOCAccion = useCallback(async (oc: OrdenCompra, accion: 'submit' | 'aprobar' | 'convertir') => {
    setAccionOCLoading(oc.id)
    try {
      const { data } = await api.post(`/compras/ordenes/${oc.id}/${accion}/`)
      const mensajes = { submit: 'OC enviada a revisión', aprobar: 'OC aprobada', convertir: 'Compra generada exitosamente' }
      toast.success(mensajes[accion])
      if (accion === 'convertir' && data.compra_id) toast.success(`Compra #${data.compra_id} creada`, { icon: '📦' })
      loadOrdenes(filterEstadoOC, pageOrdenes)
      if (detailOC?.id === oc.id) setDetailOC(null)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAccionOCLoading(null)
    }
  }, [filterEstadoOC, pageOrdenes, loadOrdenes, detailOC])

  const handleConfirmarEntrega = useCallback(async (compra: Compra) => {
    setConfirmandoEntrega(compra.id)
    try {
      await api.post(`/compras/compras/${compra.id}/confirmar-entrega/`)
      toast.success('Entrega confirmada — stock actualizado')
      loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, pageCompras)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setConfirmandoEntrega(null)
    }
  }, [searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, pageCompras, loadCompras])

  async function handleAnularCompra() {
    if (!confirmAnularCompra) return
    setAnulandoCompra(true)
    try {
      await api.post(`/compras/compras/${confirmAnularCompra.id}/anular/`)
      toast.success(`Compra #${confirmAnularCompra.id} anulada`)
      setConfirmAnularCompra(null)
      loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, pageCompras)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAnulandoCompra(false)
    }
  }

  // ── Columns ─────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const colsCompras: Column<Compra>[] = [
    { title: 'ID', key: 'id', dataIndex: 'id', width: 60, render: v => <span className="text-sm font-mono text-slate-500">#{v as number}</span> },
    { title: 'Proveedor', key: 'proveedor', render: (_, r) => <span className="text-base font-medium text-slate-800">{r.proveedor_nombre}</span> },
    { title: 'Fecha', key: 'fecha', render: (_, r) => <span className="text-base text-slate-600">{formatFecha(r.fecha)}</span> },
    { title: 'Total', key: 'total', render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_total)}</span> },
    {
      title: 'Saldo Pendiente', key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_pendiente) || 0
        return <span className={`tabular-nums font-semibold text-base ${n > 0 ? 'text-red-600' : 'text-slate-400'}`}>{formatGs(n)}</span>
      },
    },
    { title: 'Tipo', key: 'tipo', render: (_, r) => <Badge color={TIPO_PAGO_COLOR[r.tipo_pago] ?? 'default'}>{r.tipo_pago}</Badge> },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => (
        <div className="flex flex-col gap-1">
          <Badge color={ESTADO_PAGO_COLOR[r.estado_pago] ?? 'default'}>{r.estado_pago}</Badge>
          {r.tipo_pago === 'CREDITO' && <Badge color={ESTADO_ENTREGA_COLOR[r.estado_entrega] ?? 'default'}>{r.estado_entrega}</Badge>}
        </div>
      ),
    },
    {
      title: '', key: 'acciones', width: 180,
      render: (_, r) => (
        <div className="flex items-center gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => setDetailCompra(r)}><Eye className="w-3.5 h-3.5" />Ver</Button>
          <Button size="sm" variant="secondary" onClick={() => setCompraModal({ open: true, compra: r })}>Editar</Button>
          {canApprove && (r.estado_pago === 'PENDIENTE' || r.estado_pago === 'PARCIAL') && (
            <Button size="sm" variant="primary" onClick={() => setPagoModal({ open: true, compra: r })}>
              <DollarSign className="w-3.5 h-3.5" />Pagar
            </Button>
          )}
          {r.tipo_pago === 'CREDITO' && r.estado_entrega === 'PENDIENTE' && (
            <Button size="sm" variant="secondary" onClick={() => handleConfirmarEntrega(r)} disabled={confirmandoEntrega === r.id}>
              <PackageCheck className="w-3.5 h-3.5" />{confirmandoEntrega === r.id ? '...' : 'Recibir'}
            </Button>
          )}
          {canApprove && r.estado_pago !== 'ANULADA' && (
            <Button size="sm" variant="danger" onClick={() => setConfirmAnularCompra(r)}>
              <Undo2 className="w-3.5 h-3.5" />Anular
            </Button>
          )}
        </div>
      ),
    },
  ]

  const colsProveedores: Column<Proveedor>[] = [
    {
      title: 'Razón Social', key: 'razon',
      render: (_, r) => <div><p className="text-base font-medium text-slate-800">{r.razon_social}</p><p className="text-sm text-slate-400">{r.ruc}</p></div>,
    },
    {
      title: 'Contacto', key: 'contacto',
      render: (_, r) => <div><p className="text-base text-slate-600">{r.telefono || '—'}</p><p className="text-sm text-slate-400">{r.email || '—'}</p></div>,
    },
    {
      title: 'Saldo C/C', key: 'saldo_cc',
      render: (_, r) => {
        const n = Number(r.saldo_cuenta_corriente) || 0
        return <span className={`tabular-nums font-semibold text-base ${n > 0 ? 'text-red-600' : 'text-emerald-700'}`}>{formatGs(n)}</span>
      },
    },
    { title: 'Estado', key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    {
      title: '', key: 'acciones', width: 160,
      render: (_, r) => (
        <div className="flex items-center gap-2">
          <Button size="sm" variant="ghost" onClick={() => setProvModal({ open: true, prov: r })}>Editar</Button>
          <Button size="sm" variant="secondary" onClick={() => setCcProveedor(r)}>
            <Building2 className="w-3.5 h-3.5" />C/C
          </Button>
        </div>
      ),
    },
  ]

  const colsPagos: Column<PagoProveedor>[] = [
    { title: 'Compra #', key: 'compra', render: (_, r) => <span className="text-sm font-mono text-slate-500">{r.compra_id ? `#${r.compra_id}` : '—'}</span> },
    { title: 'Proveedor', key: 'prov', render: (_, r) => <span className="text-base text-slate-800">{r.proveedor_nombre}</span> },
    { title: 'Monto', key: 'monto', render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto_total)}</span> },
    { title: 'Medio', key: 'medio', render: (_, r) => <Badge color="default">{r.medio_pago_nombre}</Badge> },
    { title: 'Estado', key: 'estado', render: (_, r) => <Badge color="green">{r.estado}</Badge> },
    { title: 'Fecha', key: 'fecha', render: (_, r) => <span className="text-base text-slate-500">{formatFecha(r.fecha)}</span> },
  ]

  const colsOrdenes: Column<OrdenCompra>[] = [
    { title: 'OC #', key: 'id', width: 65, render: (_, r) => <span className="text-sm font-mono text-slate-500">#{r.id}</span> },
    { title: 'Proveedor', key: 'proveedor', render: (_, r) => <span className="text-base font-medium text-slate-800">{r.proveedor_nombre}</span> },
    { title: 'Tipo', key: 'tipo', render: (_, r) => <Badge color={TIPO_PAGO_COLOR[r.tipo_pago] ?? 'default'}>{r.tipo_pago}</Badge> },
    { title: 'Total estimado', key: 'monto', render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_total)}</span> },
    { title: 'Estado', key: 'estado', render: (_, r) => <Badge color={OC_ESTADO_COLOR[r.estado] ?? 'default'}>{OC_ESTADO_LABEL[r.estado] ?? r.estado}</Badge> },
    { title: 'Creada por', key: 'creador', render: (_, r) => <span className="text-sm text-slate-500">{r.creado_por_nombre}</span> },
    { title: 'Fecha', key: 'fecha', render: (_, r) => <span className="text-base text-slate-500">{formatFecha(r.fecha_creacion)}</span> },
    {
      title: '', key: 'acciones', width: 240,
      render: (_, r) => {
        const loading = accionOCLoading === r.id
        return (
          <div className="flex items-center gap-1.5 flex-wrap">
            <Button size="sm" variant="secondary" onClick={() => setDetailOC(r)}><Eye className="w-3.5 h-3.5" />Ver</Button>
            {r.estado === 'BORRADOR' && (
              <>
                <Button size="sm" variant="secondary" onClick={() => setOcModal({ open: true, oc: r })}>Editar</Button>
                <Button size="sm" variant="primary" disabled={loading} onClick={() => handleOCAccion(r, 'submit')}>
                  <Send className="w-3.5 h-3.5" />{loading ? '...' : 'Enviar'}
                </Button>
              </>
            )}
            {r.estado === 'PENDIENTE' && canApprove && (
              <>
                <Button size="sm" variant="primary" disabled={loading} onClick={() => handleOCAccion(r, 'aprobar')}>
                  <CheckCircle className="w-3.5 h-3.5" />{loading ? '...' : 'Aprobar'}
                </Button>
                <Button size="sm" variant="secondary" disabled={loading} onClick={() => setRechazarOC(r)}>
                  <XCircle className="w-3.5 h-3.5" />Rechazar
                </Button>
              </>
            )}
            {r.estado === 'APROBADA' && canApprove && (
              <Button size="sm" variant="primary" disabled={loading} onClick={() => handleOCAccion(r, 'convertir')}>
                <ArrowRightCircle className="w-3.5 h-3.5" />{loading ? '...' : 'Convertir'}
              </Button>
            )}
            {r.estado === 'CONVERTIDA' && r.compra_generada && (
              <span className="text-xs text-blue-600 font-medium">Compra #{r.compra_generada}</span>
            )}
          </div>
        )
      },
    },
  ]

  const colsNotas: Column<NotaCredito>[] = [
    { title: 'NC #', key: 'id', render: (_, r) => <span className="text-sm font-semibold text-slate-500">#{r.id}</span> },
    { title: 'Proveedor', key: 'proveedor', render: (_, r) => <span className="text-base font-medium text-slate-800">{r.proveedor_nombre}</span> },
    { title: 'Monto', key: 'monto_total', render: (_, r) => <span className="text-base font-bold tabular-nums text-emerald-700">{formatGs(r.monto_total)}</span> },
    {
      title: 'Compra orig.', key: 'compra_original',
      render: (_, r) => r.compra_original
        ? <span className="text-sm text-blue-600 font-medium">#{r.compra_original}</span>
        : <span className="text-sm text-slate-400">—</span>,
    },
    {
      title: 'Tipo', key: 'tipo_nc',
      render: (_, r) => r.tipo_nc === 'DEVOLUCION'
        ? <Badge color="orange">Devolución</Badge>
        : <Badge color="default">Ajuste precio</Badge>,
    },
    { title: 'Estado', key: 'estado', render: (_, r) => <Badge color={NC_ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge> },
    { title: 'Fecha', key: 'fecha', render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha)}</span> },
    {
      title: '', key: 'acciones',
      render: (_, r) => (
        <div className="flex items-center gap-2 justify-end">
          <Button size="sm" variant="secondary" onClick={() => setDetailNC(r)}><Eye className="w-3.5 h-3.5" />Ver</Button>
        </div>
      ),
    },
  ]

  // ── Render ──────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('compras.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('compras.subtitle')}</p>
        </div>
        {tab === 'ordenes' && (
          <Button variant="primary" onClick={() => setOcModal({ open: true, oc: null })}>
            <Plus className="w-4 h-4" />Nueva OC
          </Button>
        )}
        {tab === 'compras' && (
          <Button variant="primary" onClick={() => setCompraModal({ open: true, compra: null })}>
            <Plus className="w-4 h-4" />{t('compras.newCompra')}
          </Button>
        )}
        {tab === 'notas' && canApprove && (
          <Button variant="primary" onClick={() => setNcModalOpen(true)}>
            <Plus className="w-4 h-4" />Nueva Nota C/C
          </Button>
        )}
      </div>

      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />{label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'ordenes' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div>
              <label className={labelClass}>Estado</label>
              <select value={filterEstadoOC} onChange={e => { setFilterEstadoOC(e.target.value); setPageOrdenes(1) }} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                <option value="BORRADOR">Borrador</option>
                <option value="PENDIENTE">En revisión</option>
                <option value="APROBADA">Aprobada</option>
                <option value="RECHAZADA">Rechazada</option>
                <option value="CONVERTIDA">Convertida</option>
              </select>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsOrdenes} dataSource={ordenes} rowKey="id" loading={loadingOrdenes}
                pageSize={PAGE_SIZE} page={pageOrdenes} onPageChange={p => { setPageOrdenes(p); loadOrdenes(filterEstadoOC, p) }} total={totalOrdenes} />
            </div>
          </div>
        </>
      )}

      {tab === 'compras' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[180px]">
              <label className={labelClass}>Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input placeholder="Proveedor, factura..." value={searchCompras} onChange={e => setSearchCompras(e.target.value)} className={`${inputClass} pl-9`} />
              </div>
            </div>
            <div>
              <label className={labelClass}>Proveedor</label>
              <select value={filterProveedor} onChange={e => { setFilterProveedor(e.target.value); setPageCompras(1) }} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                {proveedores.map(p => <option key={p.id} value={p.id}>{p.razon_social}</option>)}
              </select>
            </div>
            <div>
              <label className={labelClass}>Estado Pago</label>
              <select value={filterEstado} onChange={e => { setFilterEstado(e.target.value); setPageCompras(1) }} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                <option value="PAGADO">Pagado</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="PARCIAL">Parcial</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Tipo Pago</label>
              <select value={filterTipo} onChange={e => { setFilterTipo(e.target.value); setPageCompras(1) }} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                <option value="CONTADO">Contado</option>
                <option value="CREDITO">Crédito</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Entrega</label>
              <select value={filterEntrega} onChange={e => { setFilterEntrega(e.target.value); setPageCompras(1) }} className={`${inputClass} w-auto`}>
                <option value="">Todas</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="RECIBIDA">Recibida</option>
              </select>
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsCompras} dataSource={compras} rowKey="id" loading={loadingCompras}
                pageSize={PAGE_SIZE} page={pageCompras}
                onPageChange={p => { setPageCompras(p); loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, p) }}
                total={totalCompras} />
            </div>
          </div>
        </>
      )}

      {tab === 'proveedores' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
            <div className="flex items-center justify-between gap-4 mb-3">
              <label className={labelClass}>Buscar proveedor</label>
              <Button size="sm" variant="primary" onClick={() => setProvModal({ open: true, prov: null })}>
                <Plus className="w-3.5 h-3.5" />Nuevo Proveedor
              </Button>
            </div>
            <div className="relative max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <input placeholder="Razón social, RUC..." value={searchProv} onChange={e => setSearchProv(e.target.value)} className={`${inputClass} pl-9`} />
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsProveedores} dataSource={proveedores} rowKey="id" loading={loadingProv}
                pageSize={PAGE_SIZE} page={pageProveedores}
                onPageChange={p => { setPageProveedores(p); loadProveedores(searchProv, p) }}
                total={totalProveedores} />
            </div>
          </div>
        </>
      )}

      {tab === 'pagos' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-800">Pagos a Proveedores</h2>
          </div>
          <div className="p-1">
            <Table columns={colsPagos} dataSource={pagos} rowKey="id" loading={loadingPagos}
              pageSize={PAGE_SIZE} page={pagePagos} onPageChange={setPagePagos} total={totalPagos} />
          </div>
        </div>
      )}

      {tab === 'notas' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-800">Notas de Crédito de Proveedores</h2>
          </div>
          <div className="p-1">
            <Table columns={colsNotas} dataSource={notas} rowKey="id" loading={loadingNotas}
              pageSize={PAGE_SIZE} page={pageNotas} onPageChange={setPageNotas} total={totalNotas} />
          </div>
        </div>
      )}

      {/* ── Modals ── */}
      <ModalProveedor
        open={provModal.open}
        editingProv={provModal.prov}
        onClose={() => setProvModal({ open: false, prov: null })}
        onSaved={() => {
          loadProveedores(searchProv, pageProveedores)
          api.get('/compras/proveedores/', { params: { activo: true, page_size: 500 } })
            .then(res => setProveedores(res.data.results ?? []))
            .catch(() => {})
        }}
      />
      <ModalCuentaCorriente
        proveedor={ccProveedor}
        onClose={() => setCcProveedor(null)}
      />
      <ModalCompra
        open={compraModal.open}
        editingCompra={compraModal.compra}
        proveedores={proveedores}
        productos={productos}
        onClose={() => setCompraModal({ open: false, compra: null })}
        onSaved={() => { setPageCompras(1); loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, 1) }}
      />
      <ModalCompraDetail
        compra={detailCompra}
        canApprove={canApprove}
        confirmandoEntrega={confirmandoEntrega}
        onClose={() => setDetailCompra(null)}
        onPago={(c) => { setDetailCompra(null); setPagoModal({ open: true, compra: c }) }}
        onConfirmarEntrega={(c) => { setDetailCompra(null); handleConfirmarEntrega(c) }}
      />
      {confirmAnularCompra && (
        <Modal
          open
          title="Anular compra"
          onCancel={() => !anulandoCompra && setConfirmAnularCompra(null)}
          footer={null}
        >
          <div className="space-y-4">
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
              <AlertTriangle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
              <div className="text-sm text-red-800 space-y-1">
                <p className="font-semibold">Esta acción es irreversible</p>
                <p>Se revertirá el stock que haya ingresado y la cuenta corriente del proveedor. No se puede anular si ya tiene pagos aplicados.</p>
              </div>
            </div>
            <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1 text-sm">
              <p className="text-slate-500">Compra <span className="font-semibold text-slate-800">#{confirmAnularCompra.id}</span></p>
              <p className="text-slate-500">Proveedor: <span className="font-semibold text-slate-800">{confirmAnularCompra.proveedor_nombre}</span></p>
              <p className="text-slate-500">Monto: <span className="font-semibold text-slate-800">{formatGs(confirmAnularCompra.monto_total)}</span></p>
              <p className="text-slate-500">Fecha: <span className="font-semibold text-slate-800">{formatFecha(confirmAnularCompra.fecha)}</span></p>
            </div>
            <div className="flex gap-3 justify-end pt-1">
              <Button variant="secondary" onClick={() => setConfirmAnularCompra(null)} disabled={anulandoCompra}>
                Cancelar
              </Button>
              <Button variant="danger" loading={anulandoCompra} onClick={handleAnularCompra}>
                Confirmar anulación
              </Button>
            </div>
          </div>
        </Modal>
      )}
      <ModalPago
        open={pagoModal.open}
        compra={pagoModal.compra}
        mediosPago={mediosPago}
        onClose={() => setPagoModal({ open: false, compra: null })}
        onSaved={() => loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, pageCompras)}
      />
      <ModalOC
        open={ocModal.open}
        editingOC={ocModal.oc}
        proveedores={proveedores}
        productos={productos}
        onClose={() => setOcModal({ open: false, oc: null })}
        onSaved={() => { setPageOrdenes(1); loadOrdenes(filterEstadoOC, 1) }}
      />
      <ModalOCDetail
        oc={detailOC}
        canApprove={canApprove}
        accionLoading={accionOCLoading !== null}
        onClose={() => setDetailOC(null)}
        onEdit={(oc) => setOcModal({ open: true, oc })}
        onRechazar={(oc) => setRechazarOC(oc)}
        onAccion={handleOCAccion}
      />
      <ModalRechazarOC
        oc={rechazarOC}
        onClose={() => setRechazarOC(null)}
        onSaved={() => loadOrdenes(filterEstadoOC, pageOrdenes)}
      />
      <ModalNC
        open={ncModalOpen}
        proveedores={proveedores}
        productos={productos}
        onClose={() => setNcModalOpen(false)}
        onSaved={() => { setPageNotas(1); loadNotas(1) }}
      />
      <ModalNCDetail
        nc={detailNC}
        canApprove={canApprove}
        onClose={() => setDetailNC(null)}
        onAnulada={() => loadNotas(pageNotas)}
      />
    </div>
  )
}
