import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import {
  AlertTriangle, Baby, Edit2, GraduationCap,
  Plus, ShieldAlert, ShoppingBag, Users,
} from 'lucide-react'
import api from '../../services/api'
import Badge, { type BadgeColor } from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import ModalHijo from './ModalHijo'
import ModalResponsables from './ModalResponsables'
import ModalConsumo from './ModalConsumo'
import { useAuthenticatedImage } from '../../hooks/useAuthenticatedImage'
import {
  extractErrorMessage, SEV_COLOR, SEV_LABEL,
  type Cliente, type Hijo, type RestriccionHijo,
} from './shared'

interface Props {
  open: boolean
  cliente: Cliente | null
  onClose: () => void
}

// Componente propio (no inline en el .map) porque useAuthenticatedImage es
// un hook — no se puede llamar dentro de un callback de lista.
function HijoAvatar({ hijo }: { hijo: Hijo }) {
  const fotoBlobUrl = useAuthenticatedImage(hijo.foto_url)
  return fotoBlobUrl
    ? <img src={fotoBlobUrl} alt="" className="w-9 h-9 rounded-full object-cover" />
    : <span className="text-blue-700 font-bold text-sm">{hijo.nombre[0]}{hijo.apellido[0]}</span>
}

export default function ModalHijos({ open, cliente, onClose }: Props) {
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [restricciones, setRestricciones] = useState<Record<number, RestriccionHijo[]>>({})
  const [loading, setLoading] = useState(false)
  const [hijoModal, setHijoModal] = useState<{ open: boolean; hijo: Hijo | null }>({ open: false, hijo: null })
  const [responsablesModal, setResponsablesModal] = useState<{ open: boolean; hijo: Hijo | null }>({ open: false, hijo: null })
  const [consumoModal, setConsumoModal] = useState<{ open: boolean; hijo: Hijo | null }>({ open: false, hijo: null })
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const loadHijos = useCallback(async () => {
    if (!cliente) return
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/hijos/', { params: { cliente_responsable: cliente.id } })
      const list: Hijo[] = data.results ?? data
      setHijos(list)
      const rest: Record<number, RestriccionHijo[]> = {}
      await Promise.all(
        list.map(async (h) => {
          const { data: rd } = await api.get('/clientes/restricciones/', { params: { hijo: h.id } })
          rest[h.id] = rd.results ?? rd
        })
      )
      setRestricciones(rest)
    } catch {
      toast.error('Error al cargar estudiantes')
    } finally {
      setLoading(false)
    }
  }, [cliente])

  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setExpandedId(null)
      loadHijos()
    } else {
      setConsumoModal({ open: false, hijo: null })
      setHijoModal({ open: false, hijo: null })
      setResponsablesModal({ open: false, hijo: null })
    }
  }, [open, loadHijos])

  async function toggleActivo(h: Hijo) {
    try {
      await api.patch(`/clientes/hijos/${h.id}/`, { activo: !h.activo })
      toast.success(h.activo ? 'Estudiante desactivado' : 'Estudiante activado')
      loadHijos()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }

  function maxSeveridad(rests: RestriccionHijo[]): BadgeColor {
    const active = rests.filter(r => r.activo)
    if (active.some(r => r.severidad === 'CRITICA')) return 'red'
    if (active.some(r => r.severidad === 'ALTA')) return 'orange'
    if (active.some(r => r.severidad === 'MEDIA')) return 'yellow'
    if (active.some(r => r.severidad === 'BAJA')) return 'blue'
    return 'default'
  }

  return (
    <>
      <Modal
        open={open}
        title={`Estudiantes — ${cliente?.apellidos ?? ''}, ${cliente?.nombres ?? ''}`}
        onCancel={onClose}
        footer={null}
        width={620}
        disableEscape={consumoModal.open || hijoModal.open || responsablesModal.open}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              {`${hijos.length} estudiante${hijos.length !== 1 ? 's' : ''} registrado${hijos.length !== 1 ? 's' : ''}`}
            </p>
            <Button variant="primary" size="sm" onClick={() => setHijoModal({ open: true, hijo: null })}>
              <Plus className="w-3.5 h-3.5" />Agregar
            </Button>
          </div>

          {loading ? (
            <Spinner className="py-10" />
          ) : hijos.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Baby className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Sin estudiantes registrados</p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100 -mx-6 px-6">
              {hijos.map((hijo) => {
                const rests = restricciones[hijo.id] ?? []
                const activeRests = rests.filter(r => r.activo)
                const isExpanded = expandedId === hijo.id

                return (
                  <li key={hijo.id} className="py-3.5">
                    <div className="flex items-start gap-3">
                      <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
                        <HijoAvatar hijo={hijo} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-base font-semibold text-slate-800">{hijo.apellido}, {hijo.nombre}</span>
                          <Badge color={hijo.activo ? 'green' : 'red'}>{hijo.activo ? 'Activo' : 'Inactivo'}</Badge>
                          {activeRests.length > 0 && (
                            <Badge color={maxSeveridad(activeRests)}>
                              <ShieldAlert className="w-3 h-3 mr-1 inline-block" />
                              {`${activeRests.length} restricción${activeRests.length !== 1 ? 'es' : ''}`}
                            </Badge>
                          )}
                        </div>
                        {hijo.grado_nombre && (
                          <p className="text-sm text-slate-500 mt-0.5 flex items-center gap-1">
                            <GraduationCap className="w-3 h-3 shrink-0" />{hijo.grado_nombre}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        {activeRests.length > 0 && (
                          <button onClick={() => setExpandedId(isExpanded ? null : hijo.id)}
                            className="flex items-center gap-1 px-2 py-1 text-sm font-medium text-orange-600 hover:bg-orange-50 rounded-lg transition-colors">
                            <AlertTriangle className="w-3 h-3" />{isExpanded ? 'Ocultar' : 'Ver'}
                          </button>
                        )}
                        <button onClick={() => setConsumoModal({ open: true, hijo })}
                          className="flex items-center gap-1 px-2 py-1 text-sm font-medium text-green-600 hover:bg-green-50 rounded-lg transition-colors" title="Ver historial de consumo">
                          <ShoppingBag className="w-3.5 h-3.5" />Consumo
                        </button>
                        <button onClick={() => setResponsablesModal({ open: true, hijo })}
                          className="flex items-center gap-1 px-2 py-1 text-sm font-medium text-purple-600 hover:bg-purple-50 rounded-lg transition-colors" title="Gestionar responsables">
                          <Users className="w-3.5 h-3.5" />Resp.
                        </button>
                        <button onClick={() => setHijoModal({ open: true, hijo })}
                          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors" title="Editar">
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button onClick={() => toggleActivo(hijo)}
                          className={['px-2 py-1 text-sm font-medium rounded-lg transition-colors', hijo.activo ? 'text-slate-400 hover:text-red-600 hover:bg-red-50' : 'text-slate-400 hover:text-green-600 hover:bg-green-50'].join(' ')}
                          title={hijo.activo ? 'Desactivar' : 'Activar'}>
                          {hijo.activo ? 'Desactivar' : 'Activar'}
                        </button>
                      </div>
                    </div>

                    {isExpanded && activeRests.length > 0 && (
                      <div className="mt-2.5 ml-12 space-y-1.5">
                        {activeRests.map((r) => (
                          <div key={r.id} className="flex items-start gap-2.5 bg-orange-50 border border-orange-100 rounded-xl px-3 py-2">
                            <Badge color={SEV_COLOR[r.severidad]} className="shrink-0 mt-0.5">{SEV_LABEL[r.severidad]}</Badge>
                            <div className="text-xs">
                              <p className="font-semibold text-slate-700">{r.tipo}</p>
                              {r.descripcion && <p className="text-slate-500 mt-0.5">{r.descripcion}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}

          <div className="pt-3 border-t border-slate-100 flex justify-end">
            <Button variant="secondary" onClick={onClose}>Cerrar</Button>
          </div>
        </div>
      </Modal>

      <ModalHijo
        open={hijoModal.open}
        hijo={hijoModal.hijo}
        clienteId={cliente?.id ?? 0}
        onClose={() => setHijoModal({ open: false, hijo: null })}
        onSaved={loadHijos}
      />
      <ModalResponsables
        open={responsablesModal.open}
        hijo={responsablesModal.hijo}
        onClose={() => setResponsablesModal({ open: false, hijo: null })}
      />
      <ModalConsumo
        open={consumoModal.open}
        hijo={consumoModal.hijo}
        onClose={() => setConsumoModal({ open: false, hijo: null })}
      />
    </>
  )
}
