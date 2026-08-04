import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { Users, Search, Download, FileText, AlertTriangle } from 'lucide-react'
import api from '../../services/api'
import { exportarCuentaCorrientePDF } from '../../utils/pdf'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import { formatGs, descargaBlob, clientSort, today, AGING_COLOR } from './reportesUtils'
import {
  EmptyState, KpiCard,
  type CuentaCorrienteData, type AgingItem,
} from './shared'

export default function TabCuentaCorriente() {
  const [ccData, setCcData] = useState<CuentaCorrienteData | null>(null)
  const [loadingCc, setLoadingCc] = useState(false)
  const [searchCc, setSearchCc] = useState('')
  const [sortDetalle, setSortDetalle] = useState<{ key: string; dir: 'asc' | 'desc' } | null>(null)

  async function cargarCuentaCorriente() {
    setLoadingCc(true)
    try {
      const { data: res } = await api.get('/clientes/reporte-cuenta-corriente/')
      setCcData(res)
    } catch { toast.error('Error al cargar cuenta corriente') }
    finally { setLoadingCc(false) }
  }

  // Carga de datos al montar: el setLoadingCc(true) inicial es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargarCuentaCorriente() }, [])

  async function exportarCuentaCorrienteCSV() {
    try {
      const res = await api.get('/clientes/reporte-cuenta-corriente/', { params: { formato: 'csv' }, responseType: 'blob' })
      const hoy2 = today()
      descargaBlob(res.data, `cuenta_corriente_${hoy2}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  async function exportarCuentaCorrienteExcel() {
    try {
      const res = await api.get('/clientes/reporte-cuenta-corriente/', { params: { formato: 'excel' }, responseType: 'blob' })
      const hoy2 = today()
      descargaBlob(res.data, `cuenta_corriente_${hoy2}.xlsx`)
      toast.success('Excel descargado')
    } catch { toast.error('Error al exportar') }
  }

  const ccDetalleFiltrado = (ccData?.detalle ?? []).filter(d =>
    !searchCc || d.cliente.toLowerCase().includes(searchCc.toLowerCase()) || d.ruc_ci.includes(searchCc)
  )
  const ccDetalleSorted = sortDetalle ? clientSort(ccDetalleFiltrado, sortDetalle.key, sortDetalle.dir) : ccDetalleFiltrado

  const colsDetalle: Column<AgingItem>[] = [
    {
      title: 'Cliente', key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.cliente}</p>
          <p className="text-sm text-slate-400">{r.ruc_ci}</p>
        </div>
      ),
    },
    {
      title: 'Contacto', key: 'contacto',
      render: (_, r) => (
        <div>
          <p className="text-sm text-slate-500">{r.telefono || '—'}</p>
          <p className="text-sm text-slate-400">{r.email || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Saldo Deuda', key: 'saldo_deuda', sortable: true,
      render: (_, r) => <span className="tabular-nums font-bold text-red-600">{formatGs(r.saldo_deuda)}</span>,
    },
    {
      title: 'Días Atraso', key: 'dias_atraso', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums font-semibold text-sm ${r.dias_atraso > 60 ? 'text-red-600' : r.dias_atraso > 30 ? 'text-orange-600' : 'text-slate-700'}`}>
          {r.dias_atraso}d
        </span>
      ),
    },
    {
      title: 'Aging', key: 'aging',
      render: (_, r) => <Badge color={AGING_COLOR[r.aging] ?? 'default'}>{r.aging}</Badge>,
    },
  ]

  return (
    <>
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <Button variant="secondary" loading={loadingCc} onClick={cargarCuentaCorriente}>
          <Search className="w-4 h-4" />Actualizar
        </Button>
        <div className="flex items-center gap-3">
          {ccData && <p className="text-sm text-slate-400">Generado: {new Date(ccData.fecha).toLocaleString('es-PY')}</p>}
          {ccData && ccDetalleSorted.length > 0 && (
            <>
              <Button variant="secondary" onClick={exportarCuentaCorrienteCSV}>
                <Download className="w-4 h-4" />CSV
              </Button>
              <Button variant="secondary" onClick={exportarCuentaCorrienteExcel}>
                <Download className="w-4 h-4" />Excel
              </Button>
              <Button variant="secondary" onClick={() => exportarCuentaCorrientePDF(ccDetalleSorted, ccData.resumen.total_deuda, ccData.fecha)}>
                <FileText className="w-4 h-4" />PDF
              </Button>
            </>
          )}
        </div>
      </div>

      {loadingCc && !ccData && <div className="text-center py-20 text-slate-400"><p className="text-sm">Cargando reporte...</p></div>}

      {ccData && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <KpiCard label="Total Deuda" value={formatGs(ccData.resumen.total_deuda)} color="text-red-700" />
            <KpiCard label="Clientes con Deuda" value={String(ccData.resumen.clientes_con_deuda)} />
            <KpiCard label="0–30 días" value={formatGs(ccData.resumen.aging['0-30'])} color="text-green-700" />
            <KpiCard label="90+ días" value={formatGs(ccData.resumen.aging['90+'])} color="text-red-600" />
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">Distribución por Aging</h3>
            <div className="grid grid-cols-4 gap-3">
              {Object.entries(ccData.resumen.aging).map(([rango, monto]) => (
                <div key={rango} className="text-center">
                  <p className="text-sm text-slate-400">{rango} días</p>
                  <p className={`text-sm font-bold tabular-nums mt-0.5 ${
                    rango === '90+' ? 'text-red-600' : rango === '61-90' ? 'text-orange-600' : rango === '31-60' ? 'text-yellow-600' : 'text-green-700'
                  }`}>{formatGs(monto)}</p>
                </div>
              ))}
            </div>
          </div>

          {ccData.resumen.aging['90+'] > 0 && (
            <div className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-2xl px-5 py-3">
              <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-700">
                <span className="font-semibold">{formatGs(ccData.resumen.aging['90+'])}</span> en deudas con más de 90 días de atraso.
              </p>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800">Detalle de Cuenta Corriente</h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                <input
                  placeholder="Filtrar cliente..."
                  value={searchCc}
                  onChange={e => setSearchCc(e.target.value)}
                  className="border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-48"
                />
              </div>
            </div>
            <div className="p-1">
              <Table columns={colsDetalle} dataSource={ccDetalleSorted} rowKey="cliente_id" pageSize={15}
                sortKey={sortDetalle?.key} sortDir={sortDetalle?.dir}
                onSort={(key, dir) => setSortDetalle({ key, dir })} />
            </div>
          </div>
        </div>
      )}
      {!ccData && !loadingCc && <EmptyState icon={<Users className="w-full h-full" />} text='Hacé clic en "Actualizar" para cargar el reporte' />}
    </>
  )
}
