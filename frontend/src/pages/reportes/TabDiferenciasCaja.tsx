import { useState } from 'react'
import toast from 'react-hot-toast'
import { AlertTriangle, Download } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import {
  formatGs, descargaBlob, fmtGsShort, primerDiaMes, today,
  FilterBar, EmptyState, KpiCard,
  type DiferenciasCajaData,
} from './shared'

export default function TabDiferenciasCaja() {
  const [dcDesde, setDcDesde] = useState(primerDiaMes())
  const [dcHasta, setDcHasta] = useState(today())
  const [dcData, setDcData] = useState<DiferenciasCajaData | null>(null)
  const [loadingDc, setLoadingDc] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

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

  return (
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
  )
}
