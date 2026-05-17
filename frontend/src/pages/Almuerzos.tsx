import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Select from '../components/ui/Select'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'
import Card from '../components/ui/Card'

interface RegistroConsumo {
  id: number
  hijo_nombre: string
  fecha_consumo: string
  tipo_almuerzo_nombre: string
  costo_almuerzo: string
  estado: string
  ya_cobrado: boolean
}

interface Hijo {
  id: number
  nombre_completo: string
  grado: string
  cliente_responsable: number
}

interface TipoAlmuerzo {
  id: number
  nombre: string
  precio_unitario: string
}

interface Tarjeta {
  nro_tarjeta: string
  hijo_nombre: string
  saldo_actual: string
  estado: string
}

interface CuentaMensual {
  id: number
  hijo_nombre: string
  anio: number
  mes: number
  cantidad_almuerzos: number
  monto_total: string
  monto_pagado: string
  estado: string
}

const estadoRegistroBadge: Record<string, BadgeColor> = {
  REGISTRADO: 'green',
  RECHAZADO: 'red',
  ANULADO: 'default',
}

const estadoCuentaBadge: Record<string, BadgeColor> = {
  PENDIENTE: 'orange',
  PAGADO: 'green',
  PARCIAL: 'blue',
  ANULADO: 'default',
}

