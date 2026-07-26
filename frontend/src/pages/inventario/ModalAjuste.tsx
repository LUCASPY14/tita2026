import { useCallback, useState } from 'react'
import toast from 'react-hot-toast'
import { Plus, X, AlertTriangle } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import Button from '../../components/ui/Button'
import Combobox from '../../components/ui/Combobox'
import { extractErrorMessage, type Producto, type DetalleAjuste, DETALLE_EMPTY } from './shared'

interface Props {
  open: boolean
  productos: Producto[]
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalAjuste({ open, productos, onClose, onSaved }: Props) {
  const [form, setForm] = useState({
    tipo: 'AUMENTO', motivo: '',
    detalles: [{ ...DETALLE_EMPTY }] as DetalleAjuste[],
  })
  const [saving, setSaving] = useState(false)

  const actualizarDetalle = useCallback((idx: number, field: keyof DetalleAjuste, val: unknown) => {
    setForm(f => ({
      ...f,
      detalles: f.detalles.map((d, i) => i === idx ? { ...d, [field]: val } : d),
    }))
  }, [])

  const handleSave = async () => {
    if (!form.motivo) { toast.error('Ingresá el motivo'); return }
    if (form.detalles.some(d => !d.producto)) { toast.error('Seleccioná todos los productos'); return }
    setSaving(true)
    try {
      await api.post('/inventario/ajustes/', {
        tipo: form.tipo,
        motivo: form.motivo,
        detalles: form.detalles.map(d => ({
          producto: d.producto!.id,
          cantidad: d.cantidad,
          motivo_detalle: d.motivo_detalle,
        })),
      })
      toast.success('Ajuste creado — pendiente de aprobación')
      setForm({ tipo: 'AUMENTO', motivo: '', detalles: [{ ...DETALLE_EMPTY }] })
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
      title="Nuevo Ajuste de Inventario"
      onOk={handleSave}
      onCancel={onClose}
      okText="Crear Ajuste"
      confirmLoading={saving}
      width={620}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Tipo de Ajuste</label>
            <select
              value={form.tipo}
              onChange={e => setForm(f => ({ ...f, tipo: e.target.value }))}
              className={inputClass}
            >
              <option value="AUMENTO">Aumento de stock</option>
              <option value="MERMA">Merma / Baja</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Motivo general *</label>
            <input
              value={form.motivo}
              onChange={e => setForm(f => ({ ...f, motivo: e.target.value }))}
              placeholder="Ej: Inventario físico, devolución..."
              className={inputClass}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className={`${labelClass} mb-0`}>Productos *</label>
            <Button size="sm" variant="ghost" onClick={() => setForm(f => ({ ...f, detalles: [...f.detalles, { ...DETALLE_EMPTY }] }))}>
              <Plus className="w-3.5 h-3.5" />
              Agregar
            </Button>
          </div>

          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {form.detalles.map((det, idx) => (
              <div key={idx} className="flex gap-2 items-center bg-slate-50 rounded-xl px-3 py-2">
                <div className="flex-1">
                  <Combobox
                    options={productos.map(p => ({ value: p.id, label: p.descripcion, data: p }))}
                    value={det.producto?.id}
                    onChange={(_, opt) => actualizarDetalle(idx, 'producto', opt.data as Producto)}
                    filterLocal
                    placeholder="Producto..."
                  />
                </div>
                <input
                  type="number"
                  min={1}
                  value={det.cantidad}
                  onChange={e => actualizarDetalle(idx, 'cantidad', Number(e.target.value) || 1)}
                  className="w-16 border border-slate-200 rounded-xl px-2 py-2 text-sm text-center bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                  placeholder="Cant."
                />
                <input
                  value={det.motivo_detalle}
                  onChange={e => actualizarDetalle(idx, 'motivo_detalle', e.target.value)}
                  placeholder="Motivo específico..."
                  className="w-36 border border-slate-200 rounded-xl px-2 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                />
                <button
                  onClick={() => setForm(f => ({ ...f, detalles: f.detalles.length > 1 ? f.detalles.filter((_, i) => i !== idx) : f.detalles }))}
                  className="p-1 text-slate-400 hover:text-red-500 transition-colors cursor-pointer shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-700">El ajuste quedará en estado PENDIENTE y debe ser aprobado por un administrador.</p>
        </div>
      </div>
    </Modal>
  )
}
