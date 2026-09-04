import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Bell, ChevronDown, Crown, Eye, Mail, Phone, Trash2, UserPlus, Users } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import ModalAgregarResponsable from './ModalAgregarResponsable'
import { extractErrorMessage, type AlumnoResponsable, type Hijo } from './shared'

interface Props {
  open: boolean
  hijo: Hijo | null
  onClose: () => void
}

export default function ModalResponsables({ open, hijo, onClose }: Props) {
  const [responsables, setResponsables] = useState<AlumnoResponsable[]>([])
  const [loading, setLoading] = useState(false)
  const [agregarOpen, setAgregarOpen] = useState(false)

  const loadResponsables = useCallback(async () => {
    if (!hijo) return
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/responsables/', { params: { hijo: hijo.id_hijo, page_size: 50 } })
      setResponsables((data.results ?? data).sort(
        (a: AlumnoResponsable, b: AlumnoResponsable) => a.orden_cobro - b.orden_cobro
      ))
    } catch {
      toast.error('Error al cargar responsables')
    } finally {
      setLoading(false)
    }
  }, [hijo])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (open) loadResponsables()
  }, [open, loadResponsables])

  async function handleSetTitular(r: AlumnoResponsable) {
    try {
      await api.post(`/clientes/responsables/${r.id_responsable}/set_titular/`)
      toast.success(`${r.cliente_nombre} ahora es el titular`)
      loadResponsables()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }

  async function handleToggle(r: AlumnoResponsable, field: 'recibe_notificaciones' | 'puede_ver_saldo' | 'activo') {
    try {
      await api.patch(`/clientes/responsables/${r.id_responsable}/`, { [field]: !r[field] })
      loadResponsables()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }

  async function handleDelete(r: AlumnoResponsable) {
    if (!window.confirm(`¿Eliminar a ${r.cliente_nombre} como responsable?`)) return
    try {
      await api.delete(`/clientes/responsables/${r.id_responsable}/`)
      toast.success('Responsable eliminado')
      loadResponsables()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }

  return (
    <>
      <Modal
        open={open}
        title={`Responsables — ${hijo?.apellido ?? ''}, ${hijo?.nombre ?? ''}`}
        onCancel={onClose}
        footer={null}
        width={600}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Los responsables son contactados en orden de cobro cuando hay deuda pendiente.
            </p>
            <Button variant="primary" size="sm" onClick={() => setAgregarOpen(true)}>
              <UserPlus className="w-3.5 h-3.5" />Agregar
            </Button>
          </div>

          {loading ? (
            <Spinner className="py-8" />
          ) : responsables.length === 0 ? (
            <div className="text-center py-10 text-slate-400">
              <Users className="w-9 h-9 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Sin responsables registrados</p>
            </div>
          ) : (
            <ul className="space-y-2">
              {responsables.map((r) => (
                <li key={r.id_responsable} className={['rounded-xl border px-4 py-3', r.es_titular ? 'border-amber-200 bg-amber-50/60' : 'border-slate-100 bg-white', !r.activo ? 'opacity-50' : ''].join(' ')}>
                  <div className="flex items-start gap-3">
                    <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center shrink-0 text-xs font-bold text-slate-500">
                      {r.orden_cobro}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-base font-semibold text-slate-800">{r.cliente_nombre}</span>
                        {r.es_titular && (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                            <Crown className="w-3 h-3" />Titular
                          </span>
                        )}
                        <Badge color="default">{r.parentesco_display}</Badge>
                        {!r.activo && <Badge color="red">Inactivo</Badge>}
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-sm text-slate-400 flex-wrap">
                        <span className="font-mono">{r.cliente_ruc_ci}</span>
                        {r.cliente_telefono && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{r.cliente_telefono}</span>}
                        {r.cliente_email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{r.cliente_email}</span>}
                      </div>
                      <div className="mt-2 flex items-center gap-3">
                        <button onClick={() => handleToggle(r, 'recibe_notificaciones')} title="Recibe notificaciones de cobro"
                          className={['flex items-center gap-1 text-sm px-2 py-0.5 rounded-full border transition-colors', r.recibe_notificaciones ? 'border-blue-200 bg-blue-50 text-blue-700' : 'border-slate-200 bg-slate-50 text-slate-400 line-through'].join(' ')}>
                          <Bell className="w-3 h-3" />Notificaciones
                        </button>
                        <button onClick={() => handleToggle(r, 'puede_ver_saldo')} title="Puede ver saldo en el portal"
                          className={['flex items-center gap-1 text-sm px-2 py-0.5 rounded-full border transition-colors', r.puede_ver_saldo ? 'border-green-200 bg-green-50 text-green-700' : 'border-slate-200 bg-slate-50 text-slate-400 line-through'].join(' ')}>
                          <Eye className="w-3 h-3" />Ver saldo
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {!r.es_titular && r.activo && (
                        <button onClick={() => handleSetTitular(r)} title="Designar como titular"
                          className="flex items-center gap-1 px-2 py-1 text-sm font-medium text-amber-600 hover:bg-amber-50 rounded-lg transition-colors">
                          <Crown className="w-3 h-3" />Titular
                        </button>
                      )}
                      <button onClick={() => handleToggle(r, 'activo')}
                        className={['px-2 py-1 text-sm font-medium rounded-lg transition-colors', r.activo ? 'text-slate-400 hover:text-orange-600 hover:bg-orange-50' : 'text-slate-400 hover:text-green-600 hover:bg-green-50'].join(' ')}
                        title={r.activo ? 'Desactivar' : 'Reactivar'}>
                        {r.activo ? 'Desactivar' : 'Reactivar'}
                      </button>
                      {!r.es_titular && (
                        <button onClick={() => handleDelete(r)}
                          className="p-1.5 text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors" title="Eliminar">
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}

          <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
            <p className="text-sm text-slate-400">
              <ChevronDown className="w-3 h-3 inline mr-1" />
              El titular se sincroniza con el responsable financiero principal del alumno.
            </p>
            <Button variant="secondary" onClick={onClose}>Cerrar</Button>
          </div>
        </div>
      </Modal>

      <ModalAgregarResponsable
        open={agregarOpen}
        hijoId={hijo?.id_hijo ?? 0}
        onClose={() => setAgregarOpen(false)}
        onSaved={loadResponsables}
      />
    </>
  )
}
