import { useState } from 'react'
import toast from 'react-hot-toast'
import { Ban } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, formatFecha, NC_ESTADO_COLOR, type NotaCredito } from './shared'

interface Props {
  nc: NotaCredito | null
  canApprove: boolean
  onClose: () => void
  onAnulada: () => void
}

export default function ModalNCDetail({ nc, canApprove, onClose, onAnulada }: Props) {
  const [anulando, setAnulando] = useState(false)

  async function handleAnular() {
    if (!nc) return
    const extraMsg = nc.tipo_nc === 'DEVOLUCION' && nc.detalles?.length
      ? '\nTambién se revertirán los movimientos de stock.'
      : ''
    if (!confirm(`¿Anular NC #${nc.id} de ${nc.proveedor_nombre} por ${formatGs(nc.monto_total)}?\nEsto revertirá el crédito en la cuenta corriente.${extraMsg}`)) return
    setAnulando(true)
    try {
      await api.post(`/compras/notas-credito/${nc.id}/anular/`)
      toast.success('Nota de crédito anulada')
      onAnulada()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAnulando(false)
    }
  }

  return (
    <Modal
      open={!!nc}
      title={nc ? `Nota de Crédito #${nc.id} — ${nc.proveedor_nombre}` : ''}
      onCancel={onClose}
      width={560}
      footer={null}
    >
      {nc && (
        <div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            {[
              { label: 'Monto', value: formatGs(nc.monto_total) },
              { label: 'Tipo', value: nc.tipo_nc === 'DEVOLUCION' ? 'Devolución mercadería' : 'Ajuste de precio' },
              { label: 'Fecha', value: formatFecha(nc.fecha) },
              { label: 'Compra origen', value: nc.compra_original ? `#${nc.compra_original}` : '—' },
              { label: 'Nro. Factura', value: nc.nro_factura_compra || '—' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-50 rounded-xl px-3 py-3">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className="text-base font-bold mt-0.5 text-slate-800">{value}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 mb-3">
            <Badge color={NC_ESTADO_COLOR[nc.estado] ?? 'default'}>{nc.estado}</Badge>
          </div>

          {nc.observacion && <p className="text-sm text-slate-500 mb-3">Obs.: {nc.observacion}</p>}

          {nc.detalles?.length > 0 && (
            <div className="mb-4">
              <p className="text-xs font-semibold text-slate-500 uppercase mb-2">Ítems devueltos</p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-slate-400 border-b">
                    <th className="pb-1">Producto</th>
                    <th className="pb-1 text-right">Cant.</th>
                    <th className="pb-1 text-right">P.Unit.</th>
                    <th className="pb-1 text-right">Subtotal</th>
                  </tr>
                </thead>
                <tbody>
                  {nc.detalles.map(d => (
                    <tr key={d.id} className="border-b border-slate-100">
                      <td className="py-1">{d.producto_nombre}</td>
                      <td className="py-1 text-right tabular-nums">{d.cantidad}</td>
                      <td className="py-1 text-right tabular-nums">{formatGs(d.precio_unitario)}</td>
                      <td className="py-1 text-right tabular-nums">{formatGs(d.subtotal)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center justify-between">
            <Button variant="secondary" onClick={onClose}>Cerrar</Button>
            {canApprove && nc.estado !== 'ANULADA' && (
              <Button variant="secondary" onClick={handleAnular} disabled={anulando}>
                <Ban className="w-4 h-4" />
                {anulando ? 'Anulando...' : 'Anular NC'}
              </Button>
            )}
          </div>
        </div>
      )}
    </Modal>
  )
}
