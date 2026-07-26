import { ArrowRightCircle, CheckCircle, Send, XCircle } from 'lucide-react'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import {
  formatGs, formatFecha,
  TIPO_PAGO_COLOR, OC_ESTADO_COLOR, OC_ESTADO_LABEL,
  type OrdenCompra,
} from './shared'

interface Props {
  oc: OrdenCompra | null
  canApprove: boolean
  accionLoading: boolean
  onClose: () => void
  onEdit: (oc: OrdenCompra) => void
  onRechazar: (oc: OrdenCompra) => void
  onAccion: (oc: OrdenCompra, accion: 'submit' | 'aprobar' | 'convertir') => void
}

export default function ModalOCDetail({ oc, canApprove, accionLoading, onClose, onEdit, onRechazar, onAccion }: Props) {
  return (
    <Modal
      open={!!oc}
      title={oc ? `OC #${oc.id} — ${oc.proveedor_nombre}` : ''}
      onCancel={onClose}
      width={680}
      footer={null}
    >
      {oc && (
        <div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            {[
              { label: 'Total', value: formatGs(oc.monto_total) },
              { label: 'Tipo Pago', value: oc.tipo_pago },
              { label: 'Fecha', value: formatFecha(oc.fecha_creacion) },
              { label: 'Factura', value: oc.nro_factura_esperada || '—' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-50 rounded-xl px-3 py-3">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className="text-base font-bold mt-0.5 text-slate-800">{value}</p>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 mb-3 flex-wrap">
            <Badge color={TIPO_PAGO_COLOR[oc.tipo_pago] ?? 'default'}>{oc.tipo_pago}</Badge>
            <Badge color={OC_ESTADO_COLOR[oc.estado] ?? 'default'}>
              {OC_ESTADO_LABEL[oc.estado] ?? oc.estado}
            </Badge>
            {oc.aprobado_por_nombre && (
              <span className="text-sm text-slate-500">Aprobado por: <strong>{oc.aprobado_por_nombre}</strong></span>
            )}
          </div>

          {oc.motivo_rechazo && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4">
              <p className="text-sm font-semibold text-red-700 mb-0.5">Motivo de rechazo</p>
              <p className="text-sm text-red-600">{oc.motivo_rechazo}</p>
            </div>
          )}
          {oc.observaciones && <p className="text-sm text-slate-500 mb-4">Obs: {oc.observaciones}</p>}

          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-2">Productos solicitados</h3>
          <div className="border border-slate-200 rounded-xl overflow-hidden mb-5">
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
                {(oc.detalles ?? []).map(d => (
                  <tr key={d.id}>
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
              {oc.estado === 'BORRADOR' && (
                <>
                  <Button variant="secondary" onClick={() => { onClose(); onEdit(oc) }}>Editar</Button>
                  <Button variant="primary" disabled={accionLoading} onClick={() => onAccion(oc, 'submit')}>
                    <Send className="w-4 h-4" /> {accionLoading ? '...' : 'Enviar a revisión'}
                  </Button>
                </>
              )}
              {oc.estado === 'PENDIENTE' && canApprove && (
                <>
                  <Button variant="secondary" onClick={() => { onClose(); onRechazar(oc) }}>
                    <XCircle className="w-4 h-4" /> Rechazar
                  </Button>
                  <Button variant="primary" disabled={accionLoading} onClick={() => onAccion(oc, 'aprobar')}>
                    <CheckCircle className="w-4 h-4" /> {accionLoading ? '...' : 'Aprobar'}
                  </Button>
                </>
              )}
              {oc.estado === 'APROBADA' && canApprove && (
                <Button variant="primary" disabled={accionLoading} onClick={() => onAccion(oc, 'convertir')}>
                  <ArrowRightCircle className="w-4 h-4" /> {accionLoading ? '...' : 'Convertir en Compra'}
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}
