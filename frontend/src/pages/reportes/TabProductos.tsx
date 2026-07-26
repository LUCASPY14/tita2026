import { useState } from 'react'
import toast from 'react-hot-toast'
import { Trophy, Search, Download, FileText } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import {
  formatGs, descargaBlob, fmtGsShort, today,
  FilterBar, EmptyState, KpiCard,
  type ProductosData, type ProductoVentaRanked,
} from './shared'

export default function TabProductos() {
  const t0 = today()
  const [desdeProd, setDesdeProd] = useState(t0)
  const [hastaProd, setHastaProd] = useState(t0)
  const [productosData, setProductosData] = useState<ProductosData | null>(null)
  const [loadingProd, setLoadingProd] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarProductos() {
    if (!desdeProd || !hastaProd) { toast.error('Seleccioná ambas fechas'); return }
    setLoadingProd(true)
    try {
      const { data: res } = await api.get('/ventas/reporte-productos/', { params: { desde: desdeProd, hasta: hastaProd } })
      setProductosData(res)
    } catch { setProductosData(null); toast.error('Error al cargar el reporte') }
    finally { setLoadingProd(false) }
  }

  async function exportarProductosCSV() {
    try {
      const res = await api.get('/ventas/reporte-productos/', {
        params: { desde: desdeProd, hasta: hastaProd, formato: 'csv' },
        responseType: 'blob',
      })
      descargaBlob(res.data, `ventas_producto_${desdeProd}_${hastaProd}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const productosRanked: ProductoVentaRanked[] = (productosData?.productos ?? []).map((p, i) => ({ ...p, rank: i + 1 }))

  const colsProductos: Column<ProductoVentaRanked>[] = [
    {
      title: '#', key: 'rank', dataIndex: 'rank',
      render: (v) => (
        <span className={`text-sm font-bold tabular-nums ${Number(v) <= 3 ? 'text-amber-600' : 'text-slate-400'}`}>
          {v as number}
        </span>
      ),
    },
    {
      title: 'Producto', key: 'descripcion',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.descripcion}</p>
          <p className="text-sm text-slate-400">{r.categoria || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Cantidad', key: 'total_cantidad', sortable: true,
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{r.total_cantidad}</span>,
    },
    {
      title: 'Nro Ventas', key: 'num_ventas', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{r.num_ventas}</span>,
    },
    {
      title: 'Total', key: 'total_monto', sortable: true,
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.total_monto)}</span>,
    },
  ]

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Desde</label>
          <input type="date" value={desdeProd} onChange={e => setDesdeProd(e.target.value)} className={inputDateClass} />
        </div>
        <div>
          <label className={labelClass}>Hasta</label>
          <input type="date" value={hastaProd} onChange={e => setHastaProd(e.target.value)} className={inputDateClass} />
        </div>
        <Button variant="primary" loading={loadingProd} onClick={buscarProductos}>
          <Search className="w-4 h-4" />Generar Reporte
        </Button>
        {productosData && (
          <>
            <Button variant="secondary" onClick={exportarProductosCSV} disabled={loadingProd}>
              <Download className="w-4 h-4" />CSV
            </Button>
            <Button variant="secondary" disabled={loadingProd} onClick={async () => {
              try {
                const res = await api.get('/ventas/reporte-productos/', {
                  params: { desde: desdeProd, hasta: hastaProd, formato: 'pdf' },
                  responseType: 'blob',
                })
                descargaBlob(res.data, `ventas_productos_${desdeProd}_${hastaProd}.pdf`)
                toast.success('PDF descargado')
              } catch { toast.error('Error al generar PDF') }
            }}>
              <FileText className="w-4 h-4" />PDF
            </Button>
          </>
        )}
      </FilterBar>

      {productosData && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <KpiCard label="Total Vendido" value={formatGs(productosData.total_monto)} color="text-emerald-700" />
            <KpiCard label="Productos distintos" value={productosData.productos.length} />
            <KpiCard label="Período" value={`${productosData.periodo.desde} — ${productosData.periodo.hasta}`} />
          </div>

          {productosData.productos.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
              <div className="px-6 py-4 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-800">Top 10 por monto vendido</h2>
              </div>
              <div className="p-4" style={{ height: `${Math.min(productosData.productos.length, 10) * 36 + 40}px`, minHeight: 200 }}>
                <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                  <BarChart
                    layout="vertical"
                    data={productosData.productos.slice(0, 10).map(p => ({
                      nombre: p.descripcion.length > 22 ? p.descripcion.slice(0, 22) + '…' : p.descripcion,
                      'Monto (k)': Math.round((Number(p.total_monto) || 0) / 1000),
                      Cantidad: p.total_cantidad,
                    }))}
                    margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#94a3b8' }}
                      tickFormatter={v => fmtGsShort(Number(v) * 1000)} />
                    <YAxis type="category" dataKey="nombre" width={140} tick={{ fontSize: 11, fill: '#64748b' }} />
                    <Tooltip
                      contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                      formatter={(v, name) =>
                        name === 'Monto (k)' ? [`${fmtGsShort((Number(v) || 0) * 1000)} Gs.`, 'Monto'] : [Number(v), 'Cantidad']
                      }
                    />
                    <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                    <Bar dataKey="Monto (k)" fill="#22c55e" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="text-sm font-semibold text-slate-800">Ranking completo</h2>
              <p className="text-sm text-slate-400 mt-0.5">Ordenado por monto vendido</p>
            </div>
            <div className="p-1">
              <Table columns={colsProductos} dataSource={productosRanked} rowKey="producto_id" pageSize={20} />
            </div>
          </div>
        </div>
      )}
      {!productosData && !loadingProd && <EmptyState icon={<Trophy className="w-full h-full" />} text="Seleccioná un período y generá el reporte" />}
    </>
  )
}
