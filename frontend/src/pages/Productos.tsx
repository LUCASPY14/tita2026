import { useEffect, useState } from 'react'
import { Table, Input, Tag, message } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '../services/api'

interface Producto {
  id: number
  codigo_barra: string
  descripcion: string
  categoria_nombre: string
  precio_actual: string
  activo: boolean
  stock_minimo: number
}

export default function Productos() {
  const [productos, setProductos] = useState<Producto[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')

  const cargarProductos = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/productos/productos/', {
        params: { search }
      })
      setProductos(data.results || [])
    } catch {
      message.error('Error al cargar productos')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarProductos()
  }, [search])

  const columns = [
    {
      title: 'Codigo',
      dataIndex: 'codigo_barra',
      key: 'codigo_barra',
    },
    {
      title: 'Descripcion',
      dataIndex: 'descripcion',
      key: 'descripcion',
    },
    {
      title: 'Categoria',
      dataIndex: 'categoria_nombre',
      key: 'categoria',
    },
    {
      title: 'Precio',
      dataIndex: 'precio_actual',
      key: 'precio',
      render: (p: string) => (
        <span className="font-bold text-green-700">
          Gs. {parseInt(p).toLocaleString('es-PY')}
        </span>
      ),
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
      <h2 className="text-2xl font-bold mb-4">Productos</h2>
      <Input
        prefix={<SearchOutlined />}
        placeholder="Buscar productos..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-md"
        size="large"
      />
      <Table
        dataSource={productos}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}