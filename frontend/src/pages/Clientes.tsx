import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Input from '../components/ui/Input'
import Badge from '../components/ui/Badge'
import Table, { type Column } from '../components/ui/Table'

interface Cliente {
  id: number
  ruc_ci: string
  nombres: string
  apellidos: string
  telefono: string
  email: string
  activo: boolean
  limite_credito: string
}

const columns: Column<Cliente>[] = [
  { title: 'RUC/CI', dataIndex: 'ruc_ci', key: 'ruc_ci' },
  {
    title: 'Nombre',
    key: 'nombre',
    render: (_, r) => <span>{r.nombres} {r.apellidos}</span>,
  },
  { title: 'Telefono', dataIndex: 'telefono', key: 'telefono' },
  { title: 'Email', dataIndex: 'email', key: 'email' },
  {
    title: 'Limite Credito',
    dataIndex: 'limite_credito',
    key: 'limite',
    render: (v) => v ? 'Gs. ' + parseInt(v as string).toLocaleString('es-PY') : '-',
  },
  {
    title: 'Estado',
    dataIndex: 'activo',
    key: 'activo',
    render: (v) => <Badge color={v ? 'green' : 'red'}>{v ? 'Activo' : 'Inactivo'}</Badge>,
  },
]

export default function Clientes() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')

  useEffect(() => {
    setLoading(true)
    api.get('/clientes/clientes/', { params: search ? { search } : {} })
      .then(({ data }) => setClientes(data.results || []))
      .catch(() => toast.error('Error al cargar clientes'))
      .finally(() => setLoading(false))
  }, [search])

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Clientes</h2>
      <Input
        placeholder="🔍 Buscar clientes..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-sm"
      />
      <Table columns={columns} dataSource={clientes} rowKey="id" loading={loading} pageSize={10} />
    </div>
  )
}
