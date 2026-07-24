import { useState } from 'react'
import { MagnifyingGlassIcon } from '@phosphor-icons/react'
import { gs, catMeta, type Producto, type RestriccionHijo } from './shared'

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
}

export default function PanelProductos({
  loadingProductos, categorias, catFiltro, prodSearch,
  productosFiltrados, favoritos, addedProductId,
  prodSearchRef, getPrecio, isRestricto,
  onCatFiltro, onProdSearch, onAgregar, onScannerFocus,
}: Props) {
  const [focused, setFocused] = useState(false)

  return (
    <main className="flex-1 flex flex-col overflow-hidden bg-slate-50">
      <div className="px-4 pt-3 pb-2 border-b border-slate-200 space-y-3 shrink-0 bg-white shadow-sm">
        <div className="relative">
          <MagnifyingGlassIcon size={20} weight="fill" className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
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
              'w-full bg-slate-50 border-2 rounded-xl pl-11 pr-4 py-3 text-base text-slate-900 placeholder:text-slate-400 outline-none transition-all',
              focused ? 'border-blue-500 ring-4 ring-blue-400/20' : 'border-slate-300',
            ].join(' ')}
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-0.5">
          {['', ...categorias].map(c => (
            <button key={c || '__all__'}
              onClick={() => onCatFiltro(c)}
              className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-bold transition-colors cursor-pointer ${
                catFiltro === c
                  ? 'bg-slate-800 text-white'
                  : 'bg-white text-slate-600 border border-slate-300 hover:bg-slate-50'
              }`}>
              {c || 'Todos'}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {catFiltro === '' && favoritos.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base">🔥</span>
              <span className="text-slate-500 text-xs font-bold uppercase tracking-wider">Más vendidos</span>
            </div>
            <div className="flex gap-3 overflow-x-auto pb-1">
              {favoritos.map(p => {
                const meta = catMeta(p.categoria_nombre)
                const restr = isRestricto(p)
                const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
                return (
                  <button key={p.id} onClick={() => onAgregar(p)} disabled={bloqueado}
                    className={[
                      'relative flex flex-col items-center justify-center shrink-0 w-36 h-28 rounded-2xl border-2 p-2 transition-all duration-100',
                      bloqueado
                        ? 'bg-red-50 border-red-200 opacity-50 cursor-not-allowed'
                        : `${meta.bg} ${meta.border} cursor-pointer hover:shadow-md hover:scale-105 active:scale-95`,
                    ].join(' ')}
                  >
                    {p.stock_actual != null && p.stock_actual <= 3 && (
                      <span className="absolute top-1 right-1 text-[9px] font-bold text-red-600 bg-red-100 rounded px-1">
                        {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                      </span>
                    )}
                    <span className="text-3xl mb-0.5">{meta.emoji}</span>
                    <span className="text-xs text-slate-700 font-semibold leading-tight line-clamp-1 text-center">{p.descripcion}</span>
                    <span className={`text-sm font-black tabular-nums mt-0.5 ${meta.accent}`}>{gs(getPrecio(p))}</span>
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
          <div className="grid grid-cols-3 xl:grid-cols-4 gap-3">
            {productosFiltrados.slice(0, 12).map((p, idx) => {
              const meta = catMeta(p.categoria_nombre)
              const restr = isRestricto(p)
              const bloqueado = !!restr && (restr.severidad === 'CRITICA' || restr.severidad === 'ALTA')
              const isAdded = p.id === addedProductId
              return (
                <button key={p.id} onClick={() => onAgregar(p)} disabled={bloqueado}
                  className={[
                    'relative flex flex-col items-center justify-center text-center rounded-2xl border-2 p-3 min-h-[150px] transition-all duration-100 select-none',
                    bloqueado
                      ? 'bg-red-50 border-red-200 opacity-50 cursor-not-allowed'
                      : `${meta.bg} ${meta.border} cursor-pointer hover:shadow-md hover:scale-[1.03] active:scale-95`,
                    isAdded && 'ring-4 ring-blue-400 scale-105',
                  ].join(' ')}
                >
                  {idx < 9 && (
                    <span className="absolute top-2 left-2.5 text-xs font-bold text-slate-300">{idx + 1}</span>
                  )}
                  {bloqueado && <span className="absolute top-2 right-2 text-sm">🚫</span>}
                  {p.stock_actual != null && !bloqueado && (
                    <span className={`absolute bottom-1.5 right-2 text-[10px] font-bold px-1.5 py-0.5 rounded tabular-nums ${
                      p.stock_actual === 0  ? 'bg-red-600 text-white' :
                      p.stock_actual <= 3   ? 'bg-red-100 text-red-700' :
                      p.stock_actual <= 10  ? 'bg-orange-100 text-orange-700' :
                      'text-slate-200'
                    }`}>
                      {p.stock_actual === 0 ? 'AGOTADO' : `${p.stock_actual}u`}
                    </span>
                  )}
                  <span className="text-4xl mb-1.5">{meta.emoji}</span>
                  <span className={`text-lg font-black tabular-nums ${meta.accent}`}>{gs(getPrecio(p))}</span>
                  <span className="text-slate-700 text-sm font-medium leading-tight line-clamp-2 mt-1 px-1">
                    {p.descripcion}
                  </span>
                </button>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}
