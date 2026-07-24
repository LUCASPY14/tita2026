import { useState } from 'react'
import toast from 'react-hot-toast'
import { LogIn, Download } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import {
  descargaBlob, primerDiaMes, today,
  FilterBar, EmptyState, KpiCard,
  type IntentosLoginData,
} from './shared'

export default function TabIntentosLogin() {
  const [ilDesde, setIlDesde] = useState(primerDiaMes())
  const [ilHasta, setIlHasta] = useState(today())
  const [ilData, setIlData] = useState<IntentosLoginData | null>(null)
  const [loadingIl, setLoadingIl] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarIntentosLogin() {
    if (!ilDesde || !ilHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingIl(true)
    try {
      const { data: res } = await api.get('/usuarios/reporte-intentos-login/', { params: { desde: ilDesde, hasta: ilHasta } })
      setIlData(res)
    } catch { toast.error('Error al cargar reporte de intentos de login') }
    finally { setLoadingIl(false) }
  }

  async function exportarIlCSV() {
    try {
      const res = await api.get('/usuarios/reporte-intentos-login/', { params: { desde: ilDesde, hasta: ilHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `intentos_login_${ilDesde}_${ilHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  return (
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
        {ilData && (
          <Button variant="secondary" onClick={exportarIlCSV}><Download className="w-4 h-4" />CSV</Button>
        )}
      </FilterBar>

      {ilData && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <KpiCard label="Total intentos" value={ilData.resumen.total_intentos} />
            <KpiCard label="Exitosos" value={ilData.resumen.exitosos} color="text-green-700" />
            <KpiCard label="Fallidos" value={ilData.resumen.fallidos}
              color={ilData.resumen.fallidos > 0 ? 'text-red-600' : 'text-slate-600'} />
            <KpiCard label="IPs bloqueadas" value={ilData.resumen.ips_bloqueadas}
              color={ilData.resumen.ips_bloqueadas > 0 ? 'text-orange-600' : 'text-slate-600'} />
          </div>

          {ilData.por_motivo.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
              <p className="text-sm font-semibold text-slate-700 mb-3">Intentos fallidos por motivo</p>
              <div className="space-y-2">
                {ilData.por_motivo.map(m => (
                  <div key={m.motivo} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                    <span className="text-sm text-slate-600">{m.motivo}</span>
                    <span className="text-sm font-bold tabular-nums text-red-600">{m.n}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {ilData.tendencia.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
              <p className="text-sm font-semibold text-slate-700 mb-4">Tendencia diaria de intentos</p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={ilData.tendencia} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="fecha" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 13 }} />
                  <Legend />
                  <Bar dataKey="exitosos" name="Exitosos" fill="#22c55e" radius={[4, 4, 0, 0]} stackId="a" />
                  <Bar dataKey="fallidos" name="Fallidos" fill="#ef4444" radius={[4, 4, 0, 0]} stackId="a" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {ilData.top_ips.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Top IPs con mayor actividad</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['IP', 'Exitosos', 'Fallidos', 'Bloqueada'].map(h => (
                          <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {ilData.top_ips.map(r => (
                        <tr key={r.ip} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2 pr-4 font-mono text-xs text-slate-700">{r.ip}</td>
                          <td className="py-2 pr-4 tabular-nums text-green-700">{r.exitosos}</td>
                          <td className="py-2 pr-4 tabular-nums text-red-600">{r.fallidos}</td>
                          <td className="py-2">
                            {r.bloqueada
                              ? <span className="text-xs font-semibold text-red-600">Sí</span>
                              : <span className="text-xs text-slate-300">No</span>
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {ilData.top_emails.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Emails con más intentos fallidos</p>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Email', 'Fallidos', 'Último intento'].map(h => (
                          <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {ilData.top_emails.map(r => (
                        <tr key={r.email} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2 pr-4 text-xs text-slate-700">{r.email}</td>
                          <td className="py-2 pr-4 tabular-nums text-red-600 font-semibold">{r.fallidos}</td>
                          <td className="py-2 tabular-nums text-slate-400 text-xs whitespace-nowrap">{r.ultimo_intento}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {!ilData && !loadingIl && (
        <EmptyState icon={<LogIn className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
      )}
    </>
  )
}
