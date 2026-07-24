import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { ShoppingCart, AlertTriangle, Search, Download } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import {
  formatGs, descargaBlob, today,
  AGING_COLOR,
  EmptyState, KpiCard,
  type AgingProveedoresData,
} from './shared'

export default function TabAgingProveedores() {
  const [apData, setApData] = useState<AgingProveedoresData | null>(null)
  const [loadingAp, setLoadingAp] = useState(false)
  const [searchAp, setSearchAp] = useState('')

  async function cargarAgingProveedores() {
    setLoadingAp(true)
    try {
      const { data: res } = await api.get('/compras/reporte-aging-proveedores/')
      setApData(res)
    } catch { toast.error('Error al cargar aging de proveedores') }
    finally { setLoadingAp(false) }
  }

  useEffect(() => { cargarAgingProveedores() }, [])

  async function exportarApCSV() {
    try {
      const res = await api.get('/compras/reporte-aging-proveedores/', { params: { formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `aging_proveedores_${today()}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  async function exportarApExcel() {
    try {
      const res = await api.get('/compras/reporte-aging-proveedores/', { params: { formato: 'excel' }, responseType: 'blob' })
      descargaBlob(res.data, `aging_proveedores_${today()}.xlsx`)
      toast.success('Excel descargado')
    } catch { toast.error('Error al exportar') }
  }

  const apDetalleFiltrado = (apData?.detalle ?? []).filter(d =>
    !searchAp || d.proveedor.toLowerCase().includes(searchAp.toLowerCase()) || d.ruc.includes(searchAp)
  )
  const apDetalleSorted = apDetalleFiltrado.slice().sort((a, b) => b.saldo_deuda - a.saldo_deuda)

  return (
    <>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button onClick={cargarAgingProveedores} loading={loadingAp}>Actualizar</Button>
          {apData && (
            <>
              <Button variant="secondary" onClick={exportarApCSV}>
                <Download className="w-4 h-4" />CSV
              </Button>
              <Button variant="secondary" onClick={exportarApExcel}>
                <Download className="w-4 h-4" />Excel
              </Button>
            </>
          )}
        </div>
        {apData && (
          <p className="text-sm text-slate-400">Al {apData.fecha}</p>
        )}
      </div>

      {apData && (
        <>
          {apData.resumen.proveedores_con_deuda > 0 && apData.resumen.aging['90+'] > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-2xl px-4 py-3 flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
              <p className="text-sm text-red-700 font-medium">
                {`Hay deuda con proveedores mayor a 90 días: ${formatGs(apData.resumen.aging['90+'])}`}
              </p>
            </div>
          )}

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <KpiCard label="Total a pagar" value={formatGs(apData.resumen.total_deuda)} color="text-red-600" />
            <KpiCard label="Proveedores" value={apData.resumen.proveedores_con_deuda} />
            <KpiCard label="0–30 días" value={formatGs(apData.resumen.aging['0-30'])} color="text-green-700" />
            <KpiCard label="+90 días" value={formatGs(apData.resumen.aging['90+'])} color="text-red-600" />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {(['0-30', '31-60', '61-90', '90+'] as const).map(bucket => (
              <div key={bucket} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
                <Badge color={AGING_COLOR[bucket]}>{bucket} días</Badge>
                <p className="text-lg font-bold tabular-nums mt-2 text-slate-800">{formatGs(apData.resumen.aging[bucket])}</p>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="relative flex-1 max-w-xs">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text" placeholder="Buscar proveedor o RUC…"
                  value={searchAp} onChange={e => setSearchAp(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                />
              </div>
            </div>
            {apDetalleSorted.length === 0
              ? <EmptyState icon={<ShoppingCart className="w-full h-full" />} text="Sin proveedores con deuda pendiente" />
              : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Proveedor', 'Contacto', 'Saldo (Gs)', 'Días', 'Aging'].map(h => (
                          <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {apDetalleSorted.map(r => (
                        <tr key={r.proveedor_id} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 pr-4">
                            <p className="font-medium text-slate-800">{r.proveedor}</p>
                            <p className="text-xs text-slate-400">{r.ruc || '—'}</p>
                          </td>
                          <td className="py-2.5 pr-4 text-sm text-slate-500">
                            {r.telefono && <p>{r.telefono}</p>}
                            {r.email && <p>{r.email}</p>}
                            {!r.telefono && !r.email && <span className="text-slate-300">—</span>}
                          </td>
                          <td className="py-2.5 pr-4 tabular-nums font-bold text-red-600">{formatGs(r.saldo_deuda)}</td>
                          <td className="py-2.5 pr-4 tabular-nums text-slate-600">{r.dias_atraso}d</td>
                          <td className="py-2.5"><Badge color={AGING_COLOR[r.aging] ?? 'gray'}>{r.aging}</Badge></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            }
          </div>
        </>
      )}

      {!apData && !loadingAp && (
        <EmptyState icon={<ShoppingCart className="w-full h-full" />} text="Hacé clic en Actualizar para cargar el reporte" />
      )}
    </>
  )
}
