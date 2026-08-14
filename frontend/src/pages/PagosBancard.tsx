import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Undo2, Eye, RotateCcw, RefreshCw, Ban, Download } from 'lucide-react'
import pagosBancardService, { type PagoBancard, type PagoBancardDetalle } from '../services/pagosBancard'
import Table, { type Column } from '../components/ui/Table'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import { descargaBlob } from './reportes/reportesUtils'

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

const MINUTOS_MINIMOS_CIERRE_MANUAL = 60

function minutosDesde(iso: string): number {
  return (Date.now() - new Date(iso).getTime()) / 60_000
}

function extractDetail(err: unknown, fallback: string): string {
  const e = err as { response?: { data?: { detail?: string } } }
  return e?.response?.data?.detail ?? fallback
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
  const [reintentando, setReintentando] = useState<PagoBancard | null>(null)
  const [procesandoReintentar, setProcesandoReintentar] = useState(false)
  const [cerrando, setCerrando] = useState<PagoBancard | null>(null)
  const [procesandoCerrar, setProcesandoCerrar] = useState(false)
  const [reconsultandoId, setReconsultandoId] = useState<string | null>(null)
  const [detalleAbierto, setDetalleAbierto] = useState<string | null>(null)
  const [detalleData, setDetalleData] = useState<PagoBancardDetalle | null>(null)
  const [detalleLoading, setDetalleLoading] = useState(false)
  const [exportando, setExportando] = useState(false)

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
      toast.error(extractDetail(err, 'No se pudo anular el pago'))
    } finally {
      setProcesando(false)
    }
  }

  const handleReintentar = async () => {
    if (!reintentando) return
    setProcesandoReintentar(true)
    try {
      const { data } = await pagosBancardService.reintentar(reintentando.shop_process_id)
      toast.success(data.detail)
      setReintentando(null)
      cargar(page, filtroEstado, filtroTipo)
    } catch (err) {
      toast.error(extractDetail(err, 'No se pudo reintentar la acreditación'))
    } finally {
      setProcesandoReintentar(false)
    }
  }

  const handleReconsultar = async (r: PagoBancard) => {
    setReconsultandoId(r.shop_process_id)
    try {
      const { data } = await pagosBancardService.reconsultar(r.shop_process_id)
      toast.success(data.detail)
      cargar(page, filtroEstado, filtroTipo)
    } catch (err) {
      toast.error(extractDetail(err, 'No se pudo reconsultar el pago'))
    } finally {
      setReconsultandoId(null)
    }
  }

  const handleCerrarManual = async () => {
    if (!cerrando) return
    setProcesandoCerrar(true)
    try {
      const { data } = await pagosBancardService.cerrarManual(cerrando.shop_process_id)
      toast.success(data.detail)
      setCerrando(null)
      cargar(page, filtroEstado, filtroTipo)
    } catch (err) {
      toast.error(extractDetail(err, 'No se pudo cerrar el pago'))
    } finally {
      setProcesandoCerrar(false)
    }
  }

  const abrirDetalle = async (shopProcessId: string) => {
    setDetalleAbierto(shopProcessId)
    setDetalleData(null)
    setDetalleLoading(true)
    try {
      const { data } = await pagosBancardService.detalle(shopProcessId)
      setDetalleData(data)
    } catch {
      toast.error('Error al cargar el detalle')
    } finally {
      setDetalleLoading(false)
    }
  }

  const handleExportarCsv = async () => {
    setExportando(true)
    try {
      const { data } = await pagosBancardService.exportarCsv({
        ...(filtroEstado && { estado: filtroEstado }),
        ...(filtroTipo && { tipo: filtroTipo }),
      })
      descargaBlob(data as unknown as Blob, 'pagos_bancard.csv')
      toast.success('CSV descargado')
    } catch {
      toast.error('Error al exportar')
    } finally {
      setExportando(false)
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
      title: '', key: 'acciones', width: 260,
      render: (_, r) => {
        const puedeAnular = r.estado === 'APROBADO' && esDeHoy(r.fecha_confirmacion ?? r.fecha_creacion)
        const puedeCerrarManual = minutosDesde(r.fecha_creacion) >= MINUTOS_MINIMOS_CIERRE_MANUAL
        return (
          <div className="flex items-center gap-1.5 flex-wrap">
            <Button size="sm" variant="ghost" onClick={() => abrirDetalle(r.shop_process_id)} title="Ver detalle">
              <Eye className="w-3.5 h-3.5" />
            </Button>
            {r.estado === 'APROBADO' && (
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
            )}
            {r.estado === 'ERROR' && (
              <Button size="sm" variant="primary" onClick={() => setReintentando(r)}>
                <RotateCcw className="w-3.5 h-3.5" />
                Reintentar
              </Button>
            )}
            {r.estado === 'PENDIENTE' && (
              <>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => handleReconsultar(r)}
                  loading={reconsultandoId === r.shop_process_id}
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Reconsultar
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => setCerrando(r)}
                  disabled={!puedeCerrarManual}
                  title={
                    puedeCerrarManual
                      ? undefined
                      : `Esperá ${MINUTOS_MINIMOS_CIERRE_MANUAL} minutos desde la creación antes de cerrarlo manualmente`
                  }
                >
                  <Ban className="w-3.5 h-3.5" />
                  Cerrar
                </Button>
              </>
            )}
          </div>
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
        <Button size="sm" variant="secondary" onClick={handleExportarCsv} loading={exportando} className="ml-auto">
          <Download className="w-3.5 h-3.5" />
          Exportar CSV
        </Button>
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

      <Modal
        open={!!reintentando}
        title="Reintentar acreditación"
        onOk={handleReintentar}
        onCancel={() => setReintentando(null)}
        okText="Sí, reintentar"
        confirmLoading={procesandoReintentar}
      >
        {reintentando && (
          <div className="space-y-3">
            <p className="text-base text-slate-700">
              Bancard cobró <strong>{formatGs(reintentando.monto)}</strong> a <strong>{reintentando.cliente_nombre}</strong>{' '}
              pero el saldo no se pudo acreditar. ¿Reintentar?
            </p>
            <p className="text-sm text-slate-500">
              Si el crédito ya existe (falló solo el guardado del registro), se vincula sin cobrar ni acreditar de nuevo.
              Si nunca se acreditó, se acredita ahora.
            </p>
          </div>
        )}
      </Modal>

      <Modal
        open={!!cerrando}
        title="Cerrar pago manualmente"
        onOk={handleCerrarManual}
        onCancel={() => setCerrando(null)}
        okText="Sí, cerrar"
        confirmLoading={procesandoCerrar}
      >
        {cerrando && (
          <div className="space-y-3">
            <p className="text-base text-slate-700">
              ¿Confirmás cerrar manualmente este pago pendiente de <strong>{formatGs(cerrando.monto)}</strong> de{' '}
              <strong>{cerrando.cliente_nombre}</strong>?
            </p>
            <p className="text-sm text-slate-500">
              Antes de cerrarlo se vuelve a consultar el resultado real en Bancard — si Bancard sí tiene un resultado,
              se aplica ese en vez de cerrarlo. Usalo solo cuando el padre abandonó el checkout.
            </p>
          </div>
        )}
      </Modal>

      <Modal
        open={!!detalleAbierto}
        title="Detalle del pago"
        onCancel={() => setDetalleAbierto(null)}
        footer={null}
        width={560}
      >
        {detalleLoading && <p className="text-base text-slate-400">Cargando...</p>}
        {detalleData && (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-slate-400 text-xs uppercase tracking-wide">Process ID</p>
                <p className="font-mono text-slate-700 break-all">{detalleData.process_id ?? '—'}</p>
              </div>
              <div>
                <p className="text-slate-400 text-xs uppercase tracking-wide">IP de origen</p>
                <p className="font-mono text-slate-700">{detalleData.ip_origen ?? '—'}</p>
              </div>
            </div>
            <div>
              <p className="text-slate-400 text-xs uppercase tracking-wide mb-1">Respuesta de Bancard</p>
              <pre className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs overflow-x-auto max-h-64 overflow-y-auto">
                {JSON.stringify(detalleData.bancard_response, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
