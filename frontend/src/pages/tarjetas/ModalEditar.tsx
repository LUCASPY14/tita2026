import { useState } from 'react'
import toast from 'react-hot-toast'
import tarjetasService from '../../services/tarjetas'
import { useAuthStore } from '../../store/authStore'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type Tarjeta, type TarjetaEditForm } from './shared'

interface Props {
  tarjeta: Tarjeta | null
  onClose: () => void
  onSaved: (updates: Partial<Tarjeta>) => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalEditar({ tarjeta, onClose, onSaved }: Props) {
  const { user } = useAuthStore()
  const puedeConfigurarAlertas = user?.rol === 'ADMIN' || user?.rol === 'SUPERVISOR'

  const [editForm, setEditForm] = useState<TarjetaEditForm>({
    limite_credito: '', permite_saldo_negativo: false, estado: 'ACTIVA', fecha_vencimiento: '',
    saldo_alerta: '', notificar_saldo_bajo: true,
  })
  const [saving, setSaving] = useState(false)

  const [prevTarjeta, setPrevTarjeta] = useState(tarjeta)
  if (tarjeta !== prevTarjeta) {
    setPrevTarjeta(tarjeta)
    if (tarjeta) {
      setEditForm({
        limite_credito: String(Number(tarjeta.limite_credito) || 0),
        permite_saldo_negativo: tarjeta.permite_saldo_negativo,
        estado: tarjeta.estado,
        fecha_vencimiento: tarjeta.fecha_vencimiento ?? '',
        saldo_alerta: tarjeta.saldo_alerta != null ? String(Number(tarjeta.saldo_alerta)) : '',
        notificar_saldo_bajo: tarjeta.notificar_saldo_bajo,
      })
    }
  }

  const handleSave = async () => {
    if (!tarjeta) return
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        limite_credito: Number(editForm.limite_credito) || 0,
        permite_saldo_negativo: editForm.permite_saldo_negativo,
        estado: editForm.estado,
        fecha_vencimiento: editForm.fecha_vencimiento || null,
      }
      if (puedeConfigurarAlertas) {
        payload.saldo_alerta = editForm.saldo_alerta ? Number(editForm.saldo_alerta) : null
        payload.notificar_saldo_bajo = editForm.notificar_saldo_bajo
      }
      await tarjetasService.actualizar(tarjeta.nro_tarjeta, payload)
      toast.success('Tarjeta actualizada')
      onSaved({
        limite_credito: editForm.limite_credito,
        permite_saldo_negativo: editForm.permite_saldo_negativo,
        estado: editForm.estado,
        fecha_vencimiento: editForm.fecha_vencimiento || null,
        ...(puedeConfigurarAlertas && {
          saldo_alerta: editForm.saldo_alerta ? Number(editForm.saldo_alerta) : null,
          notificar_saldo_bajo: editForm.notificar_saldo_bajo,
        }),
      })
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={!!tarjeta}
      title={tarjeta ? `Editar Tarjeta — ${tarjeta.nro_tarjeta}` : ''}
      onOk={handleSave}
      onCancel={onClose}
      okText="Guardar Cambios"
      confirmLoading={saving}
      width={480}
    >
      {tarjeta && (
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl px-4 py-3 text-sm text-slate-500">
            {tarjeta.es_alumno ? 'Estudiante' : 'Docente / Funcionario'}:{' '}
            <span className="font-semibold text-slate-800">{tarjeta.hijo_nombre ?? '—'}</span>
            {tarjeta.es_alumno && (
              <>{' · '} Responsable: <span className="font-semibold text-slate-800">{tarjeta.cliente_nombre ?? '—'}</span></>
            )}
          </div>

          <div>
            <label className={labelClass}>Límite de Crédito (Gs.)</label>
            <p className="text-xs text-slate-400 mb-1.5">
              Monto máximo que puede gastar con saldo negativo, autorizado con PIN del padre
            </p>
            <input
              type="number"
              value={editForm.limite_credito}
              onChange={e => setEditForm(f => ({ ...f, limite_credito: e.target.value }))}
              placeholder="0"
              min={0}
              step={1000}
              className={inputClass}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Estado</label>
              <select
                value={editForm.estado}
                onChange={e => setEditForm(f => ({ ...f, estado: e.target.value }))}
                className={inputClass}
              >
                <option value="ACTIVA">Activa</option>
                <option value="BLOQUEADA">Bloqueada</option>
                <option value="CANCELADA">Cancelada</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Fecha de Vencimiento</label>
              <input
                type="date"
                value={editForm.fecha_vencimiento}
                onChange={e => setEditForm(f => ({ ...f, fecha_vencimiento: e.target.value }))}
                className={inputClass}
              />
            </div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative shrink-0">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={editForm.permite_saldo_negativo}
                onChange={e => setEditForm(f => ({ ...f, permite_saldo_negativo: e.target.checked }))}
              />
              <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
            </div>
            <div>
              <span className="text-sm font-medium text-slate-700">Permite saldo negativo</span>
              <p className="text-xs text-slate-400">Activa la solicitud de PIN del padre cuando se excede el saldo</p>
            </div>
          </label>

          {puedeConfigurarAlertas && (
            <div className="border-t border-slate-100 pt-4 space-y-4">
              <div>
                <label className={labelClass}>Umbral de saldo bajo (Gs.)</label>
                <p className="text-xs text-slate-400 mb-1.5">
                  Se avisa al padre cuando el saldo cae a este monto o menos. Vacío = sin aviso.
                </p>
                <input
                  type="number"
                  value={editForm.saldo_alerta}
                  onChange={e => setEditForm(f => ({ ...f, saldo_alerta: e.target.value }))}
                  placeholder="Sin configurar"
                  min={0}
                  step={1000}
                  className={inputClass}
                />
              </div>

              <label className="flex items-center gap-3 cursor-pointer">
                <div className="relative shrink-0">
                  <input
                    type="checkbox"
                    className="sr-only peer"
                    checked={editForm.notificar_saldo_bajo}
                    onChange={e => setEditForm(f => ({ ...f, notificar_saldo_bajo: e.target.checked }))}
                  />
                  <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
                  <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
                </div>
                <div>
                  <span className="text-sm font-medium text-slate-700">Notificar saldo bajo</span>
                  <p className="text-xs text-slate-400">Envía el aviso al padre (push, portal y WhatsApp si lo activó)</p>
                </div>
              </label>
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}
