import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Combobox from '../../components/ui/Combobox'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, formatGs, formatFecha,
  type ClienteOption, type ProductoOption, type VentaOrigen, type NCDetalle,
} from './shared'

interface Props {
  open: boolean
  clientes: ClienteOption[]
  productos: ProductoOption[]
  /** Pre-selecciona cliente y venta al abrir desde "Emitir NC" en una venta puntual. */
  initialVenta: VentaOrigen | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalNC({ open, clientes, productos, initialVenta, onClose, onSaved }: Props) {
  const [clienteId, setClienteId] = useState<number | ''>('')
  const [ventaId, setVentaId] = useState<number | ''>('')
  const [ventasDisponibles, setVentasDisponibles] = useState<VentaOrigen[]>([])
  const [nroNC, setNroNC] = useState('')
  const [motivo, setMotivo] = useState('')
  const [monto, setMonto] = useState('')
  const [conDevolucion, setConDevolucion] = useState(false)
  const [detalles, setDetalles] = useState<NCDetalle[]>([])
  const [saving, setSaving] = useState(false)

  const resetForm = useCallback(() => {
    setClienteId(''); setVentaId(''); setVentasDisponibles([])
    setNroNC(''); setMotivo(''); setMonto('')
    setConDevolucion(false); setDetalles([])
  }, [])

  const handleClienteChange = useCallback(async (clId: number | '') => {
    setClienteId(clId)
    setVentaId('')
    setDetalles([])
    if (!clId) { setVentasDisponibles([]); return }
    try {
      const { data } = await api.get('/ventas/ventas/', { params: { cliente: clId, page_size: 50, ordering: '-fecha' } })
      setVentasDisponibles(data.results ?? [])
    } catch {
      setVentasDisponibles([])
    }
  }, [])

  const prefillDetallesFromVenta = useCallback((venta: VentaOrigen | undefined) => {
    if (!venta?.detalles?.length) { setDetalles([]); return }
    const items: NCDetalle[] = venta.detalles.map(d => ({
      producto: d.producto,
      producto_nombre: d.producto_nombre,
      cantidad: Number(d.cantidad),
      precio_unitario: Number(d.precio_unitario),
    }))
    setDetalles(items)
    setMonto(String(Math.round(items.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))))
  }, [])

  // Pre-cargar cliente/venta cuando se abre desde el botón "Emitir NC" de una venta.
  useEffect(() => {
    if (!open || !initialVenta) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setClienteId(initialVenta.cliente)
    setVentaId(initialVenta.id)
    setVentasDisponibles([initialVenta])
    setConDevolucion(true)
    prefillDetallesFromVenta(initialVenta)
  }, [open, initialVenta, prefillDetallesFromVenta])

  async function handleSave() {
    if (!clienteId) { toast.error('Seleccioná un cliente'); return }
    if (!nroNC.trim()) { toast.error('Ingresá el número de nota de crédito'); return }
    if (!motivo.trim()) { toast.error('Ingresá el motivo'); return }
    if (conDevolucion && detalles.length === 0) { toast.error('Agregá al menos un ítem devuelto'); return }
    const montoNum = Number(monto) || 0
    if (!conDevolucion && montoNum <= 0) { toast.error('Ingresá un monto válido'); return }

    setSaving(true)
    try {
      await api.post('/ventas/notas-credito/', {
        cliente: clienteId,
        venta_origen: ventaId || null,
        nro_nota_credito: nroNC.trim(),
        motivo: motivo.trim(),
        monto_total: conDevolucion ? undefined : montoNum,
        detalles: conDevolucion ? detalles.map(d => ({
          producto: d.producto, cantidad: d.cantidad, precio_unitario: d.precio_unitario,
        })) : [],
      })
      toast.success('Nota de crédito emitida')
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
    const updated = detalles.map((d, i) => i === idx ? { ...d, [field]: value } : d)
    setDetalles(updated)
    setMonto(String(Math.round(updated.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))))
  }

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title="Nueva Nota de Crédito"
      onOk={handleSave}
      onCancel={() => { resetForm(); onClose() }}
      okText="Emitir"
      confirmLoading={saving}
      width={620}
    >
      <div className="space-y-4">
        <div>
          <label className={labelClass}>Cliente *</label>
          <Combobox
            options={clientes.map(c => ({ value: c.id, label: c.nombre_completo }))}
            value={clienteId || undefined}
            onChange={v => handleClienteChange(v as number)}
            filterLocal
            placeholder="Buscar cliente..."
          />
        </div>

