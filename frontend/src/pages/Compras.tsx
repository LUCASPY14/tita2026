import { useEffect, useState } from 'react'
import { Table, Input, Button, Modal, InputNumber, Select, Tag, message, Space } from 'antd'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'
import api from '../services/api'

interface Proveedor {
  id: number
  ruc: string
  razon_social: string
  telefono: string
  activo: boolean
}

interface Producto {
  id: number
  descripcion: string
  precio_actual: string
}

interface ItemCompra {
  producto: Producto | null
  cantidad: number
  costo_unitario: number
  subtotal: number
}

interface Compra {
  id: number
  proveedor_nombre: string
  fecha: string
  monto_total: string
  estado_pago: string
  tipo_pago: string
}

export default function Compras() {
  const [compras, setCompras] = useState<Compra[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [productos, setProductos] = useState<Producto[]>([])
  const [proveedorId, setProveedorId] = useState<number>(0)
  const [tipoPago, setTipoPago] = useState<string>('CONTADO')
  const [nroFactura, setNroFactura] = useState('')
  const [items, setItems] = useState<ItemCompra[]>([{ producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0 }])
  const [registrando, setRegistrando] = useState(false)

  const cargarCompras = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/compras/compras/')
      setCompras(data.results || [])
    } catch {
      message.error('Error al cargar compras')
    } finally {
      setLoading(false)
    }
  }

  const cargarCatalogos = async () => {
    try {
      const [provRes, prodRes] = await Promise.all([
        api.get('/compras/proveedores/'),
        api.get('/productos/productos/'),
      ])
      setProveedores(provRes.data.results || [])
      setProductos(prodRes.data.results || [])
    } catch {}
  }

  useEffect(() => {
    cargarCompras()
    cargarCatalogos()
  }, [])

  const agregarItem = () => {
    setItems([...items, { producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0 }])
  }

  const quitarItem = (index: number) => {
    if (items.length === 1) return
    setItems(items.filter((_, i) => i !== index))
  }

  const actualizarItem = (index: number, field: string, value: unknown) => {
    setItems(
      items.map((item, i) => {
        if (i !== index) return item
        const updated = { ...item, [field]: value }
        if (field === 'cantidad' || field === 'costo_unitario') {
          updated.subtotal = updated.cantidad * updated.costo_unitario
        }
        if (field === 'producto') {
          updated.costo_unitario = parseInt((value as Producto).precio_actual) || 0
          updated.subtotal = updated.cantidad * updated.costo_unitario
        }
        return updated
      })
    )
  }

  const total = items.reduce((sum, item) => sum + item.subtotal, 0)

  const registrarCompra = async () => {
    if (!proveedorId || items.some((i) => !i.producto)) {
      message.warning('Complete todos los campos')
      return
    }
    setRegistrando(true)
    try {
      const payload = {
        proveedor: proveedorId,
        tipo_pago: tipoPago,
        nro_factura_proveedor: nroFactura,
        items: items.map((i) => ({
          producto: i.producto?.id,
          cantidad: i.cantidad,
          costo_unitario: i.costo_unitario,
        })),
      }
      await api.post('/compras/compras/', payload)
      message.success('Compra registrada - Gs. ' + total.toLocaleString('es-PY'))
      setModalOpen(false)
      setItems([{ producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0 }])
      setNroFactura('')
      cargarCompras()
    } catch {
      message.error('Error al registrar la compra')
    } finally {
      setRegistrando(false)
    }
  }

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Proveedor',
      dataIndex: 'proveedor_nombre',
      key: 'proveedor',
    },
    {
      title: 'Fecha',
      dataIndex: 'fecha',
      key: 'fecha',
      render: (v: string) => new Date(v).toLocaleString('es-PY'),
    },
    {
      title: 'Monto',
      dataIndex: 'monto_total',
      key: 'monto',
      render: (v: string) => 'Gs. ' + parseInt(v).toLocaleString('es-PY'),
    },
    {
      title: 'Tipo',
      dataIndex: 'tipo_pago',
      key: 'tipo',
      render: (v: string) => <Tag color={v === 'CONTADO' ? 'green' : 'orange'}>{v}</Tag>,
    },
    {
      title: 'Estado',
      dataIndex: 'estado_pago',
      key: 'estado',
      render: (v: string) => {
        const colors: Record<string, string> = {
          PAGADO: 'green',
          PENDIENTE: 'orange',
          PARCIAL: 'blue',
        }
        return <Tag color={colors[v] || 'default'}>{v}</Tag>
      },
    },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Compras</h2>
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={() => setModalOpen(true)}>
          Nueva Compra
        </Button>
      </div>

      <Table
        dataSource={compras}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="Nueva Compra"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={registrarCompra}
        confirmLoading={registrando}
        okText="Registrar"
        cancelText="Cancelar"
        width={700}
      >
        <div className="mb-4">
          <Select
            className="w-full mb-2"
            placeholder="Proveedor"
            value={proveedorId || undefined}
            onChange={(v) => setProveedorId(v)}
            size="large"
            options={proveedores.map((p) => ({ value: p.id, label: p.razon_social }))}
          />
          <div className="flex gap-2">
            <Select
              className="w-40"
              value={tipoPago}
              onChange={(v) => setTipoPago(v)}
              size="large"
              options={[
                { value: 'CONTADO', label: 'Contado' },
                { value: 'CREDITO', label: 'Credito' },
              ]}
            />
            <Input
              className="flex-1"
              placeholder="Nro. Factura Proveedor"
              value={nroFactura}
              onChange={(e) => setNroFactura(e.target.value)}
              size="large"
            />
          </div>
        </div>

        <p className="font-bold mb-2">Productos</p>
        {items.map((item, index) => (
          <div key={index} className="flex gap-2 mb-2 items-center">
            <Select
              className="flex-1"
              placeholder="Producto"
              value={item.producto?.id || undefined}
              onChange={(_, option) => actualizarItem(index, 'producto', (option as { data: Producto }).data)}
              size="large"
              showSearch
              filterOption={(input, option) =>
                (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
              }
              options={productos.map((p) => ({ value: p.id, label: p.descripcion, data: p }))}
            />
            <InputNumber
              min={1}
              value={item.cantidad}
              onChange={(v) => actualizarItem(index, 'cantidad', v || 1)}
              className="w-20"
              size="large"
            />
            <InputNumber
              min={0}
              value={item.costo_unitario}
              onChange={(v) => actualizarItem(index, 'costo_unitario', v || 0)}
              className="w-28"
              size="large"
              formatter={(v) => 'Gs. ' + (v || '').replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
              parser={(v) => parseInt((v || '').replace(/[^\d]/g, '')) || 0}
            />
            <span className="w-24 text-right font-bold">
              Gs. {item.subtotal.toLocaleString('es-PY')}
            </span>
            <Button danger onClick={() => quitarItem(index)}>-</Button>
          </div>
        ))}
        <Button onClick={agregarItem} className="mb-4">+ Agregar producto</Button>

        <div className="border-t pt-4 flex justify-between text-xl font-bold">
          <span>TOTAL</span>
          <span className="text-green-700">Gs. {total.toLocaleString('es-PY')}</span>
        </div>
      </Modal>
    </div>
  )
}