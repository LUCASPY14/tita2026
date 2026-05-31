import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Plug, FileText, Webhook, KeyRound, CheckCircle, XCircle } from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Table, { type Column } from '../components/ui/Table'
import Spinner from '../components/ui/Spinner'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface ProveedorApi {
  id: number
  nombre: string
  tipo_servicio: string
  url_base: string
  tipo_auth: string
  activo: boolean
}

interface CredencialApi {
  id: number
  proveedor: number
  proveedor_nombre?: string
  ambiente: string
  activo: boolean
  fecha_expiracion: string | null
}

interface WebhookEndpoint {
  id: number
  proveedor: number
  nombre: string
  path: string
  activo: boolean
  requiere_verificacion: boolean
  eventos: string[]
}

interface LogLlamada {
  id: number
  metodo: string
  url: string
  status_code: number
  tiempo_ms: number
  exitoso: boolean
  timestamp: string
}

interface LogWebhook {
  id: number
  evento_tipo: string
  verificacion_ok: boolean
  procesado_ok: boolean
  timestamp: string
  ip_origen: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const AMBIENTE_COLOR: Record<string, BadgeColor> = { SANDBOX: 'yellow', PRODUCCION: 'green' }
const SERVICIO_COLOR: Record<string, BadgeColor> = {
  PAGOS_QR: 'green', BANCO: 'blue', NOTIFICACIONES: 'purple', OTRO: 'default',
}

type TabKey = 'proveedores' | 'credenciales' | 'webhooks' | 'logs_llamadas' | 'logs_webhooks'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatFecha(iso: string) {
  return new Date(iso).toLocaleString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function Integraciones() {
  const [tab, setTab] = useState<TabKey>('proveedores')

  // ── Proveedores ───────────────────────────────────────────────────
  const [proveedores, setProveedores] = useState<ProveedorApi[]>([])
  const [loadingProv, setLoadingProv] = useState(false)

  const loadProveedores = useCallback(async () => {
    setLoadingProv(true)
    try {
      const { data } = await api.get('/integrations/proveedores/', { params: { page_size: 100 } })
      setProveedores(data.results ?? [])
    } catch { toast.error('Error al cargar proveedores') }
    finally { setLoadingProv(false) }
  }, [])

  useEffect(() => { if (tab === 'proveedores') loadProveedores() }, [tab, loadProveedores])

  // ── Credenciales ──────────────────────────────────────────────────
  const [credenciales, setCredenciales] = useState<CredencialApi[]>([])
  const [loadingCred, setLoadingCred] = useState(false)

  const loadCredenciales = useCallback(async () => {
    setLoadingCred(true)
    try {
      const { data } = await api.get('/integrations/credenciales/', { params: { page_size: 100 } })
      setCredenciales(data.results ?? [])
    } catch { toast.error('Error al cargar credenciales') }
    finally { setLoadingCred(false) }
  }, [])

  useEffect(() => { if (tab === 'credenciales') loadCredenciales() }, [tab, loadCredenciales])

  // ── Webhooks ──────────────────────────────────────────────────────
  const [webhooks, setWebhooks] = useState<WebhookEndpoint[]>([])
  const [loadingWh, setLoadingWh] = useState(false)

  const loadWebhooks = useCallback(async () => {
    setLoadingWh(true)
    try {
      const { data } = await api.get('/integrations/webhooks/', { params: { page_size: 100 } })
      setWebhooks(data.results ?? [])
    } catch { toast.error('Error al cargar webhooks') }
    finally { setLoadingWh(false) }
  }, [])

  useEffect(() => { if (tab === 'webhooks') loadWebhooks() }, [tab, loadWebhooks])

  // ── Logs llamadas ─────────────────────────────────────────────────
  const [logsLlamadas, setLogsLlamadas] = useState<LogLlamada[]>([])
  const [loadingLogL, setLoadingLogL] = useState(false)
  const [totalLogL, setTotalLogL] = useState(0)
  const [pageLogL, setPageLogL] = useState(1)

  const loadLogsLlamadas = useCallback(async (p: number) => {
    setLoadingLogL(true)
    try {
      const { data } = await api.get('/integrations/logs-llamadas/', { params: { page: p, page_size: 20 } })
      setLogsLlamadas(data.results ?? [])
      setTotalLogL(data.count ?? 0)
    } catch { toast.error('Error al cargar logs') }
    finally { setLoadingLogL(false) }
  }, [])

  useEffect(() => { if (tab === 'logs_llamadas') loadLogsLlamadas(1) }, [tab, loadLogsLlamadas])

  // ── Logs webhooks ─────────────────────────────────────────────────
  const [logsWebhooks, setLogsWebhooks] = useState<LogWebhook[]>([])
  const [loadingLogW, setLoadingLogW] = useState(false)
  const [totalLogW, setTotalLogW] = useState(0)
  const [pageLogW, setPageLogW] = useState(1)

  const loadLogsWebhooks = useCallback(async (p: number) => {
    setLoadingLogW(true)
    try {
      const { data } = await api.get('/integrations/logs-webhooks/', { params: { page: p, page_size: 20 } })
      setLogsWebhooks(data.results ?? [])
      setTotalLogW(data.count ?? 0)
    } catch { toast.error('Error al cargar logs') }
    finally { setLoadingLogW(false) }
  }, [])

  useEffect(() => { if (tab === 'logs_webhooks') loadLogsWebhooks(1) }, [tab, loadLogsWebhooks])

  // ── Columns ───────────────────────────────────────────────────────

  const colsProv: Column<ProveedorApi>[] = [
    {
      title: 'Proveedor',
      key: 'nombre',
      render: (_, r) => (
        <div>
          <p className="text-sm font-semibold text-slate-800">{r.nombre}</p>
          <p className="text-xs text-slate-400 font-mono">{r.url_base}</p>
        </div>
      ),
    },
    { title: 'Servicio', key: 'tipo', render: (_, r) => <Badge color={SERVICIO_COLOR[r.tipo_servicio] ?? 'default'}>{r.tipo_servicio}</Badge> },
    { title: 'Auth', key: 'auth', render: (_, r) => <code className="text-xs bg-slate-100 px-2 py-0.5 rounded">{r.tipo_auth}</code> },
    { title: 'Estado', key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
  ]

  const colsCred: Column<CredencialApi>[] = [
    {
      title: 'Proveedor / Ambiente',
      key: 'prov',
      render: (_, r) => (
        <div>
          <p className="text-sm font-medium text-slate-800">Proveedor #{r.proveedor}</p>
          <Badge color={AMBIENTE_COLOR[r.ambiente] ?? 'default'}>{r.ambiente}</Badge>
        </div>
      ),
    },
    {
      title: 'API Key',
      key: 'key',
      render: () => <code className="text-xs bg-slate-100 px-2 py-0.5 rounded text-slate-500">••••••••</code>,
    },
    {
      title: 'Vencimiento',
      key: 'exp',
      render: (_, r) => <span className="text-xs text-slate-500">{r.fecha_expiracion ? formatFecha(r.fecha_expiracion) : 'Sin vencimiento'}</span>,
    },
    { title: 'Estado', key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activa' : 'Inactiva'}</Badge> },
  ]

  const colsWh: Column<WebhookEndpoint>[] = [
    {
      title: 'Webhook',
      key: 'nombre',
      render: (_, r) => (
        <div>
          <p className="text-sm font-medium text-slate-800">{r.nombre}</p>
          <p className="text-xs text-slate-400 font-mono">{r.path}</p>
        </div>
      ),
    },
    {
      title: 'Eventos',
      key: 'eventos',
      render: (_, r) => (
        <div className="flex flex-wrap gap-1">
          {(r.eventos ?? []).slice(0, 3).map(e => (
            <code key={e} className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">{e}</code>
          ))}
          {r.eventos?.length > 3 && <span className="text-xs text-slate-400">+{r.eventos.length - 3}</span>}
        </div>
      ),
    },
    { title: 'Verificación', key: 'ver', render: (_, r) => <Badge color={r.requiere_verificacion ? 'blue' : 'default'}>{r.requiere_verificacion ? 'Habilitada' : 'No'}</Badge> },
    { title: 'Estado', key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
  ]

  const colsLogL: Column<LogLlamada>[] = [
    { title: 'Método', key: 'metodo', render: (_, r) => <code className="text-xs font-bold">{r.metodo}</code> },
    { title: 'URL', key: 'url', render: (_, r) => <span className="text-xs text-slate-600 font-mono truncate max-w-xs block">{r.url}</span> },
    {
      title: 'Status', key: 'status',
      render: (_, r) => {
        const color: BadgeColor = r.status_code < 300 ? 'green' : r.status_code < 500 ? 'yellow' : 'red'
        return <Badge color={color}>{r.status_code}</Badge>
      },
    },
    { title: 'Tiempo', key: 'tiempo', render: (_, r) => <span className="tabular-nums text-xs text-slate-600">{r.tiempo_ms}ms</span> },
    {
      title: 'OK', key: 'ok',
      render: (_, r) => r.exitoso
        ? <CheckCircle className="w-4 h-4 text-green-500" />
        : <XCircle className="w-4 h-4 text-red-500" />,
    },
    { title: 'Fecha', key: 'ts', render: (_, r) => <span className="text-xs text-slate-400">{formatFecha(r.timestamp)}</span> },
  ]

  const colsLogW: Column<LogWebhook>[] = [
    { title: 'Evento', key: 'evento', render: (_, r) => <code className="text-xs bg-slate-100 px-1.5 py-0.5 rounded">{r.evento_tipo}</code> },
    { title: 'IP Origen', key: 'ip', render: (_, r) => <span className="text-xs font-mono text-slate-600">{r.ip_origen}</span> },
    {
      title: 'Verificación', key: 'ver',
      render: (_, r) => r.verificacion_ok
        ? <CheckCircle className="w-4 h-4 text-green-500" />
        : <XCircle className="w-4 h-4 text-red-500" />,
    },
    {
      title: 'Procesado', key: 'proc',
      render: (_, r) => r.procesado_ok
        ? <CheckCircle className="w-4 h-4 text-green-500" />
        : <XCircle className="w-4 h-4 text-red-500" />,
    },
    { title: 'Fecha', key: 'ts', render: (_, r) => <span className="text-xs text-slate-400">{formatFecha(r.timestamp)}</span> },
  ]

  const TABS: { key: TabKey; label: string; icon: typeof Plug }[] = [
    { key: 'proveedores', label: 'Proveedores', icon: Plug },
    { key: 'credenciales', label: 'Credenciales', icon: KeyRound },
    { key: 'webhooks', label: 'Webhooks', icon: Webhook },
    { key: 'logs_llamadas', label: 'Logs API', icon: FileText },
    { key: 'logs_webhooks', label: 'Logs Webhooks', icon: FileText },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Integraciones</h1>
        <p className="text-sm text-slate-500 mt-0.5">Configuración de APIs externas, webhooks y logs</p>
      </div>

      <div className="border-b border-slate-200">
        <div className="flex gap-0 flex-wrap">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button key={key} type="button" onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
              <Icon className="w-4 h-4" />{label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'proveedores' && (
        loadingProv ? <div className="flex justify-center py-20"><Spinner /></div> : (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1"><Table columns={colsProv} dataSource={proveedores} rowKey="id" /></div>
          </div>
        )
      )}

      {tab === 'credenciales' && (
        loadingCred ? <div className="flex justify-center py-20"><Spinner /></div> : (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1"><Table columns={colsCred} dataSource={credenciales} rowKey="id" /></div>
          </div>
        )
      )}

      {tab === 'webhooks' && (
        loadingWh ? <div className="flex justify-center py-20"><Spinner /></div> : (
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1"><Table columns={colsWh} dataSource={webhooks} rowKey="id" /></div>
          </div>
        )
      )}

      {tab === 'logs_llamadas' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            <Table columns={colsLogL} dataSource={logsLlamadas} rowKey="id" loading={loadingLogL}
              pageSize={20} page={pageLogL} total={totalLogL}
              onPageChange={p => { setPageLogL(p); loadLogsLlamadas(p) }} />
          </div>
        </div>
      )}

      {tab === 'logs_webhooks' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            <Table columns={colsLogW} dataSource={logsWebhooks} rowKey="id" loading={loadingLogW}
              pageSize={20} page={pageLogW} total={totalLogW}
              onPageChange={p => { setPageLogW(p); loadLogsWebhooks(p) }} />
          </div>
        </div>
      )}
    </div>
  )
}
