import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Plus, Scan, X } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Combobox from '../../components/ui/Combobox'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, formatGs,
  ITEM_EMPTY,
  type Compra, type CompraFormFields, type ItemForm, type Producto, type ProductoProveedorRecord, type Proveedor,
} from './shared'

interface Props {
  open: boolean
  editingCompra: Compra | null
  proveedores: Proveedor[]
  productos: Producto[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalCompra({ open, editingCompra, proveedores, productos, onClose, onSaved }: Props) {
  const [items, setItems] = useState<ItemForm[]>([{ ...ITEM_EMPTY }])
  const [saving, setSaving] = useState(false)
  const [barcodeInput, setBarcodeInput] = useState('')
  const [preciosProveedor, setPreciosProveedor] = useState<Record<number, number>>({})
  const [listaProdProveedor, setListaProdProveedor] = useState<ProductoProveedorRecord[]>([])
  const barcodeRef = useRef<HTMLInputElement>(null)

  const { register, handleSubmit, reset, control, setValue, formState: { errors } } = useForm<CompraFormFields>({
    defaultValues: { proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' },
  })
  const proveedorId = useWatch({ control, name: 'proveedor_id' })

  const [wasOpen, setWasOpen] = useState(open)
  if (open !== wasOpen) {
    setWasOpen(open)
    if (open) {
      if (editingCompra) {
        reset({ proveedor_id: editingCompra.proveedor, tipo_pago: editingCompra.tipo_pago, nro_factura: editingCompra.nro_factura_proveedor || '' })
        setItems(
          editingCompra.detalles?.length
            ? editingCompra.detalles.map(d => ({
                producto: { id: d.producto, descripcion: d.producto_nombre, precio_actual: d.costo_unitario },
                cantidad: d.cantidad,
                costo_unitario: Number(d.costo_unitario) || 0,
                subtotal: Number(d.subtotal) || 0,
                precio_venta: 0,
              }))
            : [{ ...ITEM_EMPTY }]
        )
      } else {
        reset({ proveedor_id: '', tipo_pago: 'CONTADO', nro_factura: '' })
        setItems([{ ...ITEM_EMPTY }])
      }
      setBarcodeInput('')
    }
  }

  useEffect(() => {
    if (open) setTimeout(() => barcodeRef.current?.focus(), 100)
  }, [open])

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
      const prod = productos.find(p => p.id === pp.producto)
      if (!prod) return null
      return { value: prod.id, label: `${prod.descripcion} — ${Number(pp.precio_compra).toLocaleString('es-PY')} Gs.`, data: prod }
    }).filter(Boolean) as { value: number; label: string; data: Producto }[]
    const otros = productos.filter(p => !idsProveedor.has(p.id)).map(p => ({ value: p.id, label: p.descripcion, data: p }))
    return [...provProds, ...otros]
  }, [listaProdProveedor, productos])

  const actualizarItem = useCallback((index: number, field: keyof ItemForm, value: unknown) => {
    setItems(prev => prev.map((item, i) => {
      if (i !== index) return item
      const updated = { ...item, [field]: value }
      if (field === 'producto' && value) {
        const prod = value as Producto
        updated.precio_venta = Number(prod.precio_actual) || 0
        const precioConocido = preciosProveedor[prod.id]
        if (precioConocido) {
          updated.costo_unitario = precioConocido
          updated.subtotal = updated.cantidad * precioConocido
        } else {
          updated.costo_unitario = 0
          updated.subtotal = 0
          api.get('/compras/detalles-compra/', { params: { producto: prod.id, page_size: 1 } })
            .then(res => {
              const ultimo = res.data?.results?.[0]
              if (ultimo) {
                setItems(current => current.map((it, idx) =>
                  idx === index && it.producto?.id === prod.id
                    ? { ...it, costo_unitario: Number(ultimo.costo_unitario) || 0, subtotal: it.cantidad * (Number(ultimo.costo_unitario) || 0) }
                    : it
                ))
              }
            })
            .catch(() => toast.error('Error al cargar precio del producto'))
        }
      }
      if (field !== 'producto') {
        updated.subtotal = updated.cantidad * updated.costo_unitario
      }
      return updated
    }))
  }, [preciosProveedor])

  const [localProductos, setLocalProductos] = useState<Producto[]>(productos)
  const [prevProductos, setPrevProductos] = useState(productos)
  if (productos !== prevProductos) {
    setPrevProductos(productos)
    setLocalProductos(productos)
  }

  const handleBarcodeScan = useCallback(async (code: string) => {
    const trimmed = code.trim()
    if (!trimmed) return
    let found: Producto | undefined = localProductos.find(
      p => (p.codigo_barra && p.codigo_barra === trimmed) || (p.codigo && p.codigo === trimmed)
    )
    if (!found) {
      try {
        const { data } = await api.get('/productos/productos/', { params: { search: trimmed, page_size: 10, activo: true } })
        const results: Producto[] = Array.isArray(data) ? data : (data as { results: Producto[] }).results ?? []
        found = results.find(p => (p.codigo_barra && p.codigo_barra === trimmed) || (p.codigo && p.codigo === trimmed))
        if (found) setLocalProductos(prev => prev.some(p => p.id === found!.id) ? prev : [...prev, found!])
      } catch { /* ignorar */ }
    }
    if (!found) { toast.error(`Código no encontrado: ${trimmed}`); setBarcodeInput(''); return }
    setItems(prev => {
      const idx = prev.findIndex(it => it.producto?.id === found!.id)
      if (idx >= 0) {
        return prev.map((it, i) =>
          i === idx ? { ...it, cantidad: it.cantidad + 1, subtotal: (it.cantidad + 1) * it.costo_unitario } : it
        )
      }
      const precioConocido = preciosProveedor[found!.id] || 0
      const newItem: ItemForm = {
        producto: found!,
        cantidad: 1,
        costo_unitario: precioConocido,
        subtotal: precioConocido,
        precio_venta: Number(found!.precio_actual) || 0,
      }
      const ultimaVacia = prev.length === 1 && !prev[0].producto
      return ultimaVacia ? [newItem] : [...prev, newItem]
    })
    setBarcodeInput('')
    setTimeout(() => barcodeRef.current?.focus(), 50)
  }, [localProductos, preciosProveedor])

  const total = useMemo(() => items.reduce((s, i) => s + i.subtotal, 0), [items])

  const handleSave = handleSubmit(async (fields) => {
    if (items.some(i => !i.producto)) { toast.error('Completá todos los productos de la lista'); return }
    setSaving(true)
    try {
      const payload = {
        proveedor: fields.proveedor_id,
        tipo_pago: fields.tipo_pago,
        nro_factura_proveedor: fields.nro_factura,
        items: items.map(i => ({ producto: i.producto!.id, cantidad: i.cantidad, costo_unitario: i.costo_unitario })),
      }
      if (editingCompra) {
        await api.put(`/compras/compras/${editingCompra.id}/`, payload)
        toast.success('Compra actualizada')
      } else {
        await api.post('/compras/compras/', payload)
        toast.success(`Compra registrada — ${formatGs(total)}`)
      }
      const actualizaciones = items
        .filter(i => i.producto && i.precio_venta > 0)
        .map(i => api.post(`/productos/productos/${i.producto!.id}/set-precio/`, { precio: i.precio_venta }))
      if (actualizaciones.length > 0) {
        await Promise.allSettled(actualizaciones)
        toast.success(`Precios de venta actualizados (${actualizaciones.length} producto${actualizaciones.length > 1 ? 's' : ''})`)
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
      title={editingCompra ? `Editar Compra #${editingCompra.id}` : 'Nueva Compra'}
      onOk={handleSave}
      onCancel={onClose}
      okText={editingCompra ? 'Guardar Cambios' : 'Registrar'}
      confirmLoading={saving}
      width={700}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Proveedor *</label>
            <Combobox
              options={proveedores.map(p => ({ value: p.id, label: p.razon_social }))}
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
          <label className={labelClass}>Nro. Factura Proveedor</label>
          <input placeholder="001-001-0001234" className={inputClass} {...register('nro_factura')} />
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <label className={`${labelClass} mb-0`}>Productos *</label>
            <Button size="sm" variant="ghost" onClick={() => setItems(prev => [...prev, { ...ITEM_EMPTY }])}>
              <Plus className="w-3.5 h-3.5" /> Agregar
            </Button>
          </div>

          <div className="flex items-center gap-2 mb-3">
            <div className="relative flex-1">
              <Scan className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <input
                ref={barcodeRef}
                type="text"
                value={barcodeInput}
                onChange={e => setBarcodeInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleBarcodeScan(barcodeInput) } }}
                placeholder="Escanear o escribir código de barras..."
                className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                autoComplete="off"
              />
            </div>
          </div>

          <div className="flex gap-2 items-center px-3 mb-1">
            <span className="flex-1 text-xs font-semibold text-slate-400 uppercase">Producto</span>
            <span className="w-16 text-xs font-semibold text-slate-400 uppercase text-center">Cant.</span>
            <span className="w-28 text-xs font-semibold text-slate-400 uppercase text-right">Costo compra</span>
            <span className="w-28 text-xs font-semibold text-blue-400 uppercase text-right">P. venta</span>
            <span className="w-24 text-xs font-semibold text-slate-400 uppercase text-right">Subtotal</span>
            <span className="w-5" />
          </div>
          <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
            {items.map((item, idx) => (
              <div key={idx} className="flex gap-2 items-center bg-slate-50 rounded-xl px-3 py-2">
                <div className="flex-1">
                  <Combobox
                    options={opcionesProducto}
                    value={item.producto?.id}
                    onChange={(_, opt) => actualizarItem(idx, 'producto', opt.data as Producto)}
                    filterLocal
                    placeholder="Producto..."
                  />
                </div>
                <input
                  type="number" min={1} value={item.cantidad}
                  onChange={e => actualizarItem(idx, 'cantidad', Number(e.target.value) || 1)}
                  className="w-16 border border-slate-200 rounded-xl px-2 py-2 text-sm text-center bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                />
                <input
                  type="number" min={0} value={item.costo_unitario}
                  onChange={e => actualizarItem(idx, 'costo_unitario', Number(e.target.value) || 0)}
                  className="w-28 border border-slate-200 rounded-xl px-2 py-2 text-sm text-right bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                  placeholder="Costo"
                />
                <input
                  type="number" min={0} value={item.precio_venta || ''}
                  onChange={e => actualizarItem(idx, 'precio_venta', Number(e.target.value) || 0)}
                  className="w-28 border border-blue-200 rounded-xl px-2 py-2 text-sm text-right bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400"
                  placeholder="Opcional"
                />
                <span className="w-24 text-sm font-semibold text-right text-slate-700 tabular-nums">{formatGs(item.subtotal)}</span>
                <button
                  onClick={() => setItems(prev => prev.length > 1 ? prev.filter((_, i) => i !== idx) : prev)}
                  className="p-1 text-slate-400 hover:text-red-500 transition-colors cursor-pointer shrink-0"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex justify-between items-center mt-3 pt-3 border-t border-slate-200">
            <span className="text-sm font-semibold text-slate-600">Total</span>
            <span className="text-lg font-bold text-emerald-700 tabular-nums">{formatGs(total)}</span>
          </div>
        </div>
      </div>
    </Modal>
  )
}
