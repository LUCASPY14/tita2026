import { useState } from 'react'
import toast from 'react-hot-toast'
import { BarChart2, Search, TrendingUp, ShoppingCart, FileText, Download } from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import api from '../../services/api'
import { exportarReporteVentasPDF } from '../../utils/pdf'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import { formatGs, formatFecha, descargaBlob, fmtGsShort, clientSort, today, TIPO_LABEL, CHART_COLORS } from './reportesUtils'
import {
  FilterBar, EmptyState,
  type ReporteData, type VentaTipo, type CierreCajaReporte, type TendenciaPoint,
} from './shared'

export default function TabVentas() {
  const t0 = today()
  const [desde, setDesde] = useState(t0)
  const [hasta, setHasta] = useState(t0)
  const [data, setData] = useState<ReporteData | null>(null)
  const [tendencia, setTendencia] = useState<TendenciaPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [sortTipo, setSortTipo] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)
  const [sortCierres, setSortCierres] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

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

  const tipoSorted = sortTipo && data ? clientSort(data.ventas.por_tipo, sortTipo.key, sortTipo.dir) : (data?.ventas.por_tipo ?? [])
  const cierresSorted = sortCierres && data ? clientSort(data.cierres_caja, sortCierres.key, sortCierres.dir) : (data?.cierres_caja ?? [])

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

  return (
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
  )
}
