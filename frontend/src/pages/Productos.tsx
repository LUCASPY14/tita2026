import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Input from '../components/ui/Input'
import Badge from '../components/ui/Badge'
import Table, { type Column } from '../components/ui/Table'

interface Producto {
  id: number
  codigo_barra: string
  descripcion: string
  categoria_nombre: string
  precio_actual: string
  activo: boolean
}

const columns: Column<Producto>[] = [
  { title: 'Codigo', dataIndex: 'codigo_barra', key: 'codigo_barra' },
  { title: 'Descripcion', dataIndex: 'descripcion', key: 'descripcion' },
  { title: 'Categoria', dataIndex: 'categoria_nombre', key: 'categoria' },
  {
    title: 'Precio',
    dataIndex: 'precio_actual',
    key: 'precio',
    render: (v) => <span className="font-bold text-green-700">Gs. {parseInt(v as string).toLocaleString('es-PY')}</span>,
  },
  {
    title: 'Estado',
    dataIndex: 'activo',
    key: 'activo',
    render: (v) => <Badge color={v ? 'green' : 'red'}>{v ? 'Activo' : 'Inactivo'}</Badge>,
  },
]

export default function Productos() {
  const [productos, setProductos] = useState<Producto[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')

  useEffect(() => {
    setLoading(true)
    api.get('/productos/productos/', { params: search ? { search } : {} })
      .then(({ data }) => setProductos(data.results || []))
      .catch(() => toast.error('Error al cargar productos'))
      .finally(() => setLoading(false))
  }, [search])

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Productos</h2>
      <Input
        placeholder="🔍 Buscar productos..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-sm"
      />
      <Table columns={columns} dataSource={productos} rowKey="id" loading={loading} pageSize={10} />
    </div>
  )
}
