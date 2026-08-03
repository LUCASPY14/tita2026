import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Undo2 } from 'lucide-react'
import pagosBancardService, { type PagoBancard } from '../services/pagosBancard'
import Table, { type Column } from '../components/ui/Table'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'

// ── Utilidades ───────────────────────────────────────────────────────────────

function formatGs(n: number | string): string {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

function formatFecha(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function esDeHoy(iso: string | null): boolean {
  if (!iso) return false
  const fecha = new Date(iso)
  const hoy = new Date()
  return fecha.toDateString() === hoy.toDateString()
}

const ESTADO_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'yellow', APROBADO: 'green', RECHAZADO: 'red', CANCELADO: 'default', ERROR: 'red',
}

const ESTADO_LABEL: Record<string, string> = {
  PENDIENTE: 'Pendiente', APROBADO: 'Aprobado', RECHAZADO: 'Rechazado', CANCELADO: 'Anulado', ERROR: 'Error',
}

const TIPO_LABEL: Record<string, string> = { TARJETA: 'Recarga saldo', ALMUERZO: 'Pago almuerzo' }

export default function PagosBancard() {
  const [pagos, setPagos] = useState<PagoBancard[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [filtroEstado, setFiltroEstado] = useState('')
  const [filtroTipo, setFiltroTipo] = useState('')
  const [anulando, setAnulando] = useState<PagoBancard | null>(null)
  const [procesando, setProcesando] = useState(false)

  const cargar = useCallback(async (pagina: number, estado: string, tipo: string) => {
    setLoading(true)
    try {
      const { data } = await pagosBancardService.listar({
        page: pagina,
        ...(estado && { estado }),
        ...(tipo && { tipo }),
      })
      setPagos(data.results)
      setTotal(data.count)
    } catch {
      toast.error('Error al cargar los pagos')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    cargar(page, filtroEstado, filtroTipo)
  }, [cargar, page, filtroEstado, filtroTipo])

  const handleAnular = async () => {
    if (!anulando) return
    setProcesando(true)
    try {
      await pagosBancardService.anular(anulando.shop_process_id)
      toast.success('Pago anulado correctamente')
      setAnulando(null)
      cargar(page, filtroEstado, filtroTipo)
    } catch (err) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'No se pudo anular el pago'
      toast.error(msg)
    } finally {
      setProcesando(false)
    }
  }

  const columns: Column<PagoBancard>[] = [
    { title: 'Fecha', key: 'fecha', render: (_, r) => formatFecha(r.fecha_confirmacion ?? r.fecha_creacion) },
    { title: 'Tipo', key: 'tipo', render: (_, r) => TIPO_LABEL[r.tipo] ?? r.tipo },
    { title: 'Cliente', key: 'cliente', dataIndex: 'cliente_nombre' },
    {
      title: 'Referencia', key: 'ref',
      render: (_, r) => r.tarjeta_nro ?? (r.cuenta_almuerzo_id_display ? `Cuenta #${r.cuenta_almuerzo_id_display}` : '—'),
    },
    { title: 'Monto', key: 'monto', render: (_, r) => <span className="tabular-nums font-semibold">{formatGs(r.monto)}</span> },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado]}>{ESTADO_LABEL[r.estado] ?? r.estado}</Badge>,
    },
    {
      title: '', key: 'acciones', width: 140,
      render: (_, r) => {
        if (r.estado !== 'APROBADO') return null
        const puedeAnular = esDeHoy(r.fecha_confirmacion ?? r.fecha_creacion)
        return (
          <Button
            size="sm"
            variant="danger"
            onClick={() => setAnulando(r)}
            disabled={!puedeAnular}
            title={puedeAnular ? undefined : 'Bancard solo permite anular el mismo día de la transacción'}
          >
            <Undo2 className="w-3.5 h-3.5" />
            Anular
          </Button>
        )
      },
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Pagos Bancard</h1>
        <p className="text-base text-slate-500 mt-0.5">
          Recargas de saldo y pagos de almuerzo procesados por Bancard. Solo se pueden anular pagos aprobados el mismo día.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <select
          value={filtroEstado}
          onChange={e => { setFiltroEstado(e.target.value); setPage(1) }}
          className="border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-700 focus:outline-none focus:ring-2 focus:ring-green-500/30"
        >
          <option value="">Todos los estados</option>
          <option value="APROBADO">Aprobado</option>
          <option value="PENDIENTE">Pendiente</option>
          <option value="RECHAZADO">Rechazado</option>
          <option value="CANCELADO">Anulado</option>
          <option value="ERROR">Error</option>
        </select>
        <select
          value={filtroTipo}
          onChange={e => { setFiltroTipo(e.target.value); setPage(1) }}
          className="border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-700 focus:outline-none focus:ring-2 focus:ring-green-500/30"
        >
          <option value="">Todos los tipos</option>
          <option value="TARJETA">Recarga de saldo</option>
          <option value="ALMUERZO">Pago de almuerzo</option>
        </select>
      </div>

      <Table
        columns={columns}
        dataSource={pagos}
        rowKey="shop_process_id"
        loading={loading}
        page={page}
        onPageChange={setPage}
        total={total}
        pageSize={20}
      />

      <Modal
        open={!!anulando}
        title="Anular pago"
        onOk={handleAnular}
        onCancel={() => setAnulando(null)}
        okText="Sí, anular"
        confirmLoading={procesando}
      >
        {anulando && (
          <div className="space-y-3">
            <p className="text-base text-slate-700">
              ¿Confirmás anular este pago de <strong>{formatGs(anulando.monto)}</strong> de{' '}
              <strong>{anulando.cliente_nombre}</strong>?
            </p>
            <p className="text-sm text-slate-500">
              Se le pide la reversión a Bancard y se descuenta el saldo/cuenta acreditado. Esta acción no se puede deshacer.
            </p>
          </div>
        )}
      </Modal>
    </div>
  )
}
