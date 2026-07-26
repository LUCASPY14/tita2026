import { useEffect, useState } from 'react'
import api from '../services/api'

// ── Tipos ────────────────────────────────────────────────────────────────────

interface AuditoriaEntry {
  id_auditoria:  number
  fecha_operacion: string
  usuario__email: string | null
  operacion:     string
  tabla_afectada: string | null
  id_registro:   number | null
  resultado:     string
  ip_address:    string | null
  descripcion:   string | null
  mensaje_error: string | null
}

interface AuditoriaResumen {
  total: number
  por_resultado: { resultado: string; count: number }[]
  top_operaciones: { operacion: string; count: number }[]
  top_tablas: { tabla_afectada: string; count: number }[]
}

interface IntentosResumen {
  total: number
  fallidos: number
  exitosos: number
  tasa_fallo: number
}

// ── Utilidades ───────────────────────────────────────────────────────────────

const hoy = () => new Date().toISOString().slice(0, 10)
const hace30Dias = () => {
  const d = new Date()
  d.setDate(d.getDate() - 30)
  return d.toISOString().slice(0, 10)
}

function ResultadoBadge({ resultado }: { resultado: string }) {
  const base = 'inline-block px-2 py-0.5 rounded text-xs font-bold uppercase tracking-wide'
  if (resultado === 'EXITO') return <span className={`${base} bg-green-100 text-green-800`}>Éxito</span>
  if (resultado === 'ERROR') return <span className={`${base} bg-red-100 text-red-700`}>Error</span>
  return <span className={`${base} bg-gray-100 text-gray-600`}>{resultado}</span>
}

// ── Componente principal ─────────────────────────────────────────────────────

