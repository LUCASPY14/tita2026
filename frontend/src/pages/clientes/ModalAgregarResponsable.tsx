import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, BLANK_RESP, PARENTESCO_LABELS,
  type AgregarResponsableForm, type Cliente,
} from './shared'

interface Props {
  open: boolean
  hijoId: number
  onClose: () => void
  onSaved: () => void
}

export default function ModalAgregarResponsable({ open, hijoId, onClose, onSaved }: Props) {
  const [form, setForm] = useState<AgregarResponsableForm>(BLANK_RESP)
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setForm(BLANK_RESP)
    api.get('/clientes/clientes/', { params: { activo: 'true', page_size: 200 } })
      .then(({ data }) => setClientes(data.results ?? data))
      .catch(() => toast.error('Error al cargar clientes'))
  }, [open])

  const selectClass = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function handleSave() {
    if (!form.cliente) { toast.error('Seleccioná un cliente'); return }
    if (!form.parentesco) { toast.error('Seleccioná el parentesco'); return }
    setSaving(true)
    try {
      await api.post('/clientes/responsables/', {
        hijo: hijoId,
        cliente: Number(form.cliente),
        parentesco: form.parentesco,
        orden_cobro: Number(form.orden_cobro) || 1,
        recibe_notificaciones: form.recibe_notificaciones,
        puede_ver_saldo: form.puede_ver_saldo,
      })
      toast.success('Responsable agregado')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Agregar Responsable"
      onCancel={onClose}
      onOk={handleSave}
      okText="Agregar"
      confirmLoading={saving}
      width={460}
    >
      <div className="space-y-4">
        <div>
          <label className={labelClass}>Cliente (responsable) *</label>
          <select className={selectClass} value={form.cliente} onChange={e => setForm(p => ({ ...p, cliente: e.target.value }))}>
            <option value="">Seleccionar cliente...</option>
            {clientes.map(c => (
              <option key={c.id_cliente} value={c.id_cliente}>{c.apellidos}, {c.nombres} — {c.ruc_ci}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Parentesco *</label>
            <select className={selectClass} value={form.parentesco} onChange={e => setForm(p => ({ ...p, parentesco: e.target.value }))}>
              {Object.entries(PARENTESCO_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Orden de cobro</label>
            <input type="number" min={1} className={selectClass} value={form.orden_cobro}
              onChange={e => setForm(p => ({ ...p, orden_cobro: e.target.value }))} />
          </div>
        </div>

        <div className="border-t border-slate-100 pt-3 space-y-2.5">
          {([
            ['recibe_notificaciones', 'Recibe notificaciones de cobro'] as const,
            ['puede_ver_saldo', 'Puede consultar saldo en el portal'] as const,
          ]).map(([field, label]) => (
            <div key={field} className="flex items-center gap-3">
              <button
                type="button" role="switch" aria-checked={form[field]}
                onClick={() => setForm(p => ({ ...p, [field]: !p[field] }))}
                className={['relative w-10 h-5 rounded-full transition-colors shrink-0', form[field] ? 'bg-green-500' : 'bg-slate-200'].join(' ')}
              >
                <span className={['absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform', form[field] ? 'translate-x-5' : 'translate-x-0'].join(' ')} />
              </button>
              <span className="text-sm text-slate-700">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  )
}
