import { useCallback, useEffect, useState } from 'react'
import { HandCoins, Users, AlertTriangle, RefreshCw, Search, FileWarning } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../services/api'
import ModalPagarCC from './clientes/ModalPagarCC'
import { formatGs, type Cliente } from './clientes/shared'

interface DeudorRow {
  cliente_id: number
  cliente: string
  ruc_ci: string
  telefono: string
  email: string
  saldo_deuda: number
  dias_atraso: number
  aging: '0-30' | '31-60' | '61-90' | '90+'
}

interface ReporteCuenta {
  clientes: DeudorRow[]
  total_deuda: number
  aging_totales: Record<string, number>
}

const AGING_BADGE: Record<string, string> = {
  '0-30':  'bg-emerald-100 text-emerald-700',
  '31-60': 'bg-yellow-100 text-yellow-700',
  '61-90': 'bg-orange-100 text-orange-700',
  '90+':   'bg-red-100 text-red-700',
}

export default function Cobros() {
  const [reporte, setReporte] = useState<ReporteCuenta | null>(null)
  const [loading, setLoading] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [modal, setModal] = useState<{ open: boolean; cliente: Cliente | null }>({ open: false, cliente: null })
  const [factPendientes, setFactPendientes] = useState<Set<number>>(new Set())

  const cargarReporte = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get<ReporteCuenta>('/clientes/reporte-cuenta-corriente/')
      setReporte(data)
    } catch {
      toast.error('Error al cargar el reporte de deudas')
    } finally {
      setLoading(false)
    }
  }, [])

  const cargarFactPendientes = useCallback(async () => {
    try {
      const { data } = await api.get<{ cliente_id: number | null }[]>('/contabilidad/facturas/pendiente-facturar/')
      const ids = new Set(data.flatMap(f => f.cliente_id != null ? [f.cliente_id] : []))
      setFactPendientes(ids)
    } catch {
      // no crítico — solo indicador visual
    }
  }, [])

  useEffect(() => {
    cargarReporte()
    cargarFactPendientes()
  }, [cargarReporte, cargarFactPendientes])

  async function abrirCobrar(row: DeudorRow) {
    try {
      const { data } = await api.get<Cliente>(`/clientes/clientes/${row.cliente_id}/`)
      setModal({ open: true, cliente: data })
    } catch {
      toast.error('No se pudo cargar el cliente')
    }
  }

  const filas = (reporte?.clientes ?? []).filter(r =>
    r.cliente.toLowerCase().includes(busqueda.toLowerCase()) ||
    r.ruc_ci.includes(busqueda)
  )

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Cobranza</h1>
          <p className="text-slate-500 mt-0.5 text-sm">Clientes con saldo pendiente — registrá cobros y emitir recibos</p>
        </div>
        <button
          onClick={() => { cargarReporte(); cargarFactPendientes() }}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors text-sm font-medium cursor-pointer"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-1">Total deuda</p>
          <p className="text-2xl font-black tabular-nums text-orange-600">{formatGs(reporte?.total_deuda ?? 0)}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-1">Clientes con deuda</p>
          <p className="text-2xl font-black tabular-nums text-slate-800">{reporte?.clientes.length ?? 0}</p>
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-1">Vencidas +90 días</p>
          <p className="text-2xl font-black tabular-nums text-red-600">{formatGs(reporte?.aging_totales?.['90+'] ?? 0)}</p>
        </div>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            <input
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              placeholder="Buscar cliente o RUC/CI..."
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
            />
          </div>
          <p className="text-sm text-slate-400 shrink-0">{filas.length} cliente{filas.length !== 1 ? 's' : ''}</p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20 text-slate-400 text-sm">Cargando...</div>
        ) : filas.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
            <Users className="w-8 h-8 opacity-50" />
            <p className="text-sm">{busqueda ? 'Sin resultados para la búsqueda' : 'No hay clientes con deuda pendiente'}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/60">
                  <th className="text-left px-5 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wide">Cliente</th>
                  <th className="text-left px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wide">RUC / CI</th>
                  <th className="text-center px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wide">Antigüedad</th>
                  <th className="text-right px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wide">Deuda</th>
                  <th className="text-center px-4 py-3 font-semibold text-slate-500 text-xs uppercase tracking-wide" title="Tiene ítems pendientes de facturar">Fact.</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filas.map(row => (
                  <tr key={row.cliente_id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-5 py-3.5">
                      <p className="font-semibold text-slate-900">{row.cliente}</p>
                      {row.telefono && <p className="text-xs text-slate-400 mt-0.5">{row.telefono}</p>}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-600 text-xs">{row.ruc_ci || '—'}</td>
                    <td className="px-4 py-3.5 text-center">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold ${AGING_BADGE[row.aging] ?? 'bg-slate-100 text-slate-600'}`}>
                        {row.aging === '90+' && <AlertTriangle className="w-3 h-3" />}
                        {row.dias_atraso > 0 ? `${row.dias_atraso}d` : 'Reciente'}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right font-black tabular-nums text-orange-600">
                      {formatGs(row.saldo_deuda)}
                    </td>
                    <td className="px-4 py-3.5 text-center">
                      {factPendientes.has(row.cliente_id) && (
                        <span title="Tiene ítems pendientes de facturar">
                          <FileWarning className="w-4 h-4 text-amber-500 inline" />
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3.5">
                      <button
                        onClick={() => abrirCobrar(row)}
                        className="flex items-center gap-1.5 px-3.5 py-1.5 bg-green-600 hover:bg-green-500 text-white text-sm font-bold rounded-xl transition-colors cursor-pointer ml-auto"
                      >
                        <HandCoins className="w-4 h-4" />
                        Cobrar
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ModalPagarCC
        open={modal.open}
        cliente={modal.cliente}
        onClose={() => setModal({ open: false, cliente: null })}
        onSaved={() => { cargarReporte(); cargarFactPendientes() }}
      />
    </div>
  )
}
