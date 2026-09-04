import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { ChevronDown, ShoppingBag } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import { formatFechaConsumo, formatGsConsumo, type Hijo, type VentaConsumo } from './shared'

interface Props {
  open: boolean
  hijo: Hijo | null
  onClose: () => void
}

export default function ModalConsumo({ open, hijo, onClose }: Props) {
  const [ventas, setVentas] = useState<VentaConsumo[]>([])
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const PAGE_SIZE = 15

  const loadVentas = useCallback(async (p: number, append = false) => {
    if (!hijo) return
    if (append) { setLoadingMore(true) } else { setLoading(true) }
    try {
      const { data } = await api.get('/ventas/ventas/', {
        params: { hijo: hijo.id_hijo, page: p, page_size: PAGE_SIZE, ordering: '-fecha', estado: 'ACTIVA' },
      })
      setTotal(data.count ?? 0)
      setVentas(prev => append ? [...prev, ...(data.results ?? [])] : (data.results ?? []))
    } catch {
      toast.error('Error al cargar el historial de consumo')
    } finally {
      if (append) { setLoadingMore(false) } else { setLoading(false) }
    }
  }, [hijo])

  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPage(1)
      setExpandedId(null)
      loadVentas(1)
    }
  }, [open, loadVentas])

  function handleVerMas() {
    const next = page + 1
    setPage(next)
    loadVentas(next, true)
  }

  const totalGastado = ventas.reduce((s, v) => s + Number(v.monto_total), 0)

  return (
    <Modal
      open={open}
      title={`Consumo — ${hijo?.nombre ?? ''} ${hijo?.apellido ?? ''}`}
      onCancel={onClose}
      footer={null}
      width={600}
    >
      <div className="space-y-3">
        {loading ? (
          <Spinner className="py-10" />
        ) : ventas.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <ShoppingBag className="w-10 h-10 mx-auto mb-2 opacity-30" />
            <p className="text-sm font-medium">Sin compras registradas</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between bg-slate-50 rounded-xl px-4 py-2.5 text-sm">
              <span className="text-slate-500">{`${total} compra${total !== 1 ? 's' : ''}`}</span>
              <span className="font-semibold text-slate-700 tabular-nums">Mostradas: {formatGsConsumo(totalGastado)}</span>
            </div>

            <ul className="divide-y divide-slate-100 -mx-6 px-6">
              {ventas.map(v => {
                const isExp = expandedId === v.id_venta
                return (
                  <li key={v.id_venta} className="py-2.5">
                    <button
                      type="button"
                      onClick={() => setExpandedId(isExp ? null : v.id_venta)}
                      className="w-full flex items-center justify-between gap-3 text-left hover:bg-slate-50 rounded-xl px-3 py-2 -mx-3 transition-colors group"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-8 h-8 rounded-full bg-green-50 border border-green-100 flex items-center justify-center shrink-0">
                          <ShoppingBag className="w-3.5 h-3.5 text-green-600" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-800">
                            {`${v.detalles.length} ítem${v.detalles.length !== 1 ? 's' : ''}`}
                            {v.detalles.length > 0 && (
                              <span className="text-slate-400 font-normal">
                                {' '}· {v.detalles.slice(0, 2).map(d => d.producto_nombre).join(', ')}
                                {v.detalles.length > 2 ? '…' : ''}
                              </span>
                            )}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">{formatFechaConsumo(v.fecha)}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-sm font-bold text-slate-700 tabular-nums">{formatGsConsumo(v.monto_total)}</span>
                        <ChevronDown className={['w-4 h-4 text-slate-400 transition-transform duration-150', isExp ? 'rotate-180' : ''].join(' ')} />
                      </div>
                    </button>

                    {isExp && (
                      <div className="mt-1.5 ml-11 bg-slate-50 rounded-xl px-3 py-2 space-y-1.5">
                        {v.detalles.map(d => (
                          <div key={d.id_detalle_venta} className="flex items-baseline justify-between gap-3 text-sm">
                            <span className="text-slate-700 min-w-0">
                              <span className="font-semibold text-slate-500 tabular-nums mr-1.5">{Math.round(Number(d.cantidad))}×</span>
                              {d.producto_nombre}
                            </span>
                            <div className="shrink-0 text-right">
                              <span className="text-slate-500 text-xs tabular-nums">{formatGsConsumo(d.precio_unitario)} c/u</span>
                              <span className="font-semibold text-slate-800 tabular-nums ml-2">{formatGsConsumo(d.subtotal)}</span>
                            </div>
                          </div>
                        ))}
                        <div className="border-t border-slate-200 pt-1.5 flex justify-between text-sm">
                          <span className="text-slate-500 font-medium">Total</span>
                          <span className="font-bold text-slate-800 tabular-nums">{formatGsConsumo(v.monto_total)}</span>
                        </div>
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>

            {ventas.length < total && (
              <div className="pt-1 text-center">
                <button type="button" onClick={handleVerMas} disabled={loadingMore}
                  className="text-sm text-green-600 hover:text-green-700 font-medium disabled:opacity-50">
                  {loadingMore ? 'Cargando…' : `Ver más (${total - ventas.length} restantes)`}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  )
}
