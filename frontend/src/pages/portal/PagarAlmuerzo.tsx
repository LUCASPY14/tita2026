import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  UtensilsCrossed, CheckCircle2, XCircle, AlertCircle,
  ChevronRight, Loader2, Wallet, RefreshCw, Clock,
} from 'lucide-react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'
import { useAuthStore } from '../../store/authStore'
import TarjetasGuardadasBancard from './components/TarjetasGuardadasBancard'

// El tipo global window.Bancard se declara una sola vez en TarjetasGuardadasBancard.tsx

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface HijoSaldo {
  id: number
  nombre: string
  saldo_almuerzo: number
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const MONTOS_RAPIDOS = [25000, 50000, 100000, 150000]

function formatGs(n: number) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

// ─── Resultado del pago ───────────────────────────────────────────────────────

function ResultadoPago({ estado, monto }: { estado: string; monto: string | null }) {
  const aprobado = estado === 'aprobado'
  const cancelado = estado === 'cancelado'

  return (
    <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
      {aprobado ? (
        <>
          <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center">
            <CheckCircle2 className="w-10 h-10 text-green-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">¡Recarga aprobada!</h2>
            {monto && (
              <p className="text-emerald-700 text-xl font-semibold mt-1">
                {formatGs(Number(monto))} acreditados
              </p>
            )}
            <p className="text-slate-500 text-base mt-2">
              El saldo de almuerzo ya está disponible.
            </p>
          </div>
        </>
      ) : cancelado ? (
        <>
          <div className="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center">
            <XCircle className="w-10 h-10 text-slate-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Recarga cancelada</h2>
            <p className="text-slate-500 text-base mt-2">No se realizó ningún cargo.</p>
          </div>
        </>
      ) : (
        <>
          <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Recarga rechazada</h2>
            <p className="text-slate-500 text-base mt-2">
              No se pudo procesar el pago. Verificá los datos de tu tarjeta e intentá nuevamente.
            </p>
          </div>
        </>
      )}
    </div>
  )
}

// ─── Componente principal ─────────────────────────────────────────────────────

export default function PagarAlmuerzo() {
  const { resetInactivityTimer } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()

  const estadoRetorno = searchParams.get('estado')
  const montoRetorno  = searchParams.get('monto')

  // Pre-cargado desde Dashboard vía query param
  const hijoIdParam = searchParams.get('hijo_id')

  const [hijos, setHijos]           = useState<HijoSaldo[]>([])
  const [loading, setLoading]       = useState(true)
  const [hijoSeleccionado, setHijoSeleccionado] = useState<HijoSaldo | null>(null)
  const [montoCustom, setMontoCustom] = useState('')
  const [iniciando, setIniciando]         = useState(false)
  const [pagoEnProceso, setPagoEnProceso] = useState(false)
  const [processId, setProcessId]         = useState<string | null>(null)
  const [scriptUrl, setScriptUrl]         = useState<string | null>(null)
  const scriptRef = useRef<HTMLScriptElement | null>(null)

  // Método de pago: pago ocasional (single_buy) o tarjeta guardada (charge)
  const [metodoPago, setMetodoPago]                 = useState<'ocasional' | 'guardada'>('ocasional')
  const [cardIdSeleccionado, setCardIdSeleccionado] = useState<number | null>(null)

  // Pago con tarjeta guardada que requiere 3D Secure
  const [pago3dsEnProceso, setPago3dsEnProceso] = useState(false)
  const [processId3ds, setProcessId3ds]         = useState<string | null>(null)
  const [scriptUrl3ds, setScriptUrl3ds]         = useState<string | null>(null)
  const scriptRef3ds = useRef<HTMLScriptElement | null>(null)

  const cargarHijos = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/usuarios/portal/mi-hijo/')
      const lista: HijoSaldo[] = (data.hijos ?? []).map((h: { id: number; nombre: string; saldo_almuerzo: number }) => ({
        id: h.id, nombre: h.nombre, saldo_almuerzo: h.saldo_almuerzo,
      }))
      setHijos(lista)

      const preseleccionado = hijoIdParam
        ? lista.find(h => String(h.id) === hijoIdParam)
        : (lista.length === 1 ? lista[0] : undefined)
      if (preseleccionado) setHijoSeleccionado(preseleccionado)
    } catch {
      toast.error('Error al cargar el saldo de almuerzo')
    } finally {
      setLoading(false)
    }
  }, [hijoIdParam])

  // Carga de datos al montar (salvo al volver de un pago): el setLoading(true)
  // inicial en cargarHijos es intencional.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!estadoRetorno) cargarHijos()
  }, [estadoRetorno, cargarHijos])

  const montoEfectivo = parseInt(montoCustom.replace(/\D/g, ''), 10) || 0
  const montoValido = montoEfectivo > 0

  const handlePagar = useCallback(async () => {
    if (!hijoSeleccionado || !montoValido || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post('/core/bancard/iniciar-almuerzo/', {
        hijo_id: hijoSeleccionado.id,
        monto: montoEfectivo,
      })
      setProcessId(data.process_id)
      setScriptUrl(data.script_url)
      setPagoEnProceso(true)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al iniciar la recarga'
      toast.error(msg)
      setIniciando(false)
    }
  }, [hijoSeleccionado, montoValido, montoEfectivo, iniciando])

  // ── Pagar con tarjeta guardada (charge) ────────────────────────────────────
  const handlePagarConTarjeta = useCallback(async () => {
    if (!hijoSeleccionado || !montoValido || !cardIdSeleccionado || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post('/core/bancard/pagar-almuerzo-con-tarjeta/', {
        hijo_id: hijoSeleccionado.id,
        monto: montoEfectivo,
        card_id: cardIdSeleccionado,
      })

      if (data.requires_3ds) {
        setProcessId3ds(data.process_id)
        setScriptUrl3ds(data.script_url)
        setPago3dsEnProceso(true)
        return
      }

      const params = new URLSearchParams({ estado: data.estado, tipo: 'almuerzo' })
      if (data.monto) params.set('monto', String(data.monto))
      window.location.href = `${window.location.pathname}?${params.toString()}`
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al procesar la recarga'
      toast.error(msg)
      setIniciando(false)
    }
  }, [hijoSeleccionado, montoValido, montoEfectivo, cardIdSeleccionado, iniciando])

  useEffect(() => {
    if (!pagoEnProceso && !pago3dsEnProceso) return
    const interval = setInterval(() => resetInactivityTimer(), 60_000)
    return () => clearInterval(interval)
  }, [pagoEnProceso, pago3dsEnProceso, resetInactivityTimer])

  useEffect(() => {
    if (!pagoEnProceso || !processId || !scriptUrl) return

    if (scriptRef.current) {
      scriptRef.current.remove()
      scriptRef.current = null
    }

    const script = document.createElement('script')
    script.src = scriptUrl
    script.async = true
    script.onload = () => {
      window.Bancard?.Checkout.createForm('bancard-checkout-container-almuerzo', processId)
    }
    script.onerror = () => {
      toast.error('Error al cargar el formulario de pago')
      setPagoEnProceso(false)
      setProcessId(null)
      setScriptUrl(null)
      setIniciando(false)
    }
    scriptRef.current = script
    document.body.appendChild(script)

    return () => {
      scriptRef.current?.remove()
      scriptRef.current = null
    }
  }, [pagoEnProceso, processId, scriptUrl])

  // ── Cargar script Bancard y renderizar iframe de 3D Secure (tarjeta guardada) ──
  useEffect(() => {
    if (!pago3dsEnProceso || !processId3ds || !scriptUrl3ds) return

    if (scriptRef3ds.current) {
      scriptRef3ds.current.remove()
      scriptRef3ds.current = null
    }

    const script = document.createElement('script')
    script.src = scriptUrl3ds
    script.async = true
    script.onload = () => {
      window.Bancard?.Charge3DS.createForm('bancard-3ds-container-almuerzo', processId3ds)
    }
    script.onerror = () => {
      toast.error('Error al cargar la verificación de seguridad')
      setPago3dsEnProceso(false)
      setProcessId3ds(null)
      setScriptUrl3ds(null)
      setIniciando(false)
    }
    scriptRef3ds.current = script
    document.body.appendChild(script)

    return () => {
      scriptRef3ds.current?.remove()
      scriptRef3ds.current = null
    }
  }, [pago3dsEnProceso, processId3ds, scriptUrl3ds])

  const handleNuevoPago = () => {
    setSearchParams({})
    setMontoCustom('')
    setMetodoPago('ocasional')
    setCardIdSeleccionado(null)
    cargarHijos()
  }

  // ── Formulario embebido Bancard ────────────────────────────────────────────
  if (pagoEnProceso) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Recargar Saldo de Almuerzo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="mb-4">
            <p className="text-base font-semibold text-slate-800">Ingresá los datos de tu tarjeta</p>
            <p className="text-sm text-slate-500 mt-0.5">
              El formulario es provisto por Bancard — tus datos de tarjeta son seguros.
            </p>
          </div>
          <div id="bancard-checkout-container-almuerzo" className="min-h-[420px]" />
          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={() => {
                setPagoEnProceso(false)
                setProcessId(null)
                setScriptUrl(null)
                setIniciando(false)
              }}
              className="text-sm text-slate-500 hover:text-slate-700 transition-colors cursor-pointer"
            >
              ← Cancelar y volver
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Verificación 3D Secure para pago con tarjeta guardada
  if (pago3dsEnProceso) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Recargar Saldo de Almuerzo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="mb-4">
            <p className="text-base font-semibold text-slate-800">Verificación de seguridad</p>
            <p className="text-sm text-slate-500 mt-0.5">
              Tu banco requiere un paso adicional para confirmar el pago.
            </p>
          </div>
          <div id="bancard-3ds-container-almuerzo" className="min-h-[380px]" />
        </div>
      </div>
    )
  }

  // ── Resultado de Bancard ───────────────────────────────────────────────────
  if (estadoRetorno) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Recargar Saldo de Almuerzo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <ResultadoPago estado={estadoRetorno} monto={montoRetorno} />
          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={handleNuevoPago}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors cursor-pointer text-base"
            >
              <RefreshCw className="w-4 h-4" />
              Ver saldo
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loading) return <Spinner className="mt-16" />

  if (hijos.length === 0) {
    return (
      <div className="py-16 text-center text-slate-400">
        <UtensilsCrossed className="w-12 h-12 mx-auto mb-4 opacity-30" />
        <p className="text-base font-medium text-slate-600">Sin hijos asociados</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Recargar Saldo de Almuerzo</h1>
        <p className="text-base text-slate-500 mt-0.5">
          Cargás saldo con Visa o Mastercard vía Bancard — se descuenta en cada ingreso al comedor
        </p>
      </div>

      {/* Selección de hijo (si hay más de uno) */}
      {hijos.length > 1 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              1 — Seleccioná el hijo
            </p>
          </div>
          <div className="divide-y divide-slate-100">
            {hijos.map(h => (
              <button
                key={h.id}
                type="button"
                onClick={() => setHijoSeleccionado(h)}
                className={[
                  'w-full flex items-center justify-between px-5 py-4 text-left transition-colors cursor-pointer',
                  hijoSeleccionado?.id === h.id
                    ? 'bg-orange-50 border-l-4 border-orange-500'
                    : 'hover:bg-slate-50 border-l-4 border-transparent',
                ].join(' ')}
              >
                <p className="text-base font-semibold text-slate-800">{h.nombre}</p>
                <div className="text-right shrink-0 ml-4">
                  <p className="text-sm text-slate-400">Saldo actual</p>
                  <p className={`text-base font-bold tabular-nums ${h.saldo_almuerzo < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                    {formatGs(h.saldo_almuerzo)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Hijo único seleccionado */}
      {hijoSeleccionado && hijos.length === 1 && (
        <div className={[
          'rounded-2xl px-5 py-4 border',
          hijoSeleccionado.saldo_almuerzo < 0 ? 'bg-red-50 border-red-200' : 'bg-orange-50 border-orange-200',
        ].join(' ')}>
          <div className="flex items-center justify-between">
            <p className="text-base font-bold text-slate-800">{hijoSeleccionado.nombre}</p>
            <div className="text-right shrink-0 ml-4">
              <p className="text-sm text-slate-500">Saldo actual</p>
              <p className={`text-2xl font-bold tabular-nums ${hijoSeleccionado.saldo_almuerzo < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                {formatGs(hijoSeleccionado.saldo_almuerzo)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Monto a recargar */}
      {hijoSeleccionado && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              {hijos.length > 1 ? '2' : '1'} — Monto a recargar
            </p>
          </div>
          <div className="p-5 space-y-4">
            {/* Montos rápidos */}
            <div className="grid grid-cols-2 gap-2.5">
              {MONTOS_RAPIDOS.map(m => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMontoCustom(String(m))}
                  className={[
                    'py-3 px-4 rounded-xl border-2 text-base font-bold transition-all cursor-pointer',
                    montoEfectivo === m
                      ? 'bg-orange-600 border-orange-600 text-white shadow-sm'
                      : 'border-slate-200 text-slate-700 hover:border-orange-300 hover:bg-orange-50',
                  ].join(' ')}
                >
                  {formatGs(m)}
                </button>
              ))}
            </div>

            {/* Monto personalizado */}
            <div>
              <p className="text-sm text-slate-500 mb-2">O ingresá otro monto:</p>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-base font-medium pointer-events-none">
                  Gs.
                </span>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="0"
                  value={montoCustom}
                  onChange={e => setMontoCustom(e.target.value.replace(/\D/g, ''))}
                  className="w-full border border-slate-200 rounded-xl pl-10 pr-3.5 py-2.5 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500 transition-colors"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Método de pago */}
      {hijoSeleccionado && montoValido && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              {hijos.length > 1 ? '3' : '2'} — Método de pago
            </p>
          </div>
          <div className="flex border-b border-slate-100">
            <button
              type="button"
              onClick={() => setMetodoPago('ocasional')}
              className={[
                'flex-1 py-3 text-sm font-semibold transition-colors cursor-pointer',
                metodoPago === 'ocasional'
                  ? 'text-orange-700 border-b-2 border-orange-600'
                  : 'text-slate-400 hover:text-slate-600',
              ].join(' ')}
            >
              Pago único
            </button>
            <button
              type="button"
              onClick={() => setMetodoPago('guardada')}
              className={[
                'flex-1 py-3 text-sm font-semibold transition-colors cursor-pointer',
                metodoPago === 'guardada'
                  ? 'text-orange-700 border-b-2 border-orange-600'
                  : 'text-slate-400 hover:text-slate-600',
              ].join(' ')}
            >
              Tarjeta guardada
            </button>
          </div>
          {metodoPago === 'guardada' && (
            <TarjetasGuardadasBancard
              selectedCardId={cardIdSeleccionado}
              onSeleccionar={setCardIdSeleccionado}
              accent="orange"
              containerIdPrefix="pagar-almuerzo"
            />
          )}
        </div>
      )}

      {/* Resumen */}
      {hijoSeleccionado && montoEfectivo > 0 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Resumen</p>
          </div>
          <div className="px-5 py-4 space-y-2">
            <div className="flex justify-between text-base">
              <span className="text-slate-500">Alumno</span>
              <span className="font-semibold text-slate-800">{hijoSeleccionado.nombre}</span>
            </div>
            <div className="flex justify-between text-base">
              <span className="text-slate-500">Saldo actual</span>
              <span className={`font-semibold tabular-nums ${hijoSeleccionado.saldo_almuerzo < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                {formatGs(hijoSeleccionado.saldo_almuerzo)}
              </span>
            </div>
            <div className="flex justify-between text-base border-t border-slate-100 pt-2 mt-2">
              <span className="text-slate-500">Monto a recargar</span>
              <span className="text-xl font-bold text-orange-700 tabular-nums">
                {formatGs(montoEfectivo)}
              </span>
            </div>
            <div className="flex justify-between text-sm text-slate-400">
              <span>Saldo luego de la recarga</span>
              <span className="tabular-nums">{formatGs(hijoSeleccionado.saldo_almuerzo + montoEfectivo)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Info de seguridad */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 flex items-start gap-3">
        <Clock className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-slate-700">Pago seguro con Bancard</p>
          <p className="text-sm text-slate-500 mt-0.5">
            {metodoPago === 'guardada'
              ? 'Al presionar «Ir a pagar», se cobrará con la tarjeta guardada que seleccionaste.'
              : 'Al presionar «Ir a pagar», serás redirigido a la plataforma segura de Bancard donde ingresarás tu CI, número de tarjeta (Visa o Mastercard), vencimiento y CVV.'}
            {' '}Cantina Tita no almacena datos de tarjeta.
          </p>
        </div>
      </div>

      {/* Botón principal */}
      {(() => {
        const listo = hijoSeleccionado && montoValido && (metodoPago === 'ocasional' || cardIdSeleccionado !== null)
        return (
          <button
            type="button"
            onClick={metodoPago === 'ocasional' ? handlePagar : handlePagarConTarjeta}
            disabled={!listo || iniciando}
            className={[
              'w-full flex items-center justify-center gap-3 py-4 rounded-2xl',
              'text-lg font-bold transition-all',
              listo && !iniciando
                ? 'bg-orange-600 hover:bg-orange-700 text-white cursor-pointer shadow-lg shadow-orange-600/20 active:scale-[0.98]'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed',
            ].join(' ')}
          >
            {iniciando ? (
              <><Loader2 className="w-5 h-5 animate-spin" />Iniciando pago…</>
            ) : (
              <><Wallet className="w-5 h-5" />Ir a pagar<ChevronRight className="w-5 h-5" /></>
            )}
          </button>
        )
      })()}
    </div>
  )
}
