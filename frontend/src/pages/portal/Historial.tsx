import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { ChevronLeft, ChevronRight, UtensilsCrossed } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Hijo {
  id: number
  nombre: string
}

interface Consumo {
  id: number
  fecha_consumo: string
  costo_almuerzo: string | number
  ya_cobrado: boolean
}

interface HistorialData {
  anio: number
  mes: number
  hijo: Hijo
  consumos: Consumo[]
  total: number
  monto_total: number
  cobrados: number
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

function formatGs(n: number | string) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

function formatFecha(iso: string) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('es-PY', {
    weekday: 'short', day: '2-digit', month: '2-digit', year: '2-digit',
  })
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function PortalHistorial() {
  const today = new Date()
  const [anio, setAnio] = useState(today.getFullYear())
  const [mes, setMes] = useState(today.getMonth() + 1)
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [selectedHijo, setSelectedHijo] = useState<number | null>(null)
  const [data, setData] = useState<HistorialData | null>(null)
  const [loading, setLoading] = useState(false)

  // Load hijos list from portal dashboard endpoint
  useEffect(() => {
    api.get('/usuarios/portal/mi-hijo/')
      .then(res => {
        const h: Hijo[] = (res.data.hijos ?? []).map((x: { id: number; nombre: string }) => ({
          id: x.id, nombre: x.nombre,
        }))
        setHijos(h)
        if (h.length > 0) setSelectedHijo(h[0].id)
      })
      .catch(() => toast.error('Error al cargar hijos'))
  }, [])

  const cargar = useCallback(async () => {
    if (!selectedHijo) return
    setLoading(true)
    try {
      const { data: res } = await api.get('/usuarios/portal/historial-consumos/', {
        params: { hijo_id: selectedHijo, anio, mes },
      })
      setData(res)
    } catch {
      toast.error('Error al cargar el historial')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [selectedHijo, anio, mes])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargar() }, [cargar])

  const prevMes = () => {
    if (mes === 1) { setMes(12); setAnio(a => a - 1) }
    else setMes(m => m - 1)
  }

  const nextMes = () => {
    const isCurrentMonth = anio === today.getFullYear() && mes === today.getMonth() + 1
    if (isCurrentMonth) return
    if (mes === 12) { setMes(1); setAnio(a => a + 1) }
    else setMes(m => m + 1)
  }

  const isCurrentMonth = anio === today.getFullYear() && mes === today.getMonth() + 1

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold text-slate-900">Historial de Almuerzos</h1>

      {/* Hijo selector */}
      {hijos.length > 1 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Alumno</p>
          <div className="flex gap-2 flex-wrap">
            {hijos.map(h => (
              <button
                key={h.id}
                type="button"
                onClick={() => setSelectedHijo(h.id)}
                className={[
                  'px-3 py-1.5 rounded-xl text-sm font-medium border transition-colors cursor-pointer',
                  selectedHijo === h.id
                    ? 'bg-green-600 text-white border-green-600'
                    : 'bg-white text-slate-600 border-slate-200 hover:border-green-400',
                ].join(' ')}
              >
                {h.nombre}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Month navigator */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex items-center justify-between">
        <button
          type="button"
          onClick={prevMes}
          className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 cursor-pointer transition-colors"
        >
          <ChevronLeft className="w-5 h-5" />
        </button>
        <p className="text-base font-semibold text-slate-800">{MESES[mes]} {anio}</p>
        <button
          type="button"
          onClick={nextMes}
          disabled={isCurrentMonth}
          className={[
            'p-2 rounded-xl transition-colors',
            isCurrentMonth
              ? 'text-slate-300 cursor-not-allowed'
              : 'hover:bg-slate-100 text-slate-600 cursor-pointer',
          ].join(' ')}
        >
          <ChevronRight className="w-5 h-5" />
        </button>
      </div>

      {/* Summary */}
      {data && !loading && (
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Almuerzos', value: data.total },
            { label: 'Cobrados', value: data.cobrados },
            { label: 'Total', value: formatGs(data.monto_total) },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-3 py-3 text-center">
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide">{label}</p>
              <p className="text-lg font-bold text-slate-800 mt-0.5">{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* List */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : !data || data.consumos.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-slate-400">
            <UtensilsCrossed className="w-10 h-10 mb-3 opacity-40" />
            <p className="text-sm">Sin consumos registrados este mes</p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {data.consumos.map(c => (
              <li key={c.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-800">{formatFecha(c.fecha_consumo)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold tabular-nums text-slate-700">
                    {formatGs(c.costo_almuerzo)}
                  </span>
                  <Badge color={c.ya_cobrado ? 'green' : 'orange'}>
                    {c.ya_cobrado ? 'Cobrado' : 'Pendiente'}
                  </Badge>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
