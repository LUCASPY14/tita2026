import { useState } from 'react'
import toast from 'react-hot-toast'
import { UtensilsCrossed, Download } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import {
  formatGs, descargaBlob, primerDiaMes, today,
  FilterBar, EmptyState, KpiCard,
  type ConsumoGradoData,
} from './shared'

export default function TabConsumoGrado() {
  const [cgDesde, setCgDesde] = useState(primerDiaMes())
  const [cgHasta, setCgHasta] = useState(today())
  const [cgData, setCgData] = useState<ConsumoGradoData | null>(null)
  const [loadingCg, setLoadingCg] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

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

  return (
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
  )
}
