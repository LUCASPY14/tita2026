import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import {
  Bell, AlertTriangle, CreditCard, UtensilsCrossed,
  Calendar, Info, CheckCheck,
} from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Spinner from '../../components/ui/Spinner'
import Button from '../../components/ui/Button'
import type { LucideIcon } from 'lucide-react'

interface Notificacion {
  id: number
  tipo: string
  titulo: string
  mensaje: string
  destino: string
  leida: boolean
  fecha_envio: string
}

const TIPO_ICON: Record<string, LucideIcon> = {
  SALDO_BAJO: AlertTriangle,
  RECARGA: CreditCard,
  CONSUMO: UtensilsCrossed,
  VENCIMIENTO: Calendar,
  ALMUERZO: UtensilsCrossed,
  SISTEMA: Info,
}

const TIPO_COLOR: Record<string, string> = {
  SALDO_BAJO: 'text-amber-500',
  RECARGA: 'text-blue-500',
  CONSUMO: 'text-green-500',
  VENCIMIENTO: 'text-orange-500',
  ALMUERZO: 'text-green-500',
  SISTEMA: 'text-slate-400',
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function PortalNotificaciones() {
  const { user } = useAuthStore()
  const [notifs, setNotifs] = useState<Notificacion[]>([])
  const [loading, setLoading] = useState(true)
  const [marcando, setMarcando] = useState<number | null>(null)

  const cargar = async () => {
    if (!user) return
    setLoading(true)
    try {
      const { data } = await api.get('/notificaciones/notificaciones/', {
        params: { usuario: user.id, ordering: '-fecha_envio', page_size: 50 },
      })
      setNotifs(data.results || [])
    } catch {
      toast.error('Error al cargar notificaciones')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [user])

  const marcarLeida = async (id: number) => {
    setMarcando(id)
    try {
      await api.patch(`/notificaciones/notificaciones/${id}/`, { leida: true })
      setNotifs(prev => prev.map(n => n.id === id ? { ...n, leida: true } : n))
    } catch {
      toast.error('Error al actualizar')
    } finally {
      setMarcando(null)
    }
  }

  const marcarTodas = async () => {
    for (const n of notifs.filter(n => !n.leida)) {
      await api.patch(`/notificaciones/notificaciones/${n.id}/`, { leida: true }).catch(() => {})
    }
    setNotifs(prev => prev.map(n => ({ ...n, leida: true })))
    toast.success('Todas marcadas como leídas')
  }

  if (loading) return <Spinner className="mt-12" />

  const noLeidas = notifs.filter(n => !n.leida).length

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Notificaciones</h1>
          {noLeidas > 0 && (
            <p className="text-sm text-amber-600 mt-0.5">{noLeidas} sin leer</p>
          )}
        </div>
        {noLeidas > 0 && (
          <Button size="sm" variant="secondary" onClick={marcarTodas}>
            <CheckCheck className="w-3.5 h-3.5" />
            Marcar todas
          </Button>
        )}
      </div>

      {notifs.length === 0 ? (
        <div className="py-16 text-center text-slate-400">
          <Bell className="w-12 h-12 mx-auto mb-4 opacity-20" />
          <p className="text-base font-medium text-slate-600">Sin notificaciones</p>
          <p className="text-sm mt-1">Te avisaremos cuando haya novedades</p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifs.map(n => {
            const Icon = TIPO_ICON[n.tipo] ?? Info
            const iconColor = TIPO_COLOR[n.tipo] ?? 'text-slate-400'
            return (
              <div
                key={n.id}
                className={[
                  'bg-white rounded-xl border p-4 transition-colors',
                  n.leida ? 'border-slate-100' : 'border-amber-200 bg-amber-50',
                ].join(' ')}
              >
                <div className="flex gap-3">
                  <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${n.leida ? 'bg-slate-100' : 'bg-amber-100'}`}>
                    <Icon className={`w-4 h-4 ${iconColor}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-slate-800 leading-snug">{n.titulo}</p>
                      {!n.leida && <span className="shrink-0 w-2 h-2 bg-amber-500 rounded-full mt-1.5" />}
                    </div>
                    <p className="text-sm text-slate-600 mt-1">{n.mensaje}</p>
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-xs text-slate-400">{formatFecha(n.fecha_envio)}</p>
                      {!n.leida && (
                        <Button
                          size="sm"
                          variant="secondary"
                          loading={marcando === n.id}
                          onClick={() => marcarLeida(n.id)}
                        >
                          Marcar leída
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
