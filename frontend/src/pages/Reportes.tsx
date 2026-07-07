import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  BarChart2, Search, TrendingUp, ShoppingCart, FileText, Download,
  Users, AlertTriangle, UtensilsCrossed, Package, UserCheck, CreditCard,
  Trophy, ShoppingBag, ChevronDown, ChevronUp,
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
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

interface TendenciaPoint {
  fecha: string
  cantidad: number
  monto: number
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

const CHART_COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#8b5cf6', '#ec4899', '#14b8a6']

function fmtGsShort(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
  return String(n)
}

type TabKey = 'ventas' | 'cuenta_corriente' | 'almuerzos' | 'productos' | 'cajeros' | 'stock' | 'tarjetas' | 'consumo' | 'notas_credito' | 'aging_proveedores' | 'compras_proveedores' | 'diferencias_caja' | 'medios_pago' | 'consumo_grado' | 'cobranza_almuerzos' | 'auditoria' | 'intentos_login' | 'personal_inactivo'

// ─── Consumo por Grado ───────────────────────────────────────────────────────

interface ConsumoGradoFila {
  grado: string; nivel: number
  n_consumos: number; n_rechazados: number; n_anulados: number
  tasa_rechazo: number; monto_total: number
}

interface HorarioPico { hora: number; n: number }

interface ConsumoGradoData {
  periodo: { desde: string; hasta: string }
  resumen: { total_consumos: number; total_rechazados: number; tasa_rechazo_global: number }
  por_grado: ConsumoGradoFila[]
  horarios_pico: HorarioPico[]
}

// ─── Cobranza Almuerzos ──────────────────────────────────────────────────────

interface CobranzaMesFila {
  mes: number; mes_nombre: string
  n_alumnos: number; pagados: number; parciales: number; pendientes: number
  monto_total: number; monto_cobrado: number; monto_pendiente: number; tasa_cobro: number
}

interface CobranzaFormaFila {
  forma_cobro: string; n_cuentas: number; monto_total: number; monto_cobrado: number
}

interface CobranzaAlmuerzosData {
  anio: number
  resumen: { monto_anual: number; cobrado_anual: number; pendiente_anual: number; tasa_cobro_anual: number; meses_con_datos: number }
  por_mes: CobranzaMesFila[]
  por_forma_cobro: CobranzaFormaFila[]
}

// ─── Compras / Proveedores ───────────────────────────────────────────────────

interface CompraProveedorFila {
  proveedor_id: number; proveedor: string; ruc: string
  n_compras: number; monto_total: number
  entregadas: number; entrega_parcial: number; entrega_pendiente: number; tasa_entrega: number
  pagadas: number; pago_parcial: number; pago_pendiente: number
}

interface FunnelOC { BORRADOR: number; PENDIENTE: number; APROBADA: number; RECHAZADA: number; CONVERTIDA: number; total: number }

interface ComprasProveedoresData {
  periodo: { desde: string; hasta: string }
  resumen: { total_compras: number; monto_total: number; n_proveedores: number }
  por_proveedor: CompraProveedorFila[]
  funnel_oc: FunnelOC
}

// ─── Diferencias de Caja ─────────────────────────────────────────────────────

interface DiferenciaEmpleado {
  empleado_id: number; empleado: string
  n_cierres: number; diferencia_total: number; diferencia_promedio: number; mayor_diferencia: number
}

interface TendenciaDiferencia { fecha: string; diferencia: number; empleado: string; caja: string; cierre_id: number }

interface DiferenciasCajaData {
  periodo: { desde: string; hasta: string }
  resumen: { total_diferencia: number; n_cierres: number; n_positivos: number; n_negativos: number; n_cero: number }
  por_empleado: DiferenciaEmpleado[]
  tendencia: TendenciaDiferencia[]
}

// ─── Medios de Pago ──────────────────────────────────────────────────────────

interface MedioPagoFila {
  medio_pago_id: number; descripcion: string
  n_pagos: number; monto_total: number
  n_conciliados: number; monto_conciliado: number
  n_pendientes: number; monto_pendiente: number
}

interface MediosPagoData {
  periodo: { desde: string; hasta: string }
  resumen: { total_pagos: number; monto_total: number; n_medios: number }
  por_medio_pago: MedioPagoFila[]
}

// ─── Notas de Crédito ────────────────────────────────────────────────────────

interface NCResumen {
  total_emitidas: number; total_aplicadas: number; total_anuladas: number
  monto_emitidas: number; monto_aplicadas: number; monto_anuladas: number
  monto_total: number
}

interface NCVentaFila {
  id: number; nro_nota_credito: string; fecha_emision: string
  cliente_id: number; cliente: string; ruc_ci: string
  estado: string; motivo: string; monto_total: number
  empleado_autoriza: string; venta_origen_id: number | null
}

interface NCCompraFila {
  id: number; fecha: string
  proveedor_id: number; proveedor: string; ruc: string
  estado: string; observacion: string; nro_factura_compra: string
  monto_total: number; creado_por: string; compra_original_id: number | null
}

interface NCVentaData { periodo: { desde: string; hasta: string }; resumen: NCResumen; detalle: NCVentaFila[] }
interface NCCompraData { periodo: { desde: string; hasta: string }; resumen: NCResumen; detalle: NCCompraFila[] }

// ─── Aging Proveedores ───────────────────────────────────────────────────────

interface AgingProveedorItem {
  proveedor_id: number; proveedor: string; ruc: string; telefono: string
  email: string; saldo_deuda: number; dias_atraso: number; aging: string
}

interface AgingProveedoresData {
  fecha: string
  resumen: {
    proveedores_con_deuda: number; total_deuda: number
    aging: { '0-30': number; '31-60': number; '61-90': number; '90+': number }
  }
  detalle: AgingProveedorItem[]
}

// ─── Auditoría ───────────────────────────────────────────────────────────────

interface AuditoriaResultado { resultado: string; count: number }
interface AuditoriaTop { operacion?: string; tabla_afectada?: string; count: number }
interface AuditoriaFila {
  id_auditoria: number; fecha_operacion: string; usuario__email: string | null
  operacion: string; tabla_afectada: string | null; id_registro: number | null
  resultado: string; ip_address: string | null; descripcion: string | null; mensaje_error: string | null
}
interface AuditoriaData {
  resumen: {
    total: number
    por_resultado: AuditoriaResultado[]
    top_operaciones: AuditoriaTop[]
    top_tablas: AuditoriaTop[]
  }
  detalle: AuditoriaFila[]
}

// ─── Intentos de Login ───────────────────────────────────────────────────────

interface IntentoPorIp { ip_address: string; n_fallidos: number }
interface IntentoPorEmail { email: string; n_fallidos: number }
interface IntentoPorMotivo { motivo_fallo: string; count: number }
interface IntentoTendencia { fecha: string; total: number; fallidos: number; exitosos: number }
interface IntentosLoginData {
  resumen: { total: number; fallidos: number; exitosos: number; tasa_fallo: number }
  por_ip: IntentoPorIp[]
  por_email: IntentoPorEmail[]
  por_motivo: IntentoPorMotivo[]
  tendencia: IntentoTendencia[]
}

// ─── Personal Inactivo ───────────────────────────────────────────────────────

interface PersonalPorRol { rol: string; total: number; activos: number; sin_acceso: number }
interface PersonalFila {
  id: number; email: string; nombre: string; apellido: string; rol: string
  ultimo_acceso: string | null; fecha_creacion: string
}
interface PersonalInactivoData {
  resumen: { total: number; activos: number; inactivos: number; sin_acceso: number; n_dias: number }
  por_rol: PersonalPorRol[]
  detalle: PersonalFila[]
}

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
  const [tendencia, setTendencia] = useState<TendenciaPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [sortTipo, setSortTipo] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)
  const [sortCierres, setSortCierres] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)

  async function buscar() {
    if (!desde || !hasta) { toast.error('Seleccioná ambas fechas'); return }
    if (desde > hasta) { toast.error('La fecha Desde no puede ser mayor a Hasta'); return }
    setLoading(true)
    try {
      const [repRes, tendRes] = await Promise.all([
        api.get('/contabilidad/reportes/', { params: { fecha_desde: desde, fecha_hasta: hasta } }),
        api.get('/contabilidad/dashboard/tendencia/', { params: { desde, hasta } }),
      ])
      setData(repRes.data)
      setTendencia(tendRes.data?.data ?? [])
    } catch { setData(null); setTendencia([]); toast.error('Error al cargar el reporte') }
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

  async function exportarCuentaCorrienteCSV() {
    try {
      const res = await api.get('/clientes/reporte-cuenta-corriente/', {
        params: { formato: 'csv' },
        responseType: 'blob',
      })
      const hoy2 = new Date().toISOString().split('T')[0]
      descargaBlob(res.data, `cuenta_corriente_${hoy2}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
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

  // ── Notas de Crédito ─────────────────────────────────────────────────────────
  const hoyStr = today
  const [ncDesde, setNcDesde] = useState(hoyStr.slice(0, 7) + '-01')
  const [ncHasta, setNcHasta] = useState(hoyStr)
  const [ncSubtab, setNcSubtab] = useState<'ventas' | 'compras'>('ventas')
  const [ncVentaData, setNcVentaData] = useState<NCVentaData | null>(null)
  const [ncCompraData, setNcCompraData] = useState<NCCompraData | null>(null)
  const [loadingNc, setLoadingNc] = useState(false)
  const [searchNc, setSearchNc] = useState('')

  async function buscarNC() {
    if (!ncDesde || !ncHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingNc(true)
    try {
      const [ventaRes, compraRes] = await Promise.all([
        api.get('/ventas/reporte-notas-credito/', { params: { desde: ncDesde, hasta: ncHasta } }),
        api.get('/compras/reporte-notas-credito/', { params: { desde: ncDesde, hasta: ncHasta } }),
      ])
      setNcVentaData(ventaRes.data)
      setNcCompraData(compraRes.data)
    } catch { toast.error('Error al cargar notas de crédito') }
    finally { setLoadingNc(false) }
  }

  async function exportarNcCSV() {
    try {
      const endpoint = ncSubtab === 'ventas' ? '/ventas/reporte-notas-credito/' : '/compras/reporte-notas-credito/'
      const res = await api.get(endpoint, { params: { desde: ncDesde, hasta: ncHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `notas_credito_${ncSubtab}_${ncDesde}_${ncHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const ncVentasFiltradas = (ncVentaData?.detalle ?? []).filter(f =>
    !searchNc || f.cliente.toLowerCase().includes(searchNc.toLowerCase()) || f.nro_nota_credito.includes(searchNc)
  )
  const ncComprasFiltradas = (ncCompraData?.detalle ?? []).filter(f =>
    !searchNc || f.proveedor.toLowerCase().includes(searchNc.toLowerCase())
  )

  const NC_ESTADO_COLOR: Record<string, BadgeColor> = { EMITIDA: 'blue', APLICADA: 'green', ANULADA: 'red' }

  // ── Aging Proveedores ─────────────────────────────────────────────────────────
  const [apData, setApData] = useState<AgingProveedoresData | null>(null)
  const [loadingAp, setLoadingAp] = useState(false)
  const [searchAp, setSearchAp] = useState('')


  async function cargarAgingProveedores() {
    setLoadingAp(true)
    try {
      const { data: res } = await api.get('/compras/reporte-aging-proveedores/')
      setApData(res)
    } catch { toast.error('Error al cargar aging de proveedores') }
    finally { setLoadingAp(false) }
  }

  async function exportarApCSV() {
    try {
      const res = await api.get('/compras/reporte-aging-proveedores/', { params: { formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `aging_proveedores_${today}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const apDetalleFiltrado = (apData?.detalle ?? []).filter(d =>
    !searchAp || d.proveedor.toLowerCase().includes(searchAp.toLowerCase()) || d.ruc.includes(searchAp)
  )
  const apDetalleSorted = apDetalleFiltrado.slice().sort((a, b) => b.saldo_deuda - a.saldo_deuda)

  // ── Compras / Proveedores ─────────────────────────────────────────────────────
  const primerDiaMes = today.slice(0, 7) + '-01'
  const [cpDesde, setCpDesde] = useState(primerDiaMes)
  const [cpHasta, setCpHasta] = useState(today)
  const [cpData, setCpData] = useState<ComprasProveedoresData | null>(null)
  const [loadingCp, setLoadingCp] = useState(false)
  const [searchCp, setSearchCp] = useState('')

  async function buscarCompras() {
    if (!cpDesde || !cpHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingCp(true)
    try {
      const { data: res } = await api.get('/compras/reporte-compras/', { params: { desde: cpDesde, hasta: cpHasta } })
      setCpData(res)
    } catch { toast.error('Error al cargar reporte de compras') }
    finally { setLoadingCp(false) }
  }

  async function exportarCpCSV() {
    try {
      const res = await api.get('/compras/reporte-compras/', { params: { desde: cpDesde, hasta: cpHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `compras_proveedores_${cpDesde}_${cpHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const cpFiltrado = (cpData?.por_proveedor ?? []).filter(p =>
    !searchCp || p.proveedor.toLowerCase().includes(searchCp.toLowerCase()) || p.ruc.includes(searchCp)
  )

  // ── Diferencias de Caja ───────────────────────────────────────────────────────
  const [dcDesde, setDcDesde] = useState(primerDiaMes)
  const [dcHasta, setDcHasta] = useState(today)
  const [dcData, setDcData] = useState<DiferenciasCajaData | null>(null)
  const [loadingDc, setLoadingDc] = useState(false)

  async function buscarDiferencias() {
    if (!dcDesde || !dcHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingDc(true)
    try {
      const { data: res } = await api.get('/contabilidad/reporte-diferencias-caja/', { params: { desde: dcDesde, hasta: dcHasta } })
      setDcData(res)
    } catch { toast.error('Error al cargar diferencias de caja') }
    finally { setLoadingDc(false) }
  }

  async function exportarDcCSV() {
    try {
      const res = await api.get('/contabilidad/reporte-diferencias-caja/', { params: { desde: dcDesde, hasta: dcHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `diferencias_caja_${dcDesde}_${dcHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  // ── Medios de Pago ────────────────────────────────────────────────────────────
  const [mpDesde, setMpDesde] = useState(primerDiaMes)
  const [mpHasta, setMpHasta] = useState(today)
  const [mpData, setMpData] = useState<MediosPagoData | null>(null)
  const [loadingMp, setLoadingMp] = useState(false)

  async function buscarMediosPago() {
    if (!mpDesde || !mpHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingMp(true)
    try {
      const { data: res } = await api.get('/ventas/reporte-medios-pago/', { params: { desde: mpDesde, hasta: mpHasta } })
      setMpData(res)
    } catch { toast.error('Error al cargar medios de pago') }
    finally { setLoadingMp(false) }
  }

  async function exportarMpCSV() {
    try {
      const res = await api.get('/ventas/reporte-medios-pago/', { params: { desde: mpDesde, hasta: mpHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `medios_pago_${mpDesde}_${mpHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const mpTotal = mpData?.resumen.monto_total ?? 0

  // ── Consumo por Grado ─────────────────────────────────────────────────────────
  const [cgDesde, setCgDesde] = useState(today.slice(0, 7) + '-01')
  const [cgHasta, setCgHasta] = useState(today)
  const [cgData, setCgData] = useState<ConsumoGradoData | null>(null)
  const [loadingCg, setLoadingCg] = useState(false)

  async function buscarConsumoGrado() {
    if (!cgDesde || !cgHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingCg(true)
    try {
      const { data: res } = await api.get('/almuerzos/reporte-consumo-grado/', { params: { desde: cgDesde, hasta: cgHasta } })
      setCgData(res)
    } catch { toast.error('Error al cargar consumo por grado') }
    finally { setLoadingCg(false) }
  }

  async function exportarCgCSV() {
    try {
      const res = await api.get('/almuerzos/reporte-consumo-grado/', { params: { desde: cgDesde, hasta: cgHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `consumo_grado_${cgDesde}_${cgHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  // ── Cobranza Almuerzos ────────────────────────────────────────────────────────
  const [cbAnio, setCbAnio] = useState(new Date().getFullYear())
  const [cbData, setCbData] = useState<CobranzaAlmuerzosData | null>(null)
  const [loadingCb, setLoadingCb] = useState(false)

  async function buscarCobranza() {
    setLoadingCb(true)
    try {
      const { data: res } = await api.get('/almuerzos/reporte-cobranza/', { params: { anio: cbAnio } })
      setCbData(res)
    } catch { toast.error('Error al cargar cobranza de almuerzos') }
    finally { setLoadingCb(false) }
  }

  async function exportarCbCSV() {
    try {
      const res = await api.get('/almuerzos/reporte-cobranza/', { params: { anio: cbAnio, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `cobranza_almuerzos_${cbAnio}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const FORMA_COBRO_LABEL: Record<string, string> = {
    EFECTIVO: 'Efectivo', TRANSFERENCIA: 'Transferencia',
    ONLINE: 'Online', DEBITO_AUTOMATICO: 'Débito automático',
  }

  // ── Auditoría ─────────────────────────────────────────────────────────────────
  const [audDesde, setAudDesde] = useState(today)
  const [audHasta, setAudHasta] = useState(today)
  const [audOperacion, setAudOperacion] = useState('')
  const [audTabla, setAudTabla] = useState('')
  const [audResultado, setAudResultado] = useState('')
  const [audData, setAudData] = useState<AuditoriaData | null>(null)
  const [loadingAud, setLoadingAud] = useState(false)

  async function buscarAuditoria() {
    setLoadingAud(true)
    try {
      const params: Record<string, string> = { desde: audDesde, hasta: audHasta }
      if (audOperacion) params.operacion = audOperacion
      if (audTabla) params.tabla = audTabla
      if (audResultado) params.resultado = audResultado
      const { data: res } = await api.get('/usuarios/reporte-auditoria/', { params })
      setAudData(res)
    } catch { toast.error('Error al cargar el reporte de auditoría') }
    finally { setLoadingAud(false) }
  }

  // ── Intentos de Login ─────────────────────────────────────────────────────────
  const [ilDesde, setIlDesde] = useState(today)
  const [ilHasta, setIlHasta] = useState(today)
  const [ilData, setIlData] = useState<IntentosLoginData | null>(null)
  const [loadingIl, setLoadingIl] = useState(false)

  async function buscarIntentosLogin() {
    setLoadingIl(true)
    try {
      const { data: res } = await api.get('/usuarios/reporte-intentos-login/', { params: { desde: ilDesde, hasta: ilHasta } })
      setIlData(res)
    } catch { toast.error('Error al cargar intentos de login') }
    finally { setLoadingIl(false) }
  }

  // ── Personal Inactivo ─────────────────────────────────────────────────────────
  const [piDias, setPiDias] = useState(30)
  const [piData, setPiData] = useState<PersonalInactivoData | null>(null)
  const [loadingPi, setLoadingPi] = useState(false)

  async function buscarPersonalInactivo() {
    setLoadingPi(true)
    try {
      const { data: res } = await api.get('/usuarios/reporte-personal-inactivo/', { params: { dias: piDias } })
      setPiData(res)
    } catch { toast.error('Error al cargar personal inactivo') }
    finally { setLoadingPi(false) }
  }

  const ROL_LABEL: Record<string, string> = {
    ADMIN: 'Administrador', SUPERVISOR: 'Supervisor', CAJERO: 'Cajero',
    COBRADOR: 'Cobrador', COCINA: 'Cocina',
  }

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
          <button onClick={() => setTab('notas_credito')} className={tabClass('notas_credito')}>
            <FileText className="w-4 h-4" />Notas de Crédito
          </button>
          <button onClick={() => { setTab('aging_proveedores'); if (!apData && !loadingAp) cargarAgingProveedores() }} className={tabClass('aging_proveedores')}>
            <ShoppingCart className="w-4 h-4" />Aging Proveedores
          </button>
          <button onClick={() => setTab('compras_proveedores')} className={tabClass('compras_proveedores')}>
            <ShoppingBag className="w-4 h-4" />Compras
          </button>
          <button onClick={() => setTab('diferencias_caja')} className={tabClass('diferencias_caja')}>
            <AlertTriangle className="w-4 h-4" />Diferencias Caja
          </button>
          <button onClick={() => setTab('medios_pago')} className={tabClass('medios_pago')}>
            <CreditCard className="w-4 h-4" />Medios de Pago
          </button>
          <button onClick={() => setTab('consumo_grado')} className={tabClass('consumo_grado')}>
            <UtensilsCrossed className="w-4 h-4" />Consumo por Grado
          </button>
          <button onClick={() => setTab('cobranza_almuerzos')} className={tabClass('cobranza_almuerzos')}>
            <TrendingUp className="w-4 h-4" />Cobranza Almuerzos
          </button>
          <button onClick={() => setTab('auditoria')} className={tabClass('auditoria')}>
            <Search className="w-4 h-4" />Auditoría
          </button>
          <button onClick={() => setTab('intentos_login')} className={tabClass('intentos_login')}>
            <AlertTriangle className="w-4 h-4" />Intentos Login
          </button>
          <button onClick={() => setTab('personal_inactivo')} className={tabClass('personal_inactivo')}>
            <Users className="w-4 h-4" />Personal Inactivo
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

              {/* ── Gráficos ─────────────────────────────────────────────────── */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {tendencia.length > 1 && (
                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm lg:col-span-2">
                    <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                      <h2 className="text-sm font-semibold text-slate-800">Tendencia de ventas diarias</h2>
                      <span className="text-sm text-slate-400 tabular-nums">{tendencia.length} días</span>
                    </div>
                    <div className="p-4 h-56">
                      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                        <AreaChart
                          data={tendencia.map(d => ({
                            dia: new Date(d.fecha + 'T00:00:00').toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit' }),
                            Ventas: d.cantidad,
                            'Monto (k)': Math.round(d.monto / 1000),
                          }))}
                          margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="dia" tick={{ fontSize: 11, fill: '#94a3b8' }} interval={tendencia.length > 14 ? 2 : 0} />
                          <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                          <Tooltip
                            contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                            formatter={(v, name) =>
                              name === 'Monto (k)' ? [`${fmtGsShort((Number(v) || 0) * 1000)} Gs.`, 'Monto'] : [Number(v), String(name)]
                            }
                          />
                          <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                          <Area type="monotone" dataKey="Ventas" stroke="#22c55e" fill="#22c55e20" strokeWidth={2} dot={false} />
                          <Area type="monotone" dataKey="Monto (k)" stroke="#3b82f6" fill="#3b82f620" strokeWidth={2} dot={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {data.ventas.por_tipo.length > 0 && (
                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                    <div className="px-6 py-4 border-b border-slate-100">
                      <h2 className="text-sm font-semibold text-slate-800">Ventas por tipo</h2>
                    </div>
                    <div className="p-4 h-56">
                      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                        <BarChart
                          data={tipoSorted.map(t => ({
                            tipo: TIPO_LABEL[t.tipo] ?? t.tipo,
                            Cantidad: t.cantidad,
                            'Monto (k)': Math.round((Number(t.monto) || 0) / 1000),
                          }))}
                          margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                          <XAxis dataKey="tipo" tick={{ fontSize: 11, fill: '#64748b' }} />
                          <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                          <Tooltip
                            contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                            formatter={(v, name) =>
                              name === 'Monto (k)' ? [`${fmtGsShort((Number(v) || 0) * 1000)} Gs.`, 'Monto'] : [Number(v), String(name)]
                            }
                          />
                          <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                          <Bar dataKey="Cantidad" fill="#22c55e" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="Monto (k)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {data.ventas.por_tipo.length > 0 && (
                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                    <div className="px-6 py-4 border-b border-slate-100">
                      <h2 className="text-sm font-semibold text-slate-800">Distribución por tipo</h2>
                    </div>
                    <div className="p-4 h-56">
                      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                        <PieChart>
                          <Pie
                            data={tipoSorted.map(t => ({ name: TIPO_LABEL[t.tipo] ?? t.tipo, value: Number(t.monto) || 0 }))}
                            cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                            paddingAngle={3} dataKey="value"
                          >
                            {tipoSorted.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                          </Pie>
                          <Tooltip formatter={(v) => [`Gs. ${(Number(v) || 0).toLocaleString('es-PY')}`, 'Monto']} />
                          <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
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

              {productosData.productos.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                  <div className="px-6 py-4 border-b border-slate-100">
                    <h2 className="text-sm font-semibold text-slate-800">Top 10 por monto vendido</h2>
                  </div>
                  <div className="p-4" style={{ height: `${Math.min(productosData.productos.length, 10) * 36 + 40}px`, minHeight: 200 }}>
                    <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                      <BarChart
                        layout="vertical"
                        data={productosData.productos.slice(0, 10).map(p => ({
                          nombre: p.descripcion.length > 22 ? p.descripcion.slice(0, 22) + '…' : p.descripcion,
                          'Monto (k)': Math.round((Number(p.total_monto) || 0) / 1000),
                          Cantidad: p.total_cantidad,
                        }))}
                        margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                        <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }}
                          tickFormatter={v => fmtGsShort(Number(v) * 1000)} />
                        <YAxis type="category" dataKey="nombre" width={140} tick={{ fontSize: 11, fill: '#64748b' }} />
                        <Tooltip
                          contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                          formatter={(v, name) =>
                            name === 'Monto (k)' ? [`${fmtGsShort((Number(v) || 0) * 1000)} Gs.`, 'Monto'] : [Number(v), 'Cantidad']
                          }
                        />
                        <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                        <Bar dataKey="Monto (k)" fill="#22c55e" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">Ranking completo</h2>
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

              {cajerosData.cajeros.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                  <div className="px-6 py-4 border-b border-slate-100">
                    <h2 className="text-sm font-semibold text-slate-800">Comparativa entre cajeros</h2>
                  </div>
                  <div className="p-4 h-64">
                    <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                      <BarChart
                        data={cajerosData.cajeros.map(c => ({
                          cajero: c.nombre.split(' ')[0],
                          Ventas: c.cantidad_ventas,
                          'Monto (k)': Math.round((Number(c.monto_total) || 0) / 1000),
                          'Ticket Prom (k)': Math.round((Number(c.ticket_promedio) || 0) / 1000),
                        }))}
                        margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis dataKey="cajero" tick={{ fontSize: 12, fill: '#64748b' }} />
                        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                        <Tooltip
                          contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                          formatter={(v, name) =>
                            name !== 'Ventas' ? [`${fmtGsShort((Number(v) || 0) * 1000)} Gs.`, name === 'Monto (k)' ? 'Monto' : 'Ticket prom.'] : [Number(v), 'Ventas']
                          }
                        />
                        <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                        <Bar dataKey="Ventas" fill="#22c55e" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="Monto (k)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="Ticket Prom (k)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

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
                <>
                  <Button variant="secondary" onClick={exportarCuentaCorrienteCSV}>
                    <Download className="w-4 h-4" />CSV
                  </Button>
                  <Button variant="secondary" onClick={() => exportarCuentaCorrientePDF(ccDetalleSorted, ccData.resumen.total_deuda, ccData.fecha)}>
                    <FileText className="w-4 h-4" />PDF
                  </Button>
                </>
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

              {almuerzosData.totales.monto_total > 0 && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                    <div className="px-6 py-4 border-b border-slate-100">
                      <h2 className="text-sm font-semibold text-slate-800">Distribución de cobros</h2>
                    </div>
                    <div className="p-4 h-56">
                      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Pagado', value: almuerzosData.totales.monto_pagado },
                              { name: 'Pendiente', value: almuerzosData.totales.monto_pendiente },
                            ]}
                            cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                            paddingAngle={3} dataKey="value"
                          >
                            <Cell fill="#22c55e" />
                            <Cell fill="#f59e0b" />
                          </Pie>
                          <Tooltip formatter={(v) => [`Gs. ${(Number(v) || 0).toLocaleString('es-PY')}`, '']} />
                          <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                    <div className="px-6 py-4 border-b border-slate-100">
                      <h2 className="text-sm font-semibold text-slate-800">Alumnos por estado</h2>
                    </div>
                    <div className="p-4 h-56">
                      <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                        <PieChart>
                          <Pie
                            data={[
                              { name: 'Al día', value: almuerzosData.totales.alumnos - almuerzosData.totales.con_deuda },
                              { name: 'Con deuda', value: almuerzosData.totales.con_deuda },
                            ]}
                            cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                            paddingAngle={3} dataKey="value"
                            label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                            labelLine={false}
                          >
                            <Cell fill="#22c55e" />
                            <Cell fill="#ef4444" />
                          </Pie>
                          <Tooltip formatter={(v) => [Number(v), 'Alumnos']} />
                          <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              )}

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

      {/* ── Notas de Crédito ─────────────────────────────────────────── */}
      {tab === 'notas_credito' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={ncDesde} onChange={e => setNcDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={ncHasta} onChange={e => setNcHasta(e.target.value)} className={inputDateClass} />
            </div>
            <Button onClick={buscarNC} loading={loadingNc}>Buscar</Button>
            {(ncVentaData || ncCompraData) && (
              <Button variant="secondary" onClick={exportarNcCSV}>
                <Download className="w-4 h-4" />CSV
              </Button>
            )}
          </FilterBar>

          {(ncVentaData || ncCompraData) && (
            <>
              {/* Subtabs ventas / compras */}
              <div className="border-b border-slate-200">
                <div className="flex gap-0">
                  <button
                    onClick={() => { setNcSubtab('ventas'); setSearchNc('') }}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${ncSubtab === 'ventas' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                  >
                    Notas a Clientes {ncVentaData && `(${ncVentaData.detalle.length})`}
                  </button>
                  <button
                    onClick={() => { setNcSubtab('compras'); setSearchNc('') }}
                    className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${ncSubtab === 'compras' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                  >
                    Notas de Proveedores {ncCompraData && `(${ncCompraData.detalle.length})`}
                  </button>
                </div>
              </div>

              {/* KPIs */}
              {ncSubtab === 'ventas' && ncVentaData && (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <KpiCard label="Emitidas" value={`${ncVentaData.resumen.total_emitidas} (${formatGs(ncVentaData.resumen.monto_emitidas)})`} />
                    <KpiCard label="Aplicadas" value={`${ncVentaData.resumen.total_aplicadas} (${formatGs(ncVentaData.resumen.monto_aplicadas)})`} color="text-green-700" />
                    <KpiCard label="Anuladas" value={`${ncVentaData.resumen.total_anuladas} (${formatGs(ncVentaData.resumen.monto_anuladas)})`} color="text-slate-400" />
                    <KpiCard label="Monto activo" value={formatGs(ncVentaData.resumen.monto_total)} color="text-blue-700" />
                  </div>

                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="relative flex-1 max-w-xs">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                          type="text" placeholder="Buscar cliente o N° NC…"
                          value={searchNc} onChange={e => setSearchNc(e.target.value)}
                          className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                        />
                      </div>
                    </div>
                    {ncVentasFiltradas.length === 0
                      ? <EmptyState icon={<FileText className="w-full h-full" />} text="Sin notas de crédito en el período" />
                      : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-slate-100 text-left">
                                {['N° NC', 'Fecha', 'Cliente', 'Estado', 'Motivo', 'Autorizado por', 'Monto'].map(h => (
                                  <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50">
                              {ncVentasFiltradas.map(f => (
                                <tr key={f.id} className="hover:bg-slate-50 transition-colors">
                                  <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">{f.nro_nota_credito}</td>
                                  <td className="py-2.5 pr-4 text-slate-600 whitespace-nowrap">{f.fecha_emision}</td>
                                  <td className="py-2.5 pr-4">
                                    <p className="font-medium text-slate-800">{f.cliente}</p>
                                    <p className="text-xs text-slate-400">{f.ruc_ci}</p>
                                  </td>
                                  <td className="py-2.5 pr-4">
                                    <Badge color={NC_ESTADO_COLOR[f.estado] ?? 'gray'}>{f.estado}</Badge>
                                  </td>
                                  <td className="py-2.5 pr-4 text-slate-600 max-w-[200px] truncate" title={f.motivo}>{f.motivo}</td>
                                  <td className="py-2.5 pr-4 text-slate-600">{f.empleado_autoriza || '—'}</td>
                                  <td className="py-2.5 tabular-nums font-bold text-red-600">{formatGs(f.monto_total)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )
                    }
                  </div>
                </>
              )}

              {ncSubtab === 'compras' && ncCompraData && (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <KpiCard label="Emitidas" value={`${ncCompraData.resumen.total_emitidas} (${formatGs(ncCompraData.resumen.monto_emitidas)})`} />
                    <KpiCard label="Aplicadas" value={`${ncCompraData.resumen.total_aplicadas} (${formatGs(ncCompraData.resumen.monto_aplicadas)})`} color="text-green-700" />
                    <KpiCard label="Anuladas" value={`${ncCompraData.resumen.total_anuladas} (${formatGs(ncCompraData.resumen.monto_anuladas)})`} color="text-slate-400" />
                    <KpiCard label="Monto activo" value={formatGs(ncCompraData.resumen.monto_total)} color="text-blue-700" />
                  </div>

                  <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="relative flex-1 max-w-xs">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                          type="text" placeholder="Buscar proveedor…"
                          value={searchNc} onChange={e => setSearchNc(e.target.value)}
                          className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                        />
                      </div>
                    </div>
                    {ncComprasFiltradas.length === 0
                      ? <EmptyState icon={<FileText className="w-full h-full" />} text="Sin notas de crédito de proveedores en el período" />
                      : (
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-slate-100 text-left">
                                {['Fecha', 'Proveedor', 'Estado', 'Observación', 'N° Factura', 'Registrado por', 'Monto'].map(h => (
                                  <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-50">
                              {ncComprasFiltradas.map(f => (
                                <tr key={f.id} className="hover:bg-slate-50 transition-colors">
                                  <td className="py-2.5 pr-4 text-slate-600 whitespace-nowrap">{f.fecha}</td>
                                  <td className="py-2.5 pr-4">
                                    <p className="font-medium text-slate-800">{f.proveedor}</p>
                                    <p className="text-xs text-slate-400">{f.ruc}</p>
                                  </td>
                                  <td className="py-2.5 pr-4">
                                    <Badge color={NC_ESTADO_COLOR[f.estado] ?? 'gray'}>{f.estado}</Badge>
                                  </td>
                                  <td className="py-2.5 pr-4 text-slate-600 max-w-[180px] truncate" title={f.observacion}>{f.observacion || '—'}</td>
                                  <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">{f.nro_factura_compra || '—'}</td>
                                  <td className="py-2.5 pr-4 text-slate-600">{f.creado_por || '—'}</td>
                                  <td className="py-2.5 tabular-nums font-bold text-green-700">{formatGs(f.monto_total)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )
                    }
                  </div>
                </>
              )}
            </>
          )}

          {!ncVentaData && !ncCompraData && !loadingNc && (
            <EmptyState icon={<FileText className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Aging Proveedores ─────────────────────────────────────────── */}
      {tab === 'aging_proveedores' && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button onClick={cargarAgingProveedores} loading={loadingAp}>Actualizar</Button>
              {apData && (
                <Button variant="secondary" onClick={exportarApCSV}>
                  <Download className="w-4 h-4" />CSV
                </Button>
              )}
            </div>
            {apData && (
              <p className="text-sm text-slate-400">Al {apData.fecha}</p>
            )}
          </div>

          {apData && (
            <>
              {apData.resumen.proveedores_con_deuda > 0 && apData.resumen.aging['90+'] > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-2xl px-4 py-3 flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
                  <p className="text-sm text-red-700 font-medium">
                    {`Hay deuda con proveedores mayor a 90 días: ${formatGs(apData.resumen.aging['90+'])}`}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard label="Total a pagar" value={formatGs(apData.resumen.total_deuda)} color="text-red-600" />
                <KpiCard label="Proveedores" value={apData.resumen.proveedores_con_deuda} />
                <KpiCard label="0–30 días" value={formatGs(apData.resumen.aging['0-30'])} color="text-green-700" />
                <KpiCard label="+90 días" value={formatGs(apData.resumen.aging['90+'])} color="text-red-600" />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {(['0-30', '31-60', '61-90', '90+'] as const).map(bucket => (
                  <div key={bucket} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
                    <Badge color={AGING_COLOR[bucket]}>{bucket} días</Badge>
                    <p className="text-lg font-bold tabular-nums mt-2 text-slate-800">{formatGs(apData.resumen.aging[bucket])}</p>
                  </div>
                ))}
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="text" placeholder="Buscar proveedor o RUC…"
                      value={searchAp} onChange={e => setSearchAp(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                    />
                  </div>
                </div>
                {apDetalleSorted.length === 0
                  ? <EmptyState icon={<ShoppingCart className="w-full h-full" />} text="Sin proveedores con deuda pendiente" />
                  : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-100 text-left">
                            {['Proveedor', 'Contacto', 'Saldo (Gs)', 'Días', 'Aging'].map(h => (
                              <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                          {apDetalleSorted.map(r => (
                            <tr key={r.proveedor_id} className="hover:bg-slate-50 transition-colors">
                              <td className="py-2.5 pr-4">
                                <p className="font-medium text-slate-800">{r.proveedor}</p>
                                <p className="text-xs text-slate-400">{r.ruc || '—'}</p>
                              </td>
                              <td className="py-2.5 pr-4 text-sm text-slate-500">
                                {r.telefono && <p>{r.telefono}</p>}
                                {r.email && <p>{r.email}</p>}
                                {!r.telefono && !r.email && <span className="text-slate-300">—</span>}
                              </td>
                              <td className="py-2.5 pr-4 tabular-nums font-bold text-red-600">{formatGs(r.saldo_deuda)}</td>
                              <td className="py-2.5 pr-4 tabular-nums text-slate-600">{r.dias_atraso}d</td>
                              <td className="py-2.5"><Badge color={AGING_COLOR[r.aging] ?? 'gray'}>{r.aging}</Badge></td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
                }
              </div>
            </>
          )}

          {!apData && !loadingAp && (
            <EmptyState icon={<ShoppingCart className="w-full h-full" />} text="Hacé clic en Actualizar para cargar el reporte" />
          )}
        </>
      )}

      {/* ── Compras / Proveedores ─────────────────────────────────────── */}
      {tab === 'compras_proveedores' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={cpDesde} onChange={e => setCpDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={cpHasta} onChange={e => setCpHasta(e.target.value)} className={inputDateClass} />
            </div>
            <Button onClick={buscarCompras} loading={loadingCp}>Buscar</Button>
            {cpData && (
              <Button variant="secondary" onClick={exportarCpCSV}><Download className="w-4 h-4" />CSV</Button>
            )}
          </FilterBar>

          {cpData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <KpiCard label="Total comprado" value={formatGs(cpData.resumen.monto_total)} color="text-blue-700" />
                <KpiCard label="Compras" value={cpData.resumen.total_compras} />
                <KpiCard label="Proveedores" value={cpData.resumen.n_proveedores} />
              </div>

              {/* Funnel OC */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                <p className="text-sm font-semibold text-slate-700 mb-3">Funnel Órdenes de Compra — {cpData.periodo.desde} al {cpData.periodo.hasta}</p>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {([
                    { key: 'BORRADOR', label: 'Borrador', color: 'text-slate-500' },
                    { key: 'PENDIENTE', label: 'Pendiente', color: 'text-yellow-600' },
                    { key: 'APROBADA', label: 'Aprobada', color: 'text-blue-600' },
                    { key: 'RECHAZADA', label: 'Rechazada', color: 'text-red-600' },
                    { key: 'CONVERTIDA', label: 'Convertida', color: 'text-green-700' },
                  ] as const).map(({ key, label, color }) => (
                    <div key={key} className="text-center">
                      <p className={`text-2xl font-bold tabular-nums ${color}`}>{cpData.funnel_oc[key]}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
                    </div>
                  ))}
                </div>
                {cpData.funnel_oc.total > 0 && (
                  <p className="text-xs text-slate-400 mt-3 text-right">
                    Tasa de conversión: {cpData.funnel_oc.total > 0 ? Math.round(cpData.funnel_oc.CONVERTIDA / cpData.funnel_oc.total * 100) : 0}%
                  </p>
                )}
              </div>

              {/* Tabla por proveedor */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <div className="flex items-center gap-3 mb-4">
                  <p className="text-sm font-semibold text-slate-700 flex-1">Gasto y entrega por proveedor</p>
                  <div className="relative max-w-xs w-full">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="text" placeholder="Buscar proveedor…"
                      value={searchCp} onChange={e => setSearchCp(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                    />
                  </div>
                </div>
                {cpFiltrado.length === 0
                  ? <EmptyState icon={<ShoppingBag className="w-full h-full" />} text="Sin compras en el período" />
                  : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-100 text-left">
                            {['Proveedor', 'N° Compras', 'Monto Total', 'Entregadas', '% Entrega', 'Pagadas'].map(h => (
                              <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                          {cpFiltrado.map(p => (
                            <tr key={p.proveedor_id} className="hover:bg-slate-50 transition-colors">
                              <td className="py-2.5 pr-4">
                                <p className="font-medium text-slate-800">{p.proveedor}</p>
                                <p className="text-xs text-slate-400">{p.ruc || '—'}</p>
                              </td>
                              <td className="py-2.5 pr-4 tabular-nums text-slate-600">{p.n_compras}</td>
                              <td className="py-2.5 pr-4 tabular-nums font-bold text-blue-700">{formatGs(p.monto_total)}</td>
                              <td className="py-2.5 pr-4">
                                <span className="tabular-nums text-slate-600">{p.entregadas}</span>
                                {p.entrega_pendiente > 0 && (
                                  <span className="ml-1.5 text-xs text-orange-500">({p.entrega_pendiente} pend.)</span>
                                )}
                              </td>
                              <td className="py-2.5 pr-4">
                                <span className={`tabular-nums font-semibold text-sm ${p.tasa_entrega >= 90 ? 'text-green-700' : p.tasa_entrega >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                                  {p.tasa_entrega}%
                                </span>
                              </td>
                              <td className="py-2.5">
                                <span className="tabular-nums text-slate-600">{p.pagadas}</span>
                                {p.pago_pendiente > 0 && (
                                  <span className="ml-1.5 text-xs text-red-500">({p.pago_pendiente} pend.)</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )
                }
              </div>
            </>
          )}

          {!cpData && !loadingCp && (
            <EmptyState icon={<ShoppingBag className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Diferencias de Caja ───────────────────────────────────────── */}
      {tab === 'diferencias_caja' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={dcDesde} onChange={e => setDcDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={dcHasta} onChange={e => setDcHasta(e.target.value)} className={inputDateClass} />
            </div>
            <Button onClick={buscarDiferencias} loading={loadingDc}>Buscar</Button>
            {dcData && (
              <Button variant="secondary" onClick={exportarDcCSV}><Download className="w-4 h-4" />CSV</Button>
            )}
          </FilterBar>

          {dcData && (
            <>
              {dcData.resumen.n_positivos > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-2xl px-4 py-3 flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-orange-500 shrink-0" />
                  <p className="text-sm text-orange-700 font-medium">
                    {`${dcData.resumen.n_positivos} cierre${dcData.resumen.n_positivos > 1 ? 's' : ''} con faltante — revisá el detalle por empleado.`}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard label="Diferencia total" value={formatGs(dcData.resumen.total_diferencia)}
                  color={dcData.resumen.total_diferencia > 0 ? 'text-red-600' : dcData.resumen.total_diferencia < 0 ? 'text-green-700' : 'text-slate-600'} />
                <KpiCard label="Cierres" value={dcData.resumen.n_cierres} />
                <KpiCard label="Con faltante" value={dcData.resumen.n_positivos} color={dcData.resumen.n_positivos > 0 ? 'text-red-600' : 'text-slate-600'} />
                <KpiCard label="Con sobrante" value={dcData.resumen.n_negativos} color="text-green-700" />
              </div>

              {/* Resumen por empleado */}
              {dcData.por_empleado.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Diferencia por empleado</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 text-left">
                          {['Empleado', 'N° Cierres', 'Diferencia Total', 'Promedio', 'Mayor faltante'].map(h => (
                            <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {dcData.por_empleado.map(r => (
                          <tr key={r.empleado_id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-2.5 pr-4 font-medium text-slate-800">{r.empleado}</td>
                            <td className="py-2.5 pr-4 tabular-nums text-slate-600">{r.n_cierres}</td>
                            <td className="py-2.5 pr-4">
                              <span className={`tabular-nums font-bold text-sm ${r.diferencia_total > 0 ? 'text-red-600' : r.diferencia_total < 0 ? 'text-green-700' : 'text-slate-400'}`}>
                                {formatGs(r.diferencia_total)}
                              </span>
                            </td>
                            <td className="py-2.5 pr-4 tabular-nums text-slate-600">{formatGs(r.diferencia_promedio)}</td>
                            <td className="py-2.5 tabular-nums text-red-600 font-semibold">{formatGs(r.mayor_diferencia)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Tendencia cronológica */}
              {dcData.tendencia.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                  <p className="text-sm font-semibold text-slate-700 mb-4">Tendencia cronológica</p>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={dcData.tendencia} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="fecha" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false}
                        tickFormatter={v => fmtGsShort(v)} />
                      <Tooltip
                        formatter={(v, _n, p) => [formatGs(Number(v)), p.payload.empleado]}
                        labelFormatter={l => `Fecha: ${l}`}
                        contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }}
                      />
                      <Bar dataKey="diferencia" name="Diferencia" fill="#f97316" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}

          {!dcData && !loadingDc && (
            <EmptyState icon={<AlertTriangle className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Medios de Pago ────────────────────────────────────────────── */}
      {tab === 'medios_pago' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={mpDesde} onChange={e => setMpDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={mpHasta} onChange={e => setMpHasta(e.target.value)} className={inputDateClass} />
            </div>
            <Button onClick={buscarMediosPago} loading={loadingMp}>Buscar</Button>
            {mpData && (
              <Button variant="secondary" onClick={exportarMpCSV}><Download className="w-4 h-4" />CSV</Button>
            )}
          </FilterBar>

          {mpData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <KpiCard label="Total cobrado" value={formatGs(mpData.resumen.monto_total)} color="text-green-700" />
                <KpiCard label="Pagos" value={mpData.resumen.total_pagos} />
                <KpiCard label="Medios activos" value={mpData.resumen.n_medios} />
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                <p className="text-sm font-semibold text-slate-700 mb-4">Distribución por medio de pago</p>
                <div className="space-y-3">
                  {mpData.por_medio_pago.map(f => {
                    const pct = mpTotal > 0 ? Math.round(f.monto_total / mpTotal * 100) : 0
                    return (
                      <div key={f.medio_pago_id ?? f.descripcion}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-slate-700">{f.descripcion}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-400">{f.n_pagos} pago{f.n_pagos !== 1 ? 's' : ''}</span>
                            <span className="text-sm font-bold tabular-nums text-slate-800">{formatGs(f.monto_total)}</span>
                            <span className="text-xs font-semibold text-slate-500 w-8 text-right">{pct}%</span>
                          </div>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className="h-full bg-green-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                        </div>
                        {f.n_pendientes > 0 && (
                          <p className="text-xs text-orange-500 mt-0.5">
                            {`${f.n_pendientes} pendiente${f.n_pendientes > 1 ? 's' : ''} sin conciliar — ${formatGs(f.monto_pendiente)}`}
                          </p>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Detalle por medio de pago</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Medio de Pago', 'N° Pagos', 'Monto Total', 'Conciliados', 'Monto Conciliado', 'Pendientes'].map(h => (
                          <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {mpData.por_medio_pago.map(f => (
                        <tr key={f.medio_pago_id ?? f.descripcion} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 pr-4 font-medium text-slate-800">{f.descripcion}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-slate-600">{f.n_pagos}</td>
                          <td className="py-2.5 pr-4 tabular-nums font-bold text-slate-800">{formatGs(f.monto_total)}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-green-700">{f.n_conciliados}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-green-700">{formatGs(f.monto_conciliado)}</td>
                          <td className="py-2.5">
                            {f.n_pendientes > 0
                              ? <span className="tabular-nums text-orange-600 font-medium">{f.n_pendientes} ({formatGs(f.monto_pendiente)})</span>
                              : <span className="text-slate-300">—</span>
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {!mpData && !loadingMp && (
            <EmptyState icon={<CreditCard className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Consumo por Grado ─────────────────────────────────────────── */}
      {tab === 'consumo_grado' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={cgDesde} onChange={e => setCgDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={cgHasta} onChange={e => setCgHasta(e.target.value)} className={inputDateClass} />
            </div>
            <Button onClick={buscarConsumoGrado} loading={loadingCg}>Buscar</Button>
            {cgData && (
              <Button variant="secondary" onClick={exportarCgCSV}><Download className="w-4 h-4" />CSV</Button>
            )}
          </FilterBar>

          {cgData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <KpiCard label="Total consumos" value={cgData.resumen.total_consumos} color="text-green-700" />
                <KpiCard label="Rechazados" value={cgData.resumen.total_rechazados}
                  color={cgData.resumen.total_rechazados > 0 ? 'text-red-600' : 'text-slate-600'} />
                <KpiCard label="Tasa de rechazo" value={`${cgData.resumen.tasa_rechazo_global}%`}
                  color={cgData.resumen.tasa_rechazo_global > 5 ? 'text-red-600' : 'text-slate-600'} />
              </div>

              {/* Gráfico consumos por grado */}
              {cgData.por_grado.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                  <p className="text-sm font-semibold text-slate-700 mb-4">Consumos por grado</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={cgData.por_grado} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="grado" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <Tooltip
                        formatter={(v, n) => [v, n === 'n_consumos' ? 'Consumos' : 'Rechazados']}
                        contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }}
                      />
                      <Legend formatter={n => n === 'n_consumos' ? 'Consumos' : 'Rechazados'} />
                      <Bar dataKey="n_consumos" fill="#22c55e" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="n_rechazados" fill="#ef4444" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Tabla por grado */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Detalle por grado</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Grado', 'Consumos', 'Rechazados', 'Anulados', '% Rechazo', 'Monto'].map(h => (
                          <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {cgData.por_grado.map(r => (
                        <tr key={r.grado} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 pr-4 font-medium text-slate-800">{r.grado}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-green-700 font-semibold">{r.n_consumos}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-red-600">{r.n_rechazados || '—'}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-slate-400">{r.n_anulados || '—'}</td>
                          <td className="py-2.5 pr-4">
                            <span className={`tabular-nums font-semibold text-sm ${r.tasa_rechazo > 5 ? 'text-red-600' : r.tasa_rechazo > 0 ? 'text-yellow-600' : 'text-slate-400'}`}>
                              {r.tasa_rechazo > 0 ? `${r.tasa_rechazo}%` : '—'}
                            </span>
                          </td>
                          <td className="py-2.5 tabular-nums text-slate-700">{formatGs(r.monto_total)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Horarios pico */}
              {cgData.horarios_pico.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                  <p className="text-sm font-semibold text-slate-700 mb-4">Distribución horaria de consumos</p>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart
                      data={cgData.horarios_pico.map(h => ({ hora: `${String(h.hora).padStart(2, '0')}:00`, n: h.n }))}
                      margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="hora" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <Tooltip
                        formatter={(v) => [v, 'Consumos']}
                        contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }}
                      />
                      <Bar dataKey="n" name="Consumos" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}

          {!cgData && !loadingCg && (
            <EmptyState icon={<UtensilsCrossed className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Cobranza Almuerzos ────────────────────────────────────────── */}
      {tab === 'cobranza_almuerzos' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Año</label>
              <input
                type="number" value={cbAnio}
                onChange={e => setCbAnio(Number(e.target.value))}
                min={2020} max={2030}
                className={inputDateClass + ' w-28'}
              />
            </div>
            <Button onClick={buscarCobranza} loading={loadingCb}>Buscar</Button>
            {cbData && (
              <Button variant="secondary" onClick={exportarCbCSV}><Download className="w-4 h-4" />CSV</Button>
            )}
          </FilterBar>

          {cbData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard label="Facturado anual" value={formatGs(cbData.resumen.monto_anual)} />
                <KpiCard label="Cobrado" value={formatGs(cbData.resumen.cobrado_anual)} color="text-green-700" />
                <KpiCard label="Pendiente" value={formatGs(cbData.resumen.pendiente_anual)}
                  color={cbData.resumen.pendiente_anual > 0 ? 'text-red-600' : 'text-slate-600'} />
                <KpiCard label="Tasa de cobro" value={`${cbData.resumen.tasa_cobro_anual}%`}
                  color={cbData.resumen.tasa_cobro_anual >= 90 ? 'text-green-700' : cbData.resumen.tasa_cobro_anual >= 70 ? 'text-yellow-600' : 'text-red-600'} />
              </div>

              {/* Gráfico tendencia por mes */}
              {cbData.por_mes.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                  <p className="text-sm font-semibold text-slate-700 mb-4">Tendencia de cobro mensual — {cbData.anio}</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={cbData.por_mes} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="mes_nombre" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false}
                        tickFormatter={v => fmtGsShort(v)} />
                      <Tooltip
                        formatter={(v, n) => [formatGs(Number(v)), n === 'monto_cobrado' ? 'Cobrado' : 'Pendiente']}
                        contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }}
                      />
                      <Legend formatter={n => n === 'monto_cobrado' ? 'Cobrado' : 'Pendiente'} />
                      <Bar dataKey="monto_cobrado" stackId="a" fill="#22c55e" radius={[0, 0, 0, 0]} />
                      <Bar dataKey="monto_pendiente" stackId="a" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Tabla por mes */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Estado de cobro por mes</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Mes', 'Alumnos', 'Pagados', 'Parciales', 'Pendientes', 'Total', 'Cobrado', 'Pendiente', '% Cobro'].map(h => (
                          <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {cbData.por_mes.map(m => (
                        <tr key={m.mes} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 pr-4 font-medium text-slate-800">{m.mes_nombre}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-slate-600">{m.n_alumnos}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-green-700">{m.pagados}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-blue-600">{m.parciales || '—'}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-orange-600">{m.pendientes || '—'}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-slate-700">{formatGs(m.monto_total)}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-green-700">{formatGs(m.monto_cobrado)}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-red-600">{m.monto_pendiente > 0 ? formatGs(m.monto_pendiente) : '—'}</td>
                          <td className="py-2.5">
                            <span className={`tabular-nums font-semibold text-sm ${m.tasa_cobro >= 90 ? 'text-green-700' : m.tasa_cobro >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {m.tasa_cobro}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Por forma de cobro */}
              {cbData.por_forma_cobro.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Distribución por forma de cobro</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 text-left">
                          {['Forma de cobro', 'Cuentas', 'Total', 'Cobrado', '% Cobro'].map(h => (
                            <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {cbData.por_forma_cobro.map(f => {
                          const tasa = f.monto_total > 0 ? Math.round(f.monto_cobrado / f.monto_total * 100) : 0
                          return (
                            <tr key={f.forma_cobro} className="hover:bg-slate-50 transition-colors">
                              <td className="py-2.5 pr-4 font-medium text-slate-800">
                                {FORMA_COBRO_LABEL[f.forma_cobro] ?? f.forma_cobro}
                              </td>
                              <td className="py-2.5 pr-4 tabular-nums text-slate-600">{f.n_cuentas}</td>
                              <td className="py-2.5 pr-4 tabular-nums text-slate-700">{formatGs(f.monto_total)}</td>
                              <td className="py-2.5 pr-4 tabular-nums text-green-700">{formatGs(f.monto_cobrado)}</td>
                              <td className="py-2.5">
                                <span className={`tabular-nums font-semibold text-sm ${tasa >= 90 ? 'text-green-700' : tasa >= 70 ? 'text-yellow-600' : 'text-red-600'}`}>
                                  {tasa}%
                                </span>
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}

          {!cbData && !loadingCb && (
            <EmptyState icon={<TrendingUp className="w-full h-full" />} text='Seleccioná el año y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Auditoría ───────────────────────────────────────────────── */}
      {tab === 'auditoria' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={audDesde} onChange={e => setAudDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={audHasta} onChange={e => setAudHasta(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Operación</label>
              <input type="text" value={audOperacion} onChange={e => setAudOperacion(e.target.value)} placeholder="Filtrar..." className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Tabla</label>
              <input type="text" value={audTabla} onChange={e => setAudTabla(e.target.value)} placeholder="Filtrar..." className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Resultado</label>
              <select value={audResultado} onChange={e => setAudResultado(e.target.value)} className={inputDateClass}>
                <option value="">Todos</option>
                <option value="EXITO">Éxito</option>
                <option value="ERROR">Error</option>
              </select>
            </div>
            <Button onClick={buscarAuditoria} loading={loadingAud}>Buscar</Button>
          </FilterBar>

          {audData && (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <KpiCard label="Total operaciones" value={audData.resumen.total.toLocaleString('es-PY')} />
                {audData.resumen.por_resultado.map(r => (
                  <KpiCard
                    key={r.resultado}
                    label={r.resultado}
                    value={r.count.toLocaleString('es-PY')}
                    color={r.resultado === 'EXITO' ? 'text-green-700' : 'text-red-600'}
                  />
                ))}
              </div>

              {/* Top operaciones + tablas */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Top operaciones</p>
                  <div className="space-y-2">
                    {audData.resumen.top_operaciones.map(op => (
                      <div key={op.operacion} className="flex items-center justify-between text-sm">
                        <span className="font-mono text-slate-700 truncate max-w-[70%]">{op.operacion}</span>
                        <span className="tabular-nums font-semibold text-slate-900">{op.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Top tablas afectadas</p>
                  <div className="space-y-2">
                    {audData.resumen.top_tablas.map(t => (
                      <div key={t.tabla_afectada} className="flex items-center justify-between text-sm">
                        <span className="font-mono text-slate-700 truncate max-w-[70%]">{t.tabla_afectada}</span>
                        <span className="tabular-nums font-semibold text-slate-900">{t.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Detalle */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">
                  Últimas {audData.detalle.length} operaciones
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Fecha', 'Usuario', 'Operación', 'Tabla', 'ID Reg.', 'Resultado', 'IP', 'Descripción'].map(h => (
                          <th key={h} className="pb-2 pr-3 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {audData.detalle.map(row => (
                        <tr key={row.id_auditoria} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2 pr-3 whitespace-nowrap text-slate-500 text-xs">{formatFecha(row.fecha_operacion)}</td>
                          <td className="py-2 pr-3 text-slate-700 text-xs">{row.usuario__email ?? '—'}</td>
                          <td className="py-2 pr-3 font-mono text-slate-800 text-xs">{row.operacion}</td>
                          <td className="py-2 pr-3 font-mono text-slate-600 text-xs">{row.tabla_afectada ?? '—'}</td>
                          <td className="py-2 pr-3 tabular-nums text-slate-500 text-xs">{row.id_registro ?? '—'}</td>
                          <td className="py-2 pr-3">
                            <span className={`text-xs font-semibold ${row.resultado === 'EXITO' ? 'text-green-700' : 'text-red-600'}`}>
                              {row.resultado}
                            </span>
                          </td>
                          <td className="py-2 pr-3 font-mono text-slate-500 text-xs">{row.ip_address ?? '—'}</td>
                          <td className="py-2 text-slate-600 text-xs max-w-xs truncate">
                            {row.mensaje_error ? (
                              <span className="text-red-600">{row.mensaje_error}</span>
                            ) : (row.descripcion ?? '—')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {!audData && !loadingAud && (
            <EmptyState icon={<Search className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Intentos de Login ───────────────────────────────────────── */}
      {tab === 'intentos_login' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Desde</label>
              <input type="date" value={ilDesde} onChange={e => setIlDesde(e.target.value)} className={inputDateClass} />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input type="date" value={ilHasta} onChange={e => setIlHasta(e.target.value)} className={inputDateClass} />
            </div>
            <Button onClick={buscarIntentosLogin} loading={loadingIl}>Buscar</Button>
          </FilterBar>

          {ilData && (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <KpiCard label="Total intentos" value={ilData.resumen.total.toLocaleString('es-PY')} />
                <KpiCard label="Fallidos" value={ilData.resumen.fallidos.toLocaleString('es-PY')} color="text-red-600" />
                <KpiCard label="Exitosos" value={ilData.resumen.exitosos.toLocaleString('es-PY')} color="text-green-700" />
                <KpiCard label="Tasa de fallo" value={`${ilData.resumen.tasa_fallo}%`} color={ilData.resumen.tasa_fallo > 30 ? 'text-red-600' : 'text-yellow-600'} />
              </div>

              {/* Tendencia */}
              {ilData.tendencia.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Tendencia diaria</p>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={ilData.tendencia}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="fecha" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="exitosos" name="Exitosos" fill="#22c55e" stackId="a" />
                      <Bar dataKey="fallidos" name="Fallidos" fill="#ef4444" stackId="a" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Top IPs + Top emails */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">IPs con más fallos</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 text-left">
                          {['IP', 'Intentos fallidos'].map(h => (
                            <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {ilData.por_ip.map(row => (
                          <tr key={row.ip_address} className="hover:bg-slate-50">
                            <td className="py-2 pr-4 font-mono text-slate-800">{row.ip_address}</td>
                            <td className="py-2 tabular-nums font-semibold text-red-600">{row.n_fallidos}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Emails con más fallos</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 text-left">
                          {['Email', 'Intentos fallidos'].map(h => (
                            <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {ilData.por_email.map(row => (
                          <tr key={row.email} className="hover:bg-slate-50">
                            <td className="py-2 pr-4 text-slate-800 text-xs">{row.email}</td>
                            <td className="py-2 tabular-nums font-semibold text-red-600">{row.n_fallidos}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              {/* Por motivo */}
              {ilData.por_motivo.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Fallos por motivo</p>
                  <div className="space-y-2">
                    {ilData.por_motivo.map(m => (
                      <div key={m.motivo_fallo} className="flex items-center justify-between text-sm">
                        <span className="text-slate-700">{m.motivo_fallo}</span>
                        <span className="tabular-nums font-semibold text-red-600">{m.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {!ilData && !loadingIl && (
            <EmptyState icon={<AlertTriangle className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
          )}
        </>
      )}

      {/* ── Personal Inactivo ────────────────────────────────────────── */}
      {tab === 'personal_inactivo' && (
        <>
          <FilterBar>
            <div>
              <label className={labelClass}>Sin acceso hace más de (días)</label>
              <input
                type="number" min={1} max={365}
                value={piDias}
                onChange={e => setPiDias(Number(e.target.value))}
                className={inputDateClass}
                style={{ width: 100 }}
              />
            </div>
            <Button onClick={buscarPersonalInactivo} loading={loadingPi}>Buscar</Button>
          </FilterBar>

          {piData && (
            <>
              {/* KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <KpiCard label="Total personal" value={piData.resumen.total} />
                <KpiCard label="Activos" value={piData.resumen.activos} color="text-green-700" />
                <KpiCard label="Desactivados" value={piData.resumen.inactivos} color="text-slate-500" />
                <KpiCard
                  label={`Sin acceso +${piData.resumen.n_dias}d`}
                  value={piData.resumen.sin_acceso}
                  color={piData.resumen.sin_acceso > 0 ? 'text-red-600' : 'text-green-700'}
                />
              </div>

              {/* Por rol */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Resumen por rol</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Rol', 'Total', 'Activos', 'Sin acceso'].map(h => (
                          <th key={h} className="pb-2 pr-6 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {piData.por_rol.filter(r => r.total > 0).map(r => (
                        <tr key={r.rol} className="hover:bg-slate-50">
                          <td className="py-2.5 pr-6 font-medium text-slate-800">{ROL_LABEL[r.rol] ?? r.rol}</td>
                          <td className="py-2.5 pr-6 tabular-nums text-slate-600">{r.total}</td>
                          <td className="py-2.5 pr-6 tabular-nums text-green-700">{r.activos}</td>
                          <td className="py-2.5 tabular-nums font-semibold">
                            <span className={r.sin_acceso > 0 ? 'text-red-600' : 'text-slate-400'}>{r.sin_acceso}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Detalle */}
              {piData.detalle.length > 0 ? (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">
                    Usuarios sin acceso en los últimos {piData.resumen.n_dias} días ({piData.detalle.length})
                  </p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 text-left">
                          {['Nombre', 'Email', 'Rol', 'Último acceso', 'Creado'].map(h => (
                            <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {piData.detalle.map(u => (
                          <tr key={u.id} className="hover:bg-slate-50">
                            <td className="py-2.5 pr-4 font-medium text-slate-800">{u.nombre} {u.apellido}</td>
                            <td className="py-2.5 pr-4 text-slate-600 text-xs">{u.email}</td>
                            <td className="py-2.5 pr-4">
                              <span className="text-xs font-semibold text-slate-500">{ROL_LABEL[u.rol] ?? u.rol}</span>
                            </td>
                            <td className="py-2.5 pr-4 tabular-nums text-xs text-slate-500">
                              {u.ultimo_acceso ? formatFecha(u.ultimo_acceso) : <span className="text-orange-500 font-semibold">Nunca</span>}
                            </td>
                            <td className="py-2.5 tabular-nums text-xs text-slate-400">
                              {new Date(u.fecha_creacion).toLocaleDateString('es-PY')}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="bg-green-50 rounded-2xl border border-green-100 p-6 text-center">
                  <p className="text-green-700 font-semibold">Todo el personal activo accedió en los últimos {piData.resumen.n_dias} días</p>
                </div>
              )}
            </>
          )}

          {!piData && !loadingPi && (
            <EmptyState icon={<Users className="w-full h-full" />} text='Ingresá el umbral de días y hacé clic en "Buscar"' />
          )}
        </>
      )}
    </div>
  )
}
