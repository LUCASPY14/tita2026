import { useCallback, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Combobox from '../../components/ui/Combobox'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, formatFecha, type Compra, type NCDetalle, type Producto, type Proveedor } from './shared'

interface Props {
  open: boolean
  proveedores: Proveedor[]
  productos: Producto[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalNC({ open, proveedores, productos, onClose, onSaved }: Props) {
  const [ncProveedorId, setNcProveedorId] = useState<number | ''>('')
  const [ncCompraId, setNcCompraId] = useState<number | ''>('')
  const [ncMonto, setNcMonto] = useState('')
  const [ncNroFactura, setNcNroFactura] = useState('')
  const [ncObservacion, setNcObservacion] = useState('')
  const [ncTipoNC, setNcTipoNC] = useState<'AJUSTE_PRECIO' | 'DEVOLUCION'>('AJUSTE_PRECIO')
  const [ncDetalles, setNcDetalles] = useState<NCDetalle[]>([])
  const [ncComprasDisponibles, setNcComprasDisponibles] = useState<Compra[]>([])
  const [saving, setSaving] = useState(false)

  function resetForm() {
    setNcProveedorId('')
    setNcCompraId('')
    setNcMonto('')
    setNcNroFactura('')
    setNcObservacion('')
    setNcTipoNC('AJUSTE_PRECIO')
    setNcDetalles([])
    setNcComprasDisponibles([])
  }

  const handleProveedorChange = useCallback(async (provId: number | '') => {
    setNcProveedorId(provId)
    setNcCompraId('')
    setNcDetalles([])
    if (!provId) { setNcComprasDisponibles([]); return }
    try {
      const { data } = await api.get('/compras/compras/', { params: { proveedor: provId, page_size: 100 } })
      setNcComprasDisponibles(data.results ?? [])
    } catch {
      setNcComprasDisponibles([])
    }
  }, [])

  const prefillDetallesFromCompra = useCallback((compraId: number | '') => {
    if (!compraId) { setNcDetalles([]); return }
    const compra = ncComprasDisponibles.find(c => c.id_compra === compraId)
    if (!compra?.detalles?.length) return
    const items: NCDetalle[] = compra.detalles.map(d => ({
      producto: d.producto,
      producto_nombre: d.producto_nombre,
      cantidad: Number(d.cantidad),
      precio_unitario: Number(d.costo_unitario),
    }))
    setNcDetalles(items)
    setNcMonto(String(Math.round(items.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))))
  }, [ncComprasDisponibles])

  async function handleSave() {
    if (!ncProveedorId) { toast.error('Seleccioná un proveedor'); return }
    const montoNum = Number(ncMonto) || 0
    if (montoNum <= 0) { toast.error('Ingresá un monto válido'); return }
    if (ncTipoNC === 'DEVOLUCION' && ncDetalles.length === 0) {
      toast.error('Agregá al menos un ítem para la devolución'); return
    }
    setSaving(true)
    try {
      await api.post('/compras/notas-credito/', {
        proveedor: ncProveedorId,
        compra_original: ncCompraId || null,
        monto_total: montoNum,
        nro_factura_compra: ncNroFactura || null,
        observacion: ncObservacion || null,
        tipo_nc: ncTipoNC,
        detalles: ncTipoNC === 'DEVOLUCION' ? ncDetalles.map(d => ({
          producto: d.producto,
          cantidad: d.cantidad,
          precio_unitario: d.precio_unitario,
        })) : [],
      })
      toast.success('Nota de crédito registrada')
      resetForm()
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  function updateDetalle(idx: number, field: keyof NCDetalle, value: string | number) {
    setNcDetalles(prev => {
      const next = [...prev]
      next[idx] = { ...next[idx], [field]: value }
      return next
    })
    const updated = ncDetalles.map((d, i) => i === idx ? { ...d, [field]: value } : d)
    setNcMonto(String(Math.round(updated.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))))
  }

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title="Nueva Nota de Crédito"
      onOk={handleSave}
      onCancel={() => { resetForm(); onClose() }}
      okText="Registrar"
      confirmLoading={saving}
      width={620}
    >
      <div className="space-y-4">
        <div>
          <label className={labelClass}>Tipo de nota de crédito *</label>
          <div className="flex gap-3 mt-1">
            {([
              { value: 'AJUSTE_PRECIO', label: 'Ajuste de precio' },
              { value: 'DEVOLUCION', label: 'Devolución de mercadería' },
            ] as const).map(opt => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer text-sm">
                <input
                  type="radio" name="ncTipoNC" value={opt.value}
                  checked={ncTipoNC === opt.value}
                  onChange={() => { setNcTipoNC(opt.value); setNcDetalles([]) }}
                  className="accent-blue-600"
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className={labelClass}>Proveedor *</label>
          <Combobox
            options={proveedores.map(p => ({ value: p.id_proveedor, label: p.razon_social }))}
            value={ncProveedorId || undefined}
            onChange={v => handleProveedorChange(v as number)}
            filterLocal
            placeholder="Buscar proveedor..."
          />
        </div>

        <div>
          <label className={labelClass}>Compra de origen (opcional)</label>
          <select
            className={inputClass}
            value={ncCompraId}
            onChange={e => {
              const id = e.target.value ? Number(e.target.value) : ''
              setNcCompraId(id)
              if (ncTipoNC === 'DEVOLUCION') prefillDetallesFromCompra(id)
            }}
            disabled={!ncProveedorId}
          >
            <option value="">Sin compra asociada</option>
            {ncComprasDisponibles.map(c => (
              <option key={c.id_compra} value={c.id_compra}>
                #{c.id_compra} — {formatGs(c.monto_total)} — {formatFecha(c.fecha)}
              </option>
            ))}
          </select>
        </div>

        {ncTipoNC === 'DEVOLUCION' && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={labelClass}>Ítems devueltos *</label>
              <button
                type="button"
                onClick={() => setNcDetalles(prev => [...prev, { producto: 0, producto_nombre: '', cantidad: 1, precio_unitario: 0 }])}
                className="text-xs text-blue-600 hover:underline"
              >
                + Agregar ítem
              </button>
            </div>
            {ncDetalles.length === 0 ? (
              <p className="text-xs text-slate-400 italic">
                {ncCompraId ? 'La compra no tiene ítems registrados.' : 'No hay ítems. Seleccioná una compra para pre-llenar o agregá manualmente.'}
              </p>
            ) : (
              <div className="space-y-2">
                {ncDetalles.map((det, idx) => (
                  <div key={idx} className="grid grid-cols-[1fr_80px_100px_28px] gap-1 items-center">
                    <select
                      className={`${inputClass} text-xs py-1`}
                      value={det.producto}
                      onChange={e => {
                        const prod = productos.find(p => p.id_producto === Number(e.target.value))
                        updateDetalle(idx, 'producto', Number(e.target.value))
                        if (prod) updateDetalle(idx, 'producto_nombre', prod.descripcion)
                      }}
                    >
                      <option value={0}>Producto...</option>
                      {productos.map(p => <option key={p.id_producto} value={p.id_producto}>{p.descripcion}</option>)}
                    </select>
                    <input
                      type="number" min={0.001} step="0.001"
                      className={`${inputClass} text-xs py-1`}
                      placeholder="Cant."
                      value={det.cantidad}
                      onChange={e => updateDetalle(idx, 'cantidad', Number(e.target.value))}
                    />
                    <input
                      type="number" min={0}
                      className={`${inputClass} text-xs py-1`}
                      placeholder="P.Unit."
                      value={det.precio_unitario}
                      onChange={e => updateDetalle(idx, 'precio_unitario', Number(e.target.value))}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        const remaining = ncDetalles.filter((_, i) => i !== idx)
                        setNcDetalles(remaining)
                        setNcMonto(remaining.length ? String(Math.round(remaining.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))) : '')
                      }}
                      className="text-red-400 hover:text-red-600 text-lg leading-none"
                    >
                      ×
                    </button>
                  </div>
                ))}
                <p className="text-xs text-slate-500 text-right">
                  Total calculado: <strong>{formatGs(ncDetalles.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))}</strong>
                </p>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Monto *</label>
            <input
              type="number" min={1} className={inputClass}
              placeholder="0" value={ncMonto}
              onChange={e => setNcMonto(e.target.value)}
            />
          </div>
          <div>
            <label className={labelClass}>Nro. Factura proveedor</label>
            <input
              className={inputClass} placeholder="001-001-0000001"
              value={ncNroFactura} onChange={e => setNcNroFactura(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Observación</label>
          <textarea
            className={`${inputClass} resize-none`} rows={2}
            placeholder="Devolución de mercadería, descuento, etc."
            value={ncObservacion} onChange={e => setNcObservacion(e.target.value)}
          />
        </div>
      </div>
    </Modal>
  )
}
