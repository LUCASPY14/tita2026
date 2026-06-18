import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  BarChart2, Search, TrendingUp, ShoppingCart, FileText, Download,
  Users, AlertTriangle, UtensilsCrossed, Package, UserCheck, CreditCard,
  Trophy, ShoppingBag, ChevronDown, ChevronUp,
} from 'lucide-react'
import api from '../services/api'
import { exportarReporteVentasPDF, exportarCuentaCorrientePDF, exportarAlmuerzosPDF, exportarConsumoPDF } from '../utils/pdf'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface VentaTipo { tipo: string; cantidad: number; monto: number }

interface CierreCajaReporte {
  id: number; caja: string; fecha_apertura: string; fecha_cierre: string
  monto_inicial: number; monto_contado_fisico: number; diferencia: number
}

interface ReporteData {
  periodo: { desde: string; hasta: string }
  ventas: { cantidad: number; monto_total: number; por_tipo: VentaTipo[] }
  cierres_caja: CierreCajaReporte[]
}

interface AgingItem {
  cliente_id: number; cliente: string; ruc_ci: string; telefono: string
  email: string; saldo_deuda: number; dias_atraso: number; aging: string
}

interface CuentaCorrienteData {
  fecha: string
  resumen: {
    clientes_con_deuda: number; total_deuda: number
    aging: { '0-30': number; '31-60': number; '61-90': number; '90+': number }
  }
  detalle: AgingItem[]
}

interface AlmuerzoFila {
  hijo_id: number; hijo: string; grado: string; cantidad_almuerzos: number
  monto_total: number; monto_pagado: number; monto_pendiente: number; estado: string
}

interface AlmuerzosData {
  filas: AlmuerzoFila[]
  totales: {
    alumnos: number; cantidad_almuerzos: number; monto_total: number
    monto_pagado: number; monto_pendiente: number; con_deuda: number
  }
}

interface ProductoVenta {
  producto_id: number; descripcion: string; categoria: string
  total_cantidad: number; total_monto: number; num_ventas: number
}

type ProductoVentaRanked = ProductoVenta & { rank: number }

interface ProductosData {
  periodo: { desde: string; hasta: string }
  total_monto: number
  productos: ProductoVenta[]
}

interface CajeroVenta {
  cajero_id: number; username: string; nombre: string
  cantidad_ventas: number; monto_total: number; ticket_promedio: number
}

interface CajerosData {
  periodo: { desde: string; hasta: string }
  total_monto: number
  cajeros: CajeroVenta[]
}

interface ProductoStock {
  producto_id: number; descripcion: string; categoria: string; unidad: string
  stock_actual: number; stock_minimo: number; requiere_reposicion: boolean
  costo_promedio: number; valor_inventario: number; dias_stock: number | null
}

interface StockData {
  resumen: {
    total_productos: number; productos_bajo_minimo: number; valor_total_inventario: number
  }
  productos: ProductoStock[]
}

interface TarjetaReporte {
  nro_tarjeta: string; alumno: string; grado: string; saldo_actual: number
  total_recargado: number; total_consumido: number; num_recargas: number; num_consumos: number
}

interface TarjetasData {
  periodo: { desde: string | null; hasta: string | null }
  resumen: {
    total_tarjetas: number; saldo_total: number
    total_recargado: number; total_consumido: number
  }
  tarjetas: TarjetaReporte[]
}

