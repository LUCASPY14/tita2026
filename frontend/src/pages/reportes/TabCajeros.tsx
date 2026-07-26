import { useState } from 'react'
import toast from 'react-hot-toast'
import { UserCheck, Search, Download, FileText } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import {
  formatGs, descargaBlob, fmtGsShort, today,
  FilterBar, EmptyState, KpiCard,
  type CajerosData, type CajeroVenta,
} from './shared'

export default function TabCajeros() {
  const t0 = today()
  const [desdeCaj, setDesdeCaj] = useState(t0)
  const [hastaCaj, setHastaCaj] = useState(t0)
  const [cajerosData, setCajerosData] = useState<CajerosData | null>(null)
  const [loadingCaj, setLoadingCaj] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarCajeros() {
    if (!desdeCaj || !hastaCaj) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingCaj(true)
    try {
      const { data: res } = await api.get('/ventas/reporte-cajeros/', { params: { desde: desdeCaj, hasta: hastaCaj } })
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

  return (
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
  )
}
