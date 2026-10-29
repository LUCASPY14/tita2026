import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Save } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import { extractErrorMessage, inputClass, labelClass, type Grado } from './helpers'

interface ConfiguracionAlmuerzo {
  id_configuracion_almuerzo: number
  grado_desde: number | null
  grado_hasta: number | null
  grado_desde_nombre: string | null
  grado_hasta_nombre: string | null
}

export default function TabConfigAlmuerzo() {
  const [grados, setGrados] = useState<Grado[]>([])
  const [config, setConfig] = useState<ConfiguracionAlmuerzo | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [gradoDesde, setGradoDesde] = useState<number | ''>('')
  const [gradoHasta, setGradoHasta] = useState<number | ''>('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [gradosRes, configRes] = await Promise.all([
        api.get('/clientes/grados/', { params: { page_size: 100, activo: true } }),
        api.get('/almuerzos/configuracion/', { params: { page_size: 1 } }),
      ])
      setGrados(gradosRes.data.results ?? gradosRes.data ?? [])
      const actual: ConfiguracionAlmuerzo | null = (configRes.data.results ?? configRes.data ?? [])[0] ?? null
      setConfig(actual)
      setGradoDesde(actual?.grado_desde ?? '')
      setGradoHasta(actual?.grado_hasta ?? '')
    } catch {
      toast.error('Error al cargar la configuración de almuerzo')
    } finally {
      setLoading(false)
    }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  const guardar = useCallback(async () => {
    if ((gradoDesde === '') !== (gradoHasta === '')) {
      toast.error('Definí los dos extremos del rango, o dejalos vacíos los dos')
      return
    }
    setSaving(true)
    try {
      const payload = {
        grado_desde: gradoDesde === '' ? null : gradoDesde,
        grado_hasta: gradoHasta === '' ? null : gradoHasta,
      }
      const { data } = config
        ? await api.put(`/almuerzos/configuracion/${config.id_configuracion_almuerzo}/`, payload)
        : await api.post('/almuerzos/configuracion/', payload)
      setConfig(data)
      toast.success('Configuración guardada')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }, [config, gradoDesde, gradoHasta])

  if (loading) {
    return <div className="py-10 text-center text-slate-400 text-sm">Cargando...</div>
  }

  return (
    <div className="max-w-xl space-y-5">
      <div className="bg-blue-50 border border-blue-100 rounded-2xl px-5 py-4 text-sm text-slate-700 space-y-1.5">
        <p>
          Definí el rango de grados que pueden cargar <strong>saldo de almuerzo</strong> — tanto los padres
          desde el portal como caja/cobranza desde el panel interno. Fuera de ese rango, la carga queda bloqueada.
        </p>
        <p className="text-slate-500">Dejá los dos campos vacíos para no aplicar ninguna restricción.</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Grado desde</label>
            <select
              value={gradoDesde}
              onChange={e => setGradoDesde(e.target.value ? Number(e.target.value) : '')}
              className={inputClass}
            >
              <option value="">Sin restricción</option>
              {grados.map(g => (
                <option key={g.id_grado} value={g.id_grado}>{g.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Grado hasta</label>
            <select
              value={gradoHasta}
              onChange={e => setGradoHasta(e.target.value ? Number(e.target.value) : '')}
              className={inputClass}
            >
              <option value="">Sin restricción</option>
              {grados.map(g => (
                <option key={g.id_grado} value={g.id_grado}>{g.nombre}</option>
              ))}
            </select>
          </div>
        </div>
        <div className="flex justify-end">
          <Button variant="primary" onClick={guardar} loading={saving}>
            <Save className="w-4 h-4" /> Guardar
          </Button>
        </div>
      </div>
    </div>
  )
}
