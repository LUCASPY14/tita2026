import { useState } from 'react'
import toast from 'react-hot-toast'
import { Users, CheckCircle } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import { formatFecha, ROL_LABEL } from './reportesUtils'
import {
  FilterBar, EmptyState, KpiCard,
  type PersonalInactivoData,
} from './shared'

export default function TabPersonalInactivo() {
  const [piDias, setPiDias] = useState(30)
  const [piData, setPiData] = useState<PersonalInactivoData | null>(null)
  const [loadingPi, setLoadingPi] = useState(false)

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarPersonalInactivo() {
    setLoadingPi(true)
    try {
      const { data: res } = await api.get('/usuarios/reporte-personal-inactivo/', { params: { dias: piDias } })
      setPiData(res)
    } catch { toast.error('Error al cargar personal inactivo') }
    finally { setLoadingPi(false) }
  }

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Inactivo hace más de</label>
          <div className="flex items-center gap-2">
            <input
              type="number" min={1} max={365} value={piDias}
              onChange={e => setPiDias(Number(e.target.value))}
              className={`${inputClass} w-24`}
            />
            <span className="text-sm text-slate-500">días</span>
          </div>
        </div>
        <Button onClick={buscarPersonalInactivo} loading={loadingPi}>Buscar</Button>
      </FilterBar>

      {piData && (
        <>
          {piData.resumen.total_inactivos === 0 ? (
            <div className="bg-green-50 border border-green-200 rounded-2xl px-4 py-8 flex flex-col items-center gap-3">
              <CheckCircle className="w-10 h-10 text-green-500" />
              <p className="text-green-700 font-semibold text-center">
                Sin personal inactivo en los últimos {piDias} días
              </p>
              <p className="text-sm text-green-600 text-center">Todos los empleados registraron actividad reciente.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <KpiCard label="Personal inactivo" value={piData.resumen.total_inactivos}
                  color={piData.resumen.total_inactivos > 0 ? 'text-orange-600' : 'text-slate-600'} />
                <KpiCard label="Promedio días sin actividad" value={`${piData.resumen.promedio_dias_inactivo}d`} />
                <KpiCard label="Máx. días sin actividad" value={`${piData.resumen.max_dias_inactivo}d`}
                  color={piData.resumen.max_dias_inactivo > 90 ? 'text-red-600' : 'text-slate-600'} />
              </div>

              {piData.por_rol.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Personal inactivo por rol</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {piData.por_rol.map(r => (
                      <div key={r.rol} className="bg-slate-50 rounded-xl p-3 text-center">
                        <p className="text-2xl font-bold tabular-nums text-orange-600">{r.n}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {ROL_LABEL[r.rol as keyof typeof ROL_LABEL] ?? r.rol}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {piData.detalle.length > 0 && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                  <p className="text-sm font-semibold text-slate-700 mb-3">Detalle de personal inactivo</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-slate-100 text-left">
                          {['Nombre', 'Email', 'Rol', 'Última actividad', 'Días sin actividad'].map(h => (
                            <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-50">
                        {piData.detalle.map(r => (
                          <tr key={r.usuario_id} className="hover:bg-slate-50 transition-colors">
                            <td className="py-2.5 pr-4 font-medium text-slate-800">{r.nombre}</td>
                            <td className="py-2.5 pr-4 text-slate-500 text-xs">{r.email}</td>
                            <td className="py-2.5 pr-4 text-slate-600 text-xs">
                              {ROL_LABEL[r.rol as keyof typeof ROL_LABEL] ?? r.rol}
                            </td>
                            <td className="py-2.5 pr-4 tabular-nums text-slate-400 text-xs whitespace-nowrap">
                              {r.ultima_actividad ? formatFecha(r.ultima_actividad) : <span className="text-slate-300">Nunca</span>}
                            </td>
                            <td className="py-2.5">
                              <span className={`tabular-nums font-bold text-sm ${r.dias_inactivo > 90 ? 'text-red-600' : r.dias_inactivo > 30 ? 'text-orange-600' : 'text-yellow-600'}`}>
                                {r.dias_inactivo}d
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}

      {!piData && !loadingPi && (
        <EmptyState icon={<Users className="w-full h-full" />} text='Seleccioná el umbral de días y hacé clic en "Buscar"' />
      )}
    </>
  )
}
