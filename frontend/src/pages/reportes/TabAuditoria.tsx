import { useState } from 'react'
import toast from 'react-hot-toast'
import { Shield, Download } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import { formatFecha, descargaBlob, primerDiaMes, today } from './reportesUtils'
import {
  FilterBar, EmptyState, KpiCard,
  type AuditoriaData,
} from './shared'

export default function TabAuditoria() {
  const [audDesde, setAudDesde] = useState(primerDiaMes())
  const [audHasta, setAudHasta] = useState(today())
  const [audOperacion, setAudOperacion] = useState('')
  const [audTabla, setAudTabla] = useState('')
  const [audResultado, setAudResultado] = useState('')
  const [audData, setAudData] = useState<AuditoriaData | null>(null)
  const [loadingAud, setLoadingAud] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarAuditoria() {
    if (!audDesde || !audHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingAud(true)
    try {
      const params: Record<string, string> = { desde: audDesde, hasta: audHasta }
      if (audOperacion) params.operacion = audOperacion
      if (audTabla) params.tabla = audTabla
      if (audResultado) params.resultado = audResultado
      const { data: res } = await api.get('/usuarios/reporte-auditoria/', { params })
      setAudData(res)
    } catch { toast.error('Error al cargar reporte de auditoría') }
    finally { setLoadingAud(false) }
  }

  async function exportarAudCSV() {
    try {
      const params: Record<string, string> = { desde: audDesde, hasta: audHasta, formato: 'csv' }
      if (audOperacion) params.operacion = audOperacion
      if (audTabla) params.tabla = audTabla
      if (audResultado) params.resultado = audResultado
      const res = await api.get('/usuarios/reporte-auditoria/', { params, responseType: 'blob' })
      descargaBlob(res.data, `auditoria_${audDesde}_${audHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  return (
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
          <select value={audOperacion} onChange={e => setAudOperacion(e.target.value)} className={inputDateClass}>
            <option value="">Todas</option>
            {['CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'ACCESS'].map(o => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Resultado</label>
          <select value={audResultado} onChange={e => setAudResultado(e.target.value)} className={inputDateClass}>
            <option value="">Todos</option>
            <option value="EXITO">Éxito</option>
            <option value="FALLA">Falla</option>
          </select>
        </div>
        <Button onClick={buscarAuditoria} loading={loadingAud}>Buscar</Button>
        {audData && (
          <Button variant="secondary" onClick={exportarAudCSV}><Download className="w-4 h-4" />CSV</Button>
        )}
      </FilterBar>

      {audTabla && (
        <div className="flex gap-2 items-center">
          <span className="text-xs text-slate-500">Tabla:</span>
          <span className="text-xs bg-slate-100 rounded-full px-2 py-0.5 font-mono text-slate-700">{audTabla}</span>
          <button onClick={() => setAudTabla('')} className="text-xs text-slate-400 hover:text-slate-600">×</button>
        </div>
      )}

      {audData && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <KpiCard label="Total eventos" value={audData.resumen.total_eventos} />
            <KpiCard label="Éxito" value={audData.resumen.por_resultado.EXITO ?? 0} color="text-green-700" />
            <KpiCard label="Fallas"
              value={audData.resumen.por_resultado.FALLA ?? 0}
              color={(audData.resumen.por_resultado.FALLA ?? 0) > 0 ? 'text-red-600' : 'text-slate-600'} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {audData.top_operaciones.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Top operaciones</p>
                <div className="space-y-2">
                  {audData.top_operaciones.map(op => (
                    <div key={op.operacion} className="flex items-center justify-between">
                      <span className="font-mono text-xs bg-slate-100 rounded px-2 py-0.5 text-slate-700">{op.operacion}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">{op.n} eventos</span>
                        <button
                          onClick={() => { setAudOperacion(op.operacion ?? ''); buscarAuditoria() }}
                          className="text-xs text-green-600 hover:underline"
                        >filtrar</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {audData.top_tablas.length > 0 && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <p className="text-sm font-semibold text-slate-700 mb-3">Top tablas afectadas</p>
                <div className="space-y-2">
                  {audData.top_tablas.map(t => (
                    <div key={t.tabla} className="flex items-center justify-between">
                      <span className="font-mono text-xs bg-slate-100 rounded px-2 py-0.5 text-slate-700">{t.tabla}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">{t.n} eventos</span>
                        <button
                          onClick={() => { setAudTabla(t.tabla ?? ''); buscarAuditoria() }}
                          className="text-xs text-green-600 hover:underline"
                        >filtrar</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {audData.detalle.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
              <p className="text-sm font-semibold text-slate-700 mb-3">Detalle de eventos</p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-left">
                      {['Fecha', 'Usuario', 'Operación', 'Tabla', 'ID', 'Resultado', 'IP'].map(h => (
                        <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {audData.detalle.map((r, i) => (
                      <tr key={`${r.fecha}-${i}`} className="hover:bg-slate-50 transition-colors">
                        <td className="py-2.5 pr-4 tabular-nums text-slate-500 whitespace-nowrap">{formatFecha(r.fecha)}</td>
                        <td className="py-2.5 pr-4 text-slate-700">{r.usuario ?? <span className="text-slate-300">—</span>}</td>
                        <td className="py-2.5 pr-4">
                          <span className="font-mono text-xs bg-slate-100 rounded px-1.5 py-0.5 text-slate-700">{r.operacion}</span>
                        </td>
                        <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">{r.tabla ?? '—'}</td>
                        <td className="py-2.5 pr-4 tabular-nums text-slate-400 text-xs">{r.objeto_id ?? '—'}</td>
                        <td className="py-2.5 pr-4">
                          <span className={`text-xs font-semibold ${r.resultado === 'EXITO' ? 'text-green-700' : 'text-red-600'}`}>
                            {r.resultado}
                          </span>
                        </td>
                        <td className="py-2.5 font-mono text-xs text-slate-400">{r.ip ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {audData.resumen.total_eventos > audData.detalle.length && (
                <p className="text-xs text-slate-400 mt-3 text-center">
                  Mostrando {audData.detalle.length} de {audData.resumen.total_eventos} eventos. Exportá en CSV para ver todos.
                </p>
              )}
            </div>
          )}
        </>
      )}

      {!audData && !loadingAud && (
        <EmptyState icon={<Shield className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
      )}
    </>
  )
}
