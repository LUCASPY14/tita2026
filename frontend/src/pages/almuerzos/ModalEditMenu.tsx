import { useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type MenuDiario } from './shared'

interface Props {
  menu: MenuDiario | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalEditMenu({ menu, onClose, onSaved }: Props) {
  const [form, setForm] = useState({ fecha: '', plato_principal: '', guarnicion: '', postre: '', bebida: '', descripcion: '', activo: true })
  const [saving, setSaving] = useState(false)

  const [prevMenu, setPrevMenu] = useState(menu)
  if (menu !== prevMenu) {
    setPrevMenu(menu)
    if (menu) {
      setForm({
        fecha: menu.fecha,
        plato_principal: menu.plato_principal,
        guarnicion: menu.guarnicion,
        postre: menu.postre,
        bebida: menu.bebida,
        descripcion: menu.descripcion,
        activo: menu.activo,
      })
    }
  }

  async function handleSave() {
    if (!menu || !form.plato_principal) { toast.error('Ingresá el plato principal'); return }
    setSaving(true)
    try {
      await api.put(`/almuerzos/menu/${menu.id}/`, form)
      toast.success('Menú actualizado')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const toggleSwitch = (checked: boolean, onChange: (v: boolean) => void, label: string) => (
    <label className="flex items-center gap-3 cursor-pointer">
      <div className="relative shrink-0">
        <input type="checkbox" className="sr-only peer" checked={checked} onChange={e => onChange(e.target.checked)} />
        <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
        <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
      </div>
      <span className="text-sm text-slate-700">{label}</span>
    </label>
  )

  return (
    <Modal
      open={!!menu}
      title="Editar Menú"
      onOk={handleSave}
      onCancel={onClose}
      okText="Guardar"
      confirmLoading={saving}
      width={560}
    >
      <div className="space-y-4">
        <div>
          <label className={labelClass}>Fecha *</label>
          <input type="date" value={form.fecha} onChange={e => setForm(f => ({ ...f, fecha: e.target.value }))} className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Plato principal *</label>
          <input value={form.plato_principal} onChange={e => setForm(f => ({ ...f, plato_principal: e.target.value }))} className={inputClass} />
        </div>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className={labelClass}>Guarnición</label>
            <input value={form.guarnicion} onChange={e => setForm(f => ({ ...f, guarnicion: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Postre</label>
            <input value={form.postre} onChange={e => setForm(f => ({ ...f, postre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Bebida</label>
            <input value={form.bebida} onChange={e => setForm(f => ({ ...f, bebida: e.target.value }))} className={inputClass} />
          </div>
        </div>
        <div>
          <label className={labelClass}>Notas</label>
          <textarea value={form.descripcion} onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
        </div>
        {toggleSwitch(form.activo, v => setForm(f => ({ ...f, activo: v })), 'Activo')}
      </div>
    </Modal>
  )
}
