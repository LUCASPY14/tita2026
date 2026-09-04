import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Mail, Send, RotateCcw } from 'lucide-react'
import api from '../../services/api'
import Badge, { type BadgeColor } from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface EmailEnviado {
  id_email: number
  destinatario_email: string
  destinatario_nombre: string
  asunto: string
  estado: 'ENVIADO' | 'ENTREGADO' | 'ABIERTO' | 'REBOTADO' | 'ERROR'
  fecha_envio: string
  intentos: number
  mensaje_error: string | null
}

interface SolicitudNotificacion {
  id_solicitud_notif: number
  cliente_nombre: string
  tipo: string
  mensaje: string
  destino: 'EMAIL' | 'SISTEMA' | 'WHATSAPP'
  estado: 'PENDIENTE' | 'ENVIADA' | 'FALLIDA'
  fecha_solicitud: string
  fecha_envio: string | null
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const EMAIL_ESTADO_COLOR: Record<string, BadgeColor> = {
  ENVIADO: 'blue', ENTREGADO: 'green', ABIERTO: 'green', REBOTADO: 'red', ERROR: 'red',
}
const SOLICITUD_ESTADO_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'yellow', ENVIADA: 'green', FALLIDA: 'red',
}
const DESTINO_COLOR: Record<string, BadgeColor> = {
  EMAIL: 'blue', SISTEMA: 'purple', WHATSAPP: 'green',
}

