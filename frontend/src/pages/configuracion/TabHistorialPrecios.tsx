import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Badge from '../../components/ui/Badge'
import Table, { type Column } from '../../components/ui/Table'
import Combobox from '../../components/ui/Combobox'
import { labelClass, type HistoricoPrecioItem, type Producto } from './helpers'

export default function TabHistorialPrecios() {
  const [historico, setHistorico] = useState<HistoricoPrecioItem[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [productoId, setProductoId] = useState<number | undefined>()
  const [productosLookup, setProductosLookup] = useState<Producto[]>([])
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdRef = useRef(0)

  const loadHistorico = useCallback(async (pid: number | undefined, p: number) => {
    const reqId = ++requestIdRef.current
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering: '-fecha_cambio' }
      if (pid) params.producto = pid
      const { data } = await api.get('/productos/historico-precios/', { params })
      if (reqId !== requestIdRef.current) return
      setHistorico(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (reqId !== requestIdRef.current) return
      toast.error('Error al cargar historial')
    } finally {
      if (reqId === requestIdRef.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => { setPage(1); loadHistorico(productoId, 1) }, 300)
    return () => clearTimeout(timerRef.current)
  }, [productoId, loadHistorico])

  useEffect(() => {
    api.get('/productos/productos/', { params: { page_size: 200 } })
      .then(({ data }) => setProductosLookup(data.results ?? []))
      .catch(() => {})
  }, [])

  const columns: Column<HistoricoPrecioItem>[] = [
    { title: 'Producto', key: 'prod', render: (_, r) => <span className="text-sm text-slate-800">{r.producto_nombre}</span> },
    { title: 'Precio anterior', key: 'ant', width: 150, render: (_, r) => <span className="tabular-nums text-sm text-slate-500">Gs. {(Number(r.precio_anterior) || 0).toLocaleString('es-PY')}</span> },
    { title: 'Precio nuevo', key: 'nuevo', width: 150, render: (_, r) => <span className="tabular-nums text-sm font-semibold text-emerald-700">Gs. {(Number(r.precio_nuevo) || 0).toLocaleString('es-PY')}</span> },
    {
      title: 'Variación', key: 'var', width: 100,
      render: (_, r) => {
        const v = Number(r.variacion_porcentual) || 0
        return <Badge color={v >= 0 ? 'orange' : 'green'}>{v >= 0 ? '+' : ''}{v}%</Badge>
      },
    },
    { title: 'Fecha', key: 'fecha', width: 140, render: (_, r) => <span className="text-xs text-slate-400 tabular-nums">{new Date(r.fecha_cambio).toLocaleDateString('es-PY')}</span> },
  ]

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
        <label className={labelClass}>Filtrar por producto</label>
        <div className="max-w-sm">
          <Combobox
            options={productosLookup.map(p => ({ value: p.id, label: p.descripcion }))}
            value={productoId}
            onChange={v => { setProductoId(v as number | undefined); setPage(1) }}
            placeholder="Todos los productos..."
          />
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table
            columns={columns}
            dataSource={historico}
            rowKey="id"
            loading={loading}
            pageSize={15}
            page={page}
            onPageChange={p => { setPage(p); loadHistorico(productoId, p) }}
            total={total}
          />
        </div>
      </div>
    </div>
  )
}
