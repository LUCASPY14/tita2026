import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  CreditCard, CheckCircle2, XCircle, AlertCircle,
  ChevronRight, Loader2, Wallet, RefreshCw, UtensilsCrossed,
} from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Spinner from '../../components/ui/Spinner'
import TarjetasGuardadasBancard from './components/TarjetasGuardadasBancard'

// El tipo global window.Bancard se declara una sola vez en TarjetasGuardadasBancard.tsx

// ─── Interfaces ───────────────────────────────────────────────────────────────

type TipoSaldo = 'CANTINA' | 'ALMUERZO'

interface HijoConTarjeta {
  id_hijo: number
  nombre: string
  grado: string | null
  nro_tarjeta: string
  saldo_actual: number
  estado_tarjeta: string
  saldo_almuerzo: number
}

// ─── Constantes ───────────────────────────────────────────────────────────────

const MONTOS_RAPIDOS = [5_000, 10_000, 20_000, 50_000, 100_000, 200_000]

function formatGs(n: number) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

// ─── Resultado del pago ───────────────────────────────────────────────────────

function ResultadoPago({ estado, monto, tipo }: { estado: string; monto: string | null; tipo: TipoSaldo }) {
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
                {formatGs(Number(monto))} acreditados
              </p>
            )}
            <p className="text-slate-500 text-base mt-2">
              {tipo === 'ALMUERZO'
                ? 'El saldo fue acreditado en la cuenta corriente de almuerzo del alumno.'
                : 'El saldo fue acreditado en la tarjeta del alumno.'}
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

