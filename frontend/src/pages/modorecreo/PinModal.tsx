import { useState } from 'react'
import { CheckCircleIcon, LockKeyIcon, SpinnerIcon } from '@phosphor-icons/react'
import { gs } from './shared'

interface Props {
  saldoActual: number
  total: number
  limiteCreditoTarjeta: number
  onConfirm: (pin: string) => void
  onCancel: () => void
  loading: boolean
}

export default function PinModal({ saldoActual, total, limiteCreditoTarjeta, onConfirm, onCancel, loading }: Props) {
  const [pin, setPin] = useState('')
  const PIN_LEN = 4

  const deficit = total - saldoActual
  const puedeAutorizar = deficit <= limiteCreditoTarjeta

  const press = (digit: string) => {
    if (digit === '←') { setPin(p => p.slice(0, -1)); return }
    if (pin.length < PIN_LEN) setPin(p => p + digit)
  }

  const confirm = () => {
    if (pin.length === PIN_LEN && puedeAutorizar) onConfirm(pin)
  }

  const keys = ['1','2','3','4','5','6','7','8','9','←','0','✓']

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[300]" onClick={e => { if (e.target === e.currentTarget) onCancel() }}>
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div className="bg-amber-500 px-6 py-4 flex items-center gap-3">
          <LockKeyIcon size={28} weight="fill" className="text-white" />
          <div>
            <p className="text-white font-black text-xl">Autorización requerida</p>
            <p className="text-amber-100 text-sm">PIN del padre/tutor</p>
          </div>
        </div>

        <div className="px-6 py-4 bg-amber-50 border-b border-amber-200 grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
          <div>
            <p className="text-amber-700 text-xs font-bold uppercase tracking-wide">Saldo actual</p>
            <p className="text-amber-900 text-lg font-black tabular-nums">{gs(saldoActual)}</p>
          </div>
          <div>
            <p className="text-slate-600 text-xs font-bold uppercase tracking-wide">Total compra</p>
            <p className="text-slate-900 text-lg font-black tabular-nums">{gs(total)}</p>
          </div>
          <div>
            <p className={`text-xs font-bold uppercase tracking-wide ${puedeAutorizar ? 'text-red-600' : 'text-red-700'}`}>Déficit</p>
            <p className={`text-lg font-black tabular-nums ${puedeAutorizar ? 'text-red-600' : 'text-red-700'}`}>{gs(deficit)}</p>
          </div>
        </div>

        {!puedeAutorizar && (
          <div className="mx-6 mt-4 p-3 bg-red-50 border border-red-300 rounded-xl text-center">
            <p className="text-red-700 font-bold text-sm">Excede el límite de crédito ({gs(limiteCreditoTarjeta)})</p>
            <p className="text-red-600 text-xs mt-0.5">No es posible autorizar esta venta</p>
          </div>
        )}

        {puedeAutorizar && (
          <div className="px-6 pt-5 pb-2">
            <div className="flex justify-center gap-4 mb-6">
              {Array.from({ length: PIN_LEN }).map((_, i) => (
                <div key={i} className={`w-5 h-5 rounded-full border-2 transition-all ${
                  i < pin.length ? 'bg-amber-500 border-amber-500 scale-110' : 'bg-white border-slate-300'
                }`} />
              ))}
            </div>

            <div className="grid grid-cols-3 gap-3">
              {keys.map(k => {
                const isBack = k === '←'
                const isOk = k === '✓'
                const disabled = isOk ? (pin.length !== PIN_LEN || loading) : (isBack ? pin.length === 0 : false)
                return (
                  <button
                    key={k}
                    onClick={() => { if (!loading) { if (isOk) { confirm() } else { press(k) } } }}
                    disabled={disabled}
                    className={[
                      'h-14 rounded-2xl text-xl font-black transition-all select-none',
                      isOk
                        ? 'bg-green-500 text-white hover:bg-green-600 disabled:opacity-40'
                        : isBack
                          ? 'bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-30'
                          : 'bg-slate-100 text-slate-900 hover:bg-amber-50 active:bg-amber-100',
                      !disabled && 'active:scale-95 cursor-pointer',
                      disabled && 'cursor-not-allowed',
                    ].join(' ')}
                  >
                    {loading && isOk ? <SpinnerIcon size={20} className="animate-spin mx-auto" /> : k}
                  </button>
                )
              })}
            </div>
          </div>
        )}

        <div className="px-6 py-4 flex gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 py-3 rounded-2xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-base transition-colors cursor-pointer disabled:opacity-50"
          >
            Cancelar
          </button>
          {puedeAutorizar && (
            <button
              onClick={confirm}
              disabled={pin.length !== PIN_LEN || loading}
              className="flex-1 py-3 rounded-2xl bg-amber-500 hover:bg-amber-600 text-white font-black text-base transition-colors cursor-pointer disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {loading
                ? <><SpinnerIcon size={18} className="animate-spin" />Verificando…</>
                : <><CheckCircleIcon size={18} weight="fill" />Autorizar</>
              }
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
