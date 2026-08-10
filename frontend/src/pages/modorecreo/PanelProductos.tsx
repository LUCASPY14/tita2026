import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, ShoppingCart, X, Plus, Minus } from 'lucide-react'
import {
  gs, catMeta, esPorPeso, parseCantidadDecimal, formatCantidad,
  type Producto, type RestriccionHijo, type ItemCarrito, type DailyStats,
} from './shared'

interface Props {
  loadingProductos: boolean
  categorias: string[]
  catFiltro: string
  prodSearch: string
  productosFiltrados: Producto[]
  favoritos: Producto[]
  addedProductId: number | null
  prodSearchRef: React.RefObject<HTMLInputElement | null>
  getPrecio: (p: Producto) => number
  isRestricto: (p: Producto) => RestriccionHijo | null
  onCatFiltro: (c: string) => void
  onProdSearch: (s: string) => void
  onAgregar: (p: Producto) => void
  onScannerFocus: () => void
  carrito: ItemCarrito[]
  dailyStats: DailyStats
  avgTime: string
  onSetCarrito: React.Dispatch<React.SetStateAction<ItemCarrito[]>>
  onQuitar: (id: number) => void
  onSetCantidad: (id: number, cantidad: number) => void
}

export default function PanelProductos({
  loadingProductos, categorias, catFiltro, prodSearch,
  productosFiltrados, favoritos, addedProductId,
  prodSearchRef, getPrecio, isRestricto,
  onCatFiltro, onProdSearch, onAgregar, onScannerFocus,
  carrito, dailyStats, avgTime, onSetCarrito, onQuitar, onSetCantidad,
}: Props) {
  const { t } = useTranslation()
  const [focused, setFocused] = useState(false)
  const [cantidadTexto, setCantidadTexto] = useState<Record<number, string>>({})

  function commitCantidad(id: number, texto: string) {
    const parsed = parseCantidadDecimal(texto)
    if (parsed !== null) onSetCantidad(id, parsed)
    setCantidadTexto(prev => { const next = { ...prev }; delete next[id]; return next })
  }

  return (
    <main className="flex-1 min-w-[420px] flex flex-col overflow-hidden bg-slate-50">
      <div className="px-4 pt-2 pb-1.5 border-b border-slate-200 space-y-2 shrink-0 bg-white shadow-sm">
        <div className="relative">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            ref={prodSearchRef}
            value={prodSearch}
            onChange={e => onProdSearch(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && productosFiltrados.length > 0) {
                onAgregar(productosFiltrados[0])
                onProdSearch('')
                setTimeout(() => onScannerFocus(), 50)
              }
            }}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder="Buscar producto… (F2)"
            className={[
              'w-full bg-slate-50 border-2 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition-all',
              focused ? 'border-blue-500 ring-4 ring-blue-400/20' : 'border-slate-300',
            ].join(' ')}
          />
        </div>
        <div className="flex gap-1.5 overflow-x-auto pb-0.5">
          {['', ...categorias].map(c => (
            <button key={c || '__all__'}
              onClick={() => onCatFiltro(c)}
              className={`shrink-0 px-3 py-1 rounded-full text-xs font-bold transition-colors cursor-pointer ${
                catFiltro === c
                  ? 'bg-slate-800 text-white'
                  : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'
              }`}>
              {c || 'Todos'}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {catFiltro === '' && favoritos.length > 0 && (
          <div>
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="text-sm">🔥</span>
              <span className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">Más vendidos</span>
            </div>
            <div className="flex gap-2 overflow-x-auto pb-1">
              {favoritos.map(p => {
                const meta = catMeta(p.categoria_nombre)
                const restr = isRestricto(p)
                const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
                return (
                  <button key={p.id} onClick={() => onAgregar(p)} disabled={bloqueado}
                    className={[
                      'relative flex flex-col items-center justify-center shrink-0 w-24 h-[68px] rounded-xl border-2 p-1.5 transition-all duration-100',
                      bloqueado
                        ? 'bg-red-50 border-red-200 opacity-50 cursor-not-allowed'
                        : `${meta.bg} ${meta.border} cursor-pointer hover:shadow-md hover:scale-105 active:scale-95`,
                    ].join(' ')}
                  >
                    {p.stock_actual != null && p.stock_actual <= 3 && (
                      <span className="absolute top-0.5 right-0.5 text-[8px] font-bold text-red-600 bg-red-100 rounded px-1">
                        {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                      </span>
                    )}
                    <span className="text-xl mb-0.5">{meta.emoji}</span>
                    <span className="text-[10px] text-slate-700 font-semibold leading-tight line-clamp-1 text-center">{p.descripcion}</span>
                    <span className={`text-xs font-black tabular-nums ${meta.accent}`}>{gs(getPrecio(p))}</span>
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {loadingProductos ? (
          <div className="flex items-center justify-center h-full text-slate-400 text-base">Cargando...</div>
        ) : productosFiltrados.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-slate-400 text-base">Sin productos</div>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(104px,1fr))] gap-2.5">
            {productosFiltrados.slice(0, 12).map((p, idx) => {
              const meta = catMeta(p.categoria_nombre)
              const restr = isRestricto(p)
              const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
              const isAdded = p.id === addedProductId
              return (
                <button key={p.id} onClick={() => onAgregar(p)} disabled={bloqueado}
                  className={[
                    'relative flex flex-col items-center justify-center text-center rounded-xl border-2 p-2 min-h-[108px] transition-all duration-100 select-none',
                    bloqueado
                      ? 'bg-red-50 border-red-200 opacity-50 cursor-not-allowed'
                      : `${meta.bg} ${meta.border} cursor-pointer hover:shadow-md hover:scale-[1.03] active:scale-95`,
                    isAdded && 'ring-4 ring-blue-400 scale-105',
                  ].join(' ')}
                >
                  {idx < 9 && (
                    <span className="absolute top-1.5 left-2 text-[11px] font-bold text-slate-300">{idx + 1}</span>
                  )}
                  {bloqueado && <span className="absolute top-1.5 right-1.5 text-xs">🚫</span>}
                  {p.stock_actual != null && !bloqueado && (
                    <span className={`absolute bottom-1 right-1.5 text-[9px] font-bold px-1 py-0.5 rounded tabular-nums ${
                      p.stock_actual === 0  ? 'bg-red-600 text-white' :
                      p.stock_actual <= 3   ? 'bg-red-100 text-red-700' :
                      p.stock_actual <= 10  ? 'bg-orange-100 text-orange-700' :
                      'text-slate-200'
                    }`}>
                      {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                    </span>
                  )}
                  <span className="text-2xl mb-1">{meta.emoji}</span>
                  <span className={`text-base font-black tabular-nums ${meta.accent}`}>{gs(getPrecio(p))}</span>
                  <span className="text-slate-700 text-xs font-medium leading-tight line-clamp-2 mt-0.5 px-1">
                    {p.descripcion}
                  </span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Ítems del carrito — altura fija, no se achica cuando está vacío */}
      <div className="shrink-0 border-t-2 border-slate-200 bg-white flex flex-col h-[260px]">
        <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <ShoppingCart size={18} className="text-slate-600" />
            <span className="text-base font-black text-slate-800">
              {carrito.reduce((s, i) => s + i.cantidad, 0)} productos
            </span>
          </div>
          {carrito.length > 0 && (
            <button onClick={() => onSetCarrito([])} className="text-slate-400 hover:text-red-500 transition-colors p-1">
              <X size={18} />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {carrito.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-4">
              <ShoppingCart size={32} className="text-slate-200 mb-2" />
              <p className="text-slate-500 text-sm font-semibold mb-0.5">Sin productos</p>
              <p className="text-slate-400 text-xs">Escanear tarjeta y seleccionar productos</p>
              {dailyStats.count > 0 && (
                <div className="flex items-center gap-4 mt-3 pt-2 border-t border-slate-100 text-[11px]">
                  <span className="text-slate-400">{t('pos.todaySales')}: <strong className="text-slate-700">{dailyStats.count}</strong></span>
                  <span className="text-slate-400">Promedio: <strong className="text-slate-700">{avgTime}s</strong></span>
                </div>
              )}
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {carrito.map(item => {
                const precio = getPrecio(item.producto)
                return (
                  <li key={item.producto.id} className="px-4 py-2 flex items-center gap-3">
                    <p className="text-sm text-slate-800 font-semibold flex-1 leading-tight truncate">{item.producto.descripcion}</p>

                    {esPorPeso(item.producto) ? (
                      <div className="flex items-center gap-1.5 shrink-0">
                        <input
                          value={cantidadTexto[item.producto.id] ?? formatCantidad(item.cantidad)}
                          onChange={e => setCantidadTexto(prev => ({ ...prev, [item.producto.id]: e.target.value.replace(/[^\d,.]/g, '') }))}
                          onFocus={() => setCantidadTexto(prev => ({ ...prev, [item.producto.id]: formatCantidad(item.cantidad) }))}
                          onBlur={e => commitCantidad(item.producto.id, e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur() }}
                          inputMode="decimal"
                          className="w-16 text-base font-black text-slate-900 tabular-nums text-center bg-slate-100 rounded-lg py-1 outline-none focus:ring-2 focus:ring-blue-400"
                        />
                        <span className="text-xs font-bold text-slate-400">Kg</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 shrink-0">
                        <button onClick={() => onQuitar(item.producto.id)}
                          className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 cursor-pointer">
                          <Minus size={14} />
                        </button>
                        <span className="text-base font-black text-slate-900 tabular-nums w-6 text-center">{item.cantidad}</span>
                        <button onClick={() => onAgregar(item.producto)}
                          className="w-7 h-7 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 cursor-pointer">
                          <Plus size={14} />
                        </button>
                      </div>
                    )}

                    <span className="text-sm font-bold text-emerald-700 tabular-nums shrink-0 w-24 text-right">{gs(precio * item.cantidad)}</span>

                    <button onClick={() => onSetCarrito(p => p.filter(i => i.producto.id !== item.producto.id))}
                      className="text-slate-300 hover:text-red-500 transition-colors shrink-0 p-0.5">
                      <X size={15} />
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </div>
      </div>
    </main>
  )
}
