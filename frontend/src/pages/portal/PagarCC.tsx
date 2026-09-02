import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  CreditCard, CheckCircle2, XCircle, AlertCircle,
  ChevronRight, Loader2, Wallet, RefreshCw, BookOpen,
} from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Spinner from '../../components/ui/Spinner'
import TarjetasGuardadasBancard from './components/TarjetasGuardadasBancard'

// El tipo global window.Bancard se declara una sola vez en TarjetasGuardadasBancard.tsx

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
            <h2 className="text-2xl font-bold text-slate-900">¡Pago aprobado!</h2>
            {monto && (
              <p className="text-emerald-700 text-xl font-semibold mt-1">
                {formatGs(Number(monto))} pagados
              </p>
            )}
            <p className="text-slate-500 text-base mt-2">
              Tu deuda de cuenta corriente fue reducida.
            </p>
          </div>
        </>
      ) : cancelado ? (
        <>
          <div className="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center">
            <XCircle className="w-10 h-10 text-slate-400" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Pago cancelado</h2>
            <p className="text-slate-500 text-base mt-2">No se realizó ningún cargo.</p>
          </div>
        </>
      ) : (
        <>
          <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle className="w-10 h-10 text-red-500" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Pago rechazado</h2>
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

export default function PagarCC() {
  const { user, resetInactivityTimer } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()

  // Resultado de retorno desde Bancard
  const estadoRetorno = searchParams.get('estado')
  const montoRetorno  = searchParams.get('monto')

  // Deuda actual
  const [deuda, setDeuda] = useState<number | null>(null)
  const [deudaCantina, setDeudaCantina] = useState(0)
  const [deudaAlmuerzo, setDeudaAlmuerzo] = useState(0)
  const [loadingDeuda, setLoadingDeuda] = useState(true)

  // Categoría de la deuda (solo si debe en ambas — si no, se infiere sola)
  const [origen, setOrigen] = useState<'CANTINA' | 'ALMUERZO' | ''>('')

  // Selección de monto
  const [montoSeleccionado, setMontoSeleccionado] = useState<number | null>(null)
  const [montoCustom, setMontoCustom]   = useState('')
  const [usandoCustom, setUsandoCustom] = useState(false)

  // Método de pago: pago ocasional (single_buy) o tarjeta guardada (charge)
  const [metodoPago, setMetodoPago]           = useState<'ocasional' | 'guardada'>('ocasional')
  const [cardIdSeleccionado, setCardIdSeleccionado] = useState<number | null>(null)

  // Proceso de pago
  const [iniciando, setIniciando]         = useState(false)
  const [pagoEnProceso, setPagoEnProceso] = useState(false)
  const [processId, setProcessId]         = useState<string | null>(null)
  const [scriptUrl, setScriptUrl]         = useState<string | null>(null)
  const scriptRef = useRef<HTMLScriptElement | null>(null)

  // Pago con tarjeta guardada que requiere 3D Secure
  const [pago3dsEnProceso, setPago3dsEnProceso] = useState(false)
  const [processId3ds, setProcessId3ds]         = useState<string | null>(null)
  const [scriptUrl3ds, setScriptUrl3ds]         = useState<string | null>(null)
  const scriptRef3ds = useRef<HTMLScriptElement | null>(null)

  // ── Cargar deuda actual ────────────────────────────────────────────────────
  const cargarDeuda = useCallback(async () => {
    setLoadingDeuda(true)
    try {
      const { data } = await api.get('/usuarios/portal/mi-hijo/')
      setDeuda(Number(data?.cliente?.saldo_cuenta_corriente ?? 0))
      setDeudaCantina(Number(data?.cliente?.saldo_cc_cantina ?? 0))
      setDeudaAlmuerzo(Number(data?.cliente?.saldo_cc_almuerzo ?? 0))
    } catch {
      toast.error('Error al cargar los datos')
    } finally {
      setLoadingDeuda(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!estadoRetorno) cargarDeuda()
  }, [estadoRetorno, cargarDeuda])

  const requiereElegirOrigen = deudaCantina > 0 && deudaAlmuerzo > 0
  const deudaOrigenSeleccionado = origen === 'CANTINA' ? deudaCantina : origen === 'ALMUERZO' ? deudaAlmuerzo : (deuda ?? 0)

  // ── Monto efectivo ─────────────────────────────────────────────────────────
  const montoEfectivo = usandoCustom
    ? (parseInt(montoCustom.replace(/\D/g, ''), 10) || 0)
    : (montoSeleccionado ?? 0)

  const montoValido = montoEfectivo > 0 && deuda !== null && montoEfectivo <= deudaOrigenSeleccionado
    && (!requiereElegirOrigen || origen !== '')

  // ── Iniciar pago ocasional (single_buy) ────────────────────────────────────
  const handlePagar = useCallback(async () => {
    if (!montoValido || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post('/core/bancard/iniciar-cc/', {
        monto: montoEfectivo,
        ...(origen ? { origen } : {}),
      })
      setProcessId(data.process_id)
      setScriptUrl(data.script_url)
      setPagoEnProceso(true)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al iniciar el pago'
      toast.error(msg)
      setIniciando(false)
    }
  }, [montoValido, montoEfectivo, origen, iniciando])

  // ── Pagar con tarjeta guardada (charge) ────────────────────────────────────
  const handlePagarConTarjeta = useCallback(async () => {
    if (!montoValido || !cardIdSeleccionado || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post('/core/bancard/pagar-cc-con-tarjeta/', {
        monto: montoEfectivo, card_id: cardIdSeleccionado,
        ...(origen ? { origen } : {}),
      })

      if (data.requires_3ds) {
        setProcessId3ds(data.process_id)
        setScriptUrl3ds(data.script_url)
        setPago3dsEnProceso(true)
        return
      }

      const params = new URLSearchParams({ estado: data.estado, tipo: 'cc' })
      if (data.monto) params.set('monto', String(data.monto))
      window.location.href = `${window.location.pathname}?${params.toString()}`
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al procesar el pago'
      toast.error(msg)
      setIniciando(false)
    }
  }, [montoValido, montoEfectivo, cardIdSeleccionado, origen, iniciando])

  // ── Mantener sesión activa mientras el iframe de Bancard está visible ────────
  useEffect(() => {
    if (!pagoEnProceso && !pago3dsEnProceso) return
    const interval = setInterval(() => resetInactivityTimer(), 60_000)
    return () => clearInterval(interval)
  }, [pagoEnProceso, pago3dsEnProceso, resetInactivityTimer])

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
      window.Bancard?.Charge3DS.createForm('bancard-cc-3ds-container', processId3ds)
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

  // ── Cargar script Bancard y renderizar formulario embebido ─────────────────
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
      window.Bancard?.Checkout.createForm('bancard-cc-checkout-container', processId)
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

  // ── Nuevo pago tras resultado ──────────────────────────────────────────────
  const handleNuevoPago = () => {
    setSearchParams({})
    setMontoSeleccionado(null)
    setMontoCustom('')
    setUsandoCustom(false)
    setOrigen('')
    setMetodoPago('ocasional')
    setCardIdSeleccionado(null)
    cargarDeuda()
  }

  // ─── Renderizado ─────────────────────────────────────────────────────────

  // Formulario embebido de Bancard (iframe via JS SDK)
  if (pagoEnProceso) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Pagar Cuenta Corriente</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="mb-4">
            <p className="text-base font-semibold text-slate-800">Ingresá los datos de tu tarjeta</p>
            <p className="text-sm text-slate-500 mt-0.5">
              El formulario es provisto por Bancard — tus datos de tarjeta son seguros.
            </p>
          </div>
          <div id="bancard-cc-checkout-container" className="min-h-[420px]" />
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
        <h1 className="text-2xl font-bold text-slate-900">Pagar Cuenta Corriente</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="mb-4">
            <p className="text-base font-semibold text-slate-800">Verificación de seguridad</p>
            <p className="text-sm text-slate-500 mt-0.5">
              Tu banco requiere un paso adicional para confirmar el pago.
            </p>
          </div>
          <div id="bancard-cc-3ds-container" className="min-h-[380px]" />
        </div>
      </div>
    )
  }

  // Mostrar resultado si Bancard redirigió de vuelta
  if (estadoRetorno) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Pagar Cuenta Corriente</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <ResultadoPago estado={estadoRetorno} monto={montoRetorno} />
          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={handleNuevoPago}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors cursor-pointer text-base"
            >
              <RefreshCw className="w-4 h-4" />
              Volver a intentar
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loadingDeuda) return <Spinner className="mt-16" />

  if (!deuda || deuda <= 0) {
    return (
      <div className="py-16 text-center text-slate-400">
        <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-30" />
        <p className="text-base font-medium text-slate-600">No tenés deuda pendiente</p>
        <p className="text-sm mt-1">Tu cuenta corriente está al día.</p>
      </div>
    )
  }

  const montosRapidos = [Math.round(deudaOrigenSeleccionado / 2), deudaOrigenSeleccionado]
    .filter((m, i, arr) => m > 0 && arr.indexOf(m) === i)
  const pasoMonto = requiereElegirOrigen ? 2 : 1
  const pasoMetodo = requiereElegirOrigen ? 3 : 2

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Pagar Cuenta Corriente</h1>
        <p className="text-base text-slate-500 mt-0.5">Pagá tu deuda con Visa o Mastercard</p>
      </div>

      {/* ── Deuda actual ── */}
      <div className="bg-red-50 border border-red-200 rounded-2xl px-5 py-4">
        <p className="text-sm text-slate-500">Deuda actual</p>
        <p className="text-3xl font-bold text-red-700 tabular-nums">{formatGs(deuda)}</p>
        {requiereElegirOrigen && (
          <p className="text-sm text-red-600 mt-1">
            Cantina: {formatGs(deudaCantina)} · Almuerzo: {formatGs(deudaAlmuerzo)}
          </p>
        )}
      </div>

      {/* ── Paso: Elegí a qué corresponde (solo si debe en ambas) ── */}
      {requiereElegirOrigen && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              1 — ¿A qué deuda corresponde el pago?
            </p>
          </div>
          <div className="p-5 grid grid-cols-2 gap-2.5">
            {(['CANTINA', 'ALMUERZO'] as const).map(op => (
              <button
                key={op}
                type="button"
                onClick={() => { setOrigen(op); setMontoSeleccionado(null); setUsandoCustom(false) }}
                className={[
                  'py-3 rounded-xl border-2 text-sm font-bold transition-all cursor-pointer',
                  origen === op
                    ? 'bg-red-600 border-red-600 text-white shadow-sm'
                    : 'border-slate-200 text-slate-700 hover:border-red-300 hover:bg-red-50',
                ].join(' ')}
              >
                {op === 'CANTINA' ? 'Cantina' : 'Almuerzo'} ({formatGs(op === 'CANTINA' ? deudaCantina : deudaAlmuerzo)})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Paso: Elegí el monto ── */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
            {pasoMonto} — Elegí cuánto pagar
          </p>
        </div>
        <div className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-2.5">
            {montosRapidos.map(m => (
              <button
                key={m}
                type="button"
                onClick={() => { setMontoSeleccionado(m); setUsandoCustom(false) }}
                className={[
                  'py-3 rounded-xl border-2 text-sm font-bold transition-all cursor-pointer whitespace-nowrap',
                  !usandoCustom && montoSeleccionado === m
                    ? 'bg-red-600 border-red-600 text-white shadow-sm'
                    : 'border-slate-200 text-slate-700 hover:border-red-300 hover:bg-red-50',
                ].join(' ')}
              >
                {m === deudaOrigenSeleccionado ? `Pagar el total (${formatGs(m)})` : formatGs(m)}
              </button>
            ))}
          </div>

          <div>
            <button
              type="button"
              onClick={() => setUsandoCustom(v => !v)}
              className="text-sm text-red-600 font-medium hover:text-red-700 transition-colors cursor-pointer"
            >
              {usandoCustom ? '← Usar monto rápido' : 'Otro monto...'}
            </button>
            {usandoCustom && (
              <div className="mt-2 relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-base font-medium pointer-events-none">
                  Gs.
                </span>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="50000"
                  value={montoCustom}
                  onChange={e => setMontoCustom(e.target.value.replace(/\D/g, ''))}
                  className="w-full border border-slate-200 rounded-xl pl-10 pr-3.5 py-2.5 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-red-500/30 focus:border-red-500 transition-colors"
                />
              </div>
            )}
          </div>

          {requiereElegirOrigen && !origen && (
            <p className="text-sm text-red-500">Elegí primero a qué deuda corresponde el pago.</p>
          )}
          {montoEfectivo > 0 && origen !== '' && !montoValido && (
            <p className="text-sm text-red-500">
              El monto no puede superar la deuda de {origen === 'CANTINA' ? 'cantina' : 'almuerzo'} ({formatGs(deudaOrigenSeleccionado)}).
            </p>
          )}
          {montoEfectivo > 0 && !requiereElegirOrigen && !montoValido && (
            <p className="text-sm text-red-500">
              El monto no puede superar tu deuda actual ({formatGs(deuda)}).
            </p>
          )}
        </div>
      </div>

      {/* ── Paso: Método de pago ── */}
      {/* No depende de montoValido: llegar acá ya implica deuda > 0, y el
          catastro de tarjeta ("Tarjeta guardada") no requiere un monto elegido. */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
            {pasoMetodo} — Método de pago
          </p>
        </div>
        <div className="flex border-b border-slate-100">
          <button
            type="button"
            onClick={() => setMetodoPago('ocasional')}
            className={[
              'flex-1 py-3 text-sm font-semibold transition-colors cursor-pointer',
              metodoPago === 'ocasional'
                ? 'text-red-700 border-b-2 border-red-600'
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
                ? 'text-red-700 border-b-2 border-red-600'
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
            accent="red"
            containerIdPrefix="pagar-cc"
          />
        )}
      </div>

      {/* ── Resumen + botón ── */}
      {montoEfectivo > 0 && montoValido && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Resumen</p>
          </div>
          <div className="px-5 py-4 space-y-2">
            <div className="flex justify-between text-base">
              <span className="text-slate-500">Monto a pagar</span>
              <span className="text-xl font-bold tabular-nums text-red-700">{formatGs(montoEfectivo)}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Info de seguridad ── */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 flex items-start gap-3">
        <CreditCard className="w-5 h-5 text-slate-400 shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-slate-700">Pago seguro con Bancard</p>
          <p className="text-sm text-slate-500 mt-0.5">
            {metodoPago === 'guardada'
              ? 'Al presionar «Ir a pagar», se cobrará con la tarjeta guardada que seleccionaste.'
              : 'Al presionar «Ir a pagar», se abrirá el formulario seguro de Bancard en esta misma página. Ingresá tu CI, número de tarjeta (Visa o Mastercard), vencimiento y CVV.'}
            {' '}Cantina Tita no almacena datos de tarjeta.
          </p>
        </div>
      </div>

      {/* ── Botón principal ── */}
      {(() => {
        const listo = montoValido && (metodoPago === 'ocasional' || cardIdSeleccionado !== null)
        return (
          <button
            type="button"
            onClick={metodoPago === 'ocasional' ? handlePagar : handlePagarConTarjeta}
            disabled={!listo || iniciando}
            className={[
              'w-full flex items-center justify-center gap-3 py-4 rounded-2xl',
              'text-lg font-bold transition-all',
              listo && !iniciando
                ? 'bg-red-600 hover:bg-red-700 text-white cursor-pointer shadow-lg shadow-red-600/20 active:scale-[0.98]'
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

      <p className="text-center text-sm text-slate-400">
        Hola, {user?.nombre}. Solo se realizará un cargo si completás el pago en Bancard.
      </p>
      <p className="text-center text-xs text-slate-400">
        Al continuar, aceptás los{' '}
        <Link to="/portal/terminos" target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline">
          Términos y Condiciones
        </Link>
      </p>
    </div>
  )
}
