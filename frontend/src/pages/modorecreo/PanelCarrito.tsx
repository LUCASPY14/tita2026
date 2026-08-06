import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  ShoppingCart, X, XCircle, CheckCircle, Loader2,
  Plus, Minus, Banknote, Landmark, Smartphone,
  CreditCard, AlertTriangle,
} from 'lucide-react'
import {
  gs, esPorPeso, parseCantidadDecimal, formatCantidad,
  type Producto, type ItemCarrito, type MedioPagoDB, type ModoPago, type DailyStats,
} from './shared'

function iconMedio(desc: string) {
  const d = desc.toLowerCase()
  if (d.includes('pos') || d.includes('tarjet') || d.includes('débito') || d.includes('crédito'))
    return <Smartphone size={18} />
  if (d.includes('transfer') || d.includes('banco'))
    return <Landmark size={18} />
  return <Banknote size={18} />
}

interface Props {
  carrito: ItemCarrito[]
  total: number
  saldoDisponible: number | null
  saldoTrasCompra: number | null
  tarjeta: { nro_tarjeta: string } | null
  clienteModalidad: 'INMEDIATA' | 'MENSUAL'
  modoPago: ModoPago
  tipoVenta: 'CONTADO' | 'CREDITO'
  medioPagoSelId: number | null
  mediosPago: MedioPagoDB[]
  medioPagoSeleccionado: MedioPagoDB | null
  montoEfectivo: string
  vuelto: number
  referencia: string
  nroFacturaVenta: string
  canCobrar: boolean
  cobrando: boolean
  dailyStats: DailyStats
  avgTime: string
  getPrecio: (p: Producto) => number
  onSetCarrito: React.Dispatch<React.SetStateAction<ItemCarrito[]>>
  onAgregar: (p: Producto) => void
  onQuitar: (id: number) => void
  onSetCantidad: (id: number, cantidad: number) => void
  onModoPago: (m: ModoPago) => void
  onMedioPagoId: (id: number | null) => void
  onMontoEfectivo: (v: string) => void
  onReferencia: (v: string) => void
  onNroFacturaVenta: (v: string) => void
  onClearCliente: () => void
  onCobrar: () => void
  onCancelar: () => void
}

