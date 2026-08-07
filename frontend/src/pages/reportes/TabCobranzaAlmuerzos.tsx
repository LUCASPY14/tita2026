import { useState } from 'react'
import toast from 'react-hot-toast'
import { DollarSign, Download } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import { formatGs, descargaBlob, FORMA_COBRO_LABEL } from './reportesUtils'
import {
  FilterBar, EmptyState, KpiCard,
  type CobranzaAlmuerzosData,
} from './shared'

export default function TabCobranzaAlmuerzos() {
  const [cbAnio, setCbAnio] = useState(new Date().getFullYear())
  const [cbData, setCbData] = useState<CobranzaAlmuerzosData | null>(null)
  const [loadingCb, setLoadingCb] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarCobranza() {
    setLoadingCb(true)
    try {
      const { data: res } = await api.get('/almuerzos/reporte-cobranza/', { params: { anio: cbAnio } })
      setCbData(res)
    } catch { toast.error('Error al cargar reporte de cobranza') }
    finally { setLoadingCb(false) }
  }

  async function exportarCbCSV() {
    try {
      const res = await api.get('/almuerzos/reporte-cobranza/', { params: { anio: cbAnio, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `cobranza_almuerzos_${cbAnio}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  async function exportarCbExcel() {
    try {
      const res = await api.get('/almuerzos/reporte-cobranza/', { params: { anio: cbAnio, formato: 'excel' }, responseType: 'blob' })
      descargaBlob(res.data, `cobranza_almuerzos_${cbAnio}.xlsx`)
      toast.success('Excel descargado')
    } catch { toast.error('Error al exportar') }
  }

  const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Año</label>
          <select value={cbAnio} onChange={e => setCbAnio(Number(e.target.value))} className={inputDateClass}>
            {[new Date().getFullYear() - 1, new Date().getFullYear()].map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <Button onClick={buscarCobranza} loading={loadingCb}>Buscar</Button>
        {cbData && (
          <>
            <Button variant="secondary" onClick={exportarCbCSV}><Download className="w-4 h-4" />CSV</Button>
            <Button variant="secondary" onClick={exportarCbExcel}><Download className="w-4 h-4" />Excel</Button>
          </>
        )}
      </FilterBar>

      {cbData && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <KpiCard label="Total cobrado" value={formatGs(cbData.resumen.cobrado_anual)} color="text-green-700" />
            <KpiCard label="Pendiente" value={formatGs(cbData.resumen.pendiente_anual)}
              color={cbData.resumen.pendiente_anual > 0 ? 'text-orange-600' : 'text-slate-600'} />
            <KpiCard label="Familias con deuda" value={cbData.saldos_pendientes.length}
              color={cbData.saldos_pendientes.length > 0 ? 'text-red-600' : 'text-slate-600'} />
            <KpiCard label="% Cobrado" value={`${cbData.resumen.tasa_cobro_anual}%`}
              color={cbData.resumen.tasa_cobro_anual >= 90 ? 'text-green-700' : 'text-orange-600'} />
          </div>

          {cbData.por_mes.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
              <p className="text-sm font-semibold text-slate-700 mb-4">Tendencia mensual de cobranza {cbAnio}</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={cbData.por_mes.map(m => ({ mes: MESES[m.mes - 1], cobrado: m.monto_cobrado, pendiente: m.monto_pendiente }))}
                  margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="mes" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false}
                    tickFormatter={v => `${(v / 1_000_000).toFixed(0)}M`} />
                  <Tooltip
                    formatter={(v) => [formatGs(Number(v))]}
                    contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }}
                  />
                  <Legend />
                  <Bar dataKey="cobrado" name="Cobrado" fill="#22c55e" radius={[4, 4, 0, 0]} stackId="a" />
                  <Bar dataKey="pendiente" name="Pendiente" fill="#f97316" radius={[4, 4, 0, 0]} stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {cbData.por_mes.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
              <p className="text-sm font-semibold text-slate-700 mb-3">Cobranza por mes</p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-left">
                      {['Mes', 'Consumido', 'Cobrado', 'Diferencia', '% Cobrado'].map(h => (
                        <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {cbData.por_mes.map(m => (
                      <tr key={m.mes} className="hover:bg-slate-50 transition-colors">
                        <td className="py-2.5 pr-4 font-medium text-slate-800">{MESES[m.mes - 1]}</td>
                        <td className="py-2.5 pr-4 tabular-nums text-slate-700">{formatGs(m.monto_total)}</td>
                        <td className="py-2.5 pr-4 tabular-nums text-green-700 font-semibold">{formatGs(m.monto_cobrado)}</td>
                        <td className="py-2.5 pr-4 tabular-nums text-orange-600">{m.monto_pendiente > 0 ? formatGs(m.monto_pendiente) : '—'}</td>
                        <td className="py-2.5 pr-4">
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
          )}

          {cbData.por_forma_cobro.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
              <p className="text-sm font-semibold text-slate-700 mb-3">Recargas por método de pago</p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-left">
                      {['Método de Pago', 'N° Recargas', 'Monto Cobrado', '% del Total'].map(h => (
                        <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {cbData.por_forma_cobro.map(f => {
                      const porcentaje = cbData.resumen.cobrado_anual > 0
                        ? Math.round((f.monto_cobrado / cbData.resumen.cobrado_anual) * 1000) / 10
                        : 0
                      return (
                        <tr key={f.forma_cobro} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 pr-4 font-medium text-slate-800">
                            {FORMA_COBRO_LABEL[f.forma_cobro as keyof typeof FORMA_COBRO_LABEL] ?? f.forma_cobro}
                          </td>
                          <td className="py-2.5 pr-4 tabular-nums text-slate-600">{f.n_recargas}</td>
                          <td className="py-2.5 pr-4 tabular-nums font-bold text-slate-800">{formatGs(f.monto_cobrado)}</td>
                          <td className="py-2.5 tabular-nums text-slate-500">{porcentaje}%</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {cbData.saldos_pendientes.length > 0 && (
            <div className="bg-white rounded-2xl border border-red-100 shadow-sm p-4">
              <p className="text-sm font-semibold text-slate-700 mb-3">
                Saldos negativos actuales <span className="text-slate-400 font-normal">— cuenta corriente, no por mes</span>
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-left">
                      {['Alumno', 'Grado', 'Saldo'].map(h => (
                        <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {cbData.saldos_pendientes.map(s => (
                      <tr key={s.hijo_id} className="hover:bg-slate-50 transition-colors">
                        <td className="py-2.5 pr-4 font-medium text-slate-800">{s.hijo}</td>
                        <td className="py-2.5 pr-4 text-slate-500">{s.grado ?? '—'}</td>
                        <td className="py-2.5 tabular-nums font-bold text-red-600">{formatGs(s.saldo_actual)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {!cbData && !loadingCb && (
        <EmptyState icon={<DollarSign className="w-full h-full" />} text='Seleccioná un año y hacé clic en "Buscar"' />
      )}
    </>
  )
}
