import { useEffect, useState } from 'react'
import { Table, Input, Tag, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '../services/api'

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

export default function Clientes() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')

  const cargarClientes = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/clientes/', {
        params: { search }
      })
      setClientes(data.results || [])
    } catch {
      message.error('Error al cargar clientes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarClientes()
  }, [search])

  const columns = [
    {
      title: 'RUC/CI',
      dataIndex: 'ruc_ci',
      key: 'ruc_ci',
    },
    {
      title: 'Nombre',
      key: 'nombre',
      render: (_: unknown, record: Cliente) => (
        <span>{record.nombres} {record.apellidos}</span>
      ),
    },
    {
      title: 'Telefono',
      dataIndex: 'telefono',
      key: 'telefono',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Limite Credito',
      dataIndex: 'limite_credito',
      key: 'limite_credito',
      render: (v: string) => v ? 'Gs. ' + parseInt(v).toLocaleString('es-PY') : '-',
    },
    {
      title: 'Estado',
      dataIndex: 'activo',
      key: 'activo',
      render: (activo: boolean) => (
        <Tag color={activo ? 'green' : 'red'}>
          {activo ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Clientes</h2>
      <Input
        prefix={<SearchOutlined />}
        placeholder="Buscar clientes..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-md"
        size="large"
      />
      <Table
        dataSource={clientes}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}