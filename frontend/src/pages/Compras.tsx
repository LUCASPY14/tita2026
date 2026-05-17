import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Combobox from '../components/ui/Combobox'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'

interface Proveedor { id: number; razon_social: string }
interface Producto { id: number; descripcion: string; precio_actual: string }
interface ItemCompra { producto: Producto | null; cantidad: number; costo_unitario: number; subtotal: number }
interface Compra {
  id: number
  proveedor_nombre: string
  fecha: string
  monto_total: string
  estado_pago: string
  tipo_pago: string
}

const tipoBadge: Record<string, BadgeColor> = { CONTADO: 'green', CREDITO: 'orange' }
const estadoBadge: Record<string, BadgeColor> = { PAGADO: 'green', PENDIENTE: 'orange', PARCIAL: 'blue' }

export default function Compras() {
  const [compras, setCompras] = useState<Compra[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [proveedores, setProveedores] = useState<Proveedor[]>([])
  const [productos, setProductos] = useState<Producto[]>([])
  const [proveedorId, setProveedorId] = useState<number | undefined>()
  const [tipoPago, setTipoPago] = useState('CONTADO')
  const [nroFactura, setNroFactura] = useState('')
  const [items, setItems] = useState<ItemCompra[]>([{ producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0 }])
  const [registrando, setRegistrando] = useState(false)

  const cargarCompras = () => {
    setLoading(true)
    api.get('/compras/compras/')
      .then(({ data }) => setCompras(data.results || []))
      .catch(() => toast.error('Error al cargar compras'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    cargarCompras()
    Promise.all([api.get('/compras/proveedores/'), api.get('/productos/productos/')])
      .then(([prov, prod]) => {
        setProveedores(prov.data.results || [])
        setProductos(prod.data.results || [])
      })
      .catch(() => {})
  }, [])

  const agregarItem = () => setItems([...items, { producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0 }])
  const quitarItem = (i: number) => { if (items.length > 1) setItems(items.filter((_, idx) => idx !== i)) }

  const actualizarItem = (index: number, field: string, value: unknown) => {
    setItems(items.map((item, i) => {
      if (i !== index) return item
      const updated = { ...item, [field]: value }
      if (field === 'producto') {
        updated.costo_unitario = parseInt((value as Producto).precio_actual) || 0
      }
      if (field === 'cantidad' || field === 'costo_unitario' || field === 'producto') {
        updated.subtotal = (field === 'cantidad' ? (value as number) : updated.cantidad) *
          (field === 'costo_unitario' ? (value as number) : updated.costo_unitario)
      }
      return updated
    }))
  }

  const total = items.reduce((s, i) => s + i.subtotal, 0)

  const registrarCompra = async () => {
    if (!proveedorId || items.some((i) => !i.producto)) { toast.error('Complete todos los campos'); return }
    setRegistrando(true)
    try {
      await api.post('/compras/compras/', {
        proveedor: proveedorId,
        tipo_pago: tipoPago,
        nro_factura_proveedor: nroFactura,
        items: items.map((i) => ({ producto: i.producto?.id, cantidad: i.cantidad, costo_unitario: i.costo_unitario })),
      })
      toast.success('Compra registrada — Gs. ' + total.toLocaleString('es-PY'))
      setModalOpen(false)
      setItems([{ producto: null, cantidad: 1, costo_unitario: 0, subtotal: 0 }])
      setNroFactura('')
      cargarCompras()
    } catch {
      toast.error('Error al registrar la compra')
    } finally {
      setRegistrando(false)
    }
  }

  const columns: Column<Compra>[] = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Proveedor', dataIndex: 'proveedor_nombre', key: 'proveedor' },
    { title: 'Fecha', dataIndex: 'fecha', key: 'fecha', render: (v) => new Date(v as string).toLocaleDateString('es-PY') },
    { title: 'Monto', dataIndex: 'monto_total', key: 'monto', render: (v) => 'Gs. ' + parseInt(v as string).toLocaleString('es-PY') },
    { title: 'Tipo', dataIndex: 'tipo_pago', key: 'tipo', render: (v) => <Badge color={tipoBadge[v as string] || 'default'}>{v as string}</Badge> },
    { title: 'Estado', dataIndex: 'estado_pago', key: 'estado', render: (v) => <Badge color={estadoBadge[v as string] || 'default'}>{v as string}</Badge> },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Compras</h2>
        <Button variant="primary" size="lg" onClick={() => setModalOpen(true)}>+ Nueva Compra</Button>
      </div>
      <Table columns={columns} dataSource={compras} rowKey="id" loading={loading} pageSize={10} />

      <Modal
        open={modalOpen}
        title="Nueva Compra"
        onOk={registrarCompra}
        onCancel={() => setModalOpen(false)}
        confirmLoading={registrando}
        okText="Registrar"
        width={680}
      >
        <div className="space-y-3 mb-4">
          <Combobox
            options={proveedores.map((p) => ({ value: p.id, label: p.razon_social }))}
            value={proveedorId}
            onChange={(v) => setProveedorId(v as number)}
            filterLocal
            placeholder="Proveedor..."
          />
          <div className="flex gap-2">
            <Select
              className="w-40"
              value={tipoPago}
              onChange={(e) => setTipoPago(e.target.value)}
              options={[{ value: 'CONTADO', label: 'Contado' }, { value: 'CREDITO', label: 'Credito' }]}
            />
            <Input
              className="flex-1"
              placeholder="Nro. Factura Proveedor"
              value={nroFactura}
              onChange={(e) => setNroFactura(e.target.value)}
            />
          </div>
        </div>

        <p className="font-semibold mb-2 text-sm text-gray-700">Productos</p>
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {items.map((item, index) => (
            <div key={index} className="flex gap-2 items-center">
              <div className="flex-1">
                <Combobox
                  options={productos.map((p) => ({ value: p.id, label: p.descripcion, data: p }))}
                  value={item.producto?.id}
                  onChange={(_, opt) => actualizarItem(index, 'producto', opt.data as Producto)}
                  filterLocal
                  placeholder="Producto..."
                />
              </div>
              <input
                type="number"
                min={1}
                value={item.cantidad}
                onChange={(e) => actualizarItem(index, 'cantidad', Number(e.target.value) || 1)}
                className="w-16 border border-gray-300 rounded px-2 py-2 text-sm text-center"
              />
              <input
                type="number"
                min={0}
                value={item.costo_unitario}
                onChange={(e) => actualizarItem(index, 'costo_unitario', Number(e.target.value) || 0)}
                className="w-28 border border-gray-300 rounded px-2 py-2 text-sm text-right"
                placeholder="Costo"
              />
              <span className="w-24 text-sm font-bold text-right">Gs. {item.subtotal.toLocaleString('es-PY')}</span>
              <button onClick={() => quitarItem(index)} className="text-red-500 hover:text-red-700 cursor-pointer px-1">✕</button>
            </div>
          ))}
        </div>
        <Button variant="ghost" size="sm" onClick={agregarItem} className="mt-2">+ Agregar producto</Button>

        <div className="border-t mt-4 pt-3 flex justify-between text-lg font-bold">
          <span>TOTAL</span>
          <span className="text-green-700">Gs. {total.toLocaleString('es-PY')}</span>
        </div>
      </Modal>
    </div>
  )
}
