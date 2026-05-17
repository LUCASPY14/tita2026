import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../services/api'
import Button from '../components/ui/Button'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Input from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'
import Card from '../components/ui/Card'

interface CierreCaja {
  id: number
  caja_nombre: string
  empleado_nombre: string
  fecha_apertura: string
  fecha_cierre: string | null
  monto_inicial: string
  monto_contado_fisico: string | null
  diferencia_efectivo: string | null
  estado: string
}

interface Caja {
  id: number
  nombre: string
}

const estadoColor: Record<string, BadgeColor> = {
  ABIERTO: 'green',
  CERRADO: 'blue',
  CONCILIADO: 'purple',
}

export default function CajaPage() {
  const [cierres, setCierres] = useState<CierreCaja[]>([])
  const [cajas, setCajas] = useState<Caja[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [montoInicial, setMontoInicial] = useState('')
  const [cajaSeleccionada, setCajaSeleccionada] = useState<number>(0)
  const [abriendo, setAbriendo] = useState(false)

  const cargarCierres = () => {
    setLoading(true)
    api.get('/contabilidad/cierres-caja/')
      .then(({ data }) => setCierres(data.results || []))
      .catch(() => toast.error('Error al cargar cierres'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    api.get('/contabilidad/cajas/')
      .then(({ data }) => {
        const lista: Caja[] = data.results || []
        setCajas(lista)
        if (lista.length > 0) setCajaSeleccionada(lista[0].id)
      })
      .catch(() => {})
    cargarCierres()
  }, [])

  const abrirCaja = async () => {
    setAbriendo(true)
    try {
      await api.post('/contabilidad/cierres-caja/', {
        caja: cajaSeleccionada,
        monto_inicial: parseInt(montoInicial) || 0,
      })
      toast.success('Caja abierta')
      setModalOpen(false)
      setMontoInicial('')
      cargarCierres()
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } }
      toast.error(err?.response?.data?.error || 'Error al abrir caja')
    } finally {
      setAbriendo(false)
    }
  }

  const cerrarCaja = async (cierre: CierreCaja) => {
    const monto = prompt('Ingrese el monto contado fisicamente (Gs.):')
    if (!monto) return
    try {
      await api.patch(`/contabilidad/cierres-caja/${cierre.id}/`, {
        estado: 'CERRADO',
        monto_contado_fisico: parseInt(monto),
      })
      toast.success('Caja cerrada')
      cargarCierres()
    } catch {
      toast.error('Error al cerrar caja')
    }
  }

  const columns: Column<CierreCaja>[] = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Caja', dataIndex: 'caja_nombre', key: 'caja' },
    { title: 'Empleado', dataIndex: 'empleado_nombre', key: 'empleado' },
    {
      title: 'Apertura',
      dataIndex: 'fecha_apertura',
      key: 'apertura',
      render: (v) => new Date(v as string).toLocaleString('es-PY'),
    },
    {
      title: 'Cierre',
      dataIndex: 'fecha_cierre',
      key: 'cierre',
      render: (v) => v ? new Date(v as string).toLocaleString('es-PY') : '-',
    },
    {
      title: 'Monto Inicial',
      dataIndex: 'monto_inicial',
      key: 'inicial',
      render: (v) => 'Gs. ' + parseInt(v as string).toLocaleString('es-PY'),
    },
    {
      title: 'Diferencia',
      dataIndex: 'diferencia_efectivo',
      key: 'dif',
      render: (v) => {
        if (v === null || v === undefined) return '-'
        const n = parseInt(v as string)
        return <span className={n === 0 ? 'text-green-700 font-bold' : 'text-red-600 font-bold'}>Gs. {n.toLocaleString('es-PY')}</span>
      },
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
      width: 90,
      render: (_, r) => r.estado === 'ABIERTO'
        ? <Button size="sm" onClick={() => cerrarCaja(r)}>🔒 Cerrar</Button>
        : null,
    },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Caja</h2>
        <Button variant="primary" size="lg" onClick={() => setModalOpen(true)}>+ Abrir Caja</Button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="bg-green-50">
          <p className="text-sm text-gray-600">Cajas abiertas</p>
          <p className="text-2xl font-bold text-green-800">{cierres.filter((c) => c.estado === 'ABIERTO').length}</p>
        </Card>
        <Card className="bg-blue-50">
          <p className="text-sm text-gray-600">Total cierres</p>
          <p className="text-2xl font-bold text-blue-800">{cierres.length}</p>
        </Card>
        <Card className="bg-purple-50">
          <p className="text-sm text-gray-600">Conciliados</p>
          <p className="text-2xl font-bold text-purple-800">{cierres.filter((c) => c.estado === 'CONCILIADO').length}</p>
        </Card>
      </div>

      <Table columns={columns} dataSource={cierres} rowKey="id" loading={loading} pageSize={10} />

      <Modal
        open={modalOpen}
        title="Abrir Caja"
        onOk={abrirCaja}
        onCancel={() => setModalOpen(false)}
        confirmLoading={abriendo}
        okText="Abrir"
      >
        {cajas.length > 0 && (
          <p className="mb-3 font-medium text-gray-800">
            Caja: {cajas.find((c) => c.id === cajaSeleccionada)?.nombre}
          </p>
        )}
        <Input
          type="number"
          placeholder="Monto inicial (Gs.)"
          value={montoInicial}
          onChange={(e) => setMontoInicial(e.target.value)}
          min={0}
          step={10000}
        />
      </Modal>
    </div>
  )
}
