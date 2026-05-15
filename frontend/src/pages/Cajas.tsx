import { useEffect, useState } from 'react'
import { Table, Button, InputNumber, Modal, Tag, message, Card, Space } from 'antd'
import { PlusOutlined, LockOutlined } from '@ant-design/icons'
import api from '../services/api'

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

export default function Caja() {
  const [cierres, setCierres] = useState<CierreCaja[]>([])
  const [cajas, setCajas] = useState<Caja[]>([])
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [montoInicial, setMontoInicial] = useState<number>(0)
  const [cajaSeleccionada, setCajaSeleccionada] = useState<number>(0)
  const [abriendo, setAbriendo] = useState(false)

  const cargarCierres = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/contabilidad/cierres-caja/')
      setCierres(data.results || [])
    } catch {
      message.error('Error al cargar cierres')
    } finally {
      setLoading(false)
    }
  }

  const cargarCajas = async () => {
    try {
      const { data } = await api.get('/contabilidad/cajas/')
      setCajas(data.results || [])
      if (data.results?.length > 0) setCajaSeleccionada(data.results[0].id)
    } catch {}
  }

  useEffect(() => {
    cargarCajas()
    cargarCierres()
  }, [])

  const abrirCaja = async () => {
    setAbriendo(true)
    try {
      await api.post('/contabilidad/cierres-caja/', {
        caja: cajaSeleccionada,
        monto_inicial: montoInicial,
      })
      message.success('Caja abierta')
      setModalOpen(false)
      setMontoInicial(0)
      cargarCierres()
    } catch (e: unknown) {
      const error = e as { response?: { data?: { error?: string } } }
      message.error(error?.response?.data?.error || 'Error al abrir caja')
    } finally {
      setAbriendo(false)
    }
  }

  const cerrarCaja = async (cierre: CierreCaja) => {
    const monto = prompt('Ingrese el monto contado fisicamente (Gs.):')
    if (!monto) return
    try {
      await api.patch('/contabilidad/cierres-caja/' + cierre.id + '/', {
        estado: 'CERRADO',
        monto_contado_fisico: parseInt(monto),
      })
      message.success('Caja cerrada')
      cargarCierres()
    } catch {
      message.error('Error al cerrar caja')
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
      title: 'Caja',
      dataIndex: 'caja_nombre',
      key: 'caja',
    },
    {
      title: 'Empleado',
      dataIndex: 'empleado_nombre',
      key: 'empleado',
    },
    {
      title: 'Apertura',
      dataIndex: 'fecha_apertura',
      key: 'apertura',
      render: (v: string) => new Date(v).toLocaleString('es-PY'),
    },
    {
      title: 'Cierre',
      dataIndex: 'fecha_cierre',
      key: 'cierre',
      render: (v: string | null) => v ? new Date(v).toLocaleString('es-PY') : '-',
    },
    {
      title: 'Monto Inicial',
      dataIndex: 'monto_inicial',
      key: 'inicial',
      render: (v: string) => 'Gs. ' + parseInt(v).toLocaleString('es-PY'),
    },
    {
      title: 'Diferencia',
      dataIndex: 'diferencia_efectivo',
      key: 'diferencia',
      render: (v: string | null) => {
        if (v === null) return '-'
        const dif = parseInt(v)
        return (
          <span className={dif === 0 ? 'text-green-700 font-bold' : 'text-red-600 font-bold'}>
            Gs. {dif.toLocaleString('es-PY')}
          </span>
        )
      },
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        const colors: Record<string, string> = {
          ABIERTO: 'green',
          CERRADO: 'blue',
          CONCILIADO: 'purple',
        }
        return <Tag color={colors[estado] || 'default'}>{estado}</Tag>
      },
    },
    {
      title: 'Accion',
      key: 'accion',
      render: (_: unknown, record: CierreCaja) => (
        record.estado === 'ABIERTO' ? (
          <Button size="small" icon={<LockOutlined />} onClick={() => cerrarCaja(record)}>
            Cerrar
          </Button>
        ) : null
      ),
    },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">Caja</h2>
        <Button type="primary" icon={<PlusOutlined />} size="large" onClick={() => setModalOpen(true)}>
          Abrir Caja
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card className="bg-green-50">
          <p className="text-sm text-gray-600">Cajas abiertas</p>
          <p className="text-2xl font-bold text-green-800">
            {cierres.filter((c) => c.estado === 'ABIERTO').length}
          </p>
        </Card>
        <Card className="bg-blue-50">
          <p className="text-sm text-gray-600">Total cierres hoy</p>
          <p className="text-2xl font-bold text-blue-800">{cierres.length}</p>
        </Card>
        <Card className="bg-purple-50">
          <p className="text-sm text-gray-600">Conciliados</p>
          <p className="text-2xl font-bold text-purple-800">
            {cierres.filter((c) => c.estado === 'CONCILIADO').length}
          </p>
        </Card>
      </div>

      <Table
        dataSource={cierres}
        columns={columns}
        loading={loading}
        rowKey="id"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="Abrir Caja"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={abrirCaja}
        confirmLoading={abriendo}
        okText="Abrir"
        cancelText="Cancelar"
      >
        <p className="mb-2 font-bold">Caja: {cajas.find((c) => c.id === cajaSeleccionada)?.nombre}</p>
        <InputNumber
          className="w-full"
          size="large"
          placeholder="Monto inicial (Gs.)"
          value={montoInicial || null}
          onChange={(v) => setMontoInicial(v || 0)}
          min={0}
          step={10000}
          formatter={(v) => 'Gs. ' + (v || '').replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
          parser={(v) => parseInt((v || '').replace(/[^\d]/g, '')) || 0}
        />
      </Modal>
    </div>
  )
}