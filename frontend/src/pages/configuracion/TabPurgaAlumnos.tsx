import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { UserX, CheckCircle2 } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Table, { type Column } from '../../components/ui/Table'
import { extractErrorMessage } from './helpers'

interface HijoPendiente {
  id_hijo: number
  nombre: string
  apellido: string
  cliente_nombre: string
  fecha_baja: string | null
  purga_solicitada_en: string | null
}

function formatFecha(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PY')
}

export default function TabPurgaAlumnos() {
  const [pendientes, setPendientes] = useState<HijoPendiente[]>([])
  const [loading, setLoading] = useState(false)
  const [aprobando, setAprobando] = useState(false)
  const [target, setTarget] = useState<HijoPendiente | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<HijoPendiente[]>('/clientes/hijos/pendientes-purga/')
      setPendientes(data)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  async function confirmarPurga() {
    if (!target) return
    setAprobando(true)
    try {
      await api.post(`/clientes/hijos/${target.id_hijo}/aprobar-purga/`)
      toast.success('Datos del alumno anonimizados')
      setTarget(null)
      load()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAprobando(false)
    }
  }

  const columns: Column<HijoPendiente>[] = [
    { title: 'Alumno', key: 'nombre', render: (_, r) => `${r.apellido}, ${r.nombre}` },
    { title: 'Responsable', key: 'cliente_nombre', dataIndex: 'cliente_nombre' },
    { title: 'Fecha de baja', key: 'fecha_baja', render: (_, r) => formatFecha(r.fecha_baja) },
    { title: 'Pendiente desde', key: 'purga_solicitada_en', render: (_, r) => formatFecha(r.purga_solicitada_en) },
    {
      title: '',
      key: 'accion',
      render: (_, r) => (
        <Button
          size="sm"
          variant="danger"
          icon={<CheckCircle2 className="w-3.5 h-3.5" />}
          onClick={() => setTarget(r)}
        >
          Aprobar purga
        </Button>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        Alumnos dados de baja hace más de un año, esperando aprobación para anonimizar sus datos
        sensibles (restricciones médicas, foto, fecha de nacimiento, grado y nombre). El historial
        de ventas y facturas no se toca. <strong>La acción no se puede deshacer.</strong>
      </div>

      {!loading && pendientes.length === 0 ? (
        <div className="text-center py-12 text-slate-400">
          <UserX className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p className="text-sm">No hay alumnos pendientes de purga</p>
        </div>
      ) : (
        <Table columns={columns} dataSource={pendientes} rowKey="id_hijo" loading={loading} />
      )}

      <Modal
        open={target !== null}
        title="Aprobar purga de datos"
        onOk={confirmarPurga}
        onCancel={() => setTarget(null)}
        okText="Sí, anonimizar"
        confirmLoading={aprobando}
      >
        {target && (
          <p className="text-sm text-slate-600">
            Vas a anonimizar los datos sensibles de <strong>{target.apellido}, {target.nombre}</strong> —
            se van a borrar sus restricciones médicas y foto, y su nombre va a quedar reemplazado por
            un identificador genérico. El historial de ventas y facturas queda intacto. Esta acción no
            se puede deshacer. ¿Confirmás?
          </p>
        )}
      </Modal>
    </div>
  )
}
