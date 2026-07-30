import { useCallback, useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  CreditCard, CheckCircle2, XCircle, AlertCircle,
  ChevronRight, Loader2, Wallet, RefreshCw,
} from 'lucide-react'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Spinner from '../../components/ui/Spinner'

declare global {
  interface Window {
    Bancard?: {
      Checkout: {
        createForm: (containerId: string, processId: string) => void
      }
    }
  }
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface HijoConTarjeta {
  id: number
  nombre: string
  grado: string | null
  nro_tarjeta: string
  saldo_actual: number
  estado_tarjeta: string
}

// ─── Constantes ───────────────────────────────────────────────────────────────

const MONTOS_RAPIDOS = [50_000, 100_000, 150_000, 200_000, 300_000]

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
                {formatGs(Number(monto))} acreditados
              </p>
            )}
            <p className="text-slate-500 text-base mt-2">
              El saldo fue acreditado en la tarjeta del alumno.
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

  // Hijos disponibles
  const [hijos, setHijos]         = useState<HijoConTarjeta[]>([])
  const [loadingHijos, setLoadingHijos] = useState(true)

  // Selección
  const [hijoSeleccionado, setHijoSeleccionado] = useState<HijoConTarjeta | null>(null)
  const [montoSeleccionado, setMontoSeleccionado] = useState<number | null>(null)
  const [montoCustom, setMontoCustom]   = useState('')
  const [usandoCustom, setUsandoCustom] = useState(false)

  // Proceso de pago
  const [iniciando, setIniciando]         = useState(false)
  const [pagoEnProceso, setPagoEnProceso] = useState(false)
  const [processId, setProcessId]         = useState<string | null>(null)
  const [scriptUrl, setScriptUrl]         = useState<string | null>(null)
  const scriptRef = useRef<HTMLScriptElement | null>(null)

  // ── Cargar hijos con tarjeta ───────────────────────────────────────────────
  const cargarHijos = useCallback(async () => {
    setLoadingHijos(true)
    try {
      const { data } = await api.get('/usuarios/portal/mi-hijo/')
      const lista: HijoConTarjeta[] = (data.hijos ?? [])
        .filter((h: { tarjeta: unknown }) => h.tarjeta)
        .map((h: {
          id: number; nombre: string; grado: string | null
          tarjeta: { nro_tarjeta: string; saldo_actual: number; estado: string }
        }) => ({
          id: h.id,
          nombre: h.nombre,
          grado: h.grado,
          nro_tarjeta: h.tarjeta.nro_tarjeta,
          saldo_actual: h.tarjeta.saldo_actual,
          estado_tarjeta: h.tarjeta.estado,
        }))
      setHijos(lista)
      if (lista.length === 1) setHijoSeleccionado(lista[0])
    } catch {
      toast.error('Error al cargar los datos')
    } finally {
      setLoadingHijos(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!estadoRetorno) cargarHijos()
  }, [estadoRetorno, cargarHijos])

  // ── Monto efectivo ─────────────────────────────────────────────────────────
  const montoEfectivo = usandoCustom
    ? (parseInt(montoCustom.replace(/\D/g, ''), 10) || 0)
    : (montoSeleccionado ?? 0)

  const montoValido = montoEfectivo >= 10_000 && montoEfectivo <= 5_000_000

  // ── Iniciar pago ───────────────────────────────────────────────────────────
  const handlePagar = useCallback(async () => {
    if (!hijoSeleccionado || !montoValido || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post('/core/bancard/iniciar/', {
        nro_tarjeta: hijoSeleccionado.nro_tarjeta,
        monto: montoEfectivo,
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
  }, [hijoSeleccionado, montoValido, montoEfectivo, iniciando])

  // ── Mantener sesión activa mientras el iframe de Bancard está visible ────────
  useEffect(() => {
    if (!pagoEnProceso) return
    // El timer de inactividad no detecta clicks dentro del iframe de Bancard.
    // Reseteamos manualmente cada minuto para evitar un cierre de sesión silencioso.
    const interval = setInterval(() => resetInactivityTimer(), 60_000)
    return () => clearInterval(interval)
  }, [pagoEnProceso, resetInactivityTimer])

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

  // Mostrar resultado si Bancard redirigió de vuelta
  if (estadoRetorno) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Carga de Saldo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <ResultadoPago estado={estadoRetorno} monto={montoRetorno} />
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Carga de Saldo</h1>
        <p className="text-base text-slate-500 mt-0.5">
          Recargá la tarjeta con Visa o Mastercard
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
                key={h.id}
                type="button"
                onClick={() => setHijoSeleccionado(h)}
                className={[
                  'w-full flex items-center justify-between px-5 py-4 text-left transition-colors cursor-pointer',
                  hijoSeleccionado?.id === h.id
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
                  <p className="text-sm text-slate-400">Saldo actual</p>
                  <p className="text-base font-bold text-emerald-700 tabular-nums">
                    {formatGs(h.saldo_actual)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tarjeta única — mostrar saldo directamente */}
      {hijos.length === 1 && hijoSeleccionado && (
        <div className="bg-green-50 border border-green-200 rounded-2xl px-5 py-4 flex items-center justify-between">
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
      )}

      {/* ── Paso 2: Seleccionar monto ── */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
            {hijos.length > 1 ? '2' : '1'} — Elegí el monto a cargar
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
                  'py-3 rounded-xl border-2 text-base font-bold transition-all cursor-pointer',
                  !usandoCustom && montoSeleccionado === m
                    ? 'bg-green-600 border-green-600 text-white shadow-sm'
                    : 'border-slate-200 text-slate-700 hover:border-green-300 hover:bg-green-50',
                ].join(' ')}
              >
                {(m / 1000).toFixed(0)}k
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
              El monto debe estar entre Gs. 10.000 y Gs. 5.000.000.
            </p>
          )}
        </div>
      </div>

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
              <span className="text-slate-500">Tarjeta</span>
              <span className="font-semibold text-slate-800">{hijoSeleccionado.nro_tarjeta}</span>
            </div>
            <div className="flex justify-between text-base border-t border-slate-100 pt-2 mt-2">
              <span className="text-slate-500">Monto a cargar</span>
              <span className="text-xl font-bold text-emerald-700 tabular-nums">
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
            Al presionar «Ir a pagar», se abrirá el formulario seguro de Bancard en esta misma
            página. Ingresá tu CI, número de tarjeta (Visa o Mastercard), vencimiento y CVV.
            Cantina Tita no almacena datos de tarjeta.
          </p>
        </div>
      </div>

      {/* ── Botón principal ── */}
      <button
        type="button"
        onClick={handlePagar}
        disabled={!hijoSeleccionado || !montoValido || iniciando}
        className={[
          'w-full flex items-center justify-center gap-3 py-4 rounded-2xl',
          'text-lg font-bold transition-all',
          hijoSeleccionado && montoValido && !iniciando
            ? 'bg-green-600 hover:bg-green-700 text-white cursor-pointer shadow-lg shadow-green-600/20 active:scale-[0.98]'
            : 'bg-slate-200 text-slate-400 cursor-not-allowed',
        ].join(' ')}
      >
        {iniciando ? (
          <><Loader2 className="w-5 h-5 animate-spin" />Iniciando pago…</>
        ) : (
          <><Wallet className="w-5 h-5" />Ir a pagar<ChevronRight className="w-5 h-5" /></>
        )}
      </button>

      <p className="text-center text-sm text-slate-400">
        Hola, {user?.nombre}. Solo se realizará un cargo si completás el pago en Bancard.
      </p>
    </div>
  )
}
