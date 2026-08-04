import { useState } from 'react'
import toast from 'react-hot-toast'
import { FileText, Search, Download } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import { formatGs, descargaBlob, today, NC_ESTADO_COLOR } from './reportesUtils'
import {
  FilterBar, EmptyState, KpiCard,
  type NCVentaData, type NCCompraData,
} from './shared'

export default function TabNotasCredito() {
  const t0 = today()
  const [ncDesde, setNcDesde] = useState(t0.slice(0, 7) + '-01')
  const [ncHasta, setNcHasta] = useState(t0)
  const [ncSubtab, setNcSubtab] = useState<'ventas' | 'compras'>('ventas')
  const [ncVentaData, setNcVentaData] = useState<NCVentaData | null>(null)
  const [ncCompraData, setNcCompraData] = useState<NCCompraData | null>(null)
  const [loadingNc, setLoadingNc] = useState(false)
  const [searchNc, setSearchNc] = useState('')

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarNC() {
    if (!ncDesde || !ncHasta) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingNc(true)
    try {
      const [ventaRes, compraRes] = await Promise.all([
        api.get('/ventas/reporte-notas-credito/', { params: { desde: ncDesde, hasta: ncHasta } }),
        api.get('/compras/reporte-notas-credito/', { params: { desde: ncDesde, hasta: ncHasta } }),
      ])
      setNcVentaData(ventaRes.data)
      setNcCompraData(compraRes.data)
    } catch { toast.error('Error al cargar notas de crédito') }
    finally { setLoadingNc(false) }
  }

  async function exportarNcCSV() {
    try {
      const endpoint = ncSubtab === 'ventas' ? '/ventas/reporte-notas-credito/' : '/compras/reporte-notas-credito/'
      const res = await api.get(endpoint, { params: { desde: ncDesde, hasta: ncHasta, formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, `notas_credito_${ncSubtab}_${ncDesde}_${ncHasta}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const ncVentasFiltradas = (ncVentaData?.detalle ?? []).filter(f =>
    !searchNc || f.cliente.toLowerCase().includes(searchNc.toLowerCase()) || f.nro_nota_credito.includes(searchNc)
  )
  const ncComprasFiltradas = (ncCompraData?.detalle ?? []).filter(f =>
    !searchNc || f.proveedor.toLowerCase().includes(searchNc.toLowerCase())
  )

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Desde</label>
          <input type="date" value={ncDesde} onChange={e => setNcDesde(e.target.value)} className={inputDateClass} />
        </div>
        <div>
          <label className={labelClass}>Hasta</label>
          <input type="date" value={ncHasta} onChange={e => setNcHasta(e.target.value)} className={inputDateClass} />
        </div>
        <Button onClick={buscarNC} loading={loadingNc}>Buscar</Button>
        {(ncVentaData || ncCompraData) && (
          <Button variant="secondary" onClick={exportarNcCSV}>
            <Download className="w-4 h-4" />CSV
          </Button>
        )}
      </FilterBar>

      {(ncVentaData || ncCompraData) && (
        <>
          <div className="border-b border-slate-200">
            <div className="flex gap-0">
              <button
                onClick={() => { setNcSubtab('ventas'); setSearchNc('') }}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${ncSubtab === 'ventas' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
              >
                Notas a Clientes {ncVentaData && `(${ncVentaData.detalle.length})`}
              </button>
              <button
                onClick={() => { setNcSubtab('compras'); setSearchNc('') }}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${ncSubtab === 'compras' ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
              >
                Notas de Proveedores {ncCompraData && `(${ncCompraData.detalle.length})`}
              </button>
            </div>
          </div>

          {ncSubtab === 'ventas' && ncVentaData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard label="Emitidas" value={`${ncVentaData.resumen.total_emitidas} (${formatGs(ncVentaData.resumen.monto_emitidas)})`} />
                <KpiCard label="Aplicadas" value={`${ncVentaData.resumen.total_aplicadas} (${formatGs(ncVentaData.resumen.monto_aplicadas)})`} color="text-green-700" />
                <KpiCard label="Anuladas" value={`${ncVentaData.resumen.total_anuladas} (${formatGs(ncVentaData.resumen.monto_anuladas)})`} color="text-slate-400" />
                <KpiCard label="Monto activo" value={formatGs(ncVentaData.resumen.monto_total)} color="text-blue-700" />
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="text" placeholder="Buscar cliente o N° NC…"
                      value={searchNc} onChange={e => setSearchNc(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                    />
                  </div>
                </div>
                {ncVentasFiltradas.length === 0
                  ? <EmptyState icon={<FileText className="w-full h-full" />} text="Sin notas de crédito en el período" />
                  : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-100 text-left">
                            {['N° NC', 'Fecha', 'Cliente', 'Estado', 'Motivo', 'Autorizado por', 'Monto'].map(h => (
                              <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                          {ncVentasFiltradas.map(f => (
                            <tr key={f.id} className="hover:bg-slate-50 transition-colors">
                              <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">{f.nro_nota_credito}</td>
                              <td className="py-2.5 pr-4 text-slate-600 whitespace-nowrap">{f.fecha_emision}</td>
                              <td className="py-2.5 pr-4">
                                <p className="font-medium text-slate-800">{f.cliente}</p>
                                <p className="text-xs text-slate-400">{f.ruc_ci}</p>
                              </td>
                              <td className="py-2.5 pr-4">
                                <Badge color={NC_ESTADO_COLOR[f.estado] ?? 'gray'}>{f.estado}</Badge>
                              </td>
                              <td className="py-2.5 pr-4 text-slate-600 max-w-[200px] truncate" title={f.motivo}>{f.motivo}</td>
                              <td className="py-2.5 pr-4 text-slate-600">{f.empleado_autoriza || '—'}</td>
                              <td className="py-2.5 tabular-nums font-bold text-red-600">{formatGs(f.monto_total)}</td>
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

          {ncSubtab === 'compras' && ncCompraData && (
            <>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <KpiCard label="Emitidas" value={`${ncCompraData.resumen.total_emitidas} (${formatGs(ncCompraData.resumen.monto_emitidas)})`} />
                <KpiCard label="Aplicadas" value={`${ncCompraData.resumen.total_aplicadas} (${formatGs(ncCompraData.resumen.monto_aplicadas)})`} color="text-green-700" />
                <KpiCard label="Anuladas" value={`${ncCompraData.resumen.total_anuladas} (${formatGs(ncCompraData.resumen.monto_anuladas)})`} color="text-slate-400" />
                <KpiCard label="Monto activo" value={formatGs(ncCompraData.resumen.monto_total)} color="text-blue-700" />
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="relative flex-1 max-w-xs">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input
                      type="text" placeholder="Buscar proveedor…"
                      value={searchNc} onChange={e => setSearchNc(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
                    />
                  </div>
                </div>
                {ncComprasFiltradas.length === 0
                  ? <EmptyState icon={<FileText className="w-full h-full" />} text="Sin notas de crédito de proveedores en el período" />
                  : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-100 text-left">
                            {['Fecha', 'Proveedor', 'Estado', 'Observación', 'N° Factura', 'Registrado por', 'Monto'].map(h => (
                              <th key={h} className="pb-2 pr-4 text-xs font-semibold text-slate-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-50">
                          {ncComprasFiltradas.map(f => (
                            <tr key={f.id} className="hover:bg-slate-50 transition-colors">
                              <td className="py-2.5 pr-4 text-slate-600 whitespace-nowrap">{f.fecha}</td>
                              <td className="py-2.5 pr-4">
                                <p className="font-medium text-slate-800">{f.proveedor}</p>
                                <p className="text-xs text-slate-400">{f.ruc}</p>
                              </td>
                              <td className="py-2.5 pr-4">
                                <Badge color={NC_ESTADO_COLOR[f.estado] ?? 'gray'}>{f.estado}</Badge>
                              </td>
                              <td className="py-2.5 pr-4 text-slate-600 max-w-[180px] truncate" title={f.observacion}>{f.observacion || '—'}</td>
                              <td className="py-2.5 pr-4 font-mono text-xs text-slate-500">{f.nro_factura_compra || '—'}</td>
                              <td className="py-2.5 pr-4 text-slate-600">{f.creado_por || '—'}</td>
                              <td className="py-2.5 tabular-nums font-bold text-green-700">{formatGs(f.monto_total)}</td>
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
        </>
      )}

      {!ncVentaData && !ncCompraData && !loadingNc && (
        <EmptyState icon={<FileText className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Buscar"' />
      )}
    </>
  )
}
