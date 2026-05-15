import { useEffect, useState } from 'react'
import { Table, Input, Tag, Button, Modal, InputNumber, message } from 'antd'
import { SearchOutlined, PlusOutlined } from '@ant-design/icons'
import api from '../services/api'

interface Tarjeta {
  nro_tarjeta: string
  codigo_barras: string
  hijo_nombre: string
  saldo_actual: string
  limite_credito: string
  estado: string
  permite_saldo_negativo: boolean
}

export default function Tarjetas() {
  const [tarjetas, setTarjetas] = useState<Tarjeta[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [recargaTarjeta, setRecargaTarjeta] = useState<Tarjeta | null>(null)
  const [monto, setMonto] = useState<number>(0)
  const [recargando, setRecargando] = useState(false)

  const cargarTarjetas = async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/core/tarjetas/', {
        params: { search }
      })
      setTarjetas(data.results || [])
    } catch {
      message.error('Error al cargar tarjetas')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    cargarTarjetas()
  }, [search])

  const handleRecarga = async () => {
    if (!monto || monto <= 0) {
      message.warning('Ingrese un monto valido')
      return
    }
    setRecargando(true)
    try {
      await api.post('/core/cargas-saldo/', {
        tarjeta: recargaTarjeta?.nro_tarjeta,
        monto_cargado: monto,
        metodo_pago: 'EFECTIVO',
      })
      message.success('Recarga exitosa')
      setModalOpen(false)
      setMonto(0)
      setRecargaTarjeta(null)

      // Actualizar el saldo localmente sin hacer otra llamada a la API
      setTarjetas(prev => prev.map(t => {
        if (t.nro_tarjeta === recargaTarjeta?.nro_tarjeta) {
          const nuevoSaldo = parseInt(t.saldo_actual) + monto
          return { ...t, saldo_actual: nuevoSaldo.toString() }
        }
        return t
      }))
    } catch {
      message.error('Error al recargar')
    } finally {
      setRecargando(false)
    }
  }

  const columns = [
    {
      title: 'Nro. Tarjeta',
      dataIndex: 'nro_tarjeta',
      key: 'nro_tarjeta',
    },
    {
      title: 'Estudiante',
      dataIndex: 'hijo_nombre',
      key: 'hijo',
    },
    {
      title: 'Saldo',
      dataIndex: 'saldo_actual',
      key: 'saldo',
      render: (v: string) => (
        <span className={parseInt(v) < 0 ? 'text-red-600 font-bold' : 'text-green-700 font-bold'}>
          Gs. {parseInt(v).toLocaleString('es-PY')}
        </span>
      ),
    },
    {
      title: 'Limite Credito',
      dataIndex: 'limite_credito',
      key: 'limite',
      render: (v: string) => 'Gs. ' + parseInt(v).toLocaleString('es-PY'),
    },
    {
      title: 'Estado',
      dataIndex: 'estado',
      key: 'estado',
      render: (estado: string) => {
        const colors: Record<string, string> = {
          ACTIVA: 'green',
          BLOQUEADA: 'orange',
          VENCIDA: 'red',
          CANCELADA: 'default',
        }
        return <Tag color={colors[estado] || 'default'}>{estado}</Tag>
      },
    },
    {
      title: 'Accion',
      key: 'accion',
      render: (_: unknown, record: Tarjeta) => (
        <Button
          type="primary"
          size="small"
          icon={<PlusOutlined />}
          onClick={() => {
            setRecargaTarjeta(record)
            setModalOpen(true)
          }}
        >
          Recargar
        </Button>
      ),
    },
  ]

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Tarjetas</h2>
      <Input
        prefix={<SearchOutlined />}
        placeholder="Buscar tarjetas..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="mb-4 max-w-md"
        size="large"
      />
      <Table
        dataSource={tarjetas}
        columns={columns}
        loading={loading}
        rowKey="nro_tarjeta"
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={'Recargar: ' + (recargaTarjeta?.hijo_nombre || '')}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false)
          setMonto(0)
          setRecargaTarjeta(null)
        }}
        onOk={handleRecarga}
        confirmLoading={recargando}
        okText="Recargar"
        cancelText="Cancelar"
      >
        <p className="mb-2">Saldo actual: Gs. {parseInt(recargaTarjeta?.saldo_actual || '0').toLocaleString('es-PY')}</p>
        <InputNumber
          className="w-full"
          size="large"
          placeholder="Monto en Guaranies"
          value={monto || null}
          onChange={(v) => setMonto(v || 0)}
          min={1000}
          step={1000}
          formatter={(v) => 'Gs. ' + (v || '').replace(/\B(?=(\d{3})+(?!\d))/g, '.')}
          parser={(v) => parseInt((v || '').replace(/[^\d]/g, '')) || 0}
        />
      </Modal>
    </div>
  )
}