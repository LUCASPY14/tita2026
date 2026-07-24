import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Table, { type Column } from '../../components/ui/Table'
import { formatGs, formatFecha, type CuentaCorriente, type Proveedor } from './shared'

interface Props {
  proveedor: Proveedor | null
  onClose: () => void
}

export default function ModalCuentaCorriente({ proveedor, onClose }: Props) {
  const [movimientos, setMovimientos] = useState<CuentaCorriente[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!proveedor) return
    setLoading(true)
    api.get('/compras/cuentas-corrientes/', { params: { proveedor: proveedor.id, page_size: 200 } })
      .then(({ data }) => setMovimientos(data.results ?? data ?? []))
      .catch(() => toast.error('Error al cargar cuenta corriente'))
      .finally(() => setLoading(false))
  }, [proveedor])

  const columns: Column<CuentaCorriente>[] = [
    { title: 'Fecha', key: 'fecha', render: (_, r) => <span className="text-base text-slate-500">{formatFecha(r.fecha)}</span> },
    { title: 'Tipo', key: 'tipo', render: (_, r) => <Badge color={r.tipo === 'CARGO' ? 'orange' : 'green'}>{r.tipo}</Badge> },
    { title: 'Descripción', key: 'desc', render: (_, r) => <span className="text-base text-slate-600">{r.descripcion}</span> },
    { title: 'Monto', key: 'monto', render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto)}</span> },
    {
      title: 'Saldo',
      key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_resultante) || 0
        return <span className={`tabular-nums text-base font-medium ${n > 0 ? 'text-red-600' : 'text-emerald-700'}`}>{formatGs(n)}</span>
      },
    },
  ]

  return (
    <Modal
      open={!!proveedor}
      title={`Cuenta Corriente — ${proveedor?.razon_social ?? ''}`}
      onCancel={onClose}
      width={700}
      footer={null}
    >
      <div className="bg-slate-50 rounded-xl px-4 py-3 flex justify-between items-center mb-4">
        <div>
          <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">RUC</p>
          <p className="text-base font-semibold text-slate-800">{proveedor?.ruc}</p>
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-500 font-medium uppercase tracking-wide">Saldo Actual</p>
          <p className={`text-xl font-bold tabular-nums ${Number(proveedor?.saldo_cuenta_corriente) > 0 ? 'text-red-600' : 'text-emerald-700'}`}>
            {formatGs(proveedor?.saldo_cuenta_corriente)}
          </p>
        </div>
      </div>
      {loading ? (
        <div className="py-10 text-center text-slate-400 text-sm">Cargando...</div>
      ) : (
        <Table columns={columns} dataSource={movimientos} rowKey="id" pageSize={10} />
      )}
      <div className="flex justify-end mt-4">
        <Button variant="secondary" onClick={onClose}>Cerrar</Button>
      </div>
    </Modal>
  )
}
