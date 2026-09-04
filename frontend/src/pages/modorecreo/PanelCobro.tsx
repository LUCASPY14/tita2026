import { useRef, useState } from 'react'
import {
  XCircle, CheckCircle, Loader2,
  Banknote, Landmark, Smartphone,
  CreditCard, AlertTriangle,
} from 'lucide-react'
import { gs, type MedioPagoDB, type ModoPago } from './shared'

function iconMedio(desc: string) {
  const d = desc.toLowerCase()
  if (d.includes('pos') || d.includes('tarjet') || d.includes('débito') || d.includes('crédito'))
    return <Smartphone size={18} />
  if (d.includes('transfer') || d.includes('banco'))
    return <Landmark size={18} />
  return <Banknote size={18} />
}

interface Props {
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
  onModoPago: (m: ModoPago) => void
  onMedioPagoId: (id: number | null) => void
  onMontoEfectivo: (v: string) => void
  onReferencia: (v: string) => void
  onNroFacturaVenta: (v: string) => void
  onClearCliente: () => void
  onCobrar: () => void
  onCancelar: () => void
}

export default function PanelCobro({
  total, saldoDisponible, saldoTrasCompra, tarjeta,
  clienteModalidad, modoPago, tipoVenta,
  medioPagoSelId, mediosPago, medioPagoSeleccionado,
  montoEfectivo, vuelto, referencia, nroFacturaVenta,
  canCobrar, cobrando,
  onModoPago, onMedioPagoId, onMontoEfectivo, onReferencia, onNroFacturaVenta,
  onClearCliente, onCobrar, onCancelar,
}: Props) {
  const efectivoRef = useRef<HTMLInputElement>(null)
  const [focused, setFocused] = useState(false)

  return (
    <aside className="w-[380px] xl:w-[440px] shrink-0 bg-white border-l-2 border-slate-200 flex flex-col">

      {/* Selector de pago: dos niveles */}
      <div className="px-5 py-5 border-b border-slate-100 bg-slate-50 space-y-4">
        <div>
          <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Forma de pago</p>
          <div className="flex gap-2">
            <button
              onClick={() => { if (modoPago === 'CREDITO') { onModoPago('PREPAGO'); onClearCliente() } }}
              className={[
                'flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-base font-bold border-2 transition-all cursor-pointer',
                tipoVenta === 'CONTADO'
                  ? 'bg-slate-800 border-slate-800 text-white shadow-sm'
                  : 'bg-white border-slate-300 text-slate-600 hover:border-slate-400',
              ].join(' ')}
            >
              <Banknote size={18} />
              Contado
            </button>
            <button
              onClick={() => { onModoPago('CREDITO'); onMedioPagoId(null) }}
              className={[
                'flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-base font-bold border-2 transition-all cursor-pointer',
                tipoVenta === 'CREDITO'
                  ? 'bg-orange-500 border-orange-500 text-white shadow-sm'
                  : 'bg-white border-slate-300 text-slate-600 hover:border-orange-300',
              ].join(' ')}
            >
              <Landmark size={18} />
              Crédito
            </button>
          </div>
        </div>

        {tipoVenta === 'CONTADO' && (
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Medio de pago</p>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => { onModoPago('PREPAGO'); onMedioPagoId(null); onClearCliente() }}
                className={[
                  'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold border-2 transition-all cursor-pointer',
                  modoPago === 'PREPAGO'
                    ? 'bg-blue-600 border-blue-600 text-white shadow-sm'
                    : 'bg-white border-slate-300 text-slate-600 hover:border-blue-300',
                ].join(' ')}
              >
                <CreditCard size={16} />
                Prepago
              </button>
              {mediosPago.map(mp => (
                <button key={mp.id_medio_pago}
                  onClick={() => { onModoPago('MEDIO'); onMedioPagoId(mp.id_medio_pago) }}
                  className={[
                    'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold border-2 transition-all cursor-pointer',
                    modoPago === 'MEDIO' && medioPagoSelId === mp.id_medio_pago
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
          <p className="text-sm text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 leading-snug">
            La deuda queda registrada en la cuenta corriente del cliente.
          </p>
        )}
      </div>

      {/* Espacio flexible: empuja el footer de cobro hacia abajo */}
      <div className="flex-1" />

      {/* Footer: total + pago + botones */}
      <div className="border-t-2 border-slate-200 p-5 space-y-3 bg-white">

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