function formatFecha(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

const PAGE_SIZE = 15

// ─── Sub-tab: Emails enviados ───────────────────────────────────────────────

function SubTabEmails() {
  const [emails, setEmails] = useState<EmailEnviado[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [estado, setEstado] = useState('')
  const [loading, setLoading] = useState(false)
  const reqRef = useRef(0)

  const load = useCallback(async (p: number, est: string) => {
    const reqId = ++reqRef.current
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: PAGE_SIZE }
      if (est) params.estado = est
      const { data } = await api.get('/notificaciones/emails-enviados/', { params })
      if (reqId !== reqRef.current) return
      setEmails(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (reqId !== reqRef.current) return
      toast.error('Error al cargar emails enviados')
    } finally {
      if (reqId === reqRef.current) setLoading(false)
    }
  }, [])

  // Carga de datos al cambiar el filtro: el reset de página es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setPage(1); load(1, estado) }, [estado, load])

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors'
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1'

  const columns: Column<EmailEnviado>[] = [
    {
      title: 'Destinatario', key: 'dest',
      render: (_, r) => (
        <div>
          <p className="text-sm font-medium text-slate-800">{r.destinatario_nombre}</p>
          <p className="text-xs text-slate-400">{r.destinatario_email}</p>
        </div>
      ),
    },
    { title: 'Asunto', key: 'asunto', render: (_, r) => <span className="text-sm text-slate-600">{r.asunto}</span> },
    { title: 'Estado', key: 'estado', width: 110, render: (_, r) => <Badge color={EMAIL_ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge> },
    { title: 'Intentos', key: 'intentos', width: 80, render: (_, r) => <span className="tabular-nums text-sm text-slate-500">{r.intentos}</span> },
    { title: 'Fecha', key: 'fecha', width: 160, render: (_, r) => <span className="text-xs text-slate-400 tabular-nums">{formatFecha(r.fecha_envio)}</span> },
  ]

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
        <label className={labelClass}>Estado</label>
        <select value={estado} onChange={e => setEstado(e.target.value)} className={`${inputClass} w-auto`}>
          <option value="">Todos</option>
          <option value="ENVIADO">Enviado</option>
          <option value="ENTREGADO">Entregado</option>
          <option value="ABIERTO">Abierto</option>
          <option value="REBOTADO">Rebotado</option>
          <option value="ERROR">Error</option>
        </select>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table
            columns={columns} dataSource={emails} rowKey="id_email" loading={loading}
            pageSize={PAGE_SIZE} page={page} onPageChange={p => { setPage(p); load(p, estado) }} total={total}
          />
        </div>
      </div>
    </div>
  )
}

// ─── Sub-tab: Solicitudes de notificación ───────────────────────────────────

function SubTabSolicitudes() {
  const [solicitudes, setSolicitudes] = useState<SolicitudNotificacion[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [estado, setEstado] = useState('')
  const [destino, setDestino] = useState('')
  const [loading, setLoading] = useState(false)
  const [retryingId, setRetryingId] = useState<number | null>(null)
  const reqRef = useRef(0)

  const load = useCallback(async (p: number, est: string, dest: string) => {
    const reqId = ++reqRef.current
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: PAGE_SIZE }
      if (est) params.estado = est
      if (dest) params.destino = dest
      const { data } = await api.get('/notificaciones/solicitudes/', { params })
      if (reqId !== reqRef.current) return
      setSolicitudes(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (reqId !== reqRef.current) return
      toast.error('Error al cargar solicitudes de notificación')
    } finally {
      if (reqId === reqRef.current) setLoading(false)
    }
  }, [])

  // Carga de datos al cambiar los filtros: el reset de página es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setPage(1); load(1, estado, destino) }, [estado, destino, load])

  async function reintentar(id: number) {
    setRetryingId(id)
    try {
      await api.patch(`/notificaciones/solicitudes/${id}/`, { estado: 'PENDIENTE' })
      await api.post('/notificaciones/enviar/', { solicitud_ids: [id] })
      toast.success('Solicitud reprocesada')
      load(page, estado, destino)
    } catch {
      toast.error('No se pudo reintentar la solicitud')
    } finally {
      setRetryingId(null)
    }
  }

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors'
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1'

  const columns: Column<SolicitudNotificacion>[] = [
    { title: 'Cliente', key: 'cliente', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.cliente_nombre}</span> },
    { title: 'Tipo', key: 'tipo', render: (_, r) => <span className="text-sm text-slate-600">{r.tipo}</span> },
    { title: 'Destino', key: 'destino', width: 100, render: (_, r) => <Badge color={DESTINO_COLOR[r.destino] ?? 'default'}>{r.destino}</Badge> },
    { title: 'Estado', key: 'estado', width: 110, render: (_, r) => <Badge color={SOLICITUD_ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge> },
    { title: 'Fecha', key: 'fecha', width: 160, render: (_, r) => <span className="text-xs text-slate-400 tabular-nums">{formatFecha(r.fecha_solicitud)}</span> },
    {
      title: '', key: 'acciones', width: 110,
      render: (_, r) => r.estado === 'FALLIDA' ? (
        <Button size="sm" variant="secondary" onClick={() => reintentar(r.id_solicitud_notif)} disabled={retryingId === r.id_solicitud_notif}>
          <RotateCcw className="w-3.5 h-3.5" />
          {retryingId === r.id_solicitud_notif ? 'Reintentando...' : 'Reintentar'}
        </Button>
      ) : null,
    },
  ]

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap gap-4">
        <div>
          <label className={labelClass}>Estado</label>
          <select value={estado} onChange={e => setEstado(e.target.value)} className={`${inputClass} w-auto`}>
            <option value="">Todos</option>
            <option value="PENDIENTE">Pendiente</option>
            <option value="ENVIADA">Enviada</option>
            <option value="FALLIDA">Fallida</option>
          </select>
        </div>
        <div>
          <label className={labelClass}>Destino</label>
          <select value={destino} onChange={e => setDestino(e.target.value)} className={`${inputClass} w-auto`}>
            <option value="">Todos</option>
            <option value="EMAIL">Email</option>
            <option value="SISTEMA">Sistema</option>
            <option value="WHATSAPP">WhatsApp</option>
          </select>
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table
            columns={columns} dataSource={solicitudes} rowKey="id_solicitud_notif" loading={loading}
            pageSize={PAGE_SIZE} page={page} onPageChange={p => { setPage(p); load(p, estado, destino) }} total={total}
          />
        </div>
      </div>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function TabNotificaciones() {
  const [subtab, setSubtab] = useState<'emails' | 'solicitudes'>('emails')

  const subtabClass = (k: typeof subtab) =>
    `flex items-center gap-2 px-3.5 py-2 text-sm font-medium rounded-lg transition-colors cursor-pointer ${
      subtab === k ? 'bg-green-50 text-green-700' : 'text-slate-500 hover:bg-slate-50'
    }`

  return (
    <div className="space-y-4">
      <div className="flex gap-1">
        <button onClick={() => setSubtab('emails')} className={subtabClass('emails')}>
          <Mail className="w-4 h-4" />Emails enviados
        </button>
        <button onClick={() => setSubtab('solicitudes')} className={subtabClass('solicitudes')}>
          <Send className="w-4 h-4" />Solicitudes
        </button>
      </div>
      {subtab === 'emails' ? <SubTabEmails /> : <SubTabSolicitudes />}
    </div>
  )
}