        <div>
          <label className={labelClass}>Venta de origen (opcional)</label>
          <select
            className={inputClass}
            value={ventaId}
            onChange={e => {
              const id = e.target.value ? Number(e.target.value) : ''
              setVentaId(id)
              if (conDevolucion) prefillDetallesFromVenta(ventasDisponibles.find(v => v.id === id))
            }}
            disabled={!clienteId}
          >
            <option value="">Sin venta asociada</option>
            {ventasDisponibles.map(v => (
              <option key={v.id} value={v.id}>
                #{v.id} — {formatGs(v.monto_total)} — {formatFecha(v.fecha)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-slate-700">
            <input
              type="checkbox" checked={conDevolucion}
              onChange={e => { setConDevolucion(e.target.checked); if (!e.target.checked) setDetalles([]) }}
              className="w-4 h-4 rounded accent-blue-600"
            />
            Incluye devolución de productos (repone stock)
          </label>
        </div>

        {conDevolucion && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={labelClass}>Ítems devueltos *</label>
              <button
                type="button"
                onClick={() => setDetalles(prev => [...prev, { producto: 0, producto_nombre: '', cantidad: 1, precio_unitario: 0 }])}
                className="text-xs text-blue-600 hover:underline"
              >
                + Agregar ítem
              </button>
            </div>
            {detalles.length === 0 ? (
              <p className="text-xs text-slate-400 italic">
                {ventaId ? 'La venta no tiene ítems registrados.' : 'No hay ítems. Seleccioná una venta para pre-llenar o agregá manualmente.'}
              </p>
            ) : (
              <div className="space-y-2">
                {detalles.map((det, idx) => (
                  <div key={idx} className="grid grid-cols-[1fr_80px_100px_28px] gap-1 items-center">
                    <select
                      className={`${inputClass} text-xs py-1`}
                      value={det.producto}
                      onChange={e => {
                        const prod = productos.find(p => p.id === Number(e.target.value))
                        updateDetalle(idx, 'producto', Number(e.target.value))
                        if (prod) updateDetalle(idx, 'producto_nombre', prod.descripcion)
                      }}
                    >
                      <option value={0}>Producto...</option>
                      {productos.map(p => <option key={p.id} value={p.id}>{p.descripcion}</option>)}
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
                        const remaining = detalles.filter((_, i) => i !== idx)
                        setDetalles(remaining)
                        setMonto(remaining.length ? String(Math.round(remaining.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))) : '')
                      }}
                      className="text-red-400 hover:text-red-600 text-lg leading-none"
                    >
                      ×
                    </button>
                  </div>
                ))}
                <p className="text-xs text-slate-500 text-right">
                  Total calculado: <strong>{formatGs(detalles.reduce((s, d) => s + d.cantidad * d.precio_unitario, 0))}</strong>
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
              placeholder="0" value={monto}
              onChange={e => setMonto(e.target.value)}
              disabled={conDevolucion}
            />
          </div>
          <div>
            <label className={labelClass}>Nro. Nota de Crédito *</label>
            <input
              className={inputClass} placeholder="001-001-0000001"
              value={nroNC} onChange={e => setNroNC(e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Motivo *</label>
          <textarea
            className={`${inputClass} resize-none`} rows={2}
            placeholder="Devolución de producto vencido, descuento comercial, etc."
            value={motivo} onChange={e => setMotivo(e.target.value)}
          />
        </div>
      </div>
    </Modal>
  )
}
