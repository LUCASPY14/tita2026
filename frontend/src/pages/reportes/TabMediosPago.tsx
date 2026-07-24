import { useState } from 'react'
import toast from 'react-hot-toast'
import { CreditCard, Download } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import {
  formatGs, descargaBlob, primerDiaMes, today,
  FilterBar, EmptyState, KpiCard,
  type MediosPagoData,
} from './shared'

export default function TabMediosPago() {
  const [mpDesde, setMpDesde] = useState(primerDiaMes())
  const [mpHasta, setMpHasta] = useState(today())
  const [mpData, setMpData] = useState<MediosPagoData | null>(null)
  const [loadingMp, setLoadingMp] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

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

  return (
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
  )
}
