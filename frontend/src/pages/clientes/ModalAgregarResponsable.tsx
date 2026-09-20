import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, BLANK_RESP, PARENTESCO_LABELS, RUC_CI_REGEX,
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
    if (form.modo === 'existente') {
      if (!form.cliente) { toast.error('Seleccioná un cliente'); return }
    } else {
      if (!form.nombres.trim() || !form.apellidos.trim()) { toast.error('Ingresá nombres y apellidos'); return }
      if (!RUC_CI_REGEX.test(form.ruc_ci.trim())) { toast.error('RUC/CI inválido'); return }
    }
    if (!form.parentesco) { toast.error('Seleccioná el parentesco'); return }
    setSaving(true)
    try {
      if (form.modo === 'existente') {
        await api.post('/clientes/responsables/', {
          hijo: hijoId,
          cliente: Number(form.cliente),
          parentesco: form.parentesco,
          orden_cobro: Number(form.orden_cobro) || 1,
          recibe_notificaciones: form.recibe_notificaciones,
          puede_ver_saldo: form.puede_ver_saldo,
        })
      } else {
        await api.post('/clientes/responsables/crear-con-cliente-nuevo/', {
          hijo: hijoId,
          nombres: form.nombres.trim(),
          apellidos: form.apellidos.trim(),
          ruc_ci: form.ruc_ci.trim(),
          telefono: form.telefono.trim() || undefined,
          email: form.email.trim() || undefined,
          parentesco: form.parentesco,
          orden_cobro: Number(form.orden_cobro) || 1,
          recibe_notificaciones: form.recibe_notificaciones,
          puede_ver_saldo: form.puede_ver_saldo,
        })
      }
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
        <div className="flex rounded-xl bg-slate-100 p-1">
          {([['existente', 'Cliente existente'], ['nuevo', 'Cliente nuevo']] as const).map(([modo, label]) => (
            <button
              key={modo}
              type="button"
              onClick={() => setForm(p => ({ ...p, modo }))}
              className={[
                'flex-1 rounded-lg py-1.5 text-sm font-medium transition-colors cursor-pointer',
                form.modo === modo ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500',
              ].join(' ')}
            >
              {label}
            </button>
          ))}
        </div>

        {form.modo === 'existente' ? (
          <div>
            <label className={labelClass}>Cliente (responsable) *</label>
            <select aria-label="Cliente (responsable)" className={selectClass} value={form.cliente} onChange={e => setForm(p => ({ ...p, cliente: e.target.value }))}>
              <option value="">Seleccionar cliente...</option>
              {clientes.map(c => (
                <option key={c.id_cliente} value={c.id_cliente}>{c.apellidos}, {c.nombres} — {c.ruc_ci}</option>
              ))}
            </select>
          </div>
        ) : (
          <div className="space-y-4">
            <p className="text-sm text-slate-500">
              La persona todavía no está cargada como cliente — se crea junto con el responsable.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Nombres *</label>
                <input aria-label="Nombres" className={selectClass} value={form.nombres} onChange={e => setForm(p => ({ ...p, nombres: e.target.value }))} />
              </div>
              <div>
                <label className={labelClass}>Apellidos *</label>
                <input aria-label="Apellidos" className={selectClass} value={form.apellidos} onChange={e => setForm(p => ({ ...p, apellidos: e.target.value }))} />
              </div>
            </div>
            <div>
              <label className={labelClass}>RUC/CI *</label>
              <input aria-label="RUC/CI" className={selectClass} value={form.ruc_ci} onChange={e => setForm(p => ({ ...p, ruc_ci: e.target.value }))} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className={labelClass}>Teléfono</label>
                <input aria-label="Teléfono" className={selectClass} value={form.telefono} onChange={e => setForm(p => ({ ...p, telefono: e.target.value }))} />
              </div>
              <div>
                <label className={labelClass}>Email</label>
                <input aria-label="Email" type="email" className={selectClass} value={form.email} onChange={e => setForm(p => ({ ...p, email: e.target.value }))} />
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Parentesco *</label>
            <select aria-label="Parentesco" className={selectClass} value={form.parentesco} onChange={e => setForm(p => ({ ...p, parentesco: e.target.value }))}>
              {Object.entries(PARENTESCO_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Orden de cobro</label>
            <input aria-label="Orden de cobro" type="number" min={1} className={selectClass} value={form.orden_cobro}
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