export default function PanelCarrito({
  carrito, total, saldoDisponible, saldoTrasCompra, tarjeta,
  clienteModalidad, modoPago, tipoVenta,
  medioPagoSelId, mediosPago, medioPagoSeleccionado,
  montoEfectivo, vuelto, referencia, nroFacturaVenta,
  canCobrar, cobrando, dailyStats, avgTime,
  getPrecio, onSetCarrito, onAgregar, onQuitar, onSetCantidad,
  onModoPago, onMedioPagoId, onMontoEfectivo, onReferencia, onNroFacturaVenta,
  onClearCliente, onCobrar, onCancelar,
}: Props) {
  const { t } = useTranslation()
  const efectivoRef = useRef<HTMLInputElement>(null)
  const [focused, setFocused] = useState(false)
  const [cantidadTexto, setCantidadTexto] = useState<Record<number, string>>({})

  function commitCantidad(id: number, texto: string) {
    const parsed = parseCantidadDecimal(texto)
    if (parsed !== null) onSetCantidad(id, parsed)
    setCantidadTexto(prev => { const next = { ...prev }; delete next[id]; return next })
  }

  return (
    <aside className="w-72 lg:w-96 bg-white border-l-2 border-slate-200 flex flex-col shrink-0">

      {/* Header carrito */}
      <div className="px-5 py-3 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShoppingCart size={22} className="text-slate-600" />
          <span className="text-lg font-black text-slate-800">
            {carrito.reduce((s, i) => s + i.cantidad, 0)} productos
          </span>
        </div>
        {carrito.length > 0 && (
          <button onClick={() => onSetCarrito([])} className="text-slate-400 hover:text-red-500 transition-colors p-1">
            <X size={20} />
          </button>
        )}
      </div>

      {/* Selector de pago: dos niveles */}
      <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 space-y-3">
        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Forma de pago</p>
          <div className="flex gap-2">
            <button
              onClick={() => { if (modoPago === 'CREDITO') { onModoPago('PREPAGO'); onClearCliente() } }}
              className={[
                'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-sm font-bold border-2 transition-all cursor-pointer',
                tipoVenta === 'CONTADO'
                  ? 'bg-slate-800 border-slate-800 text-white shadow-sm'
                  : 'bg-white border-slate-300 text-slate-600 hover:border-slate-400',
              ].join(' ')}
            >
              <Banknote size={15} />
              Contado
            </button>
            <button
              onClick={() => { onModoPago('CREDITO'); onMedioPagoId(null) }}
              className={[
                'flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-sm font-bold border-2 transition-all cursor-pointer',
                tipoVenta === 'CREDITO'
                  ? 'bg-orange-500 border-orange-500 text-white shadow-sm'
                  : 'bg-white border-slate-300 text-slate-600 hover:border-orange-300',
              ].join(' ')}
            >
              <Landmark size={15} />
              Crédito
            </button>
          </div>
        </div>

        {tipoVenta === 'CONTADO' && (
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1.5">Medio de pago</p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => { onModoPago('PREPAGO'); onMedioPagoId(null); onClearCliente() }}
                className={[
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold border-2 transition-all cursor-pointer',
                  modoPago === 'PREPAGO'
                    ? 'bg-blue-600 border-blue-600 text-white shadow-sm'
                    : 'bg-white border-slate-300 text-slate-600 hover:border-blue-300',
                ].join(' ')}
              >
                <CreditCard size={14} />
                Prepago
              </button>
              {mediosPago.map(mp => (
                <button key={mp.id}
                  onClick={() => { onModoPago('MEDIO'); onMedioPagoId(mp.id) }}
                  className={[
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold border-2 transition-all cursor-pointer',
                    modoPago === 'MEDIO' && medioPagoSelId === mp.id
                      ? 'bg-emerald-600 border-emerald-600 text-white shadow-sm'
                      : 'bg-white border-slate-300 text-slate-600 hover:border-emerald-300',
                  ].join(' ')}
                >
                  {iconMedio(mp.descripcion)}
                  {mp.descripcion}
                </button>
              ))}
            </div>
          </div>
        )}

        {tipoVenta === 'CREDITO' && (
          <p className="text-xs text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 leading-snug">
            La deuda queda registrada en la cuenta corriente del cliente.
          </p>
        )}
      </div>

      {/* Lista del carrito */}
      <div className="flex-1 overflow-y-auto">
        {carrito.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4 py-6">
            <ShoppingCart size={48} className="text-slate-200 mb-3" />
            <p className="text-slate-500 text-base font-semibold mb-1">Sin productos</p>
            <p className="text-slate-400 text-sm">Escanear tarjeta y seleccionar productos</p>
            {dailyStats.count > 0 && (
              <div className="mt-6 w-full border-t border-slate-100 pt-4 space-y-2">
                <div className="flex justify-between text-sm px-4">
                  <span className="text-slate-400">{t('pos.todaySales')}</span>
                  <span className="font-bold text-slate-700">{dailyStats.count}</span>
                </div>
                <div className="flex justify-between text-sm px-4">
                  <span className="text-slate-400">Tiempo promedio</span>
                  <span className="font-bold text-slate-700">{avgTime}s</span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {carrito.map(item => {
              const precio = getPrecio(item.producto)
              return (
                <li key={item.producto.id} className="px-4 py-3">
                  <div className="flex items-start gap-2">
                    <p className="text-base text-slate-800 font-semibold flex-1 leading-tight">{item.producto.descripcion}</p>
                    <button onClick={() => onSetCarrito(p => p.filter(i => i.producto.id !== item.producto.id))}
                      className="text-slate-300 hover:text-red-500 transition-colors shrink-0 p-0.5">
                      <X size={16} />
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    {esPorPeso(item.producto) ? (
                      <div className="flex items-center gap-1.5">
                        <input
                          value={cantidadTexto[item.producto.id] ?? formatCantidad(item.cantidad)}
                          onChange={e => setCantidadTexto(prev => ({ ...prev, [item.producto.id]: e.target.value.replace(/[^\d,.]/g, '') }))}
                          onFocus={() => setCantidadTexto(prev => ({ ...prev, [item.producto.id]: formatCantidad(item.cantidad) }))}
                          onBlur={e => commitCantidad(item.producto.id, e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur() }}
                          inputMode="decimal"
                          className="w-20 text-lg font-black text-slate-900 tabular-nums text-center bg-slate-100 rounded-lg py-1.5 outline-none focus:ring-2 focus:ring-blue-400"
                        />
                        <span className="text-sm font-bold text-slate-400">Kg</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <button onClick={() => onQuitar(item.producto.id)}
                          className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 cursor-pointer">
                          <Minus size={15} />
                        </button>
                        <span className="text-xl font-black text-slate-900 tabular-nums w-7 text-center">{item.cantidad}</span>
                        <button onClick={() => onAgregar(item.producto)}
                          className="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-600 cursor-pointer">
                          <Plus size={15} />
                        </button>
                      </div>
                    )}
                    <span className="text-base font-bold text-emerald-700 tabular-nums">{gs(precio * item.cantidad)}</span>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {/* Footer: total + pago + botones */}
      <div className="border-t-2 border-slate-200 p-4 space-y-3 bg-white">

        <div className="flex items-baseline justify-between">
          <span className="text-slate-500 text-sm font-black uppercase tracking-widest">Total</span>
          <span className="text-slate-900 text-4xl font-black tabular-nums">{gs(total)}</span>
        </div>

        {tarjeta && modoPago === 'PREPAGO' && (
          <div className="flex items-baseline justify-between text-sm -mt-1">
            <span className="text-slate-400">Saldo tras cobro</span>
            <span className={`font-bold tabular-nums ${(saldoTrasCompra ?? saldoDisponible ?? 0) < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
              {gs(saldoTrasCompra ?? saldoDisponible ?? 0)}
            </span>
          </div>
        )}

        {modoPago === 'MEDIO' && medioPagoSeleccionado &&
         medioPagoSeleccionado.descripcion.toLowerCase().includes('efectivo') && (
          <div className="space-y-2 bg-emerald-50 border border-emerald-200 rounded-xl p-3">
            <div className="flex items-center gap-2">
              <Banknote size={16} className="text-emerald-600" />
              <p className="text-emerald-700 text-sm font-bold">Monto recibido</p>
            </div>
            <input
              ref={efectivoRef}
              value={montoEfectivo}
              onChange={e => onMontoEfectivo(e.target.value.replace(/[^\d]/g, ''))}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="0"
              inputMode="numeric"
              className={[
                'w-full bg-white border-2 rounded-lg px-3 py-2 text-xl font-black text-slate-900 tabular-nums text-right outline-none',
                focused ? 'border-emerald-500' : 'border-emerald-300',
              ].join(' ')}
            />
            {montoEfectivo && (
              <div className="flex justify-between items-center pt-1">
                <span className="text-emerald-700 text-sm font-bold">Vuelto:</span>
                <span className={`text-xl font-black tabular-nums ${vuelto < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                  {gs(vuelto)}
                </span>
              </div>
            )}
          </div>
        )}

        {modoPago === 'MEDIO' && medioPagoSeleccionado?.requiere_validacion && (
          <div className="space-y-1.5 bg-blue-50 border border-blue-200 rounded-xl p-3">
            <label className="flex items-center gap-2 text-blue-700 text-sm font-bold">
              <CreditCard size={15} />
              Nro. de transacción
              <span className="text-red-500 text-xs font-black">*</span>
            </label>
            <input
              value={referencia}
              onChange={e => onReferencia(e.target.value)}
              placeholder="Ingrese el código generado por el terminal"
              autoComplete="off"
              className="w-full bg-white border-2 border-blue-300 rounded-lg px-3 py-2 text-base font-mono font-semibold text-slate-900 outline-none focus:border-blue-500 placeholder:text-slate-300 placeholder:font-normal tracking-wider uppercase"
              onKeyDown={e => { if (e.key === 'Enter') e.currentTarget.blur() }}
            />
            {referencia.trim() && (
              <p className="text-blue-600 text-xs font-mono tracking-widest uppercase">{referencia.trim()}</p>
            )}
          </div>
        )}

        {modoPago === 'MEDIO' && medioPagoSelId !== null && (
          <div className="space-y-1.5">
            {clienteModalidad === 'MENSUAL' ? (
              <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-xl">
                <span className="text-base">🗓️</span>
                <span className="text-sm font-semibold text-blue-700">Se acumula al lote mensual del cliente</span>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Nro. factura (opcional)</p>
                <input
                  value={nroFacturaVenta}
                  onChange={e => onNroFacturaVenta(e.target.value)}
                  placeholder="001-001-0000001"
                  className="w-full bg-white border border-amber-300 rounded-xl px-3 py-2 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:border-amber-500 transition-colors"
                />
                <p className="text-xs text-slate-400">
                  {nroFacturaVenta.trim()
                    ? 'Factura emitida al cobrar'
                    : 'Sin número → queda pendiente en Facturación'}
                </p>
              </div>
            )}
          </div>
        )}

        {modoPago === 'PREPAGO' ? (
          tarjeta ? (
            <div className="flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
              <CreditCard size={16} className="text-blue-500 shrink-0" />
              <span className="text-blue-700 text-sm font-semibold">Descuento de saldo prepago</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
              <CreditCard size={16} className="text-slate-300 shrink-0" />
              <span className="text-slate-400 text-sm">Escanear tarjeta del alumno</span>
            </div>
          )
        ) : medioPagoSeleccionado ? (
          <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2">
            {iconMedio(medioPagoSeleccionado.descripcion)}
            <span className="text-emerald-700 text-sm font-semibold">{medioPagoSeleccionado.descripcion}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
            <AlertTriangle size={16} className="text-orange-400 shrink-0" />
            <span className="text-orange-600 text-sm font-semibold">Seleccionar medio de pago</span>
          </div>
        )}

        <button
          onClick={onCobrar}
          disabled={!canCobrar}
          className={[
            'w-full py-5 rounded-2xl font-black text-xl tracking-wide flex items-center justify-center gap-3 transition-all duration-150',
            canCobrar
              ? tipoVenta === 'CREDITO'
                ? 'bg-orange-500 hover:bg-orange-600 text-white cursor-pointer active:scale-95 shadow-lg shadow-orange-500/25'
                : 'bg-green-500 hover:bg-green-600 text-white cursor-pointer active:scale-95 shadow-lg shadow-green-500/25'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed',
          ].join(' ')}
        >
          {cobrando
            ? <><Loader2 size={24} className="animate-spin" />Procesando…</>
            : tipoVenta === 'CREDITO'
              ? <><Landmark size={24} />ACREDITAR (F9)</>
              : <><CheckCircle size={24} />COBRAR (F9)</>
          }
        </button>

        <button
          onClick={onCancelar}
          className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-red-50 text-slate-500 hover:text-red-600 text-sm font-bold transition-colors cursor-pointer flex items-center justify-center gap-2"
        >
          <XCircle size={16} />
          Cancelar (Esc)
        </button>
      </div>
    </aside>
  )
}
