import { useState } from 'react'
import toast from 'react-hot-toast'
import { BarChart2, Search, TrendingUp, ShoppingCart, FileText, Download, Users, AlertTriangle } from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface VentaTipo {
  tipo: string
  cantidad: number
  monto: number
}

interface CierreCajaReporte {
  id: number
  caja: string
  fecha_apertura: string
  fecha_cierre: string
  monto_inicial: number
  monto_contado_fisico: number
  diferencia: number
}

interface ReporteData {
  periodo: { desde: string; hasta: string }
  ventas: {
    cantidad: number
    monto_total: number
    por_tipo: VentaTipo[]
  }
  cierres_caja: CierreCajaReporte[]
}

interface AgingItem {
  cliente_id: number
  cliente: string
  ruc_ci: string
  telefono: string
  email: string
  saldo_deuda: number
  dias_atraso: number
  aging: string
}

interface CuentaCorrienteData {
  fecha: string
  resumen: {
    clientes_con_deuda: number
    total_deuda: number
    aging: {
      '0-30': number
      '31-60': number
      '61-90': number
      '90+': number
    }
  }
  detalle: AgingItem[]
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

const TIPO_LABEL: Record<string, string> = {
  VENTA_TARJETA: 'Tarjeta prepago',
  VENTA_EFECTIVO: 'Efectivo',
  CONSUMO_ALMUERZO: 'Almuerzo',
  CARGA_SALDO: 'Carga de saldo',
}

const AGING_COLOR: Record<string, BadgeColor> = {
  '0-30': 'green',
  '31-60': 'yellow',
  '61-90': 'orange',
  '90+': 'red',
}

type TabKey = 'ventas' | 'cuenta_corriente'

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Reportes() {
  const [tab, setTab] = useState<TabKey>('ventas')

  // ── Ventas tab ───────────────────────────────────────────────────
  const today = new Date().toISOString().split('T')[0]
  const [desde, setDesde] = useState(today)
  const [hasta, setHasta] = useState(today)
  const [data, setData] = useState<ReporteData | null>(null)
  const [loading, setLoading] = useState(false)

  async function buscar() {
    if (!desde || !hasta) { toast.error('Seleccioná ambas fechas'); return }
    if (desde > hasta) { toast.error('La fecha Desde no puede ser mayor a Hasta'); return }
    setLoading(true)
    try {
      const { data: res } = await api.get('/contabilidad/reportes/', {
        params: { fecha_desde: desde, fecha_hasta: hasta },
      })
      setData(res)
    } catch {
      toast.error('Error al cargar el reporte')
    } finally {
      setLoading(false)
    }
  }

  async function exportarCSV() {
    if (!desde || !hasta) { toast.error('Seleccioná un período primero'); return }
    try {
      const response = await api.get('/contabilidad/reportes/', {
        params: { fecha_desde: desde, fecha_hasta: hasta, formato: 'csv' },
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `reporte_${desde}_${hasta}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.success('CSV descargado')
    } catch {
      toast.error('Error al exportar')
    }
  }

  // ── Cuenta corriente tab ─────────────────────────────────────────
  const [ccData, setCcData] = useState<CuentaCorrienteData | null>(null)
  const [loadingCc, setLoadingCc] = useState(false)
  const [searchCc, setSearchCc] = useState('')

  async function cargarCuentaCorriente() {
    setLoadingCc(true)
    try {
      const { data: res } = await api.get('/clientes/reporte-cuenta-corriente/')
      setCcData(res)
    } catch {
      toast.error('Error al cargar cuenta corriente')
    } finally {
      setLoadingCc(false)
    }
  }

  // ── Columns ──────────────────────────────────────────────────────

  const columnsTipo: Column<VentaTipo>[] = [
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => (
        <span className="text-sm font-medium text-slate-700">{TIPO_LABEL[r.tipo] ?? r.tipo}</span>
      ),
    },
    {
      title: 'Cantidad',
      key: 'cantidad',
      dataIndex: 'cantidad',
      render: v => <span className="tabular-nums font-semibold text-slate-800">{v as number}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => (
        <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto)}</span>
      ),
    },
  ]

  const columnsCierres: Column<CierreCajaReporte>[] = [
    { title: 'Caja', key: 'caja', dataIndex: 'caja' },
    {
      title: 'Apertura',
      key: 'apertura',
      render: (_, r) => <span className="text-sm text-slate-600">{formatFecha(r.fecha_apertura)}</span>,
    },
    {
      title: 'Cierre',
      key: 'cierre',
      render: (_, r) => <span className="text-sm text-slate-600">{formatFecha(r.fecha_cierre)}</span>,
    },
    {
      title: 'Inicial',
      key: 'inicial',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.monto_inicial)}</span>,
    },
    {
      title: 'Contado',
      key: 'contado',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.monto_contado_fisico)}</span>,
    },
    {
      title: 'Diferencia',
      key: 'dif',
      render: (_, r) => {
        const n = r.diferencia
        return (
          <Badge color={n === 0 ? 'green' : n > 0 ? 'blue' : 'red'}>
            {n > 0 ? '+' : ''}{formatGs(n)}
          </Badge>
        )
      },
    },
  ]

  const colsDetalle: Column<AgingItem>[] = [
    {
      title: 'Cliente',
      key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-sm font-medium text-slate-800">{r.cliente}</p>
          <p className="text-xs text-slate-400">{r.ruc_ci}</p>
        </div>
      ),
    },
    {
      title: 'Contacto',
      key: 'contacto',
      render: (_, r) => (
        <div>
          <p className="text-xs text-slate-500">{r.telefono || '—'}</p>
          <p className="text-xs text-slate-400">{r.email || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Saldo Deuda',
      key: 'saldo',
      render: (_, r) => (
        <span className="tabular-nums font-bold text-red-600">{formatGs(r.saldo_deuda)}</span>
      ),
    },
    {
      title: 'Días Atraso',
      key: 'dias',
      render: (_, r) => (
        <span className={`tabular-nums font-semibold text-sm ${r.dias_atraso > 60 ? 'text-red-600' : r.dias_atraso > 30 ? 'text-orange-600' : 'text-slate-700'}`}>
          {r.dias_atraso}d
        </span>
      ),
    },
    {
      title: 'Aging',
      key: 'aging',
      render: (_, r) => <Badge color={AGING_COLOR[r.aging] ?? 'default'}>{r.aging}</Badge>,
    },
  ]

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const ccDetalleFiltrado = (ccData?.detalle ?? []).filter(d =>
    !searchCc || d.cliente.toLowerCase().includes(searchCc.toLowerCase()) || d.ruc_ci.includes(searchCc)
  )

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Reportes</h1>
        <p className="text-sm text-slate-500 mt-0.5">Análisis de ventas, cierres y cuenta corriente</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          <button
            onClick={() => setTab('ventas')}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              tab === 'ventas' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <BarChart2 className="w-4 h-4" />
            Ventas y Cierres
          </button>
          <button
            onClick={() => { setTab('cuenta_corriente'); if (!ccData && !loadingCc) cargarCuentaCorriente() }}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
              tab === 'cuenta_corriente' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Users className="w-4 h-4" />
            Cuenta Corriente Clientes
          </button>
        </div>
      </div>

      {/* ── Ventas tab ───────────────────────────────────────────── */}
      {tab === 'ventas' && (
        <>
          {/* Filter bar */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div>
              <label className={labelClass}>Desde</label>
              <input
                type="date"
                value={desde}
                onChange={e => setDesde(e.target.value)}
                className={inputDateClass}
              />
            </div>
            <div>
              <label className={labelClass}>Hasta</label>
              <input
                type="date"
                value={hasta}
                onChange={e => setHasta(e.target.value)}
                className={inputDateClass}
              />
            </div>
            <Button variant="primary" loading={loading} onClick={buscar}>
              <Search className="w-4 h-4" />
              Generar Reporte
            </Button>
            {data && (
              <Button variant="secondary" onClick={exportarCSV}>
                <Download className="w-4 h-4" />
                Exportar CSV
              </Button>
            )}
          </div>

          {/* Results */}
          {data && (
            <div className="space-y-5">
              <p className="text-sm text-slate-500">
                Período: <span className="font-semibold text-slate-700">
                  {data.periodo.desde} — {data.periodo.hasta}
                </span>
              </p>

              {/* Summary cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-start gap-4">
                  <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center shrink-0">
                    <TrendingUp className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Total Vendido</p>
                    <p className="text-xl font-bold text-emerald-700 mt-0.5 tabular-nums">
                      {formatGs(data.ventas.monto_total)}
                    </p>
                  </div>
                </div>
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-start gap-4">
                  <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center shrink-0">
                    <ShoppingCart className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Ventas</p>
                    <p className="text-xl font-bold text-blue-700 mt-0.5 tabular-nums">
                      {data.ventas.cantidad}
                    </p>
                  </div>
                </div>
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-start gap-4">
                  <div className="w-10 h-10 bg-purple-50 rounded-xl flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Cierres de Caja</p>
                    <p className="text-xl font-bold text-purple-700 mt-0.5 tabular-nums">
                      {data.cierres_caja.length}
                    </p>
                  </div>
                </div>
              </div>

              {/* Ventas por tipo */}
              {data.ventas.por_tipo.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100">
                    <h2 className="text-sm font-semibold text-slate-800">Ventas por Tipo</h2>
                  </div>
                  <div className="p-1">
                    <Table columns={columnsTipo} dataSource={data.ventas.por_tipo} rowKey="tipo" pageSize={10} />
                  </div>
                </div>
              )}

              {/* Cierres de caja */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">
                    Cierres de Caja ({data.cierres_caja.length})
                  </h2>
                </div>
                <div className="p-1">
                  {data.cierres_caja.length === 0 ? (
                    <p className="text-center text-slate-400 text-sm py-10">
                      No hay cierres de caja en este período.
                    </p>
                  ) : (
                    <Table columns={columnsCierres} dataSource={data.cierres_caja} rowKey="id" pageSize={10} />
                  )}
                </div>
              </div>
            </div>
          )}

          {!data && !loading && (
            <div className="text-center py-20 text-slate-400">
              <BarChart2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm font-medium">Seleccioná un período y generá el reporte</p>
              <p className="text-xs mt-1 text-slate-300">Los datos se cargarán aquí</p>
            </div>
          )}
        </>
      )}

      {/* ── Cuenta corriente tab ──────────────────────────────────── */}
      {tab === 'cuenta_corriente' && (
        <>
          <div className="flex items-center justify-between gap-4">
            <Button variant="secondary" loading={loadingCc} onClick={cargarCuentaCorriente}>
              <Search className="w-4 h-4" />
              Actualizar
            </Button>
            {ccData && (
              <p className="text-xs text-slate-400">Generado: {new Date(ccData.fecha).toLocaleString('es-PY')}</p>
            )}
          </div>

          {loadingCc && !ccData && (
            <div className="text-center py-20 text-slate-400">
              <p className="text-sm">Cargando reporte...</p>
            </div>
          )}

          {ccData && (
            <div className="space-y-5">
              {/* Aging summary */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Total Deuda', value: formatGs(ccData.resumen.total_deuda), color: 'text-red-700' },
                  { label: 'Clientes con Deuda', value: String(ccData.resumen.clientes_con_deuda), color: 'text-slate-800' },
                  { label: '0–30 días', value: formatGs(ccData.resumen.aging['0-30']), color: 'text-green-700' },
                  { label: '90+ días', value: formatGs(ccData.resumen.aging['90+']), color: 'text-red-600' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-4">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                    <p className={`text-lg font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
                  </div>
                ))}
              </div>

              {/* Aging breakdown */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">Distribución por Aging</h3>
                <div className="grid grid-cols-4 gap-3">
                  {Object.entries(ccData.resumen.aging).map(([rango, monto]) => (
                    <div key={rango} className="text-center">
                      <p className="text-xs text-slate-400">{rango} días</p>
                      <p className={`text-sm font-bold tabular-nums mt-0.5 ${
                        rango === '90+' ? 'text-red-600' : rango === '61-90' ? 'text-orange-600' : rango === '31-60' ? 'text-yellow-600' : 'text-green-700'
                      }`}>
                        {formatGs(monto)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Alert for overdue */}
              {ccData.resumen.aging['90+'] > 0 && (
                <div className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-2xl px-5 py-3">
                  <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
                  <p className="text-sm text-red-700">
                    <span className="font-semibold">{formatGs(ccData.resumen.aging['90+'])}</span> en deudas con más de 90 días de atraso.
                  </p>
                </div>
              )}

              {/* Detail table */}
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
                  <Table columns={colsDetalle} dataSource={ccDetalleFiltrado} rowKey="cliente_id" pageSize={15} />
                </div>
              </div>
            </div>
          )}

          {!ccData && !loadingCc && (
            <div className="text-center py-20 text-slate-400">
              <Users className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p className="text-sm font-medium">Hacé clic en "Actualizar" para cargar el reporte</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
