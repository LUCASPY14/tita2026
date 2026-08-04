import { useState } from 'react'
import toast from 'react-hot-toast'
import { CreditCard, Search, Download, FileText } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import { formatGs, descargaBlob } from './reportesUtils'
import {
  FilterBar, EmptyState, KpiCard,
  type TarjetasData, type TarjetaReporte,
} from './shared'

export default function TabTarjetas() {
  const [desdeTarj, setDesdeTarj] = useState('')
  const [hastaTarj, setHastaTarj] = useState('')
  const [tarjetasData, setTarjetasData] = useState<TarjetasData | null>(null)
  const [loadingTarj, setLoadingTarj] = useState(false)
  const [searchTarj, setSearchTarj] = useState('')

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function cargarTarjetas() {
    setLoadingTarj(true)
    try {
      const params: Record<string, string> = {}
      if (desdeTarj) params.desde = desdeTarj
      if (hastaTarj) params.hasta = hastaTarj
      const { data: res } = await api.get('/core/reporte-tarjetas/', { params })
      setTarjetasData(res)
    } catch { setTarjetasData(null); toast.error('Error al cargar tarjetas') }
    finally { setLoadingTarj(false) }
  }

  async function exportarTarjetasCSV() {
    try {
      const params: Record<string, string> = { formato: 'csv' }
      if (desdeTarj) params.desde = desdeTarj
      if (hastaTarj) params.hasta = hastaTarj
      const res = await api.get('/core/reporte-tarjetas/', { params, responseType: 'blob' })
      const sufijo = desdeTarj && hastaTarj ? `_${desdeTarj}_${hastaTarj}` : ''
      descargaBlob(res.data, `reporte_tarjetas${sufijo}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const tarjetasFiltradas = (tarjetasData?.tarjetas ?? []).filter(t =>
    !searchTarj || t.alumno.toLowerCase().includes(searchTarj.toLowerCase()) || t.grado.toLowerCase().includes(searchTarj.toLowerCase())
  )

  const colsTarjetas: Column<TarjetaReporte>[] = [
    {
      title: 'Alumno', key: 'alumno',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.alumno}</p>
          <p className="text-sm text-slate-400">{r.grado || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Saldo Actual', key: 'saldo_actual', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums font-bold text-sm ${r.saldo_actual < 0 ? 'text-red-600' : r.saldo_actual === 0 ? 'text-slate-400' : 'text-emerald-700'}`}>
          {formatGs(r.saldo_actual)}
        </span>
      ),
    },
    {
      title: 'Recargado', key: 'total_recargado', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-blue-700">{formatGs(r.total_recargado)}</span>,
    },
    {
      title: 'Consumido', key: 'total_consumido', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.total_consumido)}</span>,
    },
    {
      title: 'Recargas', key: 'num_recargas',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{r.num_recargas}</span>,
    },
    {
      title: 'Consumos', key: 'num_consumos',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{r.num_consumos}</span>,
    },
    {
      title: 'Tarjeta', key: 'nro_tarjeta',
      render: (_, r) => <span className="text-sm font-mono text-slate-400">{r.nro_tarjeta}</span>,
    },
  ]

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Desde (opcional)</label>
          <input type="date" value={desdeTarj} onChange={e => setDesdeTarj(e.target.value)} className={inputDateClass} />
        </div>
        <div>
          <label className={labelClass}>Hasta (opcional)</label>
          <input type="date" value={hastaTarj} onChange={e => setHastaTarj(e.target.value)} className={inputDateClass} />
        </div>
        <Button variant="primary" loading={loadingTarj} onClick={cargarTarjetas}>
          <Search className="w-4 h-4" />Generar Reporte
        </Button>
        {tarjetasData && (
          <>
            <Button variant="secondary" onClick={exportarTarjetasCSV} disabled={loadingTarj}>
              <Download className="w-4 h-4" />CSV
            </Button>
            <Button variant="secondary" disabled={loadingTarj} onClick={async () => {
              try {
                const params: Record<string, string> = { formato: 'pdf' }
                if (desdeTarj) params.desde = desdeTarj
                if (hastaTarj) params.hasta = hastaTarj
                const res = await api.get('/core/reporte-tarjetas/', { params, responseType: 'blob' })
                const sufijo = desdeTarj && hastaTarj ? `_${desdeTarj}_${hastaTarj}` : ''
                descargaBlob(res.data, `reporte_tarjetas${sufijo}.pdf`)
                toast.success('PDF descargado')
              } catch { toast.error('Error al generar PDF') }
            }}>
              <FileText className="w-4 h-4" />PDF
            </Button>
          </>
        )}
      </FilterBar>

      {!desdeTarj && !hastaTarj && !tarjetasData && (
        <p className="text-sm text-slate-400 -mt-2">Sin período: se muestran solo saldos actuales sin detalle de movimientos.</p>
      )}

      {tarjetasData && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <KpiCard label="Tarjetas activas" value={tarjetasData.resumen.total_tarjetas} />
            <KpiCard label="Saldo total" value={formatGs(tarjetasData.resumen.saldo_total)} color="text-emerald-700" />
            <KpiCard label="Total recargado" value={formatGs(tarjetasData.resumen.total_recargado)} color="text-blue-700" />
            <KpiCard label="Total consumido" value={formatGs(tarjetasData.resumen.total_consumido)} color="text-slate-700" />
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800">
                Tarjetas ({tarjetasData.resumen.total_tarjetas})
                {tarjetasData.periodo.desde && (
                  <span className="text-sm text-slate-400 font-normal ml-2">
                    {tarjetasData.periodo.desde} — {tarjetasData.periodo.hasta}
                  </span>
                )}
              </h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                <input
                  placeholder="Filtrar alumno/grado..."
                  value={searchTarj}
                  onChange={e => setSearchTarj(e.target.value)}
                  className="border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-52"
                />
              </div>
            </div>
            <div className="p-1">
              <Table columns={colsTarjetas} dataSource={tarjetasFiltradas} rowKey="nro_tarjeta" pageSize={20} />
            </div>
          </div>
        </div>
      )}
      {!tarjetasData && !loadingTarj && <EmptyState icon={<CreditCard className="w-full h-full" />} text='Hacé clic en "Generar Reporte" para cargar tarjetas' />}
    </>
  )
}