export default function Auditoria() {

  const [desde,      setDesde]      = useState(hace30Dias())
  const [hasta,      setHasta]      = useState(hoy())
  const [operacion,  setOperacion]  = useState('')
  const [tabla,      setTabla]      = useState('')
  const [resultado,  setResultado]  = useState('')
  const [tab,        setTab]        = useState<'operaciones' | 'logins'>('operaciones')

  const [resumen,    setResumen]    = useState<AuditoriaResumen | null>(null)
  const [detalle,    setDetalle]    = useState<AuditoriaEntry[]>([])
  const [intentos,   setIntentos]   = useState<IntentosResumen | null>(null)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState<string | null>(null)

  const cargarAuditoria = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (desde)     params.set('desde',     desde)
      if (hasta)     params.set('hasta',     hasta)
      if (operacion) params.set('operacion', operacion)
      if (tabla)     params.set('tabla',     tabla)
      if (resultado) params.set('resultado', resultado)

      const { data } = await api.get(`/usuarios/reporte-auditoria/?${params}`)
      setResumen(data.resumen)
      setDetalle(data.detalle)
    } catch {
      setError('No se pudieron cargar los datos de auditoría.')
    } finally {
      setLoading(false)
    }
  }

  const cargarIntentos = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (desde) params.set('desde', desde)
      if (hasta) params.set('hasta', hasta)

      const { data } = await api.get(`/usuarios/reporte-intentos-login/?${params}`)
      setIntentos(data.resumen)
    } catch {
      setError('No se pudieron cargar los intentos de login.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (tab === 'operaciones') cargarAuditoria()
    else cargarIntentos()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  const handleBuscar = (e: React.FormEvent) => {
    e.preventDefault()
    if (tab === 'operaciones') cargarAuditoria()
    else cargarIntentos()
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-1">Auditoría del sistema</h1>
      <p className="text-sm text-gray-500 mb-6">Registro de operaciones y accesos. Solo visible para Administradores.</p>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          onClick={() => setTab('operaciones')}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            tab === 'operaciones' ? 'border-amber-500 text-amber-700' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Operaciones
        </button>
        <button
          onClick={() => setTab('logins')}
          className={`px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            tab === 'logins' ? 'border-amber-500 text-amber-700' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Intentos de login
        </button>
      </div>

      {/* Filtros */}
      <form onSubmit={handleBuscar} className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Desde</label>
            <input type="date" value={desde} onChange={e => setDesde(e.target.value)}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Hasta</label>
            <input type="date" value={hasta} onChange={e => setHasta(e.target.value)}
              className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400" />
          </div>
          {tab === 'operaciones' && (
            <>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Operación</label>
                <input type="text" value={operacion} onChange={e => setOperacion(e.target.value)} placeholder="Filtrar..."
                  className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 w-40" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Tabla</label>
                <input type="text" value={tabla} onChange={e => setTabla(e.target.value)} placeholder="Filtrar..."
                  className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 w-36" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Resultado</label>
                <select value={resultado} onChange={e => setResultado(e.target.value)}
                  className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400">
                  <option value="">Todos</option>
                  <option value="EXITO">Éxito</option>
                  <option value="ERROR">Error</option>
                </select>
              </div>
            </>
          )}
          <button type="submit"
            className="px-4 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-sm font-semibold rounded transition-colors">
            Buscar
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{error}</div>
      )}

      {loading && (
        <div className="text-center py-12 text-gray-400 text-sm">Cargando...</div>
      )}

      {/* ── Tab: Operaciones ── */}
      {!loading && tab === 'operaciones' && resumen && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="text-2xl font-bold font-mono">{resumen.total.toLocaleString()}</div>
              <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Total operaciones</div>
            </div>
            {resumen.por_resultado.map(r => (
              <div key={r.resultado} className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="text-2xl font-bold font-mono">{r.count.toLocaleString()}</div>
                <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">
                  <ResultadoBadge resultado={r.resultado} />
                </div>
              </div>
            ))}
          </div>

          {/* Top operaciones y tablas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Top operaciones</h3>
              <div className="space-y-1.5">
                {resumen.top_operaciones.map(op => (
                  <div key={op.operacion} className="flex justify-between items-center text-sm">
                    <span className="font-mono text-gray-700 truncate max-w-[70%]">{op.operacion}</span>
                    <span className="font-bold text-gray-900 font-mono">{op.count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Tablas más afectadas</h3>
              <div className="space-y-1.5">
                {resumen.top_tablas.map(t => (
                  <div key={t.tabla_afectada} className="flex justify-between items-center text-sm">
                    <span className="font-mono text-gray-700 truncate max-w-[70%]">{t.tabla_afectada}</span>
                    <span className="font-bold text-gray-900 font-mono">{t.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Tabla detalle */}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-700">Últimas {detalle.length} operaciones</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs text-gray-400 uppercase tracking-widest">
                    <th className="px-4 py-3 text-left font-semibold">Fecha</th>
                    <th className="px-4 py-3 text-left font-semibold">Usuario</th>
                    <th className="px-4 py-3 text-left font-semibold">Operación</th>
                    <th className="px-4 py-3 text-left font-semibold">Tabla</th>
                    <th className="px-4 py-3 text-left font-semibold">ID</th>
                    <th className="px-4 py-3 text-left font-semibold">Resultado</th>
                    <th className="px-4 py-3 text-left font-semibold">IP</th>
                  </tr>
                </thead>
                <tbody>
                  {detalle.length === 0 && (
                    <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Sin registros para los filtros seleccionados.</td></tr>
                  )}
                  {detalle.map(row => (
                    <tr key={row.id_auditoria} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-500 whitespace-nowrap">
                        {new Date(row.fecha_operacion).toLocaleString('es-PY')}
                      </td>
                      <td className="px-4 py-2.5 text-xs text-gray-700">{row.usuario__email ?? '—'}</td>
                      <td className="px-4 py-2.5 font-mono text-xs font-semibold text-gray-800">{row.operacion}</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{row.tabla_afectada ?? '—'}</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{row.id_registro ?? '—'}</td>
                      <td className="px-4 py-2.5"><ResultadoBadge resultado={row.resultado} /></td>
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-400">{row.ip_address ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* ── Tab: Intentos de login ── */}
      {!loading && tab === 'logins' && intentos && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold font-mono">{intentos.total.toLocaleString()}</div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Total intentos</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold font-mono text-green-600">{intentos.exitosos.toLocaleString()}</div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Exitosos</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="text-2xl font-bold font-mono text-red-600">{intentos.fallidos.toLocaleString()}</div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Fallidos</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className={`text-2xl font-bold font-mono ${intentos.tasa_fallo > 30 ? 'text-red-600' : 'text-gray-800'}`}>
              {intentos.tasa_fallo}%
            </div>
            <div className="text-xs text-gray-500 uppercase tracking-wide mt-1">Tasa de fallo</div>
          </div>
        </div>
      )}
    </div>
  )
}
