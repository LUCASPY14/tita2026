import { useEffect, useState, useCallback, useRef, useMemo } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import Select from '../components/ui/Select'
import Combobox from '../components/ui/Combobox'
import Table, { type Column } from '../components/ui/Table'
import Badge from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import {
  Search, ShoppingCart, CreditCard, X, Plus, Minus, User,
  Wallet, Banknote, Tag, AlertTriangle, CheckCircle, History,
  Eye, XCircle, Download,
} from 'lucide-react'

// ─── Historial interfaces ─────────────────────────────────────────────────────

interface VentaHistorial {
  id: number
  fecha: string
  cliente_nombre: string
  tipo: string
  monto_total: string
  estado: string
}

interface DetalleVenta {
  id: number
  producto_nombre: string
  cantidad: number
  precio_unitario: string
  subtotal: string
}

interface VentaDetalle extends VentaHistorial {
  detalles: DetalleVenta[]
}

type PageTab = 'pos' | 'historial'

const TIPO_COLOR: Record<string, 'green' | 'blue' | 'orange'> = {
  CONTADO: 'green', CREDITO: 'blue', TARJETA: 'orange',
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

interface Producto {
  id: number
  codigo_barra: string
  descripcion: string
  precio_actual: string
  categoria_nombre: string
}

interface Cliente {
  id: number
  nombres: string
  apellidos: string
  ruc_ci: string
}

interface MedioPago {
  id: number
  descripcion: string
}

interface RestriccionHijo {
  id: number
  tipo: string
  descripcion: string | null
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'
  requiere_autorizacion: boolean
}

interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string
  hijo_nombre: string
  hijo_foto: string | null
  hijo_grado: string | null
  hijo_restricciones: RestriccionHijo[]
  saldo_actual: string
  saldo_disponible: string
  estado: string
  permite_saldo_negativo: boolean
  limite_credito: string
  fecha_vencimiento: string | null
  saldo_alerta: string | null
  // Datos del cliente responsable
  cliente_id: number
  cliente_nombre: string
  cliente_ruc: string
}

interface ItemCarrito {
  producto: Producto
  cantidad: number
  subtotal: number
}

function extractErrorMessage(error: unknown): string {
  const err = error as { response?: { data?: unknown } }
  const data = err?.response?.data

  if (!data) return 'Error al registrar la venta'
  if (typeof data === 'string') return data

  if (typeof data === 'object') {
    const obj = data as Record<string, unknown>
    if (typeof obj.detail === 'string') return obj.detail
    const firstKey = Object.keys(obj)[0]
    if (firstKey) {
      const value = obj[firstKey]
      if (Array.isArray(value) && typeof value[0] === 'string') return value[0]
      if (typeof value === 'string') return value
    }
  }

  return 'Error al registrar la venta'
}

const severidadConfig: Record<string, { bg: string; border: string; text: string; icon: string; badge: string }> = {
  BAJA: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: 'text-blue-500', badge: 'bg-blue-100 text-blue-700' },
  MEDIA: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-700', icon: 'text-amber-500', badge: 'bg-amber-100 text-amber-700' },
  ALTA: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', icon: 'text-orange-500', badge: 'bg-orange-100 text-orange-700' },
  CRITICA: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: 'text-red-500', badge: 'bg-red-100 text-red-700' },
}

