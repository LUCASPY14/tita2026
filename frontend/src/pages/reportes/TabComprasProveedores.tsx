import { useState } from 'react'
import toast from 'react-hot-toast'
import { ShoppingBag, Search, Download } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import {
  formatGs, descargaBlob, today, primerDiaMes,
  FilterBar, EmptyState, KpiCard,
  type ComprasProveedoresData,
} from './shared'

export default function TabComprasProveedores() {
  const [cpDesde, setCpDesde] = useState(primerDiaMes())
  const [cpHasta, setCpHasta] = useState(today())
  const [cpData, setCpData] = useState<ComprasProveedoresData | null>(null)
  const [loadingCp, setLoadingCp] = useState(false)
  const [searchCp, setSearchCp] = useState('')

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarCompras() {
    if (!cpDesde || !cpHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingCp(true)
    try {
      const { data: res } = await api.get('/compras/reporte-compras/', { params: { desde: cpDesde, hasta: cpHasta } })
      setCpData(res)
    } catch { toast.error('Error al cargar reporte de compras') }
    finally { setLoadingCp(false) }
  }

  async function exportarCpCSV() {
    try {
      const res = await api.get('/compras/reporte-compras/', { params: { desde: cpDesde, hasta: cpHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `compras_proveedores_${cpDesde}_${cpHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const cpFiltrado = (cpData?.por_proveedor ?? []).filter(p =>
    !searchCp || p.proveedor.toLowerCase().includes(searchCp.toLowerCase()) || p.ruc.includes(searchCp)
  )

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Desde</label>
          <input type="date" value={cpDesde} onChange={e => setCpDesde(e.target.value)} className={inputDateClass} />
        </div>
        <div>
          <label className={labelClass}>Hasta</label>
          <input type="date" value={cpHasta} onChange={e => setCpHasta(e.target.value)} className={inputDateClass} />
        </div>
        <Button onClick={buscarCompras} loading={loadingCp}>Buscar</Button>
        {cpData && (
          <Button variant="secondary" onClick={exportarCpCSV}><Download className="w-4 h-4" />CSV</Button>
        )}
      </FilterBar>

      {cpData && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <KpiCard label="Total comprado" value={formatGs(cpData.resumen.monto_total)} color="text-blue-700" />
            <KpiCard label="Compras" value={cpData.resumen.total_compras} />
            <KpiCard label="Proveedores" value={cpData.resumen.n_proveedores} />
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
            <p className="text-sm font-semibold text-slate-700 mb-3">Funnel Órdenes de Compra — {cpData.periodo.desde} al {cpData.periodo.hasta}</p>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {([
                { key: 'BORRADOR', label: 'Borrador', color: 'text-slate-500' },
                { key: 'PENDIENTE', label: 'Pendiente', color: 'text-yellow-600' },
                { key: 'APROBADA', label: 'Aprobada', color: 'text-blue-600' },
                { key: 'RECHAZADA', label: 'Rechazada', color: 'text-red-600' },
                { key: 'CONVERTIDA', label: 'Convertida', color: 'text-green-700' },
              ] as const).map(({ key, label, color }) => (
                <div key={key} className="text-center">
                  <p className={`text-2xl font-bold tabular-nums ${color}`}>{cpData.funnel_oc[key]}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{label}</p>
                </div>
              ))}
            </div>
            {cpData.funnel_oc.total > 0 && (
              <p className="text-xs text-slate-400 mt-3 text-right">
                Tasa de conversión: {cpData.funnel_oc.total > 0 ? Math.round(cpData.funnel_oc.CONVERTIDA / cpData.funnel_oc.total * 100) : 0}%
              </p>
            )}
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
            <div className="flex items-center gap-3 mb-4">
              <p className="text-sm font-semibold text-slate-700 flex-1">Gasto y entrega por proveedor</p>
              <div className="relative max-w-xs w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text" placeholder="Buscar proveedor…"
                  value={searchCp} onChange={e => setSearchCp(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                />
              </div>
            </div>
            {cpFiltrado.length === 0
              ? <EmptyState icon={<ShoppingBag className="w-full h-full" />} text="Sin compras en el período" />
              : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left">
                        {['Proveedor', 'N° Compras', 'Monto Total', 'Entregadas', '% Entrega', 'Pagadas'].map(h => (
                          <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {cpFiltrado.map(p => (
                        <tr key={p.proveedor_id} className="hover:bg-slate-50 transition-colors">
                          <td className="py-2.5 pr-4">
                            <p className="font-medium text-slate-800">{p.proveedor}</p>
                            <p className="text-xs text-slate-400">{p.ruc || '—'}</p>
                          </td>
                          <td className="py-2.5 pr-4 tabular-nums text-slate-600">{p.n_compras}</td>
                          <td className="py-2.5 pr-4 tabular-nums font-bold text-blue-700">{formatGs(p.monto_total)}</td>
                          <td className="py-2.5 pr-4">
                            <span className="tabular-nums text-slate-600">{p.entregadas}</span>
                            {p.entrega_pendiente > 0 && (
                              <span className="ml-1.5 text-xs text-orange-500">({p.entrega_pendiente} pend.)</span>
                            )}
                          </td>
                          <td className="py-2.5 pr-4">
                            <span className={`tabular-nums font-semibold text-sm ${p.tasa_entrega >= 90 ? 'text-green-700' : p.tasa_entrega >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                              {p.tasa_entrega}%
                            </span>
                          </td>
                          <td className="py-2.5">
                            <span className="tabular-nums text-slate-600">{p.pagadas}</span>
                            {p.pago_pendiente > 0 && (
                              <span className="ml-1.5 text-xs text-red-500">({p.pago_pendiente} pend.)</span>
                            )}
                          </td>
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

      {!cpData && !loadingCp && (
        <EmptyState icon={<ShoppingBag className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
      )}
    </>
  )
}
