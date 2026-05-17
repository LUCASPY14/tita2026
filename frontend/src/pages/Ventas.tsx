import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Input from '../components/ui/Input'
import Button from '../components/ui/Button'
import Select from '../components/ui/Select'
import Combobox from '../components/ui/Combobox'
import Table, { type Column } from '../components/ui/Table'

interface Producto {
  id: number
  codigo_barra: string
  descripcion: string
  precio_actual: string
  categoria_nombre: string
}

interface Cliente {
  id: number
  nombres: string
  apellidos: string
  ruc_ci: string
}

interface MedioPago {
  id: number
  descripcion: string
}

interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string
  hijo_nombre: string
  saldo_actual: string
  estado: string
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
  const [categorias, setCategorias] = useState<string[]>([])
  const [categoria, setCategoria] = useState('')
  const [carrito, setCarrito] = useState<ItemCarrito[]>([])
  const [cobrando, setCobrando] = useState(false)

  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteId, setClienteId] = useState<number | undefined>()
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([])
  const [medioPagoId, setMedioPagoId] = useState<number | undefined>()
  const [tipoVenta, setTipoVenta] = useState('CONTADO')
  const [tarjetaSearch, setTarjetaSearch] = useState('')
  const [tarjeta, setTarjeta] = useState<Tarjeta | null>(null)
  const [tarjetaBuscando, setTarjetaBuscando] = useState(false)

  useEffect(() => {
    Promise.all([
      api.get('/productos/categorias/'),
      api.get('/core/medios-pago/'),
    ]).then(([catRes, medRes]) => {
      setCategorias((catRes.data.results || []).map((c: { nombre: string }) => c.nombre))
      const medios: MedioPago[] = medRes.data.results || []
      setMediosPago(medios)
      if (medios.length > 0) setMedioPagoId(medios[0].id)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    const params: Record<string, string> = {}
    if (search) params.search = search
    if (categoria) params.categoria = categoria
    api.get('/productos/productos/', { params })
      .then(({ data }) => setProductos(data.results || []))
      .catch(() => toast.error('Error al cargar productos'))
      .finally(() => setLoading(false))
  }, [search, categoria])

  const buscarClientes = (q: string) => {
    if (q.length < 2) return
    api.get('/clientes/clientes/', { params: { search: q } })
      .then(({ data }) => setClientes(data.results || []))
      .catch(() => {})
  }

  const buscarTarjeta = async () => {
    if (!tarjetaSearch.trim()) { toast.error('Ingrese un codigo de tarjeta'); return }
    setTarjetaBuscando(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: tarjetaSearch } })
      const encontrada = (data.results || []).find(
        (t: Tarjeta) => t.nro_tarjeta === tarjetaSearch || t.codigo_barras === tarjetaSearch
      )
      if (encontrada) {
        if (encontrada.estado !== 'ACTIVA') {
          toast.error('Tarjeta no activa: ' + encontrada.estado)
          setTarjeta(null)
        } else {
          setTarjeta(encontrada)
          toast.success(`${encontrada.hijo_nombre} — Gs. ${parseInt(encontrada.saldo_actual).toLocaleString('es-PY')}`)
        }
      } else {
        toast.error('Tarjeta no encontrada')
        setTarjeta(null)
      }
    } catch {
      toast.error('Error al buscar tarjeta')
    } finally {
      setTarjetaBuscando(false)
    }
  }

  const agregarAlCarrito = (producto: Producto) => {
    setCarrito((prev) => {
      const existente = prev.find((i) => i.producto.id === producto.id)
      if (existente) {
        return prev.map((i) =>
          i.producto.id === producto.id
            ? { ...i, cantidad: i.cantidad + 1, subtotal: (i.cantidad + 1) * parseInt(producto.precio_actual) }
            : i
        )
      }
      return [...prev, { producto, cantidad: 1, subtotal: parseInt(producto.precio_actual) }]
    })
  }

  const cambiarCantidad = (productoId: number, cantidad: number) => {
    if (cantidad <= 0) { setCarrito((p) => p.filter((i) => i.producto.id !== productoId)); return }
    setCarrito((prev) =>
      prev.map((i) =>
        i.producto.id === productoId
          ? { ...i, cantidad, subtotal: cantidad * parseInt(i.producto.precio_actual) }
          : i
      )
    )
  }

  const total = carrito.reduce((s, i) => s + i.subtotal, 0)

  const cobrar = async () => {
    if (carrito.length === 0) { toast.error('Agregue productos al carrito'); return }
    if (!clienteId) { toast.error('Seleccione un cliente'); return }
    if (tipoVenta === 'CONTADO' && !medioPagoId) { toast.error('Seleccione un medio de pago'); return }
    setCobrando(true)
    try {
      const payload: Record<string, unknown> = {
        cliente: clienteId,
        tipo: tipoVenta,
        items: carrito.map((i) => ({
          producto: i.producto.id,
          cantidad: i.cantidad,
          precio_unitario: parseInt(i.producto.precio_actual),
          iva_10: 0, iva_5: 0, monto_exenta: 0,
        })),
        medio_pago: tipoVenta === 'CONTADO' ? medioPagoId : null,
      }
      if (tarjeta) payload.tarjeta = tarjeta.nro_tarjeta
      await api.post('/ventas/ventas/', payload)
      toast.success('Venta registrada — Gs. ' + total.toLocaleString('es-PY'))
      setCarrito([])
      setTarjeta(null)
      setTarjetaSearch('')
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      toast.error(err?.response?.data?.error || 'Error al registrar la venta')
    } finally {
      setCobrando(false)
    }
  }

  const columns: Column<Producto>[] = [
    { title: 'Codigo', dataIndex: 'codigo_barra', key: 'codigo', width: 120 },
    { title: 'Producto', dataIndex: 'descripcion', key: 'descripcion' },
    {
      title: 'Precio',
      dataIndex: 'precio_actual',
      key: 'precio',
      width: 130,
      render: (v) => <span className="font-bold text-green-700">Gs. {parseInt(v as string).toLocaleString('es-PY')}</span>,
    },
    {
      title: '',
      key: 'accion',
      width: 90,
      render: (_, r) => <Button variant="primary" size="sm" onClick={() => agregarAlCarrito(r)}>+ Agregar</Button>,
    },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Ventas</h2>
      <div className="flex gap-4">
        {/* Catalogo */}
        <div className="flex-1 min-w-0">
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="🔍 Buscar producto..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="flex-1"
            />
            <select
              className="border border-gray-300 rounded-md px-3 py-2 text-sm bg-white"
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
            >
              <option value="">Todas las categorias</option>
              {categorias.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <Table columns={columns} dataSource={productos} rowKey="id" loading={loading} pageSize={8} />
        </div>

        {/* Carrito */}
        <div className="w-96 flex-shrink-0">
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm sticky top-4">
            <div className="px-4 py-3 border-b font-medium">🛒 Carrito ({carrito.length})</div>
            <div className="p-4 space-y-3">
              <div>
                <p className="text-xs font-bold text-gray-500 mb-1">CLIENTE</p>
                <Combobox
                  options={clientes.map((c) => ({ value: c.id, label: `${c.nombres} ${c.apellidos} (${c.ruc_ci})` }))}
                  value={clienteId}
                  onChange={(v) => setClienteId(v as number)}
                  onSearch={buscarClientes}
                  placeholder="Buscar cliente..."
                />
              </div>

              <div>
                <p className="text-xs font-bold text-gray-500 mb-1">TIPO</p>
                <div className="flex gap-2">
                  {['CONTADO', 'CREDITO'].map((tipo) => (
                    <button
                      key={tipo}
                      onClick={() => setTipoVenta(tipo)}
                      className={`flex-1 py-1.5 text-sm rounded border font-medium cursor-pointer ${
                        tipoVenta === tipo ? 'bg-green-600 text-white border-green-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {tipo === 'CONTADO' ? 'Contado' : 'Credito'}
                    </button>
                  ))}
                </div>
              </div>

              {tipoVenta === 'CONTADO' && (
                <div>
                  <p className="text-xs font-bold text-gray-500 mb-1">MEDIO DE PAGO</p>
                  <Select
                    options={mediosPago.map((m) => ({ value: m.id, label: m.descripcion }))}
                    value={medioPagoId}
                    onChange={(e) => setMedioPagoId(Number(e.target.value))}
                  />
                </div>
              )}

              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-xs font-bold text-gray-500 mb-1">💳 TARJETA (opcional)</p>
                <div className="flex gap-1">
                  <Input
                    placeholder="Nro. Tarjeta"
                    value={tarjetaSearch}
                    onChange={(e) => setTarjetaSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && buscarTarjeta()}
                  />
                  <Button size="sm" loading={tarjetaBuscando} onClick={buscarTarjeta}>Buscar</Button>
                </div>
                {tarjeta && (
                  <div className="mt-2 flex items-center gap-2 text-xs">
                    <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded font-medium">{tarjeta.hijo_nombre}</span>
                    <span className="text-gray-500">Gs. {parseInt(tarjeta.saldo_actual).toLocaleString('es-PY')}</span>
                    <button onClick={() => { setTarjeta(null); setTarjetaSearch('') }} className="text-red-500 ml-auto cursor-pointer">✕</button>
                  </div>
                )}
              </div>

              <hr />

              {carrito.length === 0 ? (
                <p className="text-gray-400 text-center py-4 text-sm">Carrito vacio</p>
              ) : (
                <>
                  <div className="max-h-56 overflow-y-auto space-y-2">
                    {carrito.map((item) => (
                      <div key={item.producto.id} className="flex items-center gap-2 pb-2 border-b">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{item.producto.descripcion}</p>
                          <p className="text-xs text-gray-500">Gs. {parseInt(item.producto.precio_actual).toLocaleString('es-PY')} c/u</p>
                        </div>
                        <input
                          type="number"
                          min={0}
                          value={item.cantidad}
                          onChange={(e) => cambiarCantidad(item.producto.id, Number(e.target.value))}
                          className="w-14 border border-gray-300 rounded text-sm text-center py-1 px-1"
                        />
                        <span className="text-sm font-bold w-20 text-right">Gs. {item.subtotal.toLocaleString('es-PY')}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t pt-3">
                    <span>TOTAL</span>
                    <span className="text-green-700">Gs. {total.toLocaleString('es-PY')}</span>
                  </div>
                  <Button variant="primary" block size="lg" loading={cobrando} onClick={cobrar}>
                    Cobrar Gs. {total.toLocaleString('es-PY')}
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
