import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Truck, Search, Plus, Eye, CreditCard,
  Building2, DollarSign, X, PackageCheck,
  ClipboardList, CheckCircle, XCircle, ArrowRightCircle, Send,
} from 'lucide-react'
import api from '../services/api'
import { useCatalogoStore } from '../store/catalogoStore'
import { useAuthStore } from '../store/authStore'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import Modal from '../components/ui/Modal'
import Combobox from '../components/ui/Combobox'

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
  return new Date(iso).toLocaleDateString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Proveedor {
  id: number
  razon_social: string
  ruc: string
  telefono: string
  email: string
  activo: boolean
  saldo_cuenta_corriente: number | string
}

interface Producto {
  id: number
  descripcion: string
  precio_actual: string | number
}

interface DetalleCompra {
  id: number
  producto: number
  producto_nombre: string
  cantidad: number
  costo_unitario: string | number
  subtotal: string | number
}

interface Compra {
  id: number
  proveedor: number
  proveedor_nombre: string
  fecha: string
  monto_total: string | number
  estado_pago: string
  estado_entrega: string
  tipo_pago: string
  nro_factura_proveedor: string
  saldo_pendiente: string | number
  detalles: DetalleCompra[]
}

interface PagoProveedor {
  id: number
  compra: number
  proveedor: number
  proveedor_nombre: string
  monto: string | number
  fecha: string
  medio_pago: string
  medio_pago_nombre: string
  observaciones: string
  estado: string
}

interface CuentaCorriente {
  id: number
  tipo: string
  descripcion: string
  monto: string | number
  saldo_resultante: string | number
  fecha: string
}

interface ItemForm {
  producto: Producto | null
  cantidad: number
  costo_unitario: number
  subtotal: number
}

interface DetalleOC {
  id: number
  producto: number
  producto_nombre: string
  cantidad: number
  costo_unitario: string | number
  subtotal: string | number
}

interface OrdenCompra {
  id: number
  proveedor: number
  proveedor_nombre: string
  estado: 'BORRADOR' | 'PENDIENTE' | 'APROBADA' | 'RECHAZADA' | 'CONVERTIDA'
  tipo_pago: string
  monto_total: string | number
  nro_factura_esperada: string | null
  observaciones: string | null
  motivo_rechazo: string | null
  aprobado_por_nombre: string | null
  fecha_aprobacion: string | null
  compra_generada: number | null
  creado_por_nombre: string
  fecha_creacion: string
  detalles: DetalleOC[]
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ESTADO_PAGO_COLOR: Record<string, BadgeColor> = {
  PAGADO: 'green',
  PENDIENTE: 'orange',
  PARCIAL: 'blue',
}

const TIPO_PAGO_COLOR: Record<string, BadgeColor> = {
  CONTADO: 'green',
  CREDITO: 'orange',
}

const ESTADO_ENTREGA_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'orange',
  RECIBIDA: 'green',
}

const MEDIO_PAGO_COLOR: Record<string, BadgeColor> = {
  EFECTIVO: 'green',
  TRANSFERENCIA: 'blue',
  CHEQUE: 'purple',
}

type TabKey = 'compras' | 'proveedores' | 'pagos' | 'ordenes'

interface CompraFormFields {
  proveedor_id: number | ''
  tipo_pago: string
  nro_factura: string
}