export default function CargaSaldo() {
  const { user, resetInactivityTimer } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()

  // Resultado de retorno desde Bancard
  const estadoRetorno = searchParams.get('estado')
  const montoRetorno  = searchParams.get('monto')

  // Tipo de saldo — desde retorno de Bancard o pre-cargado desde Dashboard
  const tipoParam: TipoSaldo = searchParams.get('tipo')?.toUpperCase() === 'ALMUERZO' ? 'ALMUERZO' : 'CANTINA'
  const hijoIdParam = searchParams.get('hijo_id')

  // Tipo de saldo a cargar: cantina (tarjeta) o almuerzo (cuenta corriente)
  const [tipoSaldo, setTipoSaldo] = useState<TipoSaldo>(tipoParam)

  // Hijos disponibles
  const [hijos, setHijos]         = useState<HijoConTarjeta[]>([])
  const [loadingHijos, setLoadingHijos] = useState(true)

  // Selección
  const [hijoSeleccionado, setHijoSeleccionado] = useState<HijoConTarjeta | null>(null)
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

  // ── Cargar hijos con tarjeta ───────────────────────────────────────────────
  const cargarHijos = useCallback(async () => {
    setLoadingHijos(true)
    try {
      const { data } = await api.get('/usuarios/portal/mi-hijo/')
      const lista: HijoConTarjeta[] = (data.hijos ?? [])
        .filter((h: { tarjeta: unknown }) => h.tarjeta)
        .map((h: {
          id_hijo: number; nombre: string; grado: string | null
          tarjeta: { nro_tarjeta: string; saldo_actual: number; estado: string }
          saldo_almuerzo: number
        }) => ({
          id_hijo: h.id_hijo,
          nombre: h.nombre,
          grado: h.grado,
          nro_tarjeta: h.tarjeta.nro_tarjeta,
          saldo_actual: h.tarjeta.saldo_actual,
          estado_tarjeta: h.tarjeta.estado,
          saldo_almuerzo: h.saldo_almuerzo,
        }))
      setHijos(lista)

      const preseleccionado = hijoIdParam
        ? lista.find(h => String(h.id_hijo) === hijoIdParam)
        : (lista.length === 1 ? lista[0] : undefined)
      if (preseleccionado) setHijoSeleccionado(preseleccionado)
    } catch {
      toast.error('Error al cargar los datos')
    } finally {
      setLoadingHijos(false)
    }
  }, [hijoIdParam])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!estadoRetorno) cargarHijos()
  }, [estadoRetorno, cargarHijos])

  // ── Monto efectivo ─────────────────────────────────────────────────────────
  const montoEfectivo = usandoCustom
    ? (parseInt(montoCustom.replace(/\D/g, ''), 10) || 0)
    : (montoSeleccionado ?? 0)

  const montoValido = tipoSaldo === 'ALMUERZO'
    ? montoEfectivo > 0
    : montoEfectivo >= 5_000 && montoEfectivo <= 5_000_000

  // ── Iniciar pago ocasional (single_buy) ────────────────────────────────────
  const handlePagar = useCallback(async () => {
    if (!hijoSeleccionado || !montoValido || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post(
        tipoSaldo === 'ALMUERZO' ? '/core/bancard/iniciar-almuerzo/' : '/core/bancard/iniciar/',
        tipoSaldo === 'ALMUERZO'
          ? { hijo_id: hijoSeleccionado.id_hijo, monto: montoEfectivo }
          : { nro_tarjeta: hijoSeleccionado.nro_tarjeta, monto: montoEfectivo },
      )
      setProcessId(data.process_id)
      setScriptUrl(data.script_url)
      setPagoEnProceso(true)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al iniciar el pago'
      toast.error(msg)
      setIniciando(false)
    }
  }, [hijoSeleccionado, montoValido, montoEfectivo, iniciando, tipoSaldo])

  // ── Pagar con tarjeta guardada (charge) ────────────────────────────────────
  const handlePagarConTarjeta = useCallback(async () => {
    if (!hijoSeleccionado || !montoValido || !cardIdSeleccionado || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post(
        tipoSaldo === 'ALMUERZO' ? '/core/bancard/pagar-almuerzo-con-tarjeta/' : '/core/bancard/pagar-con-tarjeta/',
        tipoSaldo === 'ALMUERZO'
          ? { hijo_id: hijoSeleccionado.id_hijo, monto: montoEfectivo, card_id: cardIdSeleccionado }
          : { nro_tarjeta: hijoSeleccionado.nro_tarjeta, monto: montoEfectivo, card_id: cardIdSeleccionado },
      )

      if (data.requires_3ds) {
        setProcessId3ds(data.process_id)
        setScriptUrl3ds(data.script_url)
        setPago3dsEnProceso(true)
        return
      }

      // Resuelto en el mismo request: recarga completa forzada para saldo fresco
      // (mismo patrón que PagoCompletado.tsx tras volver de Bancard).
      const params = new URLSearchParams({ estado: data.estado, tipo: tipoSaldo })
      if (data.monto) params.set('monto', String(data.monto))
      window.location.href = `${window.location.pathname}?${params.toString()}`
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al procesar el pago'
      toast.error(msg)
      setIniciando(false)
    }
  }, [hijoSeleccionado, montoValido, montoEfectivo, cardIdSeleccionado, iniciando, tipoSaldo])

  // ── Mantener sesión activa mientras el iframe de Bancard está visible ────────
  useEffect(() => {
    if (!pagoEnProceso && !pago3dsEnProceso) return
    // El timer de inactividad no detecta clicks dentro del iframe de Bancard.
    // Reseteamos manualmente cada minuto para evitar un cierre de sesión silencioso.
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
      window.Bancard?.Charge3DS.createForm('bancard-3ds-container', processId3ds)
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
      window.Bancard?.Checkout.createForm('bancard-checkout-container', processId)
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
    setMetodoPago('ocasional')
    setCardIdSeleccionado(null)
    cargarHijos()
  }

  // ─── Renderizado ─────────────────────────────────────────────────────────

  // Formulario embebido de Bancard (iframe via JS SDK)
  if (pagoEnProceso) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Carga de Saldo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="mb-4">
            <p className="text-base font-semibold text-slate-800">Ingresá los datos de tu tarjeta</p>
            <p className="text-sm text-slate-500 mt-0.5">
              El formulario es provisto por Bancard — tus datos de tarjeta son seguros.
            </p>
          </div>
          <div id="bancard-checkout-container" className="min-h-[420px]" />
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
        <h1 className="text-2xl font-bold text-slate-900">Carga de Saldo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <div className="mb-4">
            <p className="text-base font-semibold text-slate-800">Verificación de seguridad</p>
            <p className="text-sm text-slate-500 mt-0.5">
              Tu banco requiere un paso adicional para confirmar el pago.
            </p>
          </div>
          <div id="bancard-3ds-container" className="min-h-[380px]" />
        </div>
      </div>
    )
  }

  // Mostrar resultado si Bancard redirigió de vuelta
  if (estadoRetorno) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Carga de Saldo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <ResultadoPago estado={estadoRetorno} monto={montoRetorno} tipo={tipoParam} />
          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={handleNuevoPago}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors cursor-pointer text-base"
            >
              <RefreshCw className="w-4 h-4" />
              Realizar otra carga
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loadingHijos) return <Spinner className="mt-16" />

  if (hijos.length === 0) {
    return (
      <div className="py-16 text-center text-slate-400">
        <CreditCard className="w-12 h-12 mx-auto mb-4 opacity-30" />
        <p className="text-base font-medium text-slate-600">Sin tarjetas asignadas</p>
        <p className="text-sm mt-1">Contactá con la administración para asignar una tarjeta.</p>
      </div>
    )
  }

  const stepHijo = hijos.length > 1 ? 1 : 0
  const stepTipo = stepHijo + 1
  const stepMonto = stepTipo + 1
  const stepMetodo = stepMonto + 1

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Carga de Saldo</h1>
        <p className="text-base text-slate-500 mt-0.5">
          {tipoSaldo === 'ALMUERZO'
            ? 'Recargá el saldo de almuerzo con Visa o Mastercard'
            : 'Recargá la tarjeta con Visa o Mastercard'}
        </p>
      </div>

      {/* ── Paso 1: Seleccionar alumno ── */}
      {hijos.length > 1 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              1 — Seleccioná el alumno
            </p>
          </div>
          <div className="divide-y divide-slate-100">
            {hijos.map(h => (
              <button
                key={h.id_hijo}
                type="button"
                onClick={() => setHijoSeleccionado(h)}
                className={[
                  'w-full flex items-center justify-between px-5 py-4 text-left transition-colors cursor-pointer',
                  hijoSeleccionado?.id_hijo === h.id_hijo
                    ? 'bg-green-50 border-l-4 border-green-500'
                    : 'hover:bg-slate-50 border-l-4 border-transparent',
                ].join(' ')}
              >
                <div>
                  <p className="text-base font-semibold text-slate-800">{h.nombre}</p>
                  <p className="text-sm text-slate-400 mt-0.5">
                    {h.grado ?? 'Sin grado'} · Tarjeta {h.nro_tarjeta}
                  </p>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <p className="text-sm text-slate-400">{tipoSaldo === 'ALMUERZO' ? 'Saldo almuerzo' : 'Saldo actual'}</p>
                  <p className={`text-base font-bold tabular-nums ${
                    tipoSaldo === 'ALMUERZO' && h.saldo_almuerzo < 0 ? 'text-red-600' : 'text-emerald-700'
                  }`}>
                    {formatGs(tipoSaldo === 'ALMUERZO' ? h.saldo_almuerzo : h.saldo_actual)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Alumno único — mostrar saldo directamente */}
      {hijos.length === 1 && hijoSeleccionado && (
        <div className="bg-green-50 border border-green-200 rounded-2xl px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-base font-bold text-slate-800">{hijoSeleccionado.nombre}</p>
              <p className="text-sm text-slate-500 mt-0.5">
                {hijoSeleccionado.grado ?? 'Sin grado'} · Tarjeta {hijoSeleccionado.nro_tarjeta}
              </p>
            </div>
            <div className="text-right shrink-0 ml-4">
              <p className="text-sm text-slate-500">Saldo actual</p>
              <p className="text-2xl font-bold text-emerald-700 tabular-nums">
                {formatGs(hijoSeleccionado.saldo_actual)}
              </p>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-green-200 flex items-center justify-between">
            <p className="text-sm text-slate-500">Saldo de almuerzo</p>
            <p className={`text-lg font-bold tabular-nums ${hijoSeleccionado.saldo_almuerzo < 0 ? 'text-red-600' : 'text-orange-700'}`}>
              {formatGs(hijoSeleccionado.saldo_almuerzo)}
            </p>
          </div>
        </div>
      )}

      {/* ── Paso: Tipo de saldo a cargar ── */}
      {hijoSeleccionado && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              {stepTipo} — ¿Qué saldo querés cargar?
            </p>
          </div>
          <div className="p-5 grid grid-cols-2 gap-2.5">
            <button
              type="button"
              onClick={() => setTipoSaldo('CANTINA')}
              className={[
                'flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold transition-colors cursor-pointer border-2',
                tipoSaldo === 'CANTINA'
                  ? 'bg-green-600 text-white border-green-600'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-green-400',
              ].join(' ')}
            >
              <CreditCard className="w-4 h-4" />
              Cantina
            </button>
            <button
              type="button"
              onClick={() => setTipoSaldo('ALMUERZO')}
              className={[
                'flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-bold transition-colors cursor-pointer border-2',
                tipoSaldo === 'ALMUERZO'
                  ? 'bg-orange-600 text-white border-orange-600'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-orange-400',
              ].join(' ')}
            >
              <UtensilsCrossed className="w-4 h-4" />
              Almuerzo
            </button>
          </div>
        </div>
      )}

      {/* ── Paso: Seleccionar monto ── */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
            {stepMonto} — Elegí el monto a cargar
          </p>
        </div>
        <div className="p-5 space-y-4">
          {/* Montos rápidos */}
          <div className="grid grid-cols-3 gap-2.5">
            {MONTOS_RAPIDOS.map(m => (
              <button
                key={m}
                type="button"
                onClick={() => { setMontoSeleccionado(m); setUsandoCustom(false) }}
                className={[
                  'py-3 rounded-xl border-2 text-sm font-bold transition-all cursor-pointer whitespace-nowrap',
                  !usandoCustom && montoSeleccionado === m
                    ? 'bg-green-600 border-green-600 text-white shadow-sm'
                    : 'border-slate-200 text-slate-700 hover:border-green-300 hover:bg-green-50',
                ].join(' ')}
              >
                {formatGs(m)}
              </button>
            ))}
          </div>

          {/* Monto personalizado */}
          <div>
            <button
              type="button"
              onClick={() => setUsandoCustom(v => !v)}
              className="text-sm text-green-600 font-medium hover:text-green-700 transition-colors cursor-pointer"
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
                  placeholder="150000"
                  value={montoCustom}
                  onChange={e => setMontoCustom(e.target.value.replace(/\D/g, ''))}
                  className="w-full border border-slate-200 rounded-xl pl-10 pr-3.5 py-2.5 text-base text-slate-900 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
                />
              </div>
            )}
          </div>

          {/* Monto mínimo hint */}
          {montoEfectivo > 0 && !montoValido && (
            <p className="text-sm text-red-500">
              {tipoSaldo === 'ALMUERZO'
                ? 'Ingresá un monto mayor a cero.'
                : 'El monto debe estar entre Gs. 5.000 y Gs. 5.000.000.'}
            </p>
          )}
        </div>
      </div>

      {/* ── Paso: Método de pago ── */}
      {/* No depende de montoValido: el catastro de tarjeta (pestaña "Tarjeta
          guardada") no requiere un monto, y esconderlo hasta tenerlo lo hacía
          indetectable para quien solo quiere gestionar tarjetas. */}
      {hijoSeleccionado && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              {stepMetodo} — Método de pago
            </p>
          </div>
          <div className="flex border-b border-slate-100">
            <button
              type="button"
              onClick={() => setMetodoPago('ocasional')}
              className={[
                'flex-1 py-3 text-sm font-semibold transition-colors cursor-pointer',
                metodoPago === 'ocasional'
                  ? 'text-green-700 border-b-2 border-green-600'
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
                  ? 'text-green-700 border-b-2 border-green-600'
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
              accent="green"
              containerIdPrefix="carga-saldo"
            />
          )}
        </div>
      )}

      {/* ── Resumen + botón ── */}
      {hijoSeleccionado && montoEfectivo > 0 && montoValido && (
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
              <span className="text-slate-500">{tipoSaldo === 'ALMUERZO' ? 'Saldo a cargar' : 'Tarjeta'}</span>
              <span className="font-semibold text-slate-800">
                {tipoSaldo === 'ALMUERZO' ? 'Almuerzo' : hijoSeleccionado.nro_tarjeta}
              </span>
            </div>
            <div className="flex justify-between text-base border-t border-slate-100 pt-2 mt-2">
              <span className="text-slate-500">Monto a cargar</span>
              <span className={`text-xl font-bold tabular-nums ${tipoSaldo === 'ALMUERZO' ? 'text-orange-700' : 'text-emerald-700'}`}>
                {formatGs(montoEfectivo)}
              </span>
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
                ? tipoSaldo === 'ALMUERZO'
                  ? 'bg-orange-600 hover:bg-orange-700 text-white cursor-pointer shadow-lg shadow-orange-600/20 active:scale-[0.98]'
                  : 'bg-green-600 hover:bg-green-700 text-white cursor-pointer shadow-lg shadow-green-600/20 active:scale-[0.98]'
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
