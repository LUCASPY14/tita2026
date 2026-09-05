import { useState } from 'react'
import toast from 'react-hot-toast'
import { ShieldAlert, RefreshCw, Monitor } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import { formatFecha, ROL_LABEL } from './reportesUtils'
import {
  EmptyState, KpiCard,
  type ActividadAccesoData,
} from './shared'

export default function TabActividadAcceso() {
  const [data, setData] = useState<ActividadAccesoData | null>(null)
  const [loading, setLoading] = useState(false)

  async function buscar() {
    setLoading(true)
    try {
      const { data: res } = await api.get('/usuarios/reporte-actividad-acceso/')
      setData(res)
    } catch { toast.error('Error al cargar actividad de acceso') }
    finally { setLoading(false) }
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Sesiones activas ahora mismo y alertas de seguridad de acceso (IP nueva para
          personal, o cuenta del portal con sesiones simultáneas desde IPs distintas).
        </p>
        <Button onClick={buscar} loading={loading}>
          <RefreshCw className="w-4 h-4" /> Actualizar
        </Button>
      </div>

      {data && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <KpiCard label="Sesiones activas ahora" value={data.sesiones_activas.length} />
            <KpiCard
              label="Alertas de seguridad recientes"
              value={data.alertas_seguridad.length}
              color={data.alertas_seguridad.length > 0 ? 'text-orange-600' : 'text-slate-600'}
            />
          </div>

          {data.alertas_seguridad.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
              <p className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-orange-500" /> Alertas de seguridad
              </p>
              <div className="space-y-2">
                {data.alertas_seguridad.map((a, i) => (
                  <div key={i} className="bg-orange-50 border border-orange-100 rounded-xl px-4 py-2.5">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold text-orange-900 text-sm">{a.titulo}</p>
                      <span className="text-xs text-orange-500 tabular-nums whitespace-nowrap">{formatFecha(a.fecha_envio)}</span>
                    </div>
                    <p className="text-slate-600 text-sm mt-0.5">{a.mensaje}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.sesiones_activas.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
              <p className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <Monitor className="w-4 h-4 text-slate-500" /> Sesiones activas
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 text-left">
                      {['Usuario', 'Rol', 'IP', 'Dispositivo', 'Desde', 'Última actividad'].map(h => (
                        <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {data.sesiones_activas.map((s, i) => (
                      <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="py-2.5 pr-4">
                          <p className="font-medium text-slate-800">{s.usuario_nombre}</p>
                          <p className="text-xs text-slate-400">{s.usuario_email}</p>
                        </td>
                        <td className="py-2.5 pr-4 text-slate-600 text-xs">
                          {ROL_LABEL[s.rol as keyof typeof ROL_LABEL] ?? s.rol}
                        </td>
                        <td className="py-2.5 pr-4 font-mono text-xs text-slate-700">{s.ip_address ?? '—'}</td>
                        <td className="py-2.5 pr-4 text-xs text-slate-500 max-w-[220px] truncate" title={s.user_agent ?? ''}>
                          {s.user_agent ?? '—'}
                        </td>
                        <td className="py-2.5 pr-4 tabular-nums text-slate-400 text-xs whitespace-nowrap">{formatFecha(s.fecha_inicio)}</td>
                        <td className="py-2.5 tabular-nums text-slate-400 text-xs whitespace-nowrap">{formatFecha(s.ultima_actividad)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {!data && !loading && (
        <EmptyState icon={<ShieldAlert className="w-full h-full" />} text='Hacé clic en "Actualizar" para ver la actividad de acceso' />
      )}
    </>
  )
}
