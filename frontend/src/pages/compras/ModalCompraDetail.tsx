import { DollarSign, PackageCheck } from 'lucide-react'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import {
  formatGs, formatFecha,
  TIPO_PAGO_COLOR, ESTADO_PAGO_COLOR, ESTADO_ENTREGA_COLOR,
  type Compra,
} from './shared'

interface Props {
  compra: Compra | null
  canApprove: boolean
  confirmandoEntrega: number | null
  onClose: () => void
  onPago: (c: Compra) => void
  onConfirmarEntrega: (c: Compra) => void
}

export default function ModalCompraDetail({ compra, canApprove, confirmandoEntrega, onClose, onPago, onConfirmarEntrega }: Props) {
  return (
    <Modal
      open={!!compra}
      title={compra ? `Compra #${compra.id_compra} — ${compra.proveedor_nombre}` : ''}
      onCancel={onClose}
      width={680}
      footer={null}
    >
      {compra && (
        <div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {[
              { label: 'Total', value: formatGs(compra.monto_total), warn: false },
              { label: 'Saldo Pendiente', value: formatGs(compra.saldo_pendiente), warn: Number(compra.saldo_pendiente) > 0 },
              { label: 'Fecha', value: formatFecha(compra.fecha), warn: false },
              { label: 'Nro. Factura', value: compra.nro_factura_proveedor || '—', warn: false },
            ].map(({ label, value, warn }) => (
              <div key={label} className="bg-slate-50 rounded-xl px-3 py-3">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className={`text-base font-bold mt-0.5 tabular-nums ${warn ? 'text-red-600' : 'text-slate-800'}`}>{value}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 mb-4">
            <Badge color={TIPO_PAGO_COLOR[compra.tipo_pago] ?? 'default'}>{compra.tipo_pago}</Badge>
            <Badge color={ESTADO_PAGO_COLOR[compra.estado_pago] ?? 'default'}>{compra.estado_pago}</Badge>
            {compra.tipo_pago === 'CREDITO' && (
              <Badge color={ESTADO_ENTREGA_COLOR[compra.estado_entrega] ?? 'default'}>
                Entrega: {compra.estado_entrega}
              </Badge>
            )}
          </div>

          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">Detalle de productos</h3>
          <div className="border border-slate-200 rounded-xl overflow-hidden mb-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200">
                  <th className="px-4 py-2 text-left text-sm font-semibold text-slate-500 uppercase">Producto</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Cant.</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Costo Unit.</th>
                  <th className="px-4 py-2 text-right text-sm font-semibold text-slate-500 uppercase">Subtotal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {(compra.detalles ?? []).map(d => (
                  <tr key={d.id_detalle_compra}>
                    <td className="px-4 py-2.5 text-slate-700">{d.producto_nombre}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">{d.cantidad}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">{formatGs(d.costo_unitario)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-slate-800">{formatGs(d.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between">
            <Button variant="secondary" onClick={onClose}>Cerrar</Button>
            <div className="flex items-center gap-2">
              {compra.tipo_pago === 'CREDITO' && compra.estado_entrega === 'PENDIENTE' && (
                <Button
                  variant="secondary"
                  onClick={() => onConfirmarEntrega(compra)}
                  disabled={confirmandoEntrega === compra.id_compra}
                >
                  <PackageCheck className="w-4 h-4" />
                  {confirmandoEntrega === compra.id_compra ? 'Confirmando...' : 'Confirmar Entrega'}
                </Button>
              )}
              {canApprove && (compra.estado_pago === 'PENDIENTE' || compra.estado_pago === 'PARCIAL') && (
                <Button variant="primary" onClick={() => onPago(compra)}>
                  <DollarSign className="w-4 h-4" />
                  Registrar Pago
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}
