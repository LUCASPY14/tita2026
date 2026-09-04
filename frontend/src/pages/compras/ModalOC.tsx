import { useEffect, useMemo, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Plus, X } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Combobox from '../../components/ui/Combobox'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, formatGs,
  ITEM_EMPTY,
  type CompraFormFields, type ItemForm, type OrdenCompra, type Producto, type ProductoProveedorRecord, type Proveedor,
} from './shared'

interface Props {
  open: boolean
  editingOC: OrdenCompra | null
  proveedores: Proveedor[]
  productos: Producto[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalOC({ open, editingOC, proveedores, productos, onClose, onSaved }: Props) {
  const [ocItems, setOcItems] = useState<ItemForm[]>([{ ...ITEM_EMPTY }])
  const [saving, setSaving] = useState(false)
  const [preciosProveedor, setPreciosProveedor] = useState<Record<number, number>>({})
  const [listaProdProveedor, setListaProdProveedor] = useState<ProductoProveedorRecord[]>([])

  const { register, handleSubmit, reset, control, setValue, formState: { errors } } = useForm<CompraFormFields>({
    defaultValues: { proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' },
  })
  const proveedorId = useWatch({ control, name: 'proveedor_id' })

  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      if (editingOC) {
        reset({ proveedor_id: editingOC.proveedor, tipo_pago: editingOC.tipo_pago, nro_factura: editingOC.nro_factura_esperada || '' })
        setOcItems(
          editingOC.detalles?.length
            ? editingOC.detalles.map(d => ({
                producto: { id_producto: d.producto, descripcion: d.producto_nombre, precio_actual: d.costo_unitario },
                cantidad: d.cantidad,
                costo_unitario: Number(d.costo_unitario) || 0,
                subtotal: Number(d.subtotal) || 0,
                precio_venta: 0,
              }))
            : [{ ...ITEM_EMPTY }]
        )
      } else {
        reset({ proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' })
        setOcItems([{ ...ITEM_EMPTY }])
      }
    }
  }

  // Carga de precios/productos del proveedor al cambiar `proveedorId`: limpiar
  // sincrónicamente cuando no hay proveedor seleccionado es intencional.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!proveedorId) { setPreciosProveedor({}); setListaProdProveedor([]); return }
    api.get('/compras/productos-proveedor/', { params: { proveedor: proveedorId, page_size: 500 } })
      .then(({ data }) => {
        const list = (data.results ?? []) as ProductoProveedorRecord[]
        const map: Record<number, number> = {}
        for (const pp of list) map[pp.producto] = Number(pp.precio_compra) || 0
        setPreciosProveedor(map)
        setListaProdProveedor(list)
      })
      .catch(() => { setPreciosProveedor({}); setListaProdProveedor([]) })
  }, [proveedorId])

  const opcionesProducto = useMemo(() => {
    const idsProveedor = new Set(listaProdProveedor.map(pp => pp.producto))
    const provProds = listaProdProveedor.map(pp => {
      const prod = productos.find(p => p.id_producto === pp.producto)
      if (!prod) return null
      return { value: prod.id_producto, label: `${prod.descripcion} — ${Number(pp.precio_compra).toLocaleString('es-PY')} Gs.`, data: prod }
    }).filter(Boolean) as { value: number; label: string; data: Producto }[]
    const otros = productos.filter(p => !idsProveedor.has(p.id_producto)).map(p => ({ value: p.id_producto, label: p.descripcion, data: p }))
    return [...provProds, ...otros]
  }, [listaProdProveedor, productos])

  const ocTotal = useMemo(() => ocItems.reduce((s, i) => s + i.subtotal, 0), [ocItems])

  const handleSave = handleSubmit(async (fields) => {
    if (ocItems.some(i => !i.producto)) { toast.error('Completá todos los productos de la OC'); return }
    setSaving(true)
    try {
      const payload = {
        proveedor: fields.proveedor_id,
        tipo_pago: fields.tipo_pago,
        nro_factura_esperada: fields.nro_factura,
        items: ocItems.map(i => ({ producto: i.producto!.id_producto, cantidad: i.cantidad, costo_unitario: i.costo_unitario })),
      }
      if (editingOC) {
        await api.put(`/compras/ordenes/${editingOC.id_orden_compra}/`, payload)
        toast.success('OC actualizada')
      } else {
        await api.post('/compras/ordenes/', payload)
        toast.success('Orden de Compra creada en Borrador')
      }
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  })

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title={editingOC ? `Editar OC #${editingOC.id_orden_compra}` : 'Nueva Orden de Compra'}
      onOk={handleSave}
      onCancel={onClose}
      okText={editingOC ? 'Guardar Cambios' : 'Crear OC'}
      confirmLoading={saving}
      width={700}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Proveedor *</label>
            <Combobox
              options={proveedores.map(p => ({ value: p.id_proveedor, label: p.razon_social }))}
              value={proveedorId || undefined}
              onChange={v => setValue('proveedor_id', v as number)}
              filterLocal
              placeholder="Buscar proveedor..."
            />
            {errors.proveedor_id && <p className="text-xs text-red-500 mt-0.5">{errors.proveedor_id.message}</p>}
          </div>
          <div>
            <label className={labelClass}>Tipo de Pago</label>
            <select className={inputClass} {...register('tipo_pago')}>
              <option value="CONTADO">Contado</option>
              <option value="CREDITO">Crédito</option>
            </select>
          </div>
        </div>

        <div>
          <label className={labelClass}>Nro. Factura Esperada</label>
          <input placeholder="001-001-0001234 (opcional)" className={inputClass} {...register('nro_factura')} />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className={`${labelClass} mb-0`}>Productos *</label>
            <Button size="sm" variant="ghost" onClick={() => setOcItems(prev => [...prev, { ...ITEM_EMPTY }])}>
              <Plus className="w-3.5 h-3.5" /> Agregar
            </Button>
          </div>
          <div className="space-y-2 max-h-52 overflow-y-auto pr-1">
            {ocItems.map((item, idx) => (
              <div key={idx} className="flex gap-2 items-center bg-slate-50 rounded-xl px-3 py-2">
                <div className="flex-1">
                  <Combobox
                    options={opcionesProducto}
                    value={item.producto?.id_producto}
                    onChange={(_, opt) => {
                      setOcItems(prev => prev.map((it, i) => {
                        if (i !== idx) return it
                        const p = opt.data as Producto
                        const costo = preciosProveedor[p.id_producto] || 0
                        return { ...it, producto: p, costo_unitario: costo, subtotal: it.cantidad * costo }
                      }))
                    }}
                    filterLocal
                    placeholder="Producto..."
                  />
                </div>
                <input
                  type="number" min={1} value={item.cantidad}
                  onChange={e => setOcItems(prev => prev.map((it, i) => {
                    if (i !== idx) return it
                    const cant = Number(e.target.value) || 1
                    return { ...it, cantidad: cant, subtotal: cant * it.costo_unitario }
                  }))}
                  className="w-16 border border-slate-200 rounded-xl px-2 py-2 text-sm text-center bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                />
                <input
                  type="number" min={0} value={item.costo_unitario}
                  onChange={e => setOcItems(prev => prev.map((it, i) => {
                    if (i !== idx) return it
                    const costo = Number(e.target.value) || 0
                    return { ...it, costo_unitario: costo, subtotal: it.cantidad * costo }
                  }))}
                  className="w-28 border border-slate-200 rounded-xl px-2 py-2 text-sm text-right bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                  placeholder="Costo"
                />
                <span className="w-28 text-sm font-semibold text-right text-slate-700 tabular-nums">{formatGs(item.subtotal)}</span>
                <button
                  onClick={() => setOcItems(prev => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev)}
                  className="p-1 text-slate-400 hover:text-red-500 transition-colors cursor-pointer shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-200">
            <span className="text-sm font-semibold text-slate-600">Total estimado</span>
            <span className="text-lg font-bold text-emerald-700 tabular-nums">{formatGs(ocTotal)}</span>
          </div>
        </div>
      </div>
    </Modal>
  )
}
