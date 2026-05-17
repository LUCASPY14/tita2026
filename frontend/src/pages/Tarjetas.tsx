import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'

interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string
  hijo_nombre: string
  saldo_actual: string
  limite_credito: string
  estado: string
  permite_saldo_negativo: boolean
}

const estadoColor: Record<string, BadgeColor> = {
  ACTIVA: 'green',
  BLOQUEADA: 'orange',
  VENCIDA: 'red',
  CANCELADA: 'default',
}

export default function Tarjetas() {
  const [tarjetas, setTarjetas] = useState<Tarjeta[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [recargaTarjeta, setRecargaTarjeta] = useState<Tarjeta | null>(null)
  const [monto, setMonto] = useState('')
  const [recargando, setRecargando] = useState(false)

  const cargar = () => {
    setLoading(true)
    api.get('/core/tarjetas/', { params: search ? { search } : {} })
      .then(({ data }) => setTarjetas(data.results || []))
      .catch(() => toast.error('Error al cargar tarjetas'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { cargar() }, [search])

  const handleRecarga = async () => {
    const montoNum = parseInt(monto)
    if (!montoNum || montoNum <= 0) { toast.error('Ingrese un monto valido'); return }
    setRecargando(true)
    try {
      await api.post('/core/cargas-saldo/', {
        tarjeta: recargaTarjeta?.nro_tarjeta,
        monto_cargado: montoNum,
        metodo_pago: 'EFECTIVO',
      })
      toast.success('Recarga exitosa')
      setModalOpen(false)
      setMonto('')
      setTarjetas((prev) =>
        prev.map((t) =>
          t.nro_tarjeta === recargaTarjeta?.nro_tarjeta
            ? { ...t, saldo_actual: String(parseInt(t.saldo_actual) + montoNum) }
            : t
        )
      )
    } catch {
      toast.error('Error al recargar')
    } finally {
      setRecargando(false)
    }
  }

  const columns: Column<Tarjeta>[] = [
    { title: 'Nro. Tarjeta', dataIndex: 'nro_tarjeta', key: 'nro_tarjeta' },
    { title: 'Estudiante', dataIndex: 'hijo_nombre', key: 'hijo' },
    {
      title: 'Saldo',
      dataIndex: 'saldo_actual',
      key: 'saldo',
      render: (v) => {
        const n = parseInt(v as string)
        return <span className={n < 0 ? 'text-red-600 font-bold' : 'text-green-700 font-bold'}>Gs. {n.toLocaleString('es-PY')}</span>
      },
    },
    {
      title: 'Limite Credito',
      dataIndex: 'limite_credito',
      key: 'limite',
      render: (v) => 'Gs. ' + parseInt(v as string).toLocaleString('es-PY'),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (v) => <Badge color={estadoColor[v as string] || 'default'}>{v as string}</Badge>,
    },
    {
      title: '',
      key: 'accion',
      width: 100,
      render: (_, r) => (
        <Button
          variant="primary"
          size="sm"
          onClick={() => { setRecargaTarjeta(r); setMonto(''); setModalOpen(true) }}
        >
          + Recargar
        </Button>
      ),
    },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Tarjetas</h2>
      <Input
        placeholder="🔍 Buscar tarjetas..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-sm"
      />
      <Table columns={columns} dataSource={tarjetas} rowKey="nro_tarjeta" loading={loading} pageSize={10} />

      <Modal
        open={modalOpen}
        title={`Recargar: ${recargaTarjeta?.hijo_nombre || ''}`}
        onOk={handleRecarga}
        onCancel={() => setModalOpen(false)}
        confirmLoading={recargando}
        okText="Recargar"
      >
        <p className="mb-3 text-sm text-gray-600">
          Saldo actual: <strong>Gs. {parseInt(recargaTarjeta?.saldo_actual || '0').toLocaleString('es-PY')}</strong>
        </p>
        <Input
          type="number"
          placeholder="Monto en Guaranies"
          value={monto}
          onChange={(e) => setMonto(e.target.value)}
          min={1000}
          step={1000}
        />
      </Modal>
    </div>
  )
}
