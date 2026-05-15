import { useEffect, useState } from 'react'
import { Table, Input, Button, Select, InputNumber, Card, Tag, message, Space } from 'antd'
import { SearchOutlined, ShoppingCartOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../services/api'

interface Producto {
  id: number
  codigo_barra: string
  descripcion: string
  precio_actual: string
  categoria_nombre: string
  iva_10: string
  iva_5: string
  monto_exenta: string
}

interface ItemCarrito {
  producto: Producto
  cantidad: number
  subtotal: number
}

export default function Ventas() {
  const [productos, setProductos] = useState<Producto[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [categoria, setCategoria] = useState<string>('')
  const [categorias, setCategorias] = useState<string[]>([])
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [cobrando, setCobrando] = useState(false)

  const cargarProductos = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (search) params.search = search
      if (categoria) params.categoria = categoria
      const { data } = await api.get('/productos/productos/', { params })
      setProductos(data.results || [])
    } catch {
      message.error('Error al cargar productos')
    } finally {
      setLoading(false)
    }
  }

  const cargarCategorias = async () => {
    try {
      const { data } = await api.get('/productos/categorias/')
      setCategorias((data.results || []).map((c: { nombre: string }) => c.nombre))
    } catch {}
  }

  useEffect(() => {
    cargarCategorias()
  }, [])

  useEffect(() => {
    cargarProductos()
  }, [search, categoria])

  const agregarAlCarrito = (producto: Producto) => {
    setCarrito((prev) => {
      const existente = prev.find((item) => item.producto.id === producto.id)
      if (existente) {
        return prev.map((item) =>
          item.producto.id === producto.id
            ? { ...item, cantidad: item.cantidad + 1, subtotal: (item.cantidad + 1) * parseInt(producto.precio_actual) }
            : item
        )
      }
      return [...prev, { producto, cantidad: 1, subtotal: parseInt(producto.precio_actual) }]
    })
  }

  const cambiarCantidad = (productoId: number, cantidad: number) => {
    if (cantidad <= 0) {
      setCarrito((prev) => prev.filter((item) => item.producto.id !== productoId))
      return
    }
    setCarrito((prev) =>
      prev.map((item) =>
        item.producto.id === productoId
          ? { ...item, cantidad, subtotal: cantidad * parseInt(item.producto.precio_actual) }
          : item
      )
    )
  }

  const eliminarDelCarrito = (productoId: number) => {
    setCarrito((prev) => prev.filter((item) => item.producto.id !== productoId))
  }

  const total = carrito.reduce((sum, item) => sum + item.subtotal, 0)

  const cobrar = async () => {
    if (carrito.length === 0) {
      message.warning('Agregue productos al carrito')
      return
    }
    setCobrando(true)
    try {
      const items = carrito.map((item) => ({
        producto: item.producto.id,
        cantidad: item.cantidad,
        precio_unitario: parseInt(item.producto.precio_actual),
        iva_10: 0,
        iva_5: 0,
        monto_exenta: 0,
      }))
      await api.post('/ventas/ventas/', {
        cliente: 1,
        tipo: 'CONTADO',
        items: items,
        medio_pago: 1, // Efectivo
      })
      message.success('Venta registrada - Gs. ' + total.toLocaleString('es-PY'))
      setCarrito([])
    } catch {
      message.error('Error al registrar la venta')
    } finally {
      setCobrando(false)
    }
  }

  const columns = [
    {
      title: 'Codigo',
      dataIndex: 'codigo_barra',
      key: 'codigo',
      width: 120,
    },
    {
      title: 'Producto',
      dataIndex: 'descripcion',
      key: 'descripcion',
    },
    {
      title: 'Precio',
      dataIndex: 'precio_actual',
      key: 'precio',
      width: 120,
      render: (v: string) => (
        <span className="font-bold">Gs. {parseInt(v).toLocaleString('es-PY')}</span>
      ),
    },
    {
      title: 'Categoria',
      dataIndex: 'categoria_nombre',
      key: 'categoria',
      width: 120,
      render: (v: string) => <Tag>{v}</Tag>,
    },
    {
      title: '',
      key: 'accion',
      width: 80,
      render: (_: unknown, record: Producto) => (
        <Button type="primary" size="small" onClick={() => agregarAlCarrito(record)}>
          + Agregar
        </Button>
      ),
    },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Ventas</h2>
      <div className="flex gap-4">
        {/* Panel izquierdo: Productos */}
        <div className="flex-1">
          <div className="flex gap-2 mb-4">
            <Input
              prefix={<SearchOutlined />}
              placeholder="Buscar producto..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
              size="large"
            />
            <Select
              placeholder="Categoria"
              value={categoria || undefined}
              onChange={(v) => setCategoria(v || '')}
              allowClear
              size="large"
              className="w-48"
              options={categorias.map((c) => ({ value: c, label: c }))}
            />
          </div>
          <Table
            dataSource={productos}
            columns={columns}
            loading={loading}
            rowKey="id"
            pagination={{ pageSize: 8 }}
            size="small"
          />
        </div>

        {/* Panel derecho: Carrito */}
        <div className="w-96">
          <Card
            title={
              <Space>
                <ShoppingCartOutlined />
                Carrito ({carrito.length})
              </Space>
            }
            className="sticky top-4"
          >
            {carrito.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Carrito vacio</p>
            ) : (
              <>
                <div className="max-h-96 overflow-y-auto mb-4">
                  {carrito.map((item) => (
                    <div key={item.producto.id} className="flex justify-between items-center mb-2 pb-2 border-b">
                      <div className="flex-1">
                        <p className="font-bold text-sm">{item.producto.descripcion}</p>
                        <p className="text-xs text-gray-500">Gs. {parseInt(item.producto.precio_actual).toLocaleString('es-PY')} c/u</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <InputNumber
                          size="small"
                          min={0}
                          value={item.cantidad}
                          onChange={(v) => cambiarCantidad(item.producto.id, v || 0)}
                          className="w-16"
                        />
                        <Button
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => eliminarDelCarrito(item.producto.id)}
                        />
                      </div>
                      <p className="font-bold ml-2 w-24 text-right">
                        Gs. {item.subtotal.toLocaleString('es-PY')}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="border-t pt-4">
                  <div className="flex justify-between text-xl font-bold mb-4">
                    <span>TOTAL</span>
                    <span className="text-green-700">Gs. {total.toLocaleString('es-PY')}</span>
                  </div>
                  <Button
                    type="primary"
                    size="large"
                    block
                    loading={cobrando}
                    onClick={cobrar}
                  >
                    Cobrar Gs. {total.toLocaleString('es-PY')}
                  </Button>
                </div>
              </>
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}