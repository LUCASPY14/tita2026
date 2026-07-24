import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type Empleado, type EmpleadoForm, type Rol, EMP_FORM_INITIAL } from './shared'

interface Props {
  open: boolean
  editingEmp: Empleado | null
  roles: Rol[]
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalEmpleado({ open, editingEmp, roles, onClose, onSaved }: Props) {
  const [empForm, setEmpForm] = useState<EmpleadoForm>(EMP_FORM_INITIAL)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    if (editingEmp) {
      setEmpForm({
        nombre: editingEmp.nombre,
        apellido: editingEmp.apellido,
        email: editingEmp.email ?? '',
        telefono: editingEmp.telefono ?? '',
        id_rol: editingEmp.id_rol,
        estado: editingEmp.estado,
      })
    } else {
      setEmpForm({ ...EMP_FORM_INITIAL, id_rol: roles[0]?.id_rol ?? '' })
    }
  }, [open, editingEmp, roles])

  const handleSave = async () => {
    if (!empForm.nombre || !empForm.apellido || !empForm.id_rol) {
      toast.error('Nombre, apellido y rol son obligatorios')
      return
    }
    setSaving(true)
    try {
      const payload = { ...empForm, id_rol: Number(empForm.id_rol) }
      if (editingEmp) {
        await api.put(`/usuarios/empleados/${editingEmp.id_empleado}/`, payload)
        toast.success('Empleado actualizado')
      } else {
        await api.post('/usuarios/empleados/', payload)
        toast.success('Empleado creado')
      }
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
      title={editingEmp ? `Editar — ${editingEmp.nombre} ${editingEmp.apellido}` : 'Nuevo Empleado'}
      onOk={handleSave}
      onCancel={onClose}
      okText={editingEmp ? 'Guardar' : 'Crear'}
      confirmLoading={saving}
      width={480}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={empForm.nombre} onChange={e => setEmpForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Nombre" className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Apellido *</label>
            <input value={empForm.apellido} onChange={e => setEmpForm(f => ({ ...f, apellido: e.target.value }))} placeholder="Apellido" className={inputClass} />
          </div>
        </div>
        <div>
          <label className={labelClass}>Email</label>
          <input type="email" value={empForm.email} onChange={e => setEmpForm(f => ({ ...f, email: e.target.value }))} placeholder="correo@ejemplo.com" className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Teléfono</label>
          <input value={empForm.telefono} onChange={e => setEmpForm(f => ({ ...f, telefono: e.target.value }))} placeholder="0981 xxxxxx" className={inputClass} />
        </div>
        <div>
          <label className={labelClass}>Rol *</label>
          <select value={empForm.id_rol} onChange={e => setEmpForm(f => ({ ...f, id_rol: Number(e.target.value) }))} className={inputClass}>
            <option value="">— Elegí un rol —</option>
            {roles.map(r => <option key={r.id_rol} value={r.id_rol}>{r.nombre_rol}</option>)}
          </select>
        </div>
        <label className="flex items-center gap-3 cursor-pointer">
          <div className="relative shrink-0">
            <input type="checkbox" className="sr-only peer" checked={empForm.estado} onChange={e => setEmpForm(f => ({ ...f, estado: e.target.checked }))} />
            <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
            <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
          </div>
          <span className="text-sm text-slate-700">Empleado activo</span>
        </label>
      </div>
    </Modal>
  )
}