interface DetalleConsumoRep {
  id: number
  producto_nombre: string
  cantidad: string
  precio_unitario: string
  subtotal: string
}
interface VentaConsumoRep {
  id: number
  fecha: string
  monto_total: string
  tarjeta: string | null
  hijo: number | null
  hijo_nombre: string | null
  hijo_grado: string | null
  cliente_nombre: string
  detalles: DetalleConsumoRep[]
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatGs(n: number | null | undefined): string {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

function formatFecha(iso: string): string {
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function descargaBlob(blob: Blob, nombre: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = nombre; a.click()
  window.URL.revokeObjectURL(url)
}

const TIPO_LABEL: Record<string, string> = {
  VENTA_TARJETA: 'Tarjeta prepago', VENTA_EFECTIVO: 'Efectivo',
  CONSUMO_ALMUERZO: 'Almuerzo', CARGA_SALDO: 'Carga de saldo',
}

const AGING_COLOR: Record<string, BadgeColor> = {
  '0-30': 'green', '31-60': 'yellow', '61-90': 'orange', '90+': 'red',
}

type TabKey = 'ventas' | 'cuenta_corriente' | 'almuerzos' | 'productos' | 'cajeros' | 'stock' | 'tarjetas' | 'consumo'

// ─── Shared sub-components (defined outside Reportes to satisfy react-hooks/static-components) ──

function KpiCard({ label, value, color = 'text-slate-800' }: { label: string; value: string | number; color?: string }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-4">
      <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
    </div>
  )
}

function FilterBar({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
      {children}
    </div>
  )
}

function EmptyState({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="text-center py-20 text-slate-400">
      <div className="w-12 h-12 mx-auto mb-3 opacity-30">{icon}</div>
      <p className="text-sm font-medium">{text}</p>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Reportes() {
  const { t } = useTranslation()
  const today = new Date().toISOString().split('T')[0]
  const hoy = new Date()
  const [tab, setTab] = useState<TabKey>('ventas')

  // ── Ventas ───────────────────────────────────────────────────────────────────
  const [desde, setDesde] = useState(today)
  const [hasta, setHasta] = useState(today)
  const [data, setData] = useState<ReporteData | null>(null)
  const [loading, setLoading] = useState(false)
  const [sortTipo, setSortTipo] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)
  const [sortCierres, setSortCierres] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)

  async function buscar() {
    if (!desde || !hasta) { toast.error('Seleccioná ambas fechas'); return }
    if (desde > hasta) { toast.error('La fecha Desde no puede ser mayor a Hasta'); return }
    setLoading(true)
    try {
      const { data: res } = await api.get('/contabilidad/reportes/', {
        params: { fecha_desde: desde, fecha_hasta: hasta },
      })
      setData(res)
    } catch { setData(null); toast.error('Error al cargar el reporte') }
    finally { setLoading(false) }
  }

  async function exportarCSV() {
    if (!desde || !hasta) { toast.error('Seleccioná un período primero'); return }
    try {
      const res = await api.get('/contabilidad/reportes/', {
        params: { fecha_desde: desde, fecha_hasta: hasta, formato: 'csv' },
        responseType: 'blob',
      })
      descargaBlob(res.data, `reporte_${desde}_${hasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  // ── Cuenta corriente ─────────────────────────────────────────────────────────
  const [ccData, setCcData] = useState<CuentaCorrienteData | null>(null)
  const [loadingCc, setLoadingCc] = useState(false)
  const [searchCc, setSearchCc] = useState('')
  const [sortDetalle, setSortDetalle] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)

  async function cargarCuentaCorriente() {
    setLoadingCc(true)
    try {
      const { data: res } = await api.get('/clientes/reporte-cuenta-corriente/')
      setCcData(res)
    } catch { toast.error('Error al cargar cuenta corriente') }
    finally { setLoadingCc(false) }
  }

  // ── Almuerzos ────────────────────────────────────────────────────────────────
  const [anioAlm, setAnioAlm] = useState(hoy.getFullYear())
  const [mesAlm, setMesAlm] = useState(hoy.getMonth() + 1)
  const [gradoAlm, setGradoAlm] = useState('')
  const [almuerzosData, setAlmuerzosData] = useState<AlmuerzosData | null>(null)
  const [loadingAlm, setLoadingAlm] = useState(false)

  async function cargarAlmuerzos() {
    setLoadingAlm(true)
    try {
      const { data: res } = await api.get('/almuerzos/reportes/', {
        params: { anio: anioAlm, mes: mesAlm, ...(gradoAlm ? { grado: gradoAlm } : {}) },
      })
      setAlmuerzosData(res)
    } catch { toast.error('Error al cargar reporte de almuerzos') }
    finally { setLoadingAlm(false) }
  }

  async function exportarAlmuerzosCSV() {
    try {
      const res = await api.get('/almuerzos/reportes/', {
        params: { anio: anioAlm, mes: mesAlm, ...(gradoAlm ? { grado: gradoAlm } : {}), formato: 'csv' },
        responseType: 'blob',
      })
      descargaBlob(res.data, `almuerzos_${anioAlm}_${String(mesAlm).padStart(2, '0')}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  function handleAlmuerzosPDF() {
    if (!almuerzosData) return
    try {
      exportarAlmuerzosPDF(almuerzosData.filas, almuerzosData.totales, anioAlm, mesAlm || undefined, gradoAlm || undefined)
      toast.success('PDF descargado')
    } catch { toast.error('Error al generar PDF') }
  }

  // ── Productos más vendidos ───────────────────────────────────────────────────
  const [desdeProd, setDesdeProd] = useState(today)
  const [hastaProd, setHastaProd] = useState(today)
  const [productosData, setProductosData] = useState<ProductosData | null>(null)
  const [loadingProd, setLoadingProd] = useState(false)

  async function buscarProductos() {
    if (!desdeProd || !hastaProd) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingProd(true)
    try {
      const { data: res } = await api.get('/ventas/reporte-productos/', {
        params: { desde: desdeProd, hasta: hastaProd },
      })
      setProductosData(res)
    } catch { setProductosData(null); toast.error('Error al cargar el reporte') }
    finally { setLoadingProd(false) }
  }

  async function exportarProductosCSV() {
    try {
      const res = await api.get('/ventas/reporte-productos/', {
        params: { desde: desdeProd, hasta: hastaProd, formato: 'csv' },
        responseType: 'blob',
      })
      descargaBlob(res.data, `ventas_producto_${desdeProd}_${hastaProd}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  // ── Ventas por cajero ───────────────────────────────────────────────────────
  const [desdeCaj, setDesdeCaj] = useState(today)
  const [hastaCaj, setHastaCaj] = useState(today)
  const [cajerosData, setCajerosData] = useState<CajerosData | null>(null)
  const [loadingCaj, setLoadingCaj] = useState(false)

  async function buscarCajeros() {
    if (!desdeCaj || !hastaCaj) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingCaj(true)
    try {
      const { data: res } = await api.get('/ventas/reporte-cajeros/', {
        params: { desde: desdeCaj, hasta: hastaCaj },
      })
      setCajerosData(res)
    } catch { setCajerosData(null); toast.error('Error al cargar el reporte') }
    finally { setLoadingCaj(false) }
  }

  async function exportarCajerosCSV() {
    try {
      const res = await api.get('/ventas/reporte-cajeros/', {
        params: { desde: desdeCaj, hasta: hastaCaj, formato: 'csv' },
        responseType: 'blob',
      })
      descargaBlob(res.data, `ventas_cajero_${desdeCaj}_${hastaCaj}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  // ── Inventario / Stock ──────────────────────────────────────────────────────
  const [stockData, setStockData] = useState<StockData | null>(null)
  const [loadingStock, setLoadingStock] = useState(false)
  const [searchStock, setSearchStock] = useState('')

  async function cargarStock() {
    setLoadingStock(true)
    try {
      const { data: res } = await api.get('/inventario/reporte-stock/')
      setStockData(res)
    } catch { setStockData(null); toast.error('Error al cargar inventario') }
    finally { setLoadingStock(false) }
  }

  async function exportarStockCSV() {
    try {
      const res = await api.get('/inventario/reporte-stock/', {
        params: { formato: 'csv' },
        responseType: 'blob',
      })
      descargaBlob(res.data, 'reporte_stock.csv')
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  // ── Tarjetas prepago ────────────────────────────────────────────────────────
  const [desdeTarj, setDesdeTarj] = useState('')
  const [hastaTarj, setHastaTarj] = useState('')
  const [tarjetasData, setTarjetasData] = useState<TarjetasData | null>(null)
  const [loadingTarj, setLoadingTarj] = useState(false)
  const [searchTarj, setSearchTarj] = useState('')

  async function cargarTarjetas() {
    setLoadingTarj(true)
    try {
      const params: Record<string, string> = {}
      if (desdeTarj) params.desde = desdeTarj
      if (hastaTarj) params.hasta = hastaTarj
      const { data: res } = await api.get('/core/reporte-tarjetas/', { params })
      setTarjetasData(res)
    } catch { setTarjetasData(null); toast.error('Error al cargar tarjetas') }
    finally { setLoadingTarj(false) }
  }

  async function exportarTarjetasCSV() {
    try {
      const params: Record<string, string> = { formato: 'csv' }
      if (desdeTarj) params.desde = desdeTarj
      if (hastaTarj) params.hasta = hastaTarj
      const res = await api.get('/core/reporte-tarjetas/', { params, responseType: 'blob' })
      const sufijo = desdeTarj && hastaTarj ? `_${desdeTarj}_${hastaTarj}` : ''
      descargaBlob(res.data, `reporte_tarjetas${sufijo}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  // ── Consumo por tarjeta ─────────────────────────────────────────────────────
  const [desdeConsumo, setDesdeConsumo] = useState(today)
  const [hastaConsumo, setHastaConsumo] = useState(today)
  const [tarjetaConsumo, setTarjetaConsumo] = useState('')
  const [consumos, setConsumos] = useState<VentaConsumoRep[]>([])
  const [totalConsumo, setTotalConsumo] = useState(0)
  const [loadingConsumo, setLoadingConsumo] = useState(false)
  const [loadingMoreConsumo, setLoadingMoreConsumo] = useState(false)
  const [pageConsumo, setPageConsumo] = useState(1)
  const [expandedConsumoId, setExpandedConsumoId] = useState<number | null>(null)
  const [consumoGenerated, setConsumoGenerated] = useState(false)
  const PAGE_CONSUMO = 30

  async function buscarConsumo() {
    if (!desdeConsumo || !hastaConsumo) { toast.error('Seleccioná ambas fechas'); return }
    if (desdeConsumo > hastaConsumo) { toast.error('La fecha Desde no puede ser mayor a Hasta'); return }
    setLoadingConsumo(true)
    setPageConsumo(1)
    setExpandedConsumoId(null)
    setConsumoGenerated(false)
    try {
      const params: Record<string, string | number> = {
        estado: 'ACTIVA', ordering: '-fecha', page: 1, page_size: PAGE_CONSUMO,
        fecha_desde: desdeConsumo, fecha_hasta: hastaConsumo,
      }
      if (tarjetaConsumo.trim()) params.tarjeta = tarjetaConsumo.trim()
      const { data: res } = await api.get('/ventas/ventas/', { params })
      setTotalConsumo(res.count ?? 0)
      setConsumos(res.results ?? [])
      setConsumoGenerated(true)
    } catch { toast.error('Error al cargar consumos') }
    finally { setLoadingConsumo(false) }
  }

  async function cargarMasConsumo() {
    const next = pageConsumo + 1
    setPageConsumo(next)
    setLoadingMoreConsumo(true)
    try {
      const params: Record<string, string | number> = {
        estado: 'ACTIVA', ordering: '-fecha', page: next, page_size: PAGE_CONSUMO,
        fecha_desde: desdeConsumo, fecha_hasta: hastaConsumo,
      }
      if (tarjetaConsumo.trim()) params.tarjeta = tarjetaConsumo.trim()
      const { data: res } = await api.get('/ventas/ventas/', { params })
      setConsumos(prev => [...prev, ...(res.results ?? [])])
    } catch { toast.error('Error al cargar más registros') }
    finally { setLoadingMoreConsumo(false) }
  }

  function exportarConsumoCSV() {
    if (!consumos.length) return
    const filas: string[][] = [
      ['Fecha', 'Alumno', 'Grado', 'Tarjeta', 'Producto', 'Cantidad', 'Precio Unit. (Gs)', 'Subtotal (Gs)', 'Total Venta (Gs)'],
    ]
    for (const v of consumos) {
      const alumno = v.hijo_nombre ?? v.cliente_nombre
      if (v.detalles.length === 0) {
        filas.push([formatFecha(v.fecha), alumno, v.hijo_grado ?? '', v.tarjeta ?? '', '—', '', '', '', v.monto_total])
      } else {
        for (const d of v.detalles) {
          filas.push([formatFecha(v.fecha), alumno, v.hijo_grado ?? '', v.tarjeta ?? '', d.producto_nombre, d.cantidad, d.precio_unitario, d.subtotal, v.monto_total])
        }
      }
    }
    const csv = filas.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
    descargaBlob(blob, `consumo_${desdeConsumo}_${hastaConsumo}.csv`)
    toast.success('CSV descargado')
  }

  const totalCargado = consumos.reduce((s, v) => s + Number(v.monto_total), 0)

  function handleConsumoPDF() {
    if (!consumos.length) return
    try {
      exportarConsumoPDF(
        consumos.map(v => ({
          fecha: v.fecha,
          alumno: v.hijo_nombre ?? v.cliente_nombre,
          grado: v.hijo_grado,
          tarjeta: v.tarjeta,
          monto_total: v.monto_total,
          detalles: v.detalles,
        })),
        desdeConsumo,
        hastaConsumo,
        tarjetaConsumo.trim() || undefined,
      )
      toast.success('PDF descargado')
    } catch { toast.error('Error al generar PDF') }
  }

  // ── Sort helper ──────────────────────────────────────────────────────────────
  function clientSort<T>(arr: T[], key: string, dir: 'asc' | 'desc'): T[] {
    return [...arr].sort((a, b) => {
      const av = (a as Record<string, unknown>)[key]
      const bv = (b as Record<string, unknown>)[key]
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === 'number' && typeof bv === 'number')
        return dir === 'asc' ? av - bv : bv - av
      return dir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    })
  }

  // ── Column definitions ───────────────────────────────────────────────────────

  const columnsTipo: Column<VentaTipo>[] = [
    {
      title: 'Tipo', key: 'tipo',
      render: (_, r) => <span className="text-sm font-medium text-slate-700">{TIPO_LABEL[r.tipo] ?? r.tipo}</span>,
    },
    {
      title: 'Cantidad', key: 'cantidad', dataIndex: 'cantidad', sortable: true,
      render: v => <span className="tabular-nums font-semibold text-slate-800">{v as number}</span>,
    },
    {
      title: 'Monto', key: 'monto', sortable: true,
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto)}</span>,
    },
  ]

  const columnsCierres: Column<CierreCajaReporte>[] = [
    { title: 'Caja', key: 'caja', dataIndex: 'caja' },
    {
      title: 'Apertura', key: 'fecha_apertura', sortable: true,
      render: (_, r) => <span className="text-sm text-slate-600">{formatFecha(r.fecha_apertura)}</span>,
    },
    {
      title: 'Cierre', key: 'fecha_cierre',
      render: (_, r) => <span className="text-sm text-slate-600">{formatFecha(r.fecha_cierre)}</span>,
    },
    {
      title: 'Inicial', key: 'monto_inicial',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.monto_inicial)}</span>,
    },
    {
      title: 'Contado', key: 'monto_contado_fisico',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.monto_contado_fisico)}</span>,
    },
    {
      title: 'Diferencia', key: 'diferencia', sortable: true,
      render: (_, r) => {
        const n = r.diferencia
        return <Badge color={n === 0 ? 'green' : n > 0 ? 'blue' : 'red'}>{n > 0 ? '+' : ''}{formatGs(n)}</Badge>
      },
    },
  ]

  const colsDetalle: Column<AgingItem>[] = [
    {
      title: 'Cliente', key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.cliente}</p>
          <p className="text-sm text-slate-400">{r.ruc_ci}</p>
        </div>
      ),
    },
    {
      title: 'Contacto', key: 'contacto',
      render: (_, r) => (
        <div>
          <p className="text-sm text-slate-500">{r.telefono || '—'}</p>
          <p className="text-sm text-slate-400">{r.email || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Saldo Deuda', key: 'saldo_deuda', sortable: true,
      render: (_, r) => <span className="tabular-nums font-bold text-red-600">{formatGs(r.saldo_deuda)}</span>,
    },
    {
      title: 'Días Atraso', key: 'dias_atraso', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums font-semibold text-sm ${r.dias_atraso > 60 ? 'text-red-600' : r.dias_atraso > 30 ? 'text-orange-600' : 'text-slate-700'}`}>
          {r.dias_atraso}d
        </span>
      ),
    },
    {
      title: 'Aging', key: 'aging',
      render: (_, r) => <Badge color={AGING_COLOR[r.aging] ?? 'default'}>{r.aging}</Badge>,
    },
  ]

  const ESTADO_ALM_COLOR: Record<string, BadgeColor> = {
    PAGADO: 'green', PARCIAL: 'blue', PENDIENTE: 'orange',
  }

  const colsAlmuerzos: Column<AlmuerzoFila>[] = [
    {
      title: 'Alumno', key: 'hijo',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.hijo}</p>
          <p className="text-sm text-slate-400">{r.grado || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Almuerzos', key: 'cantidad_almuerzos',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{r.cantidad_almuerzos}</span>,
    },
    {
      title: 'Total', key: 'monto_total',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'Pagado', key: 'monto_pagado',
      render: (_, r) => <span className="tabular-nums text-sm text-emerald-700 font-semibold">{formatGs(r.monto_pagado)}</span>,
    },
    {
      title: 'Pendiente', key: 'monto_pendiente',
      render: (_, r) => (
        <span className={`tabular-nums text-sm font-bold ${r.monto_pendiente > 0 ? 'text-red-600' : 'text-slate-400'}`}>
          {formatGs(r.monto_pendiente)}
        </span>
      ),
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_ALM_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
  ]

  const colsProductos: Column<ProductoVentaRanked>[] = [
    {
      title: '#', key: 'rank', dataIndex: 'rank',
      render: (v) => (
        <span className={`text-sm font-bold tabular-nums ${Number(v) <= 3 ? 'text-amber-600' : 'text-slate-400'}`}>
          {v as number}
        </span>
      ),
    },
    {
      title: 'Producto', key: 'descripcion',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.descripcion}</p>
          <p className="text-sm text-slate-400">{r.categoria || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Cantidad', key: 'total_cantidad', sortable: true,
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{r.total_cantidad}</span>,
    },
    {
      title: 'Nro Ventas', key: 'num_ventas', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{r.num_ventas}</span>,
    },
    {
      title: 'Total', key: 'total_monto', sortable: true,
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.total_monto)}</span>,
    },
  ]

  const colsCajeros: Column<CajeroVenta>[] = [
    {
      title: 'Cajero', key: 'nombre',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.nombre}</p>
          <p className="text-sm text-slate-400">@{r.username}</p>
        </div>
      ),
    },
    {
      title: 'Nro Ventas', key: 'cantidad_ventas', sortable: true,
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{r.cantidad_ventas}</span>,
    },
    {
      title: 'Total', key: 'monto_total', sortable: true,
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'Ticket Promedio', key: 'ticket_promedio', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-blue-700">{formatGs(r.ticket_promedio)}</span>,
    },
  ]

  const colsStock: Column<ProductoStock>[] = [
    {
      title: 'Producto', key: 'descripcion',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.descripcion}</p>
          <p className="text-sm text-slate-400">{r.categoria || '—'} {r.unidad ? `· ${r.unidad}` : ''}</p>
        </div>
      ),
    },
    {
      title: 'Stock', key: 'stock_actual', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums font-bold text-sm ${r.requiere_reposicion ? 'text-red-600' : 'text-slate-800'}`}>
          {r.stock_actual}
        </span>
      ),
    },
    {
      title: 'Mínimo', key: 'stock_minimo',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-500">{r.stock_minimo}</span>,
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => (
        <Badge color={r.requiere_reposicion ? 'red' : 'green'}>
          {r.requiere_reposicion ? 'Bajo mínimo' : 'OK'}
        </Badge>
      ),
    },
    {
      title: 'Costo Prom.', key: 'costo_promedio', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{formatGs(r.costo_promedio)}</span>,
    },
    {
      title: 'Valor Inv.', key: 'valor_inventario', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm font-semibold text-slate-800">{formatGs(r.valor_inventario)}</span>,
    },
    {
      title: 'Días Stock', key: 'dias_stock', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums text-sm ${r.dias_stock !== null && r.dias_stock < 7 ? 'text-red-600 font-bold' : 'text-slate-600'}`}>
          {r.dias_stock !== null ? `${r.dias_stock}d` : '—'}
        </span>
      ),
    },
  ]

  const colsTarjetas: Column<TarjetaReporte>[] = [
    {
      title: 'Alumno', key: 'alumno',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.alumno}</p>
          <p className="text-sm text-slate-400">{r.grado || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Saldo Actual', key: 'saldo_actual', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums font-bold text-sm ${r.saldo_actual < 0 ? 'text-red-600' : r.saldo_actual === 0 ? 'text-slate-400' : 'text-emerald-700'}`}>
          {formatGs(r.saldo_actual)}
        </span>
      ),
    },
    {
      title: 'Recargado', key: 'total_recargado', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-blue-700">{formatGs(r.total_recargado)}</span>,
    },
    {
      title: 'Consumido', key: 'total_consumido', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.total_consumido)}</span>,
    },
    {
      title: 'Recargas', key: 'num_recargas',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{r.num_recargas}</span>,
    },
    {
      title: 'Consumos', key: 'num_consumos',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{r.num_consumos}</span>,
    },
    {
      title: 'Tarjeta', key: 'nro_tarjeta',
      render: (_, r) => <span className="text-sm font-mono text-slate-400">{r.nro_tarjeta}</span>,
    },
  ]

  // ── Computed ─────────────────────────────────────────────────────────────────

  const tipoSorted = sortTipo && data ? clientSort(data.ventas.por_tipo, sortTipo.key, sortTipo.dir) : (data?.ventas.por_tipo ?? [])
  const cierresSorted = sortCierres && data ? clientSort(data.cierres_caja, sortCierres.key, sortCierres.dir) : (data?.cierres_caja ?? [])
  const ccDetalleFiltrado = (ccData?.detalle ?? []).filter(d =>
    !searchCc || d.cliente.toLowerCase().includes(searchCc.toLowerCase()) || d.ruc_ci.includes(searchCc)
  )
  const ccDetalleSorted = sortDetalle ? clientSort(ccDetalleFiltrado, sortDetalle.key, sortDetalle.dir) : ccDetalleFiltrado

  const productosRanked: ProductoVentaRanked[] = (productosData?.productos ?? []).map((p, i) => ({ ...p, rank: i + 1 }))

  const stockFiltrado = (stockData?.productos ?? []).filter(p =>
    !searchStock || p.descripcion.toLowerCase().includes(searchStock.toLowerCase()) || p.categoria.toLowerCase().includes(searchStock.toLowerCase())
  )
  const tarjetasFiltradas = (tarjetasData?.tarjetas ?? []).filter(t =>
    !searchTarj || t.alumno.toLowerCase().includes(searchTarj.toLowerCase()) || t.grado.toLowerCase().includes(searchTarj.toLowerCase())
  )

  // ── Styles ───────────────────────────────────────────────────────────────────

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const tabClass = (t: TabKey) =>
    `flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
      tab === t ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
    }`

  // ─── JSX ─────────────────────────────────────────────────────────────────────

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t('reportes.title')}</h1>
        <p className="text-base text-slate-500 mt-0.5">{t('reportes.subtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 overflow-x-auto">
        <div className="flex gap-0 min-w-max">
          <button onClick={() => setTab('ventas')} className={tabClass('ventas')}>
            <BarChart2 className="w-4 h-4" />Ventas y Cierres
          </button>
          <button onClick={() => { setTab('productos') }} className={tabClass('productos')}>
            <Trophy className="w-4 h-4" />Productos
          </button>
          <button onClick={() => { setTab('cajeros') }} className={tabClass('cajeros')}>
            <UserCheck className="w-4 h-4" />Cajeros
          </button>
          <button onClick={() => { setTab('cuenta_corriente'); if (!ccData && !loadingCc) cargarCuentaCorriente() }} className={tabClass('cuenta_corriente')}>
            <Users className="w-4 h-4" />Cuenta Corriente
          </button>
          <button onClick={() => { setTab('tarjetas') }} className={tabClass('tarjetas')}>
            <CreditCard className="w-4 h-4" />Tarjetas
          </button>
          <button onClick={() => { setTab('consumo') }} className={tabClass('consumo')}>
            <ShoppingBag className="w-4 h-4" />Consumo
          </button>
          <button onClick={() => { setTab('stock') }} className={tabClass('stock')}>
            <Package className="w-4 h-4" />Inventario
          </button>
          <button onClick={() => setTab('almuerzos')} className={tabClass('almuerzos')}>
            <UtensilsCrossed className="w-4 h-4" />Almuerzos
          </button>
        </div>
      </div>

      {/* ── Ventas y Cierres ─────────────────────────────────────────── */}
      {tab === 'ventas' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={desde} onChange={e => setDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} className={inputDateClass} />
            </div>
            <Button variant="primary" loading={loading} onClick={buscar}>
              <Search className="w-4 h-4" />Generar Reporte
            </Button>
            {data && (
              <>
                <Button variant="secondary" onClick={exportarCSV} disabled={loading}>
                  <Download className="w-4 h-4" />CSV
                </Button>
                <Button variant="secondary" onClick={() => exportarReporteVentasPDF(data, desde, hasta)} disabled={loading}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              </>
            )}
          </FilterBar>

          {data && (
            <div className="space-y-5">
              <p className="text-sm text-slate-500">
                Período: <span className="font-semibold text-slate-700">{data.periodo.desde} — {data.periodo.hasta}</span>
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-start gap-4">
                  <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center shrink-0">
                    <TrendingUp className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Total Vendido</p>
                    <p className="text-xl font-bold text-emerald-700 mt-0.5 tabular-nums">{formatGs(data.ventas.monto_total)}</p>
                  </div>
                </div>
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-start gap-4">
                  <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center shrink-0">
                    <ShoppingCart className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Ventas</p>
                    <p className="text-xl font-bold text-blue-700 mt-0.5 tabular-nums">{data.ventas.cantidad}</p>
                  </div>
                </div>
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-start gap-4">
                  <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Cierres de Caja</p>
                    <p className="text-xl font-bold text-purple-700 mt-0.5 tabular-nums">{data.cierres_caja.length}</p>
                  </div>
                </div>
              </div>

              {data.ventas.por_tipo.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100">
                    <h2 className="text-sm font-semibold text-slate-800">Ventas por Tipo</h2>
                  </div>
                  <div className="p-1">
                    <Table columns={columnsTipo} dataSource={tipoSorted} rowKey="tipo" pageSize={10}
                      sortKey={sortTipo?.key} sortDir={sortTipo?.dir}
                      onSort={(key, dir) => setSortTipo({ key, dir })} />
                  </div>
                </div>
              )}

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">Cierres de Caja ({data.cierres_caja.length})</h2>
                </div>
                <div className="p-1">
                  {data.cierres_caja.length === 0
                    ? <p className="text-center text-slate-400 text-sm py-10">No hay cierres en este período.</p>
                    : <Table columns={columnsCierres} dataSource={cierresSorted} rowKey="id" pageSize={10}
                        sortKey={sortCierres?.key} sortDir={sortCierres?.dir}
                        onSort={(key, dir) => setSortCierres({ key, dir })} />
                  }
                </div>
              </div>
            </div>
          )}
          {!data && !loading && <EmptyState icon={<BarChart2 className="w-full h-full" />} text="Seleccioná un período y generá el reporte" />}
        </>
      )}

      {/* ── Productos más vendidos ──────────────────────────────────── */}
      {tab === 'productos' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={desdeProd} onChange={e => setDesdeProd(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={hastaProd} onChange={e => setHastaProd(e.target.value)} className={inputDateClass} />
            </div>
            <Button variant="primary" loading={loadingProd} onClick={buscarProductos}>
              <Search className="w-4 h-4" />Generar Reporte
            </Button>
            {productosData && (
              <>
                <Button variant="secondary" onClick={exportarProductosCSV} disabled={loadingProd}>
                  <Download className="w-4 h-4" />CSV
                </Button>
                <Button variant="secondary" disabled={loadingProd} onClick={async () => {
                  try {
                    const res = await api.get('/ventas/reporte-productos/', {
                      params: { desde: desdeProd, hasta: hastaProd, formato: 'pdf' },
                      responseType: 'blob',
                    })
                    descargaBlob(res.data, `ventas_productos_${desdeProd}_${hastaProd}.pdf`)
                    toast.success('PDF descargado')
                  } catch { toast.error('Error al generar PDF') }
                }}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              </>
            )}
          </FilterBar>

          {productosData && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <KpiCard label="Total Vendido" value={formatGs(productosData.total_monto)} color="text-emerald-700" />
                <KpiCard label="Productos distintos" value={productosData.productos.length} />
                <KpiCard label="Período" value={`${productosData.periodo.desde} — ${productosData.periodo.hasta}`} />
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">Ranking de productos</h2>
                  <p className="text-sm text-slate-400 mt-0.5">Ordenado por monto vendido</p>
                </div>
                <div className="p-1">
                  <Table columns={colsProductos} dataSource={productosRanked} rowKey="producto_id" pageSize={20} />
                </div>
              </div>
            </div>
          )}
          {!productosData && !loadingProd && <EmptyState icon={<Trophy className="w-full h-full" />} text="Seleccioná un período y generá el reporte" />}
        </>
      )}

      {/* ── Ventas por cajero ────────────────────────────────────────── */}
      {tab === 'cajeros' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={desdeCaj} onChange={e => setDesdeCaj(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={hastaCaj} onChange={e => setHastaCaj(e.target.value)} className={inputDateClass} />
            </div>
            <Button variant="primary" loading={loadingCaj} onClick={buscarCajeros}>
              <Search className="w-4 h-4" />Generar Reporte
            </Button>
            {cajerosData && (
              <>
                <Button variant="secondary" onClick={exportarCajerosCSV} disabled={loadingCaj}>
                  <Download className="w-4 h-4" />CSV
                </Button>
                <Button variant="secondary" disabled={loadingCaj} onClick={async () => {
                  try {
                    const res = await api.get('/ventas/reporte-cajeros/', {
                      params: { desde: desdeCaj, hasta: hastaCaj, formato: 'pdf' },
                      responseType: 'blob',
                    })
                    descargaBlob(res.data, `ventas_cajeros_${desdeCaj}_${hastaCaj}.pdf`)
                    toast.success('PDF descargado')
                  } catch { toast.error('Error al generar PDF') }
                }}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              </>
            )}
          </FilterBar>

          {cajerosData && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <KpiCard label="Total Vendido" value={formatGs(cajerosData.total_monto)} color="text-emerald-700" />
                <KpiCard label="Cajeros activos" value={cajerosData.cajeros.length} />
                <KpiCard label="Período" value={`${cajerosData.periodo.desde} — ${cajerosData.periodo.hasta}`} />
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">Rendimiento por cajero</h2>
                </div>
                <div className="p-1">
                  <Table columns={colsCajeros} dataSource={cajerosData.cajeros} rowKey="cajero_id" pageSize={20} />
                </div>
              </div>
            </div>
          )}
          {!cajerosData && !loadingCaj && <EmptyState icon={<UserCheck className="w-full h-full" />} text="Seleccioná un período y generá el reporte" />}
        </>
      )}

      {/* ── Cuenta corriente ──────────────────────────────────────────── */}
      {tab === 'cuenta_corriente' && (
        <>
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <Button variant="secondary" loading={loadingCc} onClick={cargarCuentaCorriente}>
              <Search className="w-4 h-4" />Actualizar
            </Button>
            <div className="flex items-center gap-3">
              {ccData && <p className="text-sm text-slate-400">Generado: {new Date(ccData.fecha).toLocaleString('es-PY')}</p>}
              {ccData && ccDetalleSorted.length > 0 && (
                <Button variant="secondary" onClick={() => exportarCuentaCorrientePDF(ccDetalleSorted, ccData.resumen.total_deuda, ccData.fecha)}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              )}
            </div>
          </div>

          {loadingCc && !ccData && <div className="text-center py-20 text-slate-400"><p className="text-sm">Cargando reporte...</p></div>}

          {ccData && (
            <div className="space-y-5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard label="Total Deuda" value={formatGs(ccData.resumen.total_deuda)} color="text-red-700" />
                <KpiCard label="Clientes con Deuda" value={String(ccData.resumen.clientes_con_deuda)} />
                <KpiCard label="0–30 días" value={formatGs(ccData.resumen.aging['0-30'])} color="text-green-700" />
                <KpiCard label="90+ días" value={formatGs(ccData.resumen.aging['90+'])} color="text-red-600" />
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Distribución por Aging</h3>
                <div className="grid grid-cols-4 gap-3">
                  {Object.entries(ccData.resumen.aging).map(([rango, monto]) => (
                    <div key={rango} className="text-center">
                      <p className="text-sm text-slate-400">{rango} días</p>
                      <p className={`text-sm font-bold tabular-nums mt-0.5 ${
                        rango === '90+' ? 'text-red-600' : rango === '61-90' ? 'text-orange-600' : rango === '31-60' ? 'text-yellow-600' : 'text-green-700'
                      }`}>{formatGs(monto)}</p>
                    </div>
                  ))}
                </div>
              </div>

              {ccData.resumen.aging['90+'] > 0 && (
                <div className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-2xl px-5 py-3">
                  <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
                  <p className="text-sm text-red-700">
                    <span className="font-semibold">{formatGs(ccData.resumen.aging['90+'])}</span> en deudas con más de 90 días de atraso.
                  </p>
                </div>
              )}

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-800">Detalle de Cuenta Corriente</h2>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                    <input
                      placeholder="Filtrar cliente..."
                      value={searchCc}
                      onChange={e => setSearchCc(e.target.value)}
                      className="border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-48"
                    />
                  </div>
                </div>
                <div className="p-1">
                  <Table columns={colsDetalle} dataSource={ccDetalleSorted} rowKey="cliente_id" pageSize={15}
                    sortKey={sortDetalle?.key} sortDir={sortDetalle?.dir}
                    onSort={(key, dir) => setSortDetalle({ key, dir })} />
                </div>
              </div>
            </div>
          )}
          {!ccData && !loadingCc && <EmptyState icon={<Users className="w-full h-full" />} text='Hacé clic en "Actualizar" para cargar el reporte' />}
        </>
      )}

      {/* ── Tarjetas prepago ──────────────────────────────────────────── */}
      {tab === 'tarjetas' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde (opcional)</label>
              <input type="date" value={desdeTarj} onChange={e => setDesdeTarj(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta (opcional)</label>
              <input type="date" value={hastaTarj} onChange={e => setHastaTarj(e.target.value)} className={inputDateClass} />
            </div>
            <Button variant="primary" loading={loadingTarj} onClick={cargarTarjetas}>
              <Search className="w-4 h-4" />Generar Reporte
            </Button>
            {tarjetasData && (
              <>
                <Button variant="secondary" onClick={exportarTarjetasCSV} disabled={loadingTarj}>
                  <Download className="w-4 h-4" />CSV
                </Button>
                <Button variant="secondary" disabled={loadingTarj} onClick={async () => {
                  try {
                    const params: Record<string, string> = { formato: 'pdf' }
                    if (desdeTarj) params.desde = desdeTarj
                    if (hastaTarj) params.hasta = hastaTarj
                    const res = await api.get('/core/reporte-tarjetas/', { params, responseType: 'blob' })
                    const sufijo = desdeTarj && hastaTarj ? `_${desdeTarj}_${hastaTarj}` : ''
                    descargaBlob(res.data, `reporte_tarjetas${sufijo}.pdf`)
                    toast.success('PDF descargado')
                  } catch { toast.error('Error al generar PDF') }
                }}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              </>
            )}
          </FilterBar>

          {!desdeTarj && !hastaTarj && !tarjetasData && (
            <p className="text-sm text-slate-400 -mt-2">Sin período: se muestran solo saldos actuales sin detalle de movimientos.</p>
          )}

          {tarjetasData && (
            <div className="space-y-5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard label="Tarjetas activas" value={tarjetasData.resumen.total_tarjetas} />
                <KpiCard label="Saldo total" value={formatGs(tarjetasData.resumen.saldo_total)} color="text-emerald-700" />
                <KpiCard label="Total recargado" value={formatGs(tarjetasData.resumen.total_recargado)} color="text-blue-700" />
                <KpiCard label="Total consumido" value={formatGs(tarjetasData.resumen.total_consumido)} color="text-slate-700" />
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-800">
                    Tarjetas ({tarjetasData.resumen.total_tarjetas})
                    {tarjetasData.periodo.desde && (
                      <span className="text-sm text-slate-400 font-normal ml-2">
                        {tarjetasData.periodo.desde} — {tarjetasData.periodo.hasta}
                      </span>
                    )}
                  </h2>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                    <input
                      placeholder="Filtrar alumno/grado..."
                      value={searchTarj}
                      onChange={e => setSearchTarj(e.target.value)}
                      className="border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-52"
                    />
                  </div>
                </div>
                <div className="p-1">
                  <Table columns={colsTarjetas} dataSource={tarjetasFiltradas} rowKey="nro_tarjeta" pageSize={20} />
                </div>
              </div>
            </div>
          )}
          {!tarjetasData && !loadingTarj && <EmptyState icon={<CreditCard className="w-full h-full" />} text='Hacé clic en "Generar Reporte" para cargar tarjetas' />}
        </>
      )}

      {/* ── Inventario / Stock ────────────────────────────────────────── */}
      {tab === 'stock' && (
        <>
          <div className="flex items-center gap-3 flex-wrap">
            <Button variant="primary" loading={loadingStock} onClick={cargarStock}>
              <Search className="w-4 h-4" />Cargar Inventario
            </Button>
            {stockData && (
              <>
                <Button variant="secondary" onClick={exportarStockCSV} disabled={loadingStock}>
                  <Download className="w-4 h-4" />CSV
                </Button>
                <Button variant="secondary" disabled={loadingStock} onClick={async () => {
                  try {
                    const res = await api.get('/inventario/reporte-stock/', {
                      params: { formato: 'pdf' },
                      responseType: 'blob',
                    })
                    descargaBlob(res.data, 'reporte_stock.pdf')
                    toast.success('PDF descargado')
                  } catch { toast.error('Error al generar PDF') }
                }}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              </>
            )}
          </div>

          {stockData && (
            <div className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <KpiCard label="Total productos" value={stockData.resumen.total_productos} />
                <KpiCard
                  label="Bajo mínimo"
                  value={stockData.resumen.productos_bajo_minimo}
                  color={stockData.resumen.productos_bajo_minimo > 0 ? 'text-red-600' : 'text-emerald-700'}
                />
                <KpiCard label="Valor total inventario" value={formatGs(stockData.resumen.valor_total_inventario)} color="text-slate-800" />
              </div>

              {stockData.resumen.productos_bajo_minimo > 0 && (
                <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-2xl px-5 py-3">
                  <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                  <p className="text-sm text-amber-800">
                    <span className="font-semibold">{stockData.resumen.productos_bajo_minimo} productos</span> con stock por debajo del mínimo configurado.
                  </p>
                </div>
              )}

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-slate-800">Inventario completo</h2>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                    <input
                      placeholder="Filtrar producto/categoría..."
                      value={searchStock}
                      onChange={e => setSearchStock(e.target.value)}
                      className="border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-52"
                    />
                  </div>
                </div>
                <div className="p-1">
                  <Table columns={colsStock} dataSource={stockFiltrado} rowKey="producto_id" pageSize={20} />
                </div>
              </div>
            </div>
          )}
          {!stockData && !loadingStock && <EmptyState icon={<Package className="w-full h-full" />} text='Hacé clic en "Cargar Inventario"' />}
        </>
      )}

      {/* ── Almuerzos ────────────────────────────────────────────────── */}
      {tab === 'almuerzos' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Año</label>
              <input
                type="number" min={2020} max={2099} value={anioAlm}
                onChange={e => setAnioAlm(Number(e.target.value))}
                className={`${inputDateClass} w-24`}
              />
            </div>
            <div>
              <label className={labelClass}>Mes</label>
              <select value={mesAlm} onChange={e => setMesAlm(Number(e.target.value))} className={`${inputDateClass} w-auto`}>
                {['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                  'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'].map((m, i) => (
                  <option key={i + 1} value={i + 1}>{m}</option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Grado</label>
              <input
                placeholder="Filtrar por grado..."
                value={gradoAlm}
                onChange={e => setGradoAlm(e.target.value)}
                className={`${inputDateClass} w-40`}
              />
            </div>
            <Button variant="primary" onClick={cargarAlmuerzos} disabled={loadingAlm}>
              <TrendingUp className="w-4 h-4" />{loadingAlm ? 'Cargando...' : 'Buscar'}
            </Button>
            {almuerzosData && (
              <>
                <Button variant="secondary" onClick={exportarAlmuerzosCSV}>
                  <Download className="w-4 h-4" />CSV
                </Button>
                <Button variant="secondary" onClick={handleAlmuerzosPDF}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              </>
            )}
          </FilterBar>

          {almuerzosData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {[
                  { label: 'Alumnos', value: almuerzosData.totales.alumnos },
                  { label: 'Almuerzos', value: almuerzosData.totales.cantidad_almuerzos },
                  { label: 'Total', value: formatGs(almuerzosData.totales.monto_total) },
                  { label: 'Pagado', value: formatGs(almuerzosData.totales.monto_pagado) },
                  { label: 'Pendiente', value: formatGs(almuerzosData.totales.monto_pendiente) },
                  { label: 'Con deuda', value: almuerzosData.totales.con_deuda },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-3 py-3 text-center">
                    <p className="text-sm font-semibold text-slate-400 uppercase tracking-wide">{label}</p>
                    <p className="text-sm font-bold text-slate-800 mt-0.5 tabular-nums">{value}</p>
                  </div>
                ))}
              </div>
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="p-1">
                  <Table columns={colsAlmuerzos} dataSource={almuerzosData.filas} rowKey="hijo_id"
                    loading={loadingAlm} pageSize={almuerzosData.filas.length} />
                </div>
              </div>
            </>
          )}
          {!almuerzosData && !loadingAlm && <EmptyState icon={<UtensilsCrossed className="w-full h-full" />} text='Seleccioná año y mes, luego hacé clic en "Buscar"' />}
        </>
      )}

      {/* ── Consumo por tarjeta ───────────────────────────────────────── */}
      {tab === 'consumo' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={desdeConsumo} onChange={e => setDesdeConsumo(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={hastaConsumo} onChange={e => setHastaConsumo(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Tarjeta (opcional)</label>
              <input
                placeholder="Nro. de tarjeta..."
                value={tarjetaConsumo}
                onChange={e => setTarjetaConsumo(e.target.value)}
                className={`${inputDateClass} w-44`}
              />
            </div>
            <Button variant="primary" loading={loadingConsumo} onClick={buscarConsumo}>
              <Search className="w-4 h-4" />Generar Reporte
            </Button>
            {consumos.length > 0 && (
              <>
                <Button variant="secondary" onClick={exportarConsumoCSV} disabled={loadingConsumo}>
                  <Download className="w-4 h-4" />CSV
                </Button>
                <Button variant="secondary" onClick={handleConsumoPDF} disabled={loadingConsumo}>
                  <FileText className="w-4 h-4" />PDF
                </Button>
              </>
            )}
          </FilterBar>

          {consumoGenerated && (
            <div className="space-y-4">
              {/* KPIs */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <KpiCard label="Total en período" value={`${totalConsumo} compras`} />
                <KpiCard
                  label={`Total cargado (${consumos.length} reg.)`}
                  value={formatGs(totalCargado)}
                  color="text-emerald-700"
                />
                <KpiCard
                  label="Filtro activo"
                  value={tarjetaConsumo.trim() ? `Tarjeta: ${tarjetaConsumo.trim()}` : `${desdeConsumo} — ${hastaConsumo}`}
                />
              </div>

              {consumos.length === 0 ? (
                <EmptyState icon={<ShoppingBag className="w-full h-full" />} text="Sin consumos en el período seleccionado" />
              ) : (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100">
                    <h2 className="text-sm font-semibold text-slate-800">
                      {`Detalle de consumos — ${desdeConsumo} al ${hastaConsumo}`}
                    </h2>
                  </div>
                  <ul className="divide-y divide-slate-100">
                    {consumos.map(v => {
                      const isExp = expandedConsumoId === v.id
                      const alumno = v.hijo_nombre ?? v.cliente_nombre
                      return (
                        <li key={v.id}>
                          <button
                            type="button"
                            onClick={() => setExpandedConsumoId(isExp ? null : v.id)}
                            className="w-full flex items-center gap-4 px-5 py-3.5 text-left hover:bg-slate-50 transition-colors group"
                          >
                            <div className="w-8 h-8 rounded-full bg-green-50 border border-green-100 flex items-center justify-center shrink-0">
                              <ShoppingBag className="w-3.5 h-3.5 text-green-600" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-semibold text-slate-800 truncate">
                                {alumno}
                                {v.hijo_grado && (
                                  <span className="ml-1.5 text-slate-400 font-normal">{v.hijo_grado}</span>
                                )}
                              </p>
                              <p className="text-xs text-slate-400 mt-0.5">
                                {`${formatFecha(v.fecha)}${v.tarjeta ? ` · ${v.tarjeta}` : ''}`}
                              </p>
                            </div>
                            <div className="flex items-center gap-3 shrink-0">
                              <span className="text-sm font-bold tabular-nums text-slate-800">
                                {formatGs(Number(v.monto_total))}
                              </span>
                              {isExp
                                ? <ChevronUp className="w-4 h-4 text-slate-400" />
                                : <ChevronDown className="w-4 h-4 text-slate-400" />}
                            </div>
                          </button>
                          {isExp && v.detalles.length > 0 && (
                            <ul className="px-5 pb-3 ml-12 space-y-1.5">
                              {v.detalles.map(d => (
                                <li key={d.id} className="flex items-center justify-between text-sm text-slate-600">
                                  <span>
                                    <span className="font-semibold text-slate-700 tabular-nums">{d.cantidad}×</span>
                                    {' '}{d.producto_nombre}
                                    <span className="text-slate-400 ml-1.5">{`${formatGs(Number(d.precio_unitario))} c/u`}</span>
                                  </span>
                                  <span className="tabular-nums font-semibold text-slate-700 shrink-0">
                                    {formatGs(Number(d.subtotal))}
                                  </span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </li>
                      )
                    })}
                  </ul>
                  {consumos.length < totalConsumo && (
                    <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between">
                      <p className="text-sm text-slate-400">
                        {`Mostrando ${consumos.length} de ${totalConsumo}`}
                      </p>
                      <Button variant="secondary" loading={loadingMoreConsumo} onClick={cargarMasConsumo}>
                        Ver más
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          {!consumoGenerated && !loadingConsumo && (
            <EmptyState icon={<ShoppingBag className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Generar Reporte"' />
          )}
        </>
      )}
    </div>
  )
}