export default function Ventas() {
  const [pageTab, setPageTab] = useState<PageTab>('pos')

  // ── POS state ──────────────────────────────────────────────────────
  const [productos, setProductos] = useState<Producto[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [categorias, setCategorias] = useState<string[]>([])
  const [categoria, setCategoria] = useState('')
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [cobrando, setCobrando] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)

  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | undefined>()
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([])
  const [medioPagoId, setMedioPagoId] = useState<number | undefined>()
  const [tipoVenta, setTipoVenta] = useState('CONTADO')
  const [tarjetaSearch, setTarjetaSearch] = useState('')
  const [tarjeta, setTarjeta] = useState<Tarjeta | null>(null)
  const [tarjetaBuscando, setTarjetaBuscando] = useState(false)

  const productSearchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const clientSearchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Historial state ────────────────────────────────────────────────
  const [historial, setHistorial] = useState<VentaHistorial[]>([])
  const [histLoading, setHistLoading] = useState(false)
  const [histSearch, setHistSearch] = useState('')
  const [histDesde, setHistDesde] = useState('')
  const [histHasta, setHistHasta] = useState('')
  const [histTipo, setHistTipo] = useState('')
  const [histPage, setHistPage] = useState(1)
  const [histTotal, setHistTotal] = useState(0)
  const histTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  // ── Venta detail modal ─────────────────────────────────────────────
  const [ventaDetalle, setVentaDetalle] = useState<VentaDetalle | null>(null)
  const [loadingDetalle, setLoadingDetalle] = useState(false)

  // ── Anular venta ───────────────────────────────────────────────────
  const [ventaAnular, setVentaAnular] = useState<VentaHistorial | null>(null)
  const [anulando, setAnulando] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get('/productos/categorias/'),
      api.get('/core/medios-pago/'),
    ]).then(([catRes, medRes]) => {
      setCategorias((catRes.data.results || []).map((c: { nombre: string }) => c.nombre))
      const medios: MedioPago[] = medRes.data.results || []
      setMediosPago(medios)
      if (medios.length > 0) setMedioPagoId(medios[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (productSearchTimerRef.current) clearTimeout(productSearchTimerRef.current)
    
    productSearchTimerRef.current = setTimeout(() => {
      setLoading(true)
      const params: Record<string, string> = {}
      if (search) params.search = search
      if (categoria) params.categoria = categoria
      api.get('/productos/productos/', { params })
        .then(({ data }) => setProductos(data.results || []))
        .catch(() => toast.error('Error al cargar productos'))
        .finally(() => setLoading(false))
    }, 300)

    return () => {
      if (productSearchTimerRef.current) clearTimeout(productSearchTimerRef.current)
    }
  }, [search, categoria])

  const buscarClientes = useCallback((q: string) => {
    if (clientSearchTimerRef.current) clearTimeout(clientSearchTimerRef.current)
    
    if (q.length < 2) {
      setClientes([])
      return
    }
    
    clientSearchTimerRef.current = setTimeout(() => {
      api.get('/clientes/clientes/', { params: { search: q } })
        .then(({ data }) => setClientes(data.results || []))
        .catch(() => {})
    }, 300)
  }, [])

  const buscarTarjeta = async () => {
    if (!tarjetaSearch.trim()) { toast.error('Ingrese un codigo de tarjeta'); return }
    setTarjetaBuscando(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: tarjetaSearch } })
      const encontrada = (data.results || []).find(
        (t: Tarjeta) => t.nro_tarjeta === tarjetaSearch || t.codigo_barras === tarjetaSearch
      )
      if (encontrada) {
        if (encontrada.estado !== 'ACTIVA') {
          toast.error('Tarjeta no activa: ' + encontrada.estado)
          setTarjeta(null)
        } else {
          setTarjeta(encontrada)
          
          // Autocompletar cliente desde la tarjeta
          if (encontrada.cliente_id) {
            setClienteId(encontrada.cliente_id)
            setClientes([{
              id: encontrada.cliente_id,
              nombres: encontrada.cliente_nombre.split(' ')[0] || '',
              apellidos: encontrada.cliente_nombre.split(' ').slice(1).join(' ') || '',
              ruc_ci: encontrada.cliente_ruc,
            }])
          }
          
          const saldo = Number(encontrada.saldo_disponible || encontrada.saldo_actual || 0)
          toast.success(`${encontrada.hijo_nombre} — Gs. ${saldo.toLocaleString('es-PY')}`)
          
          const criticas = (encontrada.hijo_restricciones || []).filter((r: RestriccionHijo) => r.severidad === 'CRITICA')
          if (criticas.length > 0) {
            toast.error(`⚠️ ¡Atención! ${criticas.length} restricción(es) crítica(s)`, { duration: 5000 })
          }
        }
      } else {
        toast.error('Tarjeta no encontrada')
        setTarjeta(null)
      }
    } catch {
      toast.error('Error al buscar tarjeta')
    } finally {
      setTarjetaBuscando(false)
    }
  }

  const agregarAlCarrito = (producto: Producto) => {
    const precio = Number(producto.precio_actual) || 0
    setCarrito((prev) => {
      const existente = prev.find((i) => i.producto.id === producto.id)
      if (existente) {
        return prev.map((i) =>
          i.producto.id === producto.id
            ? { ...i, cantidad: i.cantidad + 1, subtotal: (i.cantidad + 1) * precio }
            : i
        )
      }
      return [...prev, { producto, cantidad: 1, subtotal: precio }]
    })
  }

  const cambiarCantidad = (productoId: number, cantidad: number) => {
    if (cantidad <= 0) { setCarrito((p) => p.filter((i) => i.producto.id !== productoId)); return }
    setCarrito((prev) =>
      prev.map((i) => {
        if (i.producto.id !== productoId) return i
        const precio = Number(i.producto.precio_actual) || 0
        return { ...i, cantidad, subtotal: cantidad * precio }
      })
    )
  }

  const total = useMemo(() => carrito.reduce((s, i) => s + i.subtotal, 0), [carrito])

  const cobrar = async () => {
    if (carrito.length === 0) { toast.error('Agregue productos al carrito'); return }
    if (!clienteId) { toast.error('Seleccione un cliente'); return }
    if (tipoVenta === 'CONTADO' && !medioPagoId) { toast.error('Seleccione un medio de pago'); return }
    setCobrando(true)
    try {
      const payload: Record<string, unknown> = {
        cliente: clienteId,
        tipo: tipoVenta,
        items: carrito.map((i) => ({
          producto: i.producto.id,
          cantidad: i.cantidad,
          precio_unitario: Number(i.producto.precio_actual) || 0,
          iva_10: 0, iva_5: 0, monto_exenta: 0,
        })),
        medio_pago: tipoVenta === 'CONTADO' ? medioPagoId : null,
      }
      if (tarjeta) payload.tarjeta = tarjeta.nro_tarjeta
      await api.post('/ventas/ventas/', payload)
      toast.success('Venta registrada — Gs. ' + total.toLocaleString('es-PY'))
      setCarrito([])
      setTarjeta(null)
      setTarjetaSearch('')
      setShowConfirm(false)
    } catch (e: unknown) {
      toast.error(extractErrorMessage(e))
    } finally {
      setCobrando(false)
    }
  }

  // ── Historial load ────────────────────────────────────────────────
  const loadHistorial = useCallback(async (q: string, desde: string, hasta: string, tipo: string, p: number) => {
    setHistLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering: '-fecha' }
      if (q) params.search = q
      if (desde) params.fecha__date__gte = desde
      if (hasta) params.fecha__date__lte = hasta
      if (tipo) params.tipo = tipo
      const { data } = await api.get('/ventas/ventas/', { params })
      setHistorial(data.results ?? [])
      setHistTotal(data.count ?? 0)
    } catch {
      toast.error('Error al cargar historial')
    } finally {
      setHistLoading(false)
    }
  }, [])

  const loadVentaDetalle = useCallback(async (id: number) => {
    setLoadingDetalle(true)
    try {
      const { data } = await api.get(`/ventas/ventas/${id}/`)
      setVentaDetalle(data)
    } catch {
      toast.error('Error al cargar detalles de la venta')
    } finally {
      setLoadingDetalle(false)
    }
  }, [])

  const exportarPDF = useCallback((venta: VentaDetalle) => {
    const win = window.open('', '_blank', 'width=600,height=800')
    if (!win) { toast.error('Bloqueá el bloqueo de ventanas emergentes'); return }
    const rows = (venta.detalles ?? []).map(d => `
      <tr>
        <td>${d.producto_nombre}</td>
        <td style="text-align:center">${d.cantidad}</td>
        <td style="text-align:right">Gs. ${(Number(d.precio_unitario) || 0).toLocaleString('es-PY')}</td>
        <td style="text-align:right">Gs. ${(Number(d.subtotal) || 0).toLocaleString('es-PY')}</td>
      </tr>`).join('')
    win.document.write(`<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"/>
<title>Venta #${venta.id} — Cantina Tita</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1e293b;padding:32px;max-width:520px;margin:0 auto}
h1{font-size:22px;font-weight:800;margin-bottom:2px}
.sub{font-size:12px;color:#64748b;margin-bottom:24px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}
.card{background:#f8fafc;border-radius:8px;padding:12px}
.card .lbl{font-size:9px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px}
.card .val{font-size:13px;font-weight:600;color:#1e293b}
.sec{font-size:9px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px}
table{width:100%;border-collapse:collapse}
th{font-size:10px;color:#64748b;padding:8px 10px;border-bottom:1px solid #e2e8f0;text-align:left}
th:nth-child(2){text-align:center}th:nth-child(3),th:nth-child(4){text-align:right}
td{padding:9px 10px;font-size:12px;color:#334155;border-bottom:1px solid #f1f5f9}
.total{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;background:#f0fdf4;border-radius:8px;margin-top:16px}
.tl{font-size:15px;font-weight:700}
.tv{font-size:22px;font-weight:800;color:#059669}
.footer{text-align:center;font-size:10px;color:#94a3b8;margin-top:28px;padding-top:14px;border-top:1px dashed #e2e8f0}
@media print{body{padding:16px}}
</style></head>
<body>
<h1>Cantina Tita</h1>
<p class="sub">Comprobante de Venta #${venta.id}</p>
<div class="grid">
  <div class="card"><div class="lbl">Cliente</div><div class="val">${venta.cliente_nombre || '—'}</div></div>
  <div class="card"><div class="lbl">Fecha</div><div class="val">${formatFecha(venta.fecha)}</div></div>
  <div class="card"><div class="lbl">Tipo</div><div class="val">${venta.tipo}</div></div>
  <div class="card"><div class="lbl">Estado</div><div class="val">${venta.estado}</div></div>
</div>
<p class="sec">Productos</p>
<table>
  <thead><tr><th>Producto</th><th>Cant.</th><th>P. Unit.</th><th>Subtotal</th></tr></thead>
  <tbody>${rows}</tbody>
</table>
<div class="total">
  <span class="tl">TOTAL</span>
  <span class="tv">Gs. ${(Number(venta.monto_total) || 0).toLocaleString('es-PY')}</span>
</div>
<div class="footer">Cantina Tita · ${new Date().toLocaleDateString('es-PY')}</div>
<script>window.onload=function(){window.print()}<\/script>
</body></html>`)
    win.document.close()
  }, [])

  const anularVenta = async () => {
    if (!ventaAnular) return
    setAnulando(true)
    try {
      await api.post(`/ventas/ventas/${ventaAnular.id}/anular/`)
      toast.success('Venta anulada correctamente')
      setVentaAnular(null)
      loadHistorial(histSearch, histDesde, histHasta, histTipo, histPage)
    } catch (e: unknown) {
      toast.error(extractErrorMessage(e))
    } finally {
      setAnulando(false)
    }
  }

  const exportCSV = useCallback(() => {
    if (historial.length === 0) { toast.error('No hay datos para exportar'); return }
    const headers = ['ID', 'Fecha', 'Cliente', 'Tipo', 'Monto', 'Estado']
    const rows = historial.map(v => [
      v.id,
      v.fecha,
      v.cliente_nombre || '',
      v.tipo,
      Number(v.monto_total) || 0,
      v.estado,
    ])
    const csv = [headers, ...rows].map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'ventas.csv'; a.click()
    URL.revokeObjectURL(url)
  }, [historial])

  // Ctrl+Enter to trigger cobrar confirmation from POS
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'Enter' && pageTab === 'pos' && carrito.length > 0 && !showConfirm) {
        setShowConfirm(true)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [pageTab, carrito.length, showConfirm])

  useEffect(() => {
    if (pageTab !== 'historial') return
    clearTimeout(histTimer.current)
    histTimer.current = setTimeout(() => {
      setHistPage(1)
      loadHistorial(histSearch, histDesde, histHasta, histTipo, 1)
    }, 350)
    return () => clearTimeout(histTimer.current)
  }, [pageTab, histSearch, histDesde, histHasta, histTipo, loadHistorial])

  useEffect(() => {
    if (pageTab !== 'historial') return
    loadHistorial(histSearch, histDesde, histHasta, histTipo, histPage)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [histPage])

  const histCols: Column<VentaHistorial>[] = [
    {
      title: 'Fecha', key: 'fecha', width: 130,
      render: (_, r) => <span className="text-xs text-slate-500 tabular-nums">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Cliente', key: 'cliente',
      render: (_, r) => <span className="text-sm text-slate-800">{r.cliente_nombre || '—'}</span>,
    },
    {
      title: 'Tipo', key: 'tipo', width: 100,
      render: (_, r) => <Badge color={TIPO_COLOR[r.tipo] ?? 'default'}>{r.tipo}</Badge>,
    },
    {
      title: 'Monto', key: 'monto', width: 150,
      render: (_, r) => (
        <span className="font-semibold text-emerald-700 tabular-nums">
          Gs. {(Number(r.monto_total) || 0).toLocaleString('es-PY')}
        </span>
      ),
    },
    {
      title: 'Estado', key: 'estado', width: 100,
      render: (_, r) => <Badge color={r.estado === 'ACTIVA' ? 'green' : 'default'}>{r.estado}</Badge>,
    },
    {
      title: '', key: 'acciones', width: 90,
      render: (_, r) => (
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => loadVentaDetalle(r.id)}
            title="Ver detalle"
            className="p-1.5 rounded-lg text-slate-400 hover:text-green-600 hover:bg-green-50 transition-colors cursor-pointer"
          >
            <Eye className="w-4 h-4" />
          </button>
          {r.estado !== 'ANULADA' && (
            <button
              onClick={() => setVentaAnular(r)}
              title="Anular venta"
              className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors cursor-pointer"
            >
              <XCircle className="w-4 h-4" />
            </button>
          )}
        </div>
      ),
    },
  ]

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors w-full'

  const columns: Column<Producto>[] = [
    { title: 'Código', dataIndex: 'codigo_barra', key: 'codigo', width: 120 },
    { title: 'Producto', dataIndex: 'descripcion', key: 'descripcion' },
    {
      title: 'Precio',
      dataIndex: 'precio_actual',
      key: 'precio',
      width: 130,
      render: (v) => {
        const precio = Number(v) || 0
        return <span className="font-semibold text-emerald-700 tabular-nums">Gs. {precio.toLocaleString('es-PY')}</span>
      },
    },
    {
      title: '',
      key: 'accion',
      width: 90,
      render: (_, r) => <Button variant="primary" size="sm" onClick={() => agregarAlCarrito(r)}>+ Agregar</Button>,
    },
  ]

  return (
    <div className="p-4 md:p-6 h-full bg-slate-50/50 space-y-4">
      {/* Header + tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-2xl font-extrabold text-slate-800 tracking-tight flex items-center gap-2">
          <Banknote className="w-6 h-6 text-green-600" />
          Ventas
        </h2>
        <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
          {([['pos', ShoppingCart, 'POS'], ['historial', History, 'Historial']] as const).map(([key, Icon, label]) => (
            <button
              key={key}
              onClick={() => setPageTab(key)}
              className={[
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer',
                pageTab === key ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700',
              ].join(' ')}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Historial tab ─────────────────────────────────────────── */}
      {pageTab === 'historial' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[180px]">
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  placeholder="Cliente..."
                  value={histSearch}
                  onChange={e => setHistSearch(e.target.value)}
                  className={`${inputClass} pl-9`}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Desde</label>
              <input type="date" value={histDesde} onChange={e => { setHistDesde(e.target.value); setHistPage(1) }} className={inputClass} style={{ width: 150 }} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Hasta</label>
              <input type="date" value={histHasta} onChange={e => { setHistHasta(e.target.value); setHistPage(1) }} className={inputClass} style={{ width: 150 }} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Tipo</label>
              <select value={histTipo} onChange={e => { setHistTipo(e.target.value); setHistPage(1) }} className={inputClass} style={{ width: 140 }}>
                <option value="">Todos</option>
                <option value="CONTADO">Contado</option>
                <option value="CREDITO">Crédito</option>
              </select>
            </div>
            <button
              onClick={exportCSV}
              title="Exportar CSV"
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 hover:text-green-700 hover:border-green-300 transition-colors cursor-pointer"
            >
              <Download className="w-4 h-4" />
              CSV
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={histCols}
                dataSource={historial}
                rowKey="id"
                loading={histLoading}
                pageSize={15}
                page={histPage}
                onPageChange={setHistPage}
                total={histTotal}
              />
            </div>
          </div>
        </div>
      )}

      {/* ── POS tab ───────────────────────────────────────────────── */}
      {pageTab === 'pos' && <div className="flex flex-col lg:flex-row gap-6 items-start">
        
        {/* COLUMNA IZQUIERDA: CATÁLOGO */}
        <div className="flex-1 min-w-0 w-full">
          <div className="flex gap-3 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <Input
                placeholder="Buscar producto..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 w-full"
              />
            </div>
            <div className="relative">
              <Tag className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10" />
              <select
                className="bg-white border border-slate-200 rounded-xl pl-9 pr-8 py-2 text-sm shadow-xs focus:outline-hidden focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all cursor-pointer appearance-none h-full min-w-[180px] text-slate-700"
                value={categoria}
                onChange={(e) => setCategoria(e.target.value)}
              >
                <option value="">Todas las categorías</option>
                {categorias.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <Table columns={columns} dataSource={productos} rowKey="id" loading={loading} pageSize={8} />
        </div>

        {/* COLUMNA DERECHA: PANEL DE VENTA */}
        <div className="lg:w-[420px] w-full flex-shrink-0">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-xl shadow-slate-100/50 sticky top-6 flex flex-col">
            
            {/* ============================================ */}
            {/* SECCIÓN 1: TARJETA (LO PRIMERO) */}
            {/* ============================================ */}
            <div className="px-6 py-4 border-b border-slate-100 bg-gradient-to-r from-green-50/50 to-white">
              <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                <CreditCard className="w-3.5 h-3.5 text-green-600" />
                Tarjeta del Alumno
              </p>
              
              {/* Buscador de tarjeta */}
              <div className="flex gap-2">
                <Input
                  placeholder="Escanear o escribir tarjeta..."
                  value={tarjetaSearch}
                  onChange={(e) => setTarjetaSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && buscarTarjeta()}
                  className="flex-1"
                  autoFocus
                />
                <Button size="sm" loading={tarjetaBuscando} onClick={buscarTarjeta}>
                  Buscar
                </Button>
              </div>

              {/* Resultado de la tarjeta */}
              {tarjeta && (
                <div className="mt-4 bg-white rounded-xl border border-green-200 shadow-sm overflow-hidden">
                  {/* Foto y datos principales */}
                  <div className="p-4 flex items-center gap-4">
                    <div className="w-16 h-16 rounded-xl bg-slate-100 border-2 border-green-300 overflow-hidden flex-shrink-0 shadow-sm">
                      {tarjeta.hijo_foto ? (
                        <img
                          src={tarjeta.hijo_foto}
                          alt={tarjeta.hijo_nombre}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement
                            target.style.display = 'none'
                            target.parentElement!.innerHTML = '<div class="w-full h-full flex items-center justify-center"><svg class="w-8 h-8 text-slate-400">...</svg></div>'
                          }}
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-green-50">
                          <User className="w-8 h-8 text-green-400" />
                        </div>
                      )}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-base font-bold text-slate-800 truncate">
                        {tarjeta.hijo_nombre}
                      </p>
                      {tarjeta.hijo_grado && (
                        <p className="text-xs text-slate-500">{tarjeta.hijo_grado}</p>
                      )}
                      <div className="flex items-baseline gap-1 mt-1">
                        <span className="text-xs text-slate-400">Saldo:</span>
                        <span className="text-lg font-extrabold text-emerald-700 tabular-nums">
                          Gs. {Number(tarjeta.saldo_disponible || tarjeta.saldo_actual || 0).toLocaleString('es-PY')}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => { setTarjeta(null); setTarjetaSearch(''); setClienteId(undefined); setClientes([]) }}
                      className="text-slate-300 hover:text-red-500 transition-colors p-1 cursor-pointer flex-shrink-0 self-start"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Restricciones */}
                  {tarjeta.hijo_restricciones && tarjeta.hijo_restricciones.length > 0 && (
                    <div className="border-t border-slate-100 px-4 py-3 space-y-2 bg-slate-50/50">
                      <p className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                        Restricciones ({tarjeta.hijo_restricciones.length})
                      </p>
                      <div className="space-y-1.5">
                        {tarjeta.hijo_restricciones.map((r: RestriccionHijo) => {
                          const colors = severidadConfig[r.severidad] || severidadConfig.MEDIA
                          return (
                            <div
                              key={r.id}
                              className={`${colors.bg} ${colors.border} border rounded-lg p-2.5`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                  <p className={`text-xs font-semibold ${colors.text} flex items-center gap-1.5 flex-wrap`}>
                                    {r.tipo}
                                    {r.requiere_autorizacion && (
                                      <span className="px-1.5 py-0.5 bg-red-100 text-red-700 rounded text-[10px] font-bold">
                                        Requiere autorización
                                      </span>
                                    )}
                                  </p>
                                  {r.descripcion && (
                                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                                      {r.descripcion}
                                    </p>
                                  )}
                                </div>
                                <span className={`text-[10px] font-bold uppercase px-1.5 py-0.5 rounded ${colors.badge} flex-shrink-0`}>
                                  {r.severidad}
                                </span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ============================================ */}
            {/* CUERPO DEL CARRITO */}
            {/* ============================================ */}
            <div className="p-6 space-y-5">
              
              {/* SECCIÓN CLIENTE (autocompletado de tarjeta) */}
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <User className="w-3 h-3" /> 
                  Cliente
                  {tarjeta && (
                    <span className="text-green-600 flex items-center gap-0.5 ml-1">
                      <CheckCircle className="w-3 h-3" />
                      <span className="text-[10px]">desde tarjeta</span>
                    </span>
                  )}
                </p>
                <Combobox
                  options={clientes.map((c) => ({ value: c.id, label: `${c.nombres} ${c.apellidos} (${c.ruc_ci})` }))}
                  value={clienteId}
                  onChange={(v) => setClienteId(v as number)}
                  onSearch={buscarClientes}
                  placeholder="Buscar cliente..."
                />
              </div>

              {/* TIPO DE VENTA */}
              <div>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5">Tipo de Venta</p>
                <div className="grid grid-cols-2 gap-2">
                  {['CONTADO', 'CREDITO'].map((tipo) => (
                    <button
                      key={tipo}
                      onClick={() => setTipoVenta(tipo)}
                      className={`py-2.5 px-4 text-sm rounded-xl border font-medium transition-all duration-200 cursor-pointer ${
                        tipoVenta === tipo
                          ? 'bg-green-600 text-white border-green-600 shadow-md shadow-green-600/20 scale-[1.02]'
                          : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300'
                      }`}
                    >
                      {tipo === 'CONTADO' ? 'Contado' : 'Crédito'}
                    </button>
                  ))}
                </div>
              </div>

              {tipoVenta === 'CONTADO' && (
                <div>
                  <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                    <Wallet className="w-3 h-3" /> Medio de Pago
                  </p>
                  <Select
                    options={mediosPago.map((m) => ({ value: m.id, label: m.descripcion }))}
                    value={medioPagoId}
                    onChange={(e) => setMedioPagoId(Number(e.target.value))}
                  />
                </div>
              )}

              <hr className="border-slate-100" />

              {/* CARRITO */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-semibold text-slate-700">
                  <ShoppingCart className="w-4 h-4 text-green-600" />
                  <span className="text-sm">Productos</span>
                  {carrito.length > 0 && (
                    <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-0.5 rounded-full tabular-nums">
                      {carrito.length}
                    </span>
                  )}
                </div>
              </div>

              {carrito.length === 0 ? (
                <p className="text-slate-400 text-center py-6 text-sm italic">Agregue productos del catálogo</p>
              ) : (
                <>
                  <div className="max-h-56 overflow-y-auto space-y-3 pr-1">
                    {carrito.map((item) => (
                      <div key={item.producto.id} className="flex items-center gap-3 pb-3 border-b border-slate-50">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-800 truncate">{item.producto.descripcion}</p>
                          <p className="text-xs text-slate-500 tabular-nums">
                            Gs. {Number(item.producto.precio_actual || 0).toLocaleString('es-PY')} c/u
                          </p>
                        </div>
                        <div className="flex items-center border border-slate-200 rounded-lg overflow-hidden shadow-xs">
                          <button
                            onClick={() => cambiarCantidad(item.producto.id, item.cantidad - 1)}
                            className="p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer"
                          >
                            <Minus className="w-4 h-4" />
                          </button>
                          <span className="px-3 py-1 text-sm font-semibold text-slate-700 bg-white min-w-[2.5rem] text-center select-none tabular-nums">
                            {item.cantidad}
                          </span>
                          <button
                            onClick={() => cambiarCantidad(item.producto.id, item.cantidad + 1)}
                            className="p-1.5 text-slate-500 hover:bg-green-50 hover:text-green-600 transition-colors cursor-pointer"
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                        </div>
                        <span className="text-sm font-semibold text-slate-800 w-24 text-right tabular-nums">
                          Gs. {item.subtotal.toLocaleString('es-PY')}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="flex justify-between items-center border-t border-slate-200 pt-4">
                    <span className="text-base font-bold text-slate-700">TOTAL</span>
                    <span className="text-xl font-extrabold text-emerald-700 tabular-nums">
                      Gs. {total.toLocaleString('es-PY')}
                    </span>
                  </div>
                  <Button variant="primary" block size="lg" loading={cobrando} onClick={() => setShowConfirm(true)}>
                    Cobrar Gs. {total.toLocaleString('es-PY')}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
      }

      {/* ── Modal detalle de venta ────────────────────────────────── */}
      <Modal
        open={ventaDetalle !== null}
        title={`Venta #${ventaDetalle?.id ?? ''}`}
        onOk={() => setVentaDetalle(null)}
        onCancel={() => setVentaDetalle(null)}
        okText="Cerrar"
        width={520}
      >
        {loadingDetalle ? (
          <div className="py-8 text-center text-slate-400 text-sm">Cargando...</div>
        ) : ventaDetalle ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Cliente</p>
                <p className="font-medium text-slate-800">{ventaDetalle.cliente_nombre || '—'}</p>
              </div>
              <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Fecha</p>
                <p className="font-medium text-slate-800 tabular-nums">{formatFecha(ventaDetalle.fecha)}</p>
              </div>
              <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Tipo</p>
                <Badge color={TIPO_COLOR[ventaDetalle.tipo] ?? 'default'}>{ventaDetalle.tipo}</Badge>
              </div>
              <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">Estado</p>
                <Badge color={ventaDetalle.estado === 'ACTIVA' ? 'green' : 'default'}>{ventaDetalle.estado}</Badge>
              </div>
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Productos</p>
              <div className="divide-y divide-slate-100 rounded-xl border border-slate-200 overflow-hidden">
                {(ventaDetalle.detalles ?? []).map((d) => (
                  <div key={d.id} className="flex items-center justify-between px-4 py-2.5 text-sm">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-800 truncate">{d.producto_nombre}</p>
                      <p className="text-xs text-slate-500 tabular-nums">
                        {d.cantidad} × Gs. {(Number(d.precio_unitario) || 0).toLocaleString('es-PY')}
                      </p>
                    </div>
                    <span className="font-semibold text-emerald-700 tabular-nums ml-4">
                      Gs. {(Number(d.subtotal) || 0).toLocaleString('es-PY')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex justify-between items-center px-4 py-3 bg-green-50 rounded-xl border border-green-100">
              <span className="text-base font-bold text-slate-700">TOTAL</span>
              <span className="text-xl font-extrabold text-emerald-700 tabular-nums">
                Gs. {(Number(ventaDetalle.monto_total) || 0).toLocaleString('es-PY')}
              </span>
            </div>
            <div className="flex justify-end">
              <button
                onClick={() => exportarPDF(ventaDetalle)}
                className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-green-700 transition-colors cursor-pointer"
              >
                <Download className="w-4 h-4" />
                Descargar PDF
              </button>
            </div>
          </div>
        ) : null}
      </Modal>

      {/* ── Modal anular venta ────────────────────────────────────── */}
      <Modal
        open={ventaAnular !== null}
        title="Anular venta"
        onOk={anularVenta}
        onCancel={() => setVentaAnular(null)}
        confirmLoading={anulando}
        okText="Anular"
        width={400}
      >
        <div className="space-y-3 text-sm">
          <p className="text-slate-600">
            ¿Confirma la anulación de la venta <span className="font-semibold">#{ventaAnular?.id}</span>?
          </p>
          {ventaAnular && (
            <div className="bg-red-50 border border-red-100 rounded-xl px-4 py-3 space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Cliente</span>
                <span className="font-medium text-slate-800">{ventaAnular.cliente_nombre || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Monto</span>
                <span className="font-semibold text-emerald-700 tabular-nums">
                  Gs. {(Number(ventaAnular.monto_total) || 0).toLocaleString('es-PY')}
                </span>
              </div>
            </div>
          )}
          <p className="text-xs text-slate-400">Esta acción no se puede deshacer.</p>
        </div>
      </Modal>

      <Modal
        open={showConfirm}
        title="Confirmar cobro"
        onOk={cobrar}
        onCancel={() => setShowConfirm(false)}
        confirmLoading={cobrando}
        okText="Cobrar"
        width={440}
      >
        <div className="space-y-3">
          <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Cliente</span>
              <span className="font-semibold text-slate-800">
                {clientes.find(c => c.id === clienteId)
                  ? `${clientes.find(c => c.id === clienteId)!.nombres} ${clientes.find(c => c.id === clienteId)!.apellidos}`.trim()
                  : tarjeta?.cliente_nombre || '—'}
              </span>
            </div>
            {tarjeta && (
              <div className="flex justify-between">
                <span className="text-slate-500">Alumno</span>
                <span className="font-medium text-slate-700">{tarjeta.hijo_nombre}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-500">Tipo</span>
              <span className="font-medium text-slate-700">{tipoVenta}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Productos</span>
              <span className="font-medium text-slate-700">{carrito.length} ítem{carrito.length !== 1 ? 's' : ''}</span>
            </div>
          </div>
          <div className="flex justify-between items-center px-4 py-3 bg-green-50 rounded-xl border border-green-100">
            <span className="text-base font-bold text-slate-700">TOTAL</span>
            <span className="text-xl font-extrabold text-emerald-700 tabular-nums">
              Gs. {total.toLocaleString('es-PY')}
            </span>
          </div>
        </div>
      </Modal>
    </div>
  )
}