const meses = [
  '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

function formatDate(iso: string) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export default function Almuerzos() {
  const [registros, setRegistros] = useState<RegistroConsumo[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [tiposAlmuerzo, setTiposAlmuerzo] = useState<TipoAlmuerzo[]>([])
  const [hijoId, setHijoId] = useState<number>(0)
  const [tipoAlmuerzoId, setTipoAlmuerzoId] = useState<number>(0)
  const [fecha, setFecha] = useState(todayISO())
  const [tarjetaSearch, setTarjetaSearch] = useState('')
  const [tarjeta, setTarjeta] = useState<Tarjeta | null>(null)
  const [tarjetaBuscando, setTarjetaBuscando] = useState(false)
  const [registrando, setRegistrando] = useState(false)
  const [cuentas, setCuentas] = useState<CuentaMensual[]>([])
  const [tabActivo, setTabActivo] = useState<'registros' | 'cuentas'>('registros')

  const cargarRegistros = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = { ordering: '-fecha_consumo' }
      if (search) params.search = search
      const { data } = await api.get('/almuerzos/registros-consumo/', { params })
      setRegistros(data.results || [])
    } catch {
      toast.error('Error al cargar registros')
    } finally {
      setLoading(false)
    }
  }

  const cargarCuentas = async () => {
    try {
      const { data } = await api.get('/almuerzos/cuentas-mensuales/', {
        params: { ordering: '-anio,-mes' },
      })
      setCuentas(data.results || [])
    } catch {}
  }

  const cargarCatalogos = async () => {
    try {
      const [hijosRes, tiposRes] = await Promise.all([
        api.get('/clientes/hijos/'),
        api.get('/almuerzos/tipos-almuerzo/'),
      ])
      setHijos(hijosRes.data.results || [])
      setTiposAlmuerzo(tiposRes.data.results || [])
    } catch {}
  }

  useEffect(() => {
    cargarRegistros()
    cargarCatalogos()
    cargarCuentas()
  }, [search])

  const buscarTarjeta = async () => {
    if (!tarjetaSearch.trim()) { toast.error('Ingrese un numero de tarjeta'); return }
    setTarjetaBuscando(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: tarjetaSearch } })
      const encontrada = (data.results || []).find(
        (t: Tarjeta) => t.nro_tarjeta === tarjetaSearch
      )
      if (encontrada) {
        if (encontrada.estado !== 'ACTIVA') {
          toast.error('Tarjeta no activa: ' + encontrada.estado)
          setTarjeta(null)
        } else {
          setTarjeta(encontrada)
          const hijo = hijos.find((h) => h.nombre_completo === encontrada.hijo_nombre)
          if (hijo) setHijoId(hijo.id)
          toast.success(encontrada.hijo_nombre)
        }
      } else {
        toast.error('Tarjeta no encontrada')
      }
    } catch {
      toast.error('Error al buscar tarjeta')
    } finally {
      setTarjetaBuscando(false)
    }
  }

  const registrarConsumo = async () => {
    if (!hijoId) { toast.error('Seleccione un estudiante'); return }
    if (!tarjeta) { toast.error('Escanee la tarjeta del estudiante'); return }
    setRegistrando(true)
    try {
      const payload: Record<string, unknown> = {
        hijo: hijoId,
        fecha_consumo: fecha,
        nro_tarjeta: tarjeta.nro_tarjeta,
      }
      if (tipoAlmuerzoId) payload.tipo_almuerzo = tipoAlmuerzoId
      await api.post('/almuerzos/registros-consumo/', payload)
      toast.success('Consumo registrado')
      setModalOpen(false)
      setTarjeta(null)
      setTarjetaSearch('')
      setHijoId(0)
      setTipoAlmuerzoId(0)
      setFecha(todayISO())
      cargarRegistros()
      cargarCuentas()
    } catch (e: unknown) {
      const error = e as { response?: { data?: { error?: string } } }
      toast.error(error?.response?.data?.error || 'Error al registrar')
    } finally {
      setRegistrando(false)
    }
  }

  const hoy = todayISO()
  const mesActual = new Date().getMonth() + 1
  const anioActual = new Date().getFullYear()

  const columnsRegistros: Column<RegistroConsumo>[] = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Estudiante', dataIndex: 'hijo_nombre', key: 'hijo' },
    {
      title: 'Fecha',
      dataIndex: 'fecha_consumo',
      key: 'fecha',
      width: 110,
      render: (v) => formatDate(v as string),
    },
    { title: 'Tipo', dataIndex: 'tipo_almuerzo_nombre', key: 'tipo' },
    {
      title: 'Costo',
      dataIndex: 'costo_almuerzo',
      key: 'costo',
      width: 120,
      render: (v) => v ? 'Gs. ' + parseInt(v as string).toLocaleString('es-PY') : '-',
    },
    {
      title: 'Cobrado',
      dataIndex: 'ya_cobrado',
      key: 'cobra',
      width: 80,
      render: (v) => <Badge color={v ? 'blue' : 'default'}>{v ? 'Si' : 'No'}</Badge>,
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      width: 110,
      render: (v) => <Badge color={estadoRegistroBadge[v as string] || 'default'}>{v as string}</Badge>,
    },
  ]

  const columnsCuentas: Column<CuentaMensual>[] = [
    { title: 'Estudiante', dataIndex: 'hijo_nombre', key: 'hijo' },
    {
      title: 'Periodo',
      key: 'periodo',
      render: (_, r) => `${meses[r.mes]} ${r.anio}`,
    },
    { title: 'Cantidad', dataIndex: 'cantidad_almuerzos', key: 'cantidad', width: 90 },
    {
      title: 'Total',
      dataIndex: 'monto_total',
      key: 'total',
      render: (v) => 'Gs. ' + parseInt(v as string).toLocaleString('es-PY'),
    },
    {
      title: 'Pagado',
      dataIndex: 'monto_pagado',
      key: 'pagado',
      render: (v) => 'Gs. ' + parseInt(v as string).toLocaleString('es-PY'),
    },
    {
      title: 'Saldo',
      key: 'saldo',
      render: (_, r) => {
        const saldo = parseInt(r.monto_total) - parseInt(r.monto_pagado)
        return (
          <span className={saldo > 0 ? 'text-red-600 font-bold' : 'text-green-700 font-bold'}>
            Gs. {saldo.toLocaleString('es-PY')}
          </span>
        )
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      width: 100,
      render: (v) => <Badge color={estadoCuentaBadge[v as string] || 'default'}>{v as string}</Badge>,
    },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Almuerzos</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setTabActivo('registros')}
            className={`px-4 py-2 rounded-md text-sm font-medium border cursor-pointer ${
              tabActivo === 'registros'
                ? 'bg-green-600 text-white border-green-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            Registros
          </button>
          <button
            onClick={() => setTabActivo('cuentas')}
            className={`px-4 py-2 rounded-md text-sm font-medium border cursor-pointer ${
              tabActivo === 'cuentas'
                ? 'bg-green-600 text-white border-green-600'
                : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
            }`}
          >
            Cuentas Mensuales
          </button>
          <Button variant="primary" size="lg" onClick={() => setModalOpen(true)}>
            + Registrar Consumo
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="bg-blue-50">
          <p className="text-sm text-gray-600">Consumos Hoy</p>
          <p className="text-2xl font-bold text-blue-800">
            {registros.filter((r) => r.fecha_consumo === hoy).length}
          </p>
        </Card>
        <Card className="bg-green-50">
          <p className="text-sm text-gray-600">Cuentas Pendientes</p>
          <p className="text-2xl font-bold text-orange-800">
            {cuentas.filter((c) => c.estado !== 'PAGADO').length}
          </p>
        </Card>
        <Card className="bg-purple-50">
          <p className="text-sm text-gray-600">Facturado este Mes</p>
          <p className="text-2xl font-bold text-purple-800">
            Gs.{' '}
            {cuentas
              .filter((c) => c.mes === mesActual && c.anio === anioActual)
              .reduce((sum, c) => sum + parseInt(c.monto_total), 0)
              .toLocaleString('es-PY')}
          </p>
        </Card>
      </div>

      {tabActivo === 'registros' ? (
        <div>
          <Input
            placeholder="Buscar por estudiante..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mb-4 max-w-md"
          />
          <Table columns={columnsRegistros} dataSource={registros} rowKey="id" loading={loading} pageSize={15} />
        </div>
      ) : (
        <Table columns={columnsCuentas} dataSource={cuentas} rowKey="id" pageSize={10} />
      )}

      <Modal
        open={modalOpen}
        title="Registrar Consumo de Almuerzo"
        onOk={registrarConsumo}
        onCancel={() => { setModalOpen(false); setTarjeta(null); setTarjetaSearch('') }}
        confirmLoading={registrando}
        okText="Registrar"
        width={480}
      >
        <div className="space-y-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-sm font-bold mb-2">Tarjeta del estudiante</p>
            <div className="flex gap-2">
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
                <span className="text-gray-500">Saldo: Gs. {parseInt(tarjeta.saldo_actual).toLocaleString('es-PY')}</span>
                <button
                  onClick={() => { setTarjeta(null); setTarjetaSearch('') }}
                  className="text-red-500 ml-auto cursor-pointer"
                >
                  ✕
                </button>
              </div>
            )}
          </div>

          <div>
            <p className="text-sm font-bold mb-1">Estudiante</p>
            <Select
              value={hijoId || ''}
              onChange={(e) => setHijoId(Number(e.target.value))}
              options={hijos.map((h) => ({ value: h.id, label: `${h.nombre_completo} (${h.grado})` }))}
              placeholder="Seleccionar estudiante"
            />
          </div>

          <div>
            <p className="text-sm font-bold mb-1">Tipo de Almuerzo (opcional)</p>
            <Select
              value={tipoAlmuerzoId || ''}
              onChange={(e) => setTipoAlmuerzoId(Number(e.target.value))}
              options={tiposAlmuerzo.map((t) => ({
                value: t.id,
                label: `${t.nombre} - Gs. ${parseInt(t.precio_unitario).toLocaleString('es-PY')}`,
              }))}
              placeholder="Tipo (opcional)"
            />
          </div>

          <div>
            <p className="text-sm font-bold mb-1">Fecha</p>
            <input
              type="date"
              value={fecha}
              onChange={(e) => setFecha(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}
