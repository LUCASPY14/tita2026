import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, type Rol } from './shared'

interface Props {
  open: boolean
  rol: Rol | null
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalRol({ open, rol, onClose, onSaved }: Props) {
  const [nombre, setNombre] = useState('')
  const [descripcion, setDescripcion] = useState('')
  const [estado, setEstado] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    if (rol) {
      setNombre(rol.nombre_rol)
      setDescripcion(rol.descripcion ?? '')
      setEstado(rol.estado)
    } else {
      setNombre('')
      setDescripcion('')
      setEstado(true)
    }
  }, [open, rol])

  async function handleSave() {
    if (!nombre.trim()) { toast.error('El nombre del rol es obligatorio'); return }
    setSaving(true)
    try {
      const payload = { nombre_rol: nombre.trim(), descripcion: descripcion.trim() || null, estado }
      if (rol) {
        await api.patch(`/usuarios/roles/${rol.id_rol}/`, payload)
        toast.success('Rol actualizado')
      } else {
        await api.post('/usuarios/roles/', payload)
        toast.success('Rol creado')
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
      title={rol ? `Editar rol — ${rol.nombre_rol}` : 'Nuevo rol'}
      onOk={handleSave}
      onCancel={onClose}
      okText={rol ? 'Guardar' : 'Crear'}
      confirmLoading={saving}
      width={420}
    >
      <div className="space-y-4">
        <div>
          <label className={labelClass}>Nombre del rol *</label>
          <input
            value={nombre}
            onChange={e => setNombre(e.target.value)}
            placeholder="ej: Auxiliar de cocina"
            className={inputClass}
            autoFocus
          />
        </div>
        <div>
          <label className={labelClass}>Descripción</label>
          <input
            value={descripcion}
            onChange={e => setDescripcion(e.target.value)}
            placeholder="Descripción opcional"
            className={inputClass}
          />
        </div>
        <label className="flex items-center gap-3 cursor-pointer">
          <div className="relative shrink-0">
            <input type="checkbox" className="sr-only peer" checked={estado} onChange={e => setEstado(e.target.checked)} />
            <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
            <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
          </div>
          <span className="text-sm text-slate-700">Rol activo</span>
        </label>
      </div>
    </Modal>
  )
}
