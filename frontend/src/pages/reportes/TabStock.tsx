import { useState } from 'react'
import toast from 'react-hot-toast'
import { Package, Search, Download, FileText, AlertTriangle } from 'lucide-react'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import { formatGs, descargaBlob } from './reportesUtils'
import {
  EmptyState, KpiCard,
  type StockData, type ProductoStock,
} from './shared'

export default function TabStock() {
  const [stockData, setStockData] = useState<StockData | null>(null)
  const [loadingStock, setLoadingStock] = useState(false)
  const [searchStock, setSearchStock] = useState('')

  async function cargarStock() {
    setLoadingStock(true)
    try {
      const { data: res } = await api.get('/inventario/reporte-stock/')
      setStockData(res)
    } catch { setStockData(null); toast.error('Error al cargar inventario') }
    finally { setLoadingStock(false) }
  }

  async function exportarStockCSV() {
    try {
      const res = await api.get('/inventario/reporte-stock/', { params: { formato: 'csv' }, responseType: 'blob' })
      descargaBlob(res.data, 'reporte_stock.csv')
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  const stockFiltrado = (stockData?.productos ?? []).filter(p =>
    !searchStock || p.descripcion.toLowerCase().includes(searchStock.toLowerCase()) || p.categoria.toLowerCase().includes(searchStock.toLowerCase())
  )

  const colsStock: Column<ProductoStock>[] = [
    {
      title: 'Producto', key: 'descripcion',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.descripcion}</p>
          <p className="text-sm text-slate-400">{r.categoria || '—'} {r.unidad ? `· ${r.unidad}` : ''}</p>
        </div>
      ),
    },
    {
      title: 'Stock', key: 'stock_actual', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums font-bold text-sm ${r.requiere_reposicion ? 'text-red-600' : 'text-slate-800'}`}>
          {r.stock_actual}
        </span>
      ),
    },
    {
      title: 'Mínimo', key: 'stock_minimo',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-500">{r.stock_minimo}</span>,
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => (
        <Badge color={r.requiere_reposicion ? 'red' : 'green'}>
          {r.requiere_reposicion ? 'Bajo mínimo' : 'OK'}
        </Badge>
      ),
    },
    {
      title: 'Costo Prom.', key: 'costo_promedio', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-600">{formatGs(r.costo_promedio)}</span>,
    },
    {
      title: 'Valor Inv.', key: 'valor_inventario', sortable: true,
      render: (_, r) => <span className="tabular-nums text-sm font-semibold text-slate-800">{formatGs(r.valor_inventario)}</span>,
    },
    {
      title: 'Días Stock', key: 'dias_stock', sortable: true,
      render: (_, r) => (
        <span className={`tabular-nums text-sm ${r.dias_stock !== null && r.dias_stock < 7 ? 'text-red-600 font-bold' : 'text-slate-600'}`}>
          {r.dias_stock !== null ? `${r.dias_stock}d` : '—'}
        </span>
      ),
    },
  ]

  return (
    <>
      <div className="flex items-center gap-3 flex-wrap">
        <Button variant="primary" loading={loadingStock} onClick={cargarStock}>
          <Search className="w-4 h-4" />Cargar Inventario
        </Button>
        {stockData && (
          <>
            <Button variant="secondary" onClick={exportarStockCSV} disabled={loadingStock}>
              <Download className="w-4 h-4" />CSV
            </Button>
            <Button variant="secondary" disabled={loadingStock} onClick={async () => {
              try {
                const res = await api.get('/inventario/reporte-stock/', { params: { formato: 'pdf' }, responseType: 'blob' })
                descargaBlob(res.data, 'reporte_stock.pdf')
                toast.success('PDF descargado')
              } catch { toast.error('Error al generar PDF') }
            }}>
              <FileText className="w-4 h-4" />PDF
            </Button>
          </>
        )}
      </div>

      {stockData && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <KpiCard label="Total productos" value={stockData.resumen.total_productos} />
            <KpiCard
              label="Bajo mínimo"
              value={stockData.resumen.productos_bajo_minimo}
              color={stockData.resumen.productos_bajo_minimo > 0 ? 'text-red-600' : 'text-emerald-700'}
            />
            <KpiCard label="Valor total inventario" value={formatGs(stockData.resumen.valor_total_inventario)} color="text-slate-800" />
          </div>

          {stockData.resumen.productos_bajo_minimo > 0 && (
            <div className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-2xl px-5 py-3">
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
              <p className="text-sm text-amber-800">
                <span className="font-semibold">{stockData.resumen.productos_bajo_minimo} productos</span> con stock por debajo del mínimo configurado.
              </p>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800">Inventario completo</h2>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-400 pointer-events-none" />
                <input
                  placeholder="Filtrar producto/categoría..."
                  value={searchStock}
                  onChange={e => setSearchStock(e.target.value)}
                  className="border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-52"
                />
              </div>
            </div>
            <div className="p-1">
              <Table columns={colsStock} dataSource={stockFiltrado} rowKey="producto_id" pageSize={20} />
            </div>
          </div>
        </div>
      )}
      {!stockData && !loadingStock && <EmptyState icon={<Package className="w-full h-full" />} text='Hacé clic en "Cargar Inventario"' />}
    </>
  )
}