const ITEM_EMPTY: ItemForm = { producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0 }

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Compras() {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const canApprove = user?.rol === 'ADMIN' || user?.rol === 'SUPERVISOR'
  const [tab, setTab] = useState<TabKey>('compras')
  const getProductos = useCatalogoStore(state => state.getProductos)

  // ── Catalogs ────────────────────────────────────────────────────
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [productos, setProductos] = useState<Producto[]>([])

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
  const requestIdComprasRef = useRef(0)

  // ── Proveedores list ────────────────────────────────────────────
  const [pageProveedores, setPageProveedores] = useState(1)
  const [totalProveedores, setTotalProveedores] = useState(0)
  const [loadingProv, setLoadingProv] = useState(false)
  const [searchProv, setSearchProv] = useState('')
  const searchTimerProv = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdProvRef = useRef(0)

  // ── Pagos list ──────────────────────────────────────────────────
  const [pagos, setPagos] = useState<PagoProveedor[]>([])
  const [loadingPagos, setLoadingPagos] = useState(false)
  const [pagePagos, setPagePagos] = useState(1)
  const [totalPagos, setTotalPagos] = useState(0)
  const requestIdPagosRef = useRef(0)

  // ── Compra detail modal ─────────────────────────────────────────
  const [detailCompra, setDetailCompra] = useState<Compra | null>(null)

  // ── Create/Edit compra modal ────────────────────────────────────
  const [compraModalOpen, setCompraModalOpen] = useState(false)
  const [editingCompra, setEditingCompra] = useState<Compra | null>(null)
  const [items, setItems] = useState<ItemForm[]>([{ ...ITEM_EMPTY }])
  const [savingCompra, setSavingCompra] = useState(false)

  const {
    register: registerCompra,
    handleSubmit: handleSubmitCompra,
    reset: resetCompra,
    watch: watchCompra,
    setValue: setValueCompra,
    formState: { errors: compraErrors },
  } = useForm<CompraFormFields>({
    defaultValues: { proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' },
  })
  const proveedorId = watchCompra('proveedor_id')

  // ── Pago modal ──────────────────────────────────────────────────
  const [pagoModalOpen, setPagoModalOpen] = useState(false)
  const [pagoCompra, setPagoCompra] = useState<Compra | null>(null)
  const [montoPago, setMontoPago] = useState('')
  const [medioPago, setMedioPago] = useState('EFECTIVO')
  const [obsPago, setObsPago] = useState('')
  const [savingPago, setSavingPago] = useState(false)
  const [confirmandoEntrega, setConfirmandoEntrega] = useState<number | null>(null)

  // ── Órdenes de Compra ───────────────────────────────────────────
  const [ordenes, setOrdenes] = useState<OrdenCompra[]>([])
  const [loadingOrdenes, setLoadingOrdenes] = useState(false)
  const [pageOrdenes, setPageOrdenes] = useState(1)
  const [totalOrdenes, setTotalOrdenes] = useState(0)
  const [filterEstadoOC, setFilterEstadoOC] = useState('')
  const requestIdOCRef = useRef(0)

  // OC create/edit modal
  const [ocModalOpen, setOcModalOpen] = useState(false)
  const [editingOC, setEditingOC] = useState<OrdenCompra | null>(null)
  const [ocItems, setOcItems] = useState<ItemForm[]>([{ ...ITEM_EMPTY }])
  const [savingOC, setSavingOC] = useState(false)
  const {
    register: registerOC,
    handleSubmit: handleSubmitOC,
    reset: resetOC,
    watch: watchOC,
    setValue: setValueOC,
    formState: { errors: ocErrors },
  } = useForm<CompraFormFields>({
    defaultValues: { proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' },
  })
  const proveedorIdOC = watchOC('proveedor_id')

  // OC detail modal
  const [detailOC, setDetailOC] = useState<OrdenCompra | null>(null)

  // Rechazar modal
  const [rechazarOC, setRechazarOC] = useState<OrdenCompra | null>(null)
  const [motivoRechazo, setMotivoRechazo] = useState('')
  const [savingRechazar, setSavingRechazar] = useState(false)

  // Acción individual loading (submit/aprobar/convertir)
  const [accionOCLoading, setAccionOCLoading] = useState<number | null>(null)

  // ── Cuenta corriente modal ──────────────────────────────────────
  const [ccProveedor, setCcProveedor] = useState<Proveedor | null>(null)
  const [cuentaCorriente, setCuentaCorriente] = useState<CuentaCorriente[]>([])
  const [loadingCc, setLoadingCc] = useState(false)

  // ── Load catalogs ────────────────────────────────────────────────
  useEffect(() => {
    api.get('/compras/proveedores/', { params: { activo: true, page_size: 500 } })
      .then(res => setProveedores(res.data.results ?? []))
      .catch(() => {})
    getProductos().then(prods => setProductos(prods as Producto[])).catch(() => {})
  }, [getProductos])

  // ── Load compras ─────────────────────────────────────────────────
  const loadCompras = useCallback(async (search: string, estado: string, tipo: string, prov: string, entrega: string, p: number) => {
    const requestId = ++requestIdComprasRef.current
    setLoadingCompras(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15 }
      if (search) params.search = search
      if (estado) params.estado_pago = estado
      if (tipo) params.tipo_pago = tipo
      if (prov) params.proveedor = prov
      if (entrega) params.estado_entrega = entrega
      const { data } = await api.get('/compras/compras/', { params })
      if (requestId !== requestIdComprasRef.current) return
      setCompras(data.results ?? [])
      setTotalCompras(data.count ?? 0)
    } catch {
      if (requestId !== requestIdComprasRef.current) return
      toast.error('Error al cargar compras')
    } finally {
      if (requestId === requestIdComprasRef.current) setLoadingCompras(false)
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

  // ── Load proveedores with pagination ─────────────────────────────
  const loadProveedores = useCallback(async (search: string, p: number) => {
    const requestId = ++requestIdProvRef.current
    setLoadingProv(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15 }
      if (search) params.search = search
      const { data } = await api.get('/compras/proveedores/', { params })
      if (requestId !== requestIdProvRef.current) return
      setProveedores(data.results ?? [])
      setTotalProveedores(data.count ?? 0)
    } catch {
      if (requestId !== requestIdProvRef.current) return
      toast.error('Error al cargar proveedores')
    } finally {
      if (requestId === requestIdProvRef.current) setLoadingProv(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'proveedores') {
      clearTimeout(searchTimerProv.current)
      searchTimerProv.current = setTimeout(() => {
        setPageProveedores(1)
        loadProveedores(searchProv, 1)
      }, 350)
      return () => clearTimeout(searchTimerProv.current)
    }
  }, [searchProv, tab, loadProveedores])

  // ── Load pagos ───────────────────────────────────────────────────
  const loadPagos = useCallback(async (p: number) => {
    const requestId = ++requestIdPagosRef.current
    setLoadingPagos(true)
    try {
      const { data } = await api.get('/compras/pagos/', { params: { page: p, page_size: 15 } })
      if (requestId !== requestIdPagosRef.current) return
      setPagos(data.results ?? [])
      setTotalPagos(data.count ?? 0)
    } catch {
      if (requestId !== requestIdPagosRef.current) return
      toast.error('Error al cargar pagos')
    } finally {
      if (requestId === requestIdPagosRef.current) setLoadingPagos(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'pagos') loadPagos(pagePagos)
  }, [tab, pagePagos, loadPagos])

  // ── Load órdenes de compra ───────────────────────────────────────
  const loadOrdenes = useCallback(async (estado: string, p: number) => {
    const requestId = ++requestIdOCRef.current
    setLoadingOrdenes(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15 }
      if (estado) params.estado = estado
      const { data } = await api.get('/compras/ordenes/', { params })
      if (requestId !== requestIdOCRef.current) return
      setOrdenes(data.results ?? [])
      setTotalOrdenes(data.count ?? 0)
    } catch {
      if (requestId !== requestIdOCRef.current) return
      toast.error('Error al cargar órdenes de compra')
    } finally {
      if (requestId === requestIdOCRef.current) setLoadingOrdenes(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'ordenes') loadOrdenes(filterEstadoOC, pageOrdenes)
  }, [tab, filterEstadoOC, pageOrdenes, loadOrdenes])

  // ── OC actions ────────────────────────────────────────────────────
  const handleOCAccion = useCallback(async (oc: OrdenCompra, accion: 'submit' | 'aprobar' | 'convertir') => {
    setAccionOCLoading(oc.id)
    try {
      const { data } = await api.post(`/compras/ordenes/${oc.id}/${accion}/`)
      const mensajes = { submit: 'OC enviada a revisión', aprobar: 'OC aprobada', convertir: 'Compra generada exitosamente' }
      toast.success(mensajes[accion])
      if (accion === 'convertir' && data.compra_id) {
        toast.success(`Compra #${data.compra_id} creada`, { icon: '📦' })
      }
      loadOrdenes(filterEstadoOC, pageOrdenes)
      if (detailOC?.id === oc.id) setDetailOC(null)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAccionOCLoading(null)
    }
  }, [filterEstadoOC, pageOrdenes, loadOrdenes, detailOC])

  const handleOCRechazar = useCallback(async () => {
    if (!rechazarOC) return
    const motivo = motivoRechazo.trim()
    if (!motivo) { toast.error('Ingresá el motivo del rechazo'); return }
    setSavingRechazar(true)
    try {
      await api.post(`/compras/ordenes/${rechazarOC.id}/rechazar/`, { motivo })
      toast.success('OC rechazada')
      setRechazarOC(null)
      setMotivoRechazo('')
      loadOrdenes(filterEstadoOC, pageOrdenes)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingRechazar(false)
    }
  }, [rechazarOC, motivoRechazo, filterEstadoOC, pageOrdenes, loadOrdenes])

  const openCreateOC = useCallback(() => {
    setEditingOC(null)
    resetOC({ proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' })
    setOcItems([{ ...ITEM_EMPTY }])
    setOcModalOpen(true)
  }, [resetOC])

  const openEditOC = useCallback((oc: OrdenCompra) => {
    if (oc.estado !== 'BORRADOR') { toast.error('Solo se puede editar una OC en Borrador'); return }
    setEditingOC(oc)
    resetOC({ proveedor_id: oc.proveedor, tipo_pago: oc.tipo_pago, nro_factura: oc.nro_factura_esperada || '' })
    setOcItems(
      oc.detalles?.length
        ? oc.detalles.map(d => ({
            producto: { id: d.producto, descripcion: d.producto_nombre, precio_actual: d.costo_unitario },
            cantidad: d.cantidad,
            costo_unitario: Number(d.costo_unitario) || 0,
            subtotal: Number(d.subtotal) || 0,
          }))
        : [{ ...ITEM_EMPTY }]
    )
    setOcModalOpen(true)
  }, [resetOC])

  const ocTotal = useMemo(() => ocItems.reduce((s, i) => s + i.subtotal, 0), [ocItems])

  const handleSaveOC = handleSubmitOC(async (fields) => {
    if (ocItems.some(i => !i.producto)) {
      toast.error('Completá todos los productos de la OC')
      return
    }
    setSavingOC(true)
    try {
      const payload = {
        proveedor: fields.proveedor_id,
        tipo_pago: fields.tipo_pago,
        nro_factura_esperada: fields.nro_factura,
        items: ocItems.map(i => ({
          producto: i.producto!.id,
          cantidad: i.cantidad,
          costo_unitario: i.costo_unitario,
        })),
      }
      if (editingOC) {
        await api.put(`/compras/ordenes/${editingOC.id}/`, payload)
        toast.success('OC actualizada')
      } else {
        await api.post('/compras/ordenes/', payload)
        toast.success('Orden de Compra creada en Borrador')
      }
      setOcModalOpen(false)
      loadOrdenes(filterEstadoOC, 1)
      setPageOrdenes(1)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingOC(false)
    }
  })

  // ── Open create modal ────────────────────────────────────────────
  const openCreate = useCallback(() => {
    setEditingCompra(null)
    resetCompra({ proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' })
    setItems([{ ...ITEM_EMPTY }])
    setCompraModalOpen(true)
  }, [resetCompra])

  // ── Open edit modal ──────────────────────────────────────────────
  const openEdit = useCallback((c: Compra) => {
    setEditingCompra(c)
    resetCompra({ proveedor_id: c.proveedor, tipo_pago: c.tipo_pago, nro_factura: c.nro_factura_proveedor || '' })
    setItems(
      c.detalles?.length
        ? c.detalles.map(d => ({
            producto: { id: d.producto, descripcion: d.producto_nombre, precio_actual: d.costo_unitario },
            cantidad: d.cantidad,
            costo_unitario: Number(d.costo_unitario) || 0,
            subtotal: Number(d.subtotal) || 0,
          }))
        : [{ ...ITEM_EMPTY }]
    )
    setCompraModalOpen(true)
  }, [resetCompra])

  // ── Items management ─────────────────────────────────────────────
  const actualizarItem = useCallback((index: number, field: keyof ItemForm, value: unknown) => {
    setItems(prev => prev.map((item, i) => {
      if (i !== index) return item
      const updated = { ...item, [field]: value }
      if (field === 'producto' && value) {
        updated.costo_unitario = Number((value as Producto).precio_actual) || 0
      }
      updated.subtotal = updated.cantidad * updated.costo_unitario
      return updated
    }))
  }, [])

  const total = useMemo(() => items.reduce((s, i) => s + i.subtotal, 0), [items])

  // ── Save compra ──────────────────────────────────────────────────
  const handleSaveCompra = handleSubmitCompra(async (fields) => {
    if (items.some(i => !i.producto)) {
      toast.error('Completá todos los productos de la lista')
      return
    }
    setSavingCompra(true)
    try {
      const payload = {
        proveedor: fields.proveedor_id,
        tipo_pago: fields.tipo_pago,
        nro_factura_proveedor: fields.nro_factura,
        items: items.map(i => ({
          producto: i.producto!.id,
          cantidad: i.cantidad,
          costo_unitario: i.costo_unitario,
        })),
      }
      if (editingCompra) {
        await api.put(`/compras/compras/${editingCompra.id}/`, payload)
        toast.success('Compra actualizada')
      } else {
        await api.post('/compras/compras/', payload)
        toast.success(`Compra registrada — ${formatGs(total)}`)
      }
      setCompraModalOpen(false)
      setPageCompras(1)
      loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, 1)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingCompra(false)
    }
  })

  // ── Open pago modal ──────────────────────────────────────────────
  const openPago = useCallback((c: Compra) => {
    setPagoCompra(c)
    setMontoPago(String(Number(c.saldo_pendiente) || ''))
    setMedioPago('EFECTIVO')
    setObsPago('')
    setPagoModalOpen(true)
  }, [])

  const handleSavePago = useCallback(async () => {
    const montoNum = Number(montoPago) || 0
    if (montoNum <= 0) { toast.error('Ingresá un monto válido'); return }
    setSavingPago(true)
    try {
      await api.post('/compras/pagos/', {
        compra: pagoCompra!.id,
        proveedor: pagoCompra!.proveedor,
        monto: montoNum,
        medio_pago: medioPago,
        observaciones: obsPago,
      })
      toast.success('Pago registrado')
      setPagoModalOpen(false)
      loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, pageCompras)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingPago(false)
    }
  }, [montoPago, pagoCompra, medioPago, obsPago, searchCompras, filterEstado, filterTipo, filterProveedor, pageCompras, loadCompras])

  // ── Confirmar entrega ─────────────────────────────────────────────
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

  // ── Cuenta corriente ─────────────────────────────────────────────
  const openCuentaCorriente = useCallback(async (p: Proveedor) => {
    setCcProveedor(p)
    setLoadingCc(true)
    try {
      const { data } = await api.get('/compras/cuentas-corrientes/', { params: { proveedor: p.id, page_size: 200 } })
      setCuentaCorriente(data.results ?? data ?? [])
    } catch {
      toast.error('Error al cargar cuenta corriente')
    } finally {
      setLoadingCc(false)
    }
  }, [])

  // ── Columns ─────────────────────────────────────────────────────

  const colsCompras: Column<Compra>[] = [
    {
      title: 'ID',
      key: 'id',
      dataIndex: 'id',
      width: 60,
      render: v => <span className="text-sm font-mono text-slate-500">#{v as number}</span>,
    },
    {
      title: 'Proveedor',
      key: 'proveedor',
      render: (_, r) => <span className="text-base font-medium text-slate-800">{r.proveedor_nombre}</span>,
    },
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-base text-slate-600">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Total',
      key: 'total',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'Saldo Pendiente',
      key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_pendiente) || 0
        return <span className={`tabular-nums font-semibold text-base ${n > 0 ? 'text-red-600' : 'text-slate-400'}`}>{formatGs(n)}</span>
      },
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <Badge color={TIPO_PAGO_COLOR[r.tipo_pago] ?? 'default'}>{r.tipo_pago}</Badge>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => (
        <div className="flex flex-col gap-1">
          <Badge color={ESTADO_PAGO_COLOR[r.estado_pago] ?? 'default'}>{r.estado_pago}</Badge>
          {r.tipo_pago === 'CREDITO' && (
            <Badge color={ESTADO_ENTREGA_COLOR[r.estado_entrega] ?? 'default'}>{r.estado_entrega}</Badge>
          )}
        </div>
      ),
    },
    {
      title: '',
      key: 'acciones',
      width: 180,
      render: (_, r) => (
        <div className="flex items-center gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => setDetailCompra(r)}>
            <Eye className="w-3.5 h-3.5" />
            Ver
          </Button>
          <Button size="sm" variant="secondary" onClick={() => openEdit(r)}>
            Editar
          </Button>
          {(r.estado_pago === 'PENDIENTE' || r.estado_pago === 'PARCIAL') && (
            <Button size="sm" variant="primary" onClick={() => openPago(r)}>
              <DollarSign className="w-3.5 h-3.5" />
              Pagar
            </Button>
          )}
          {r.tipo_pago === 'CREDITO' && r.estado_entrega === 'PENDIENTE' && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => handleConfirmarEntrega(r)}
              disabled={confirmandoEntrega === r.id}
            >
              <PackageCheck className="w-3.5 h-3.5" />
              {confirmandoEntrega === r.id ? '...' : 'Recibir'}
            </Button>
          )}
        </div>
      ),
    },
  ]

  const colsProveedores: Column<Proveedor>[] = [
    {
      title: 'Razón Social',
      key: 'razon',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.razon_social}</p>
          <p className="text-sm text-slate-400">{r.ruc}</p>
        </div>
      ),
    },
    {
      title: 'Contacto',
      key: 'contacto',
      render: (_, r) => (
        <div>
          <p className="text-base text-slate-600">{r.telefono || '—'}</p>
          <p className="text-sm text-slate-400">{r.email || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Saldo C/C',
      key: 'saldo_cc',
      render: (_, r) => {
        const n = Number(r.saldo_cuenta_corriente) || 0
        return (
          <span className={`tabular-nums font-semibold text-base ${n > 0 ? 'text-red-600' : 'text-emerald-700'}`}>
            {formatGs(n)}
          </span>
        )
      },
    },
    {
      title: 'Estado',
      key: 'activo',
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 120,
      render: (_, r) => (
        <Button size="sm" variant="secondary" onClick={() => openCuentaCorriente(r)}>
          <Building2 className="w-3.5 h-3.5" />
          C/C
        </Button>
      ),
    },
  ]

  const colsPagos: Column<PagoProveedor>[] = [
    {
      title: 'Compra #',
      key: 'compra',
      render: (_, r) => <span className="text-sm font-mono text-slate-500">#{r.compra}</span>,
    },
    {
      title: 'Proveedor',
      key: 'prov',
      render: (_, r) => <span className="text-base text-slate-800">{r.proveedor_nombre}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto)}</span>,
    },
    {
      title: 'Medio',
      key: 'medio',
      render: (_, r) => (
        <Badge color={MEDIO_PAGO_COLOR[r.medio_pago] ?? 'default'}>{r.medio_pago_nombre || r.medio_pago}</Badge>
      ),
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={r.estado === 'APROBADO' ? 'green' : 'orange'}>{r.estado}</Badge>,
    },
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-base text-slate-500">{formatFecha(r.fecha)}</span>,
    },
  ]

  const colsCc: Column<CuentaCorriente>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-base text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <Badge color={r.tipo === 'CARGO' ? 'orange' : 'green'}>{r.tipo}</Badge>,
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-base text-slate-600">{r.descripcion}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto)}</span>,
    },
    {
      title: 'Saldo',
      key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_resultante) || 0
        return <span className={`tabular-nums text-base font-medium ${n > 0 ? 'text-red-600' : 'text-emerald-700'}`}>{formatGs(n)}</span>
      },
    },
  ]

  // ── Styles ──────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const OC_ESTADO_COLOR: Record<string, BadgeColor> = {
    BORRADOR:   'default',
    PENDIENTE:  'orange',
    APROBADA:   'green',
    RECHAZADA:  'red',
    CONVERTIDA: 'blue',
  }

  const OC_ESTADO_LABEL: Record<string, string> = {
    BORRADOR:   'Borrador',
    PENDIENTE:  'En revisión',
    APROBADA:   'Aprobada',
    RECHAZADA:  'Rechazada',
    CONVERTIDA: 'Convertida',
  }

  const colsOrdenes: Column<OrdenCompra>[] = [
    {
      title: 'OC #',
      key: 'id',
      width: 65,
      render: (_, r) => <span className="text-sm font-mono text-slate-500">#{r.id}</span>,
    },
    {
      title: 'Proveedor',
      key: 'proveedor',
      render: (_, r) => <span className="text-base font-medium text-slate-800">{r.proveedor_nombre}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <Badge color={TIPO_PAGO_COLOR[r.tipo_pago] ?? 'default'}>{r.tipo_pago}</Badge>,
    },
    {
      title: 'Total estimado',
      key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={OC_ESTADO_COLOR[r.estado] ?? 'default'}>{OC_ESTADO_LABEL[r.estado] ?? r.estado}</Badge>,
    },
    {
      title: 'Creada por',
      key: 'creador',
      render: (_, r) => <span className="text-sm text-slate-500">{r.creado_por_nombre}</span>,
    },
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-base text-slate-500">{formatFecha(r.fecha_creacion)}</span>,
    },
    {
      title: '',
      key: 'acciones',
      width: 240,
      render: (_, r) => {
        const loading = accionOCLoading === r.id
        return (
          <div className="flex items-center gap-1.5 flex-wrap">
            <Button size="sm" variant="secondary" onClick={() => setDetailOC(r)}>
              <Eye className="w-3.5 h-3.5" /> Ver
            </Button>
            {r.estado === 'BORRADOR' && (
              <>
                <Button size="sm" variant="secondary" onClick={() => openEditOC(r)}>Editar</Button>
                <Button size="sm" variant="primary" disabled={loading} onClick={() => handleOCAccion(r, 'submit')}>
                  <Send className="w-3.5 h-3.5" /> {loading ? '...' : 'Enviar'}
                </Button>
              </>
            )}
            {r.estado === 'PENDIENTE' && canApprove && (
              <>
                <Button size="sm" variant="primary" disabled={loading} onClick={() => handleOCAccion(r, 'aprobar')}>
                  <CheckCircle className="w-3.5 h-3.5" /> {loading ? '...' : 'Aprobar'}
                </Button>
                <Button size="sm" variant="secondary" disabled={loading} onClick={() => { setRechazarOC(r); setMotivoRechazo('') }}>
                  <XCircle className="w-3.5 h-3.5" /> Rechazar
                </Button>
              </>
            )}
            {r.estado === 'APROBADA' && canApprove && (
              <Button size="sm" variant="primary" disabled={loading} onClick={() => handleOCAccion(r, 'convertir')}>
                <ArrowRightCircle className="w-3.5 h-3.5" /> {loading ? '...' : 'Convertir'}
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

  const TABS: { key: TabKey; label: string; icon: typeof Truck }[] = [
    { key: 'ordenes',    label: 'Órdenes',    icon: ClipboardList },
    { key: 'compras',    label: 'Compras',    icon: Truck },
    { key: 'proveedores', label: 'Proveedores', icon: Building2 },
    { key: 'pagos',      label: 'Pagos',      icon: CreditCard },
  ]

  // ── Render ──────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('compras.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('compras.subtitle')}</p>
        </div>
        {tab === 'ordenes' && (
          <Button variant="primary" onClick={openCreateOC}>
            <Plus className="w-4 h-4" />
            Nueva OC
          </Button>
        )}
        {tab === 'compras' && (
          <Button variant="primary" onClick={openCreate}>
            <Plus className="w-4 h-4" />
            {t('compras.newCompra')}
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key
                  ? 'border-green-600 text-green-700'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Órdenes de Compra tab ────────────────────────────────── */}
      {tab === 'ordenes' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div>
              <label className={labelClass}>Estado</label>
              <select
                value={filterEstadoOC}
                onChange={e => { setFilterEstadoOC(e.target.value); setPageOrdenes(1) }}
                className={`${inputClass} w-auto`}
              >
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
              <Table
                columns={colsOrdenes}
                dataSource={ordenes}
                rowKey="id"
                loading={loadingOrdenes}
                pageSize={15}
                page={pageOrdenes}
                onPageChange={p => { setPageOrdenes(p); loadOrdenes(filterEstadoOC, p) }}
                total={totalOrdenes}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Compras tab ──────────────────────────────────────────── */}
      {tab === 'compras' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[180px]">
              <label className={labelClass}>Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  placeholder="Proveedor, factura..."
                  value={searchCompras}
                  onChange={e => setSearchCompras(e.target.value)}
                  className={`${inputClass} pl-9`}
                />
              </div>
            </div>
            <div>
              <label className={labelClass}>Proveedor</label>
              <select
                value={filterProveedor}
                onChange={e => { setFilterProveedor(e.target.value); setPageCompras(1) }}
                className={`${inputClass} w-auto`}
              >
                <option value="">Todos</option>
                {proveedores.map(p => (
                  <option key={p.id} value={p.id}>{p.razon_social}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Estado Pago</label>
              <select
                value={filterEstado}
                onChange={e => { setFilterEstado(e.target.value); setPageCompras(1) }}
                className={`${inputClass} w-auto`}
              >
                <option value="">Todos</option>
                <option value="PAGADO">Pagado</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="PARCIAL">Parcial</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Tipo Pago</label>
              <select
                value={filterTipo}
                onChange={e => { setFilterTipo(e.target.value); setPageCompras(1) }}
                className={`${inputClass} w-auto`}
              >
                <option value="">Todos</option>
                <option value="CONTADO">Contado</option>
                <option value="CREDITO">Crédito</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Entrega</label>
              <select
                value={filterEntrega}
                onChange={e => { setFilterEntrega(e.target.value); setPageCompras(1) }}
                className={`${inputClass} w-auto`}
              >
                <option value="">Todas</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="RECIBIDA">Recibida</option>
              </select>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={colsCompras}
                dataSource={compras}
                rowKey="id"
                loading={loadingCompras}
                pageSize={15}
                page={pageCompras}
                onPageChange={p => { setPageCompras(p); loadCompras(searchCompras, filterEstado, filterTipo, filterProveedor, filterEntrega, p) }}
                total={totalCompras}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Proveedores tab ──────────────────────────────────────── */}
      {tab === 'proveedores' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
            <label className={labelClass}>Buscar proveedor</label>
            <div className="relative max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <input
                placeholder="Razón social, RUC..."
                value={searchProv}
                onChange={e => setSearchProv(e.target.value)}
                className={`${inputClass} pl-9`}
              />
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={colsProveedores}
                dataSource={proveedores}
                rowKey="id"
                loading={loadingProv}
                pageSize={15}
                page={pageProveedores}
                onPageChange={p => { setPageProveedores(p); loadProveedores(searchProv, p) }}
                total={totalProveedores}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Pagos tab ────────────────────────────────────────────── */}
      {tab === 'pagos' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-base font-semibold text-slate-800">Pagos a Proveedores</h2>
          </div>
          <div className="p-1">
            <Table
              columns={colsPagos}
              dataSource={pagos}
              rowKey="id"
              loading={loadingPagos}
              pageSize={15}
              page={pagePagos}
              onPageChange={setPagePagos}
              total={totalPagos}
            />
          </div>
        </div>
      )}

      {/* ── Compra detail modal ───────────────────────────────────── */}
      {detailCompra && (
        <Modal
          open
          title={`Compra #${detailCompra.id} — ${detailCompra.proveedor_nombre}`}
          onCancel={() => setDetailCompra(null)}
          width={680}
          footer={null}
        >
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {[
              { label: 'Total', value: formatGs(detailCompra.monto_total) },
              { label: 'Saldo Pendiente', value: formatGs(detailCompra.saldo_pendiente), warn: Number(detailCompra.saldo_pendiente) > 0 },
              { label: 'Fecha', value: formatFecha(detailCompra.fecha) },
              { label: 'Nro. Factura', value: detailCompra.nro_factura_proveedor || '—' },
            ].map(({ label, value, warn }) => (
              <div key={label} className="bg-slate-50 rounded-xl px-3 py-3">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className={`text-base font-bold mt-0.5 tabular-nums ${warn ? 'text-red-600' : 'text-slate-800'}`}>{value}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mb-4">
            <Badge color={TIPO_PAGO_COLOR[detailCompra.tipo_pago] ?? 'default'}>{detailCompra.tipo_pago}</Badge>
            <Badge color={ESTADO_PAGO_COLOR[detailCompra.estado_pago] ?? 'default'}>{detailCompra.estado_pago}</Badge>
            {detailCompra.tipo_pago === 'CREDITO' && (
              <Badge color={ESTADO_ENTREGA_COLOR[detailCompra.estado_entrega] ?? 'default'}>
                Entrega: {detailCompra.estado_entrega}
              </Badge>
            )}
          </div>

          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">Detalle de productos</h3>
          <div className="border border-slate-200 rounded-xl overflow-hidden mb-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-2 text-left text-sm font-semibold text-slate-500 uppercase">Producto</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Cant.</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Costo Unit.</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(detailCompra.detalles ?? []).map(d => (
                  <tr key={d.id}>
                    <td className="px-4 py-2.5 text-slate-700">{d.producto_nombre}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">{d.cantidad}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">{formatGs(d.costo_unitario)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-slate-800">{formatGs(d.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <Button variant="secondary" onClick={() => setDetailCompra(null)}>Cerrar</Button>
            <div className="flex items-center gap-2">
              {detailCompra.tipo_pago === 'CREDITO' && detailCompra.estado_entrega === 'PENDIENTE' && (
                <Button variant="secondary" onClick={() => { setDetailCompra(null); handleConfirmarEntrega(detailCompra) }}>
                  <PackageCheck className="w-4 h-4" />
                  Confirmar Entrega
                </Button>
              )}
              {(detailCompra.estado_pago === 'PENDIENTE' || detailCompra.estado_pago === 'PARCIAL') && (
                <Button variant="primary" onClick={() => { setDetailCompra(null); openPago(detailCompra) }}>
                  <DollarSign className="w-4 h-4" />
                  Registrar Pago
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* ── Create/Edit compra modal ──────────────────────────────── */}
      <Modal
        open={compraModalOpen}
        title={editingCompra ? `Editar Compra #${editingCompra.id}` : 'Nueva Compra'}
        onOk={handleSaveCompra}
        onCancel={() => setCompraModalOpen(false)}
        okText={editingCompra ? 'Guardar Cambios' : 'Registrar'}
        confirmLoading={savingCompra}
        width={700}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Proveedor *</label>
              <Combobox
                options={proveedores.map(p => ({ value: p.id, label: p.razon_social }))}
                value={proveedorId || undefined}
                onChange={v => setValueCompra('proveedor_id', v as number)}
                filterLocal
                placeholder="Buscar proveedor..."
              />
              {compraErrors.proveedor_id && (
                <p className="text-xs text-red-500 mt-0.5">{compraErrors.proveedor_id.message}</p>
              )}
            </div>
            <div>
              <label className={labelClass}>Tipo de Pago</label>
              <select className={inputClass} {...registerCompra('tipo_pago')}>
                <option value="CONTADO">Contado</option>
                <option value="CREDITO">Crédito</option>
              </select>
            </div>
          </div>

          <div>
            <label className={labelClass}>Nro. Factura Proveedor</label>
            <input
              placeholder="001-001-0001234"
              className={inputClass}
              {...registerCompra('nro_factura')}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={`${labelClass} mb-0`}>Productos *</label>
              <Button size="sm" variant="ghost" onClick={() => setItems(prev => [...prev, { ...ITEM_EMPTY }])}>
                <Plus className="w-3.5 h-3.5" />
                Agregar
              </Button>
            </div>

            <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
              {items.map((item, idx) => (
                <div key={idx} className="flex gap-2 items-center bg-slate-50 rounded-xl px-3 py-2">
                  <div className="flex-1">
                    <Combobox
                      options={productos.map(p => ({ value: p.id, label: p.descripcion, data: p }))}
                      value={item.producto?.id}
                      onChange={(_, opt) => actualizarItem(idx, 'producto', opt.data as Producto)}
                      filterLocal
                      placeholder="Producto..."
                    />
                  </div>
                  <input
                    type="number"
                    min={1}
                    value={item.cantidad}
                    onChange={e => actualizarItem(idx, 'cantidad', Number(e.target.value) || 1)}
                    className="w-16 border border-slate-200 rounded-xl px-2 py-2 text-sm text-center bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                  />
                  <input
                    type="number"
                    min={0}
                    value={item.costo_unitario}
                    onChange={e => actualizarItem(idx, 'costo_unitario', Number(e.target.value) || 0)}
                    className="w-28 border border-slate-200 rounded-xl px-2 py-2 text-sm text-right bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                    placeholder="Costo"
                  />
                  <span className="w-28 text-sm font-semibold text-right text-slate-700 tabular-nums">
                    {formatGs(item.subtotal)}
                  </span>
                  <button
                    onClick={() => setItems(prev => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev)}
                    className="p-1 text-slate-400 hover:text-red-500 transition-colors cursor-pointer shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-200">
              <span className="text-sm font-semibold text-slate-600">Total</span>
              <span className="text-lg font-bold text-emerald-700 tabular-nums">{formatGs(total)}</span>
            </div>
          </div>
        </div>
      </Modal>

      {/* ── Pago modal ────────────────────────────────────────────── */}
      <Modal
        open={pagoModalOpen}
        title={`Registrar Pago — Compra #${pagoCompra?.id}`}
        onOk={handleSavePago}
        onCancel={() => setPagoModalOpen(false)}
        okText="Registrar Pago"
        confirmLoading={savingPago}
        width={440}
      >
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl px-4 py-3 flex justify-between items-center">
            <div>
              <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Proveedor</p>
              <p className="text-base font-semibold text-slate-800">{pagoCompra?.proveedor_nombre}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Saldo Pendiente</p>
              <p className="text-lg font-bold tabular-nums text-red-600">{formatGs(pagoCompra?.saldo_pendiente)}</p>
            </div>
          </div>

          <div>
            <label className={labelClass}>Monto a Pagar *</label>
            <input
              type="number"
              value={montoPago}
              onChange={e => setMontoPago(e.target.value)}
              placeholder="Guaraníes"
              min={1}
              step={1000}
              className={inputClass}
              autoFocus
            />
          </div>

          <div>
            <label className={labelClass}>Medio de Pago</label>
            <select value={medioPago} onChange={e => setMedioPago(e.target.value)} className={inputClass}>
              <option value="EFECTIVO">Efectivo</option>
              <option value="TRANSFERENCIA">Transferencia</option>
              <option value="CHEQUE">Cheque</option>
            </select>
          </div>

          <div>
            <label className={labelClass}>Observaciones</label>
            <textarea
              value={obsPago}
              onChange={e => setObsPago(e.target.value)}
              rows={2}
              placeholder="Opcional..."
              className={`${inputClass} resize-none`}
            />
          </div>
        </div>
      </Modal>

      {/* ── OC create/edit modal ─────────────────────────────────── */}
      <Modal
        open={ocModalOpen}
        title={editingOC ? `Editar OC #${editingOC.id}` : 'Nueva Orden de Compra'}
        onOk={handleSaveOC}
        onCancel={() => setOcModalOpen(false)}
        okText={editingOC ? 'Guardar Cambios' : 'Crear OC'}
        confirmLoading={savingOC}
        width={700}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Proveedor *</label>
              <Combobox
                options={proveedores.map(p => ({ value: p.id, label: p.razon_social }))}
                value={proveedorIdOC || undefined}
                onChange={v => setValueOC('proveedor_id', v as number)}
                filterLocal
                placeholder="Buscar proveedor..."
              />
              {ocErrors.proveedor_id && (
                <p className="text-xs text-red-500 mt-0.5">{ocErrors.proveedor_id.message}</p>
              )}
            </div>
            <div>
              <label className={labelClass}>Tipo de Pago</label>
              <select className={inputClass} {...registerOC('tipo_pago')}>
                <option value="CONTADO">Contado</option>
                <option value="CREDITO">Crédito</option>
              </select>
            </div>
          </div>

          <div>
            <label className={labelClass}>Nro. Factura Esperada</label>
            <input
              placeholder="001-001-0001234 (opcional)"
              className={inputClass}
              {...registerOC('nro_factura')}
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={`${labelClass} mb-0`}>Productos *</label>
              <Button size="sm" variant="ghost" onClick={() => setOcItems(prev => [...prev, { ...ITEM_EMPTY }])}>
                <Plus className="w-3.5 h-3.5" /> Agregar
              </Button>
            </div>
            <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
              {ocItems.map((item, idx) => (
                <div key={idx} className="flex gap-2 items-center bg-slate-50 rounded-xl px-3 py-2">
                  <div className="flex-1">
                    <Combobox
                      options={productos.map(p => ({ value: p.id, label: p.descripcion, data: p }))}
                      value={item.producto?.id}
                      onChange={(_, opt) => {
                        setOcItems(prev => prev.map((it, i) => {
                          if (i !== idx) return it
                          const p = opt.data as Producto
                          const costo = Number(p.precio_actual) || 0
                          return { ...it, producto: p, costo_unitario: costo, subtotal: it.cantidad * costo }
                        }))
                      }}
                      filterLocal
                      placeholder="Producto..."
                    />
                  </div>
                  <input
                    type="number" min={1} value={item.cantidad}
                    onChange={e => setOcItems(prev => prev.map((it, i) => {
                      if (i !== idx) return it
                      const cant = Number(e.target.value) || 1
                      return { ...it, cantidad: cant, subtotal: cant * it.costo_unitario }
                    }))}
                    className="w-16 border border-slate-200 rounded-xl px-2 py-2 text-sm text-center bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                  />
                  <input
                    type="number" min={0} value={item.costo_unitario}
                    onChange={e => setOcItems(prev => prev.map((it, i) => {
                      if (i !== idx) return it
                      const costo = Number(e.target.value) || 0
                      return { ...it, costo_unitario: costo, subtotal: it.cantidad * costo }
                    }))}
                    className="w-28 border border-slate-200 rounded-xl px-2 py-2 text-sm text-right bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                    placeholder="Costo"
                  />
                  <span className="w-28 text-sm font-semibold text-right text-slate-700 tabular-nums">
                    {formatGs(item.subtotal)}
                  </span>
                  <button
                    onClick={() => setOcItems(prev => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev)}
                    className="p-1 text-slate-400 hover:text-red-500 transition-colors cursor-pointer shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
            <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-200">
              <span className="text-sm font-semibold text-slate-600">Total estimado</span>
              <span className="text-lg font-bold text-emerald-700 tabular-nums">{formatGs(ocTotal)}</span>
            </div>
          </div>
        </div>
      </Modal>

      {/* ── OC detail modal ───────────────────────────────────────── */}
      {detailOC && (
        <Modal
          open
          title={`OC #${detailOC.id} — ${detailOC.proveedor_nombre}`}
          onCancel={() => setDetailOC(null)}
          width={680}
          footer={null}
        >
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {[
              { label: 'Total', value: formatGs(detailOC.monto_total) },
              { label: 'Tipo Pago', value: detailOC.tipo_pago },
              { label: 'Fecha', value: formatFecha(detailOC.fecha_creacion) },
              { label: 'Factura', value: detailOC.nro_factura_esperada || '—' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-50 rounded-xl px-3 py-3">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className="text-base font-bold mt-0.5 text-slate-800">{value}</p>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <Badge color={OC_ESTADO_COLOR[detailOC.estado] ?? 'default'}>
              {OC_ESTADO_LABEL[detailOC.estado] ?? detailOC.estado}
            </Badge>
            {detailOC.aprobado_por_nombre && (
              <span className="text-sm text-slate-500">Aprobado por: <strong>{detailOC.aprobado_por_nombre}</strong></span>
            )}
          </div>
          {detailOC.motivo_rechazo && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4">
              <p className="text-sm font-semibold text-red-700 mb-0.5">Motivo de rechazo</p>
              <p className="text-sm text-red-600">{detailOC.motivo_rechazo}</p>
            </div>
          )}
          {detailOC.observaciones && (
            <p className="text-sm text-slate-500 mb-4">Obs: {detailOC.observaciones}</p>
          )}

          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">Productos solicitados</h3>
          <div className="border border-slate-200 rounded-xl overflow-hidden mb-5">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-2 text-left text-sm font-semibold text-slate-500 uppercase">Producto</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Cant.</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Costo Unit.</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(detailOC.detalles ?? []).map(d => (
                  <tr key={d.id}>
                    <td className="px-4 py-2.5 text-slate-700">{d.producto_nombre}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">{d.cantidad}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">{formatGs(d.costo_unitario)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-slate-800">{formatGs(d.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <Button variant="secondary" onClick={() => setDetailOC(null)}>Cerrar</Button>
            <div className="flex items-center gap-2">
              {detailOC.estado === 'BORRADOR' && (
                <>
                  <Button variant="secondary" onClick={() => { setDetailOC(null); openEditOC(detailOC) }}>Editar</Button>
                  <Button variant="primary" disabled={accionOCLoading === detailOC.id}
                    onClick={() => handleOCAccion(detailOC, 'submit')}>
                    <Send className="w-4 h-4" /> Enviar a revisión
                  </Button>
                </>
              )}
              {detailOC.estado === 'PENDIENTE' && canApprove && (
                <>
                  <Button variant="secondary" onClick={() => { setDetailOC(null); setRechazarOC(detailOC); setMotivoRechazo('') }}>
                    <XCircle className="w-4 h-4" /> Rechazar
                  </Button>
                  <Button variant="primary" disabled={accionOCLoading === detailOC.id}
                    onClick={() => handleOCAccion(detailOC, 'aprobar')}>
                    <CheckCircle className="w-4 h-4" /> Aprobar
                  </Button>
                </>
              )}
              {detailOC.estado === 'APROBADA' && canApprove && (
                <Button variant="primary" disabled={accionOCLoading === detailOC.id}
                  onClick={() => handleOCAccion(detailOC, 'convertir')}>
                  <ArrowRightCircle className="w-4 h-4" /> Convertir en Compra
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* ── Rechazar OC modal ─────────────────────────────────────── */}
      <Modal
        open={!!rechazarOC}
        title={`Rechazar OC #${rechazarOC?.id}`}
        onOk={handleOCRechazar}
        onCancel={() => { setRechazarOC(null); setMotivoRechazo('') }}
        okText="Confirmar Rechazo"
        confirmLoading={savingRechazar}
        width={440}
      >
        <div className="space-y-3">
          <p className="text-sm text-slate-600">
            Vas a rechazar la OC de <strong>{rechazarOC?.proveedor_nombre}</strong> por{' '}
            <strong>{formatGs(rechazarOC?.monto_total)}</strong>.
          </p>
          <div>
            <label className={labelClass}>Motivo del rechazo *</label>
            <textarea
              value={motivoRechazo}
              onChange={e => setMotivoRechazo(e.target.value)}
              rows={3}
              placeholder="Explicá el motivo del rechazo..."
              className={`${inputClass} resize-none`}
              autoFocus
            />
          </div>
        </div>
      </Modal>

      {/* ── Cuenta corriente modal ────────────────────────────────── */}
      {ccProveedor && (
        <Modal
          open
          title={`Cuenta Corriente — ${ccProveedor.razon_social}`}
          onCancel={() => setCcProveedor(null)}
          width={700}
          footer={null}
        >
          <div className="bg-slate-50 rounded-xl px-4 py-3 flex justify-between items-center mb-4">
            <div>
              <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">RUC</p>
              <p className="text-base font-semibold text-slate-800">{ccProveedor.ruc}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Saldo Actual</p>
              <p className={`text-xl font-bold tabular-nums ${Number(ccProveedor.saldo_cuenta_corriente) > 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                {formatGs(ccProveedor.saldo_cuenta_corriente)}
              </p>
            </div>
          </div>
          {loadingCc ? (
            <div className="py-10 text-center text-slate-400 text-sm">Cargando...</div>
          ) : (
            <Table columns={colsCc} dataSource={cuentaCorriente} rowKey="id" pageSize={10} />
          )}
          <div className="flex justify-end mt-4">
            <Button variant="secondary" onClick={() => setCcProveedor(null)}>Cerrar</Button>
          </div>
        </Modal>
      )}
    </div>
  )
}
