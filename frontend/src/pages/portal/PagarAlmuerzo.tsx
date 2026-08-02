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

interface CuentaAlmuerzo {
  id: number
  hijo_nombre: string
  mes: number
  anio: number
  cantidad_almuerzos: number
  monto_total: number
  monto_pagado: number
  saldo_pendiente: number
  estado: string
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
               'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

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
                {formatGs(Number(monto))} abonados
              </p>
            )}
            <p className="text-slate-500 text-base mt-2">
              El pago fue registrado en la cuenta de almuerzo.
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

export default function PagarAlmuerzo() {
  const { resetInactivityTimer } = useAuthStore()
  const [searchParams, setSearchParams] = useSearchParams()

  const estadoRetorno = searchParams.get('estado')
  const montoRetorno  = searchParams.get('monto')

  // Pre-cargado desde Dashboard vía query params
  const cuentaIdParam = searchParams.get('cuenta_id')
  const montoParam    = searchParams.get('monto')

  const [cuentas, setCuentas]       = useState<CuentaAlmuerzo[]>([])
  const [loading, setLoading]       = useState(true)
  const [cuentaSeleccionada, setCuentaSeleccionada] = useState<CuentaAlmuerzo | null>(null)
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

  const cargarCuentas = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/almuerzos/cuentas-mensuales/', {
        params: { estado: 'PENDIENTE,PARCIAL', ordering: '-anio,-mes' },
      })
      const lista: CuentaAlmuerzo[] = (data.results ?? data).filter(
        (c: CuentaAlmuerzo) => Number(c.saldo_pendiente) > 0
      )
      setCuentas(lista)

      // Pre-seleccionar si vino desde Dashboard
      if (cuentaIdParam) {
        const preseleccionada = lista.find(c => String(c.id) === cuentaIdParam)
        if (preseleccionada) {
          setCuentaSeleccionada(preseleccionada)
          if (montoParam && !estadoRetorno) {
            setMontoCustom(montoParam)
          }
        }
      } else if (lista.length === 1) {
        setCuentaSeleccionada(lista[0])
        setMontoCustom(String(lista[0].saldo_pendiente))
      }
    } catch {
      toast.error('Error al cargar las cuentas de almuerzo')
    } finally {
      setLoading(false)
    }
  }, [cuentaIdParam, montoParam, estadoRetorno])

  useEffect(() => {
    if (!estadoRetorno) cargarCuentas()
  }, [estadoRetorno, cargarCuentas])

  const montoEfectivo = parseInt(montoCustom.replace(/\D/g, ''), 10) || 0
  const pendiente = cuentaSeleccionada ? Number(cuentaSeleccionada.saldo_pendiente) : 0
  const montoValido = montoEfectivo > 0 && montoEfectivo <= pendiente

  const handlePagar = useCallback(async () => {
    if (!cuentaSeleccionada || !montoValido || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post('/core/bancard/iniciar-almuerzo/', {
        cuenta_id: cuentaSeleccionada.id,
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
  }, [cuentaSeleccionada, montoValido, montoEfectivo, iniciando])

  // ── Pagar con tarjeta guardada (charge) ────────────────────────────────────
  const handlePagarConTarjeta = useCallback(async () => {
    if (!cuentaSeleccionada || !montoValido || !cardIdSeleccionado || iniciando) return

    setIniciando(true)
    try {
      const { data } = await api.post('/core/bancard/pagar-almuerzo-con-tarjeta/', {
        cuenta_id: cuentaSeleccionada.id,
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
        ?.response?.data?.detail ?? 'Error al procesar el pago'
      toast.error(msg)
      setIniciando(false)
    }
  }, [cuentaSeleccionada, montoValido, montoEfectivo, cardIdSeleccionado, iniciando])

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
    cargarCuentas()
  }

  // ── Formulario embebido Bancard ────────────────────────────────────────────
  if (pagoEnProceso) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Pago de Almuerzo</h1>
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
        <h1 className="text-2xl font-bold text-slate-900">Pago de Almuerzo</h1>
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
        <h1 className="text-2xl font-bold text-slate-900">Pago de Almuerzo</h1>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <ResultadoPago estado={estadoRetorno} monto={montoRetorno} />
          <div className="mt-6 flex justify-center">
            <button
              type="button"
              onClick={handleNuevoPago}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors cursor-pointer text-base"
            >
              <RefreshCw className="w-4 h-4" />
              Ver cuentas pendientes
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (loading) return <Spinner className="mt-16" />

  if (cuentas.length === 0) {
    return (
      <div className="py-16 text-center text-slate-400">
        <UtensilsCrossed className="w-12 h-12 mx-auto mb-4 opacity-30" />
        <p className="text-base font-medium text-slate-600">Sin cuentas pendientes</p>
        <p className="text-sm mt-1">No hay deudas de almuerzo para tus hijos.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Pago de Almuerzo</h1>
        <p className="text-base text-slate-500 mt-0.5">
          Abonás la cuenta con Visa o Mastercard vía Bancard
        </p>
      </div>

      {/* Selección de cuenta (si hay más de una) */}
      {cuentas.length > 1 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              1 — Seleccioná la cuenta
            </p>
          </div>
          <div className="divide-y divide-slate-100">
            {cuentas.map(c => (
              <button
                key={c.id}
                type="button"
                onClick={() => {
                  setCuentaSeleccionada(c)
                  setMontoCustom(String(c.saldo_pendiente))
                }}
                className={[
                  'w-full flex items-center justify-between px-5 py-4 text-left transition-colors cursor-pointer',
                  cuentaSeleccionada?.id === c.id
                    ? 'bg-orange-50 border-l-4 border-orange-500'
                    : 'hover:bg-slate-50 border-l-4 border-transparent',
                ].join(' ')}
              >
                <div>
                  <p className="text-base font-semibold text-slate-800">{c.hijo_nombre}</p>
                  <p className="text-sm text-slate-400 mt-0.5">
                    {MESES[c.mes]} {c.anio} · {c.cantidad_almuerzos} almuerzos
                  </p>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <p className="text-sm text-slate-400">Pendiente</p>
                  <p className="text-base font-bold text-red-600 tabular-nums">
                    {formatGs(c.saldo_pendiente)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tarjeta única seleccionada */}
      {cuentaSeleccionada && cuentas.length === 1 && (
        <div className="bg-orange-50 border border-orange-200 rounded-2xl px-5 py-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-base font-bold text-slate-800">{cuentaSeleccionada.hijo_nombre}</p>
              <p className="text-sm text-slate-500 mt-0.5">
                {MESES[cuentaSeleccionada.mes]} {cuentaSeleccionada.anio} · {cuentaSeleccionada.cantidad_almuerzos} almuerzos
              </p>
            </div>
            <div className="text-right shrink-0 ml-4">
              <p className="text-sm text-slate-500">Saldo pendiente</p>
              <p className="text-2xl font-bold text-red-600 tabular-nums">
                {formatGs(cuentaSeleccionada.saldo_pendiente)}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-orange-200">
            <div>
              <p className="text-xs text-slate-400">Total del mes</p>
              <p className="text-sm font-semibold text-slate-700 tabular-nums">{formatGs(cuentaSeleccionada.monto_total)}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Ya pagado</p>
              <p className="text-sm font-semibold text-emerald-700 tabular-nums">{formatGs(cuentaSeleccionada.monto_pagado)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Monto a pagar */}
      {cuentaSeleccionada && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              {cuentas.length > 1 ? '2' : '1'} — Monto a abonar
            </p>
          </div>
          <div className="p-5 space-y-4">
            {/* Botón rápido: total pendiente */}
            <button
              type="button"
              onClick={() => setMontoCustom(String(cuentaSeleccionada.saldo_pendiente))}
              className={[
                'w-full py-3 px-4 rounded-xl border-2 text-base font-bold transition-all cursor-pointer flex items-center justify-between',
                montoEfectivo === pendiente
                  ? 'bg-orange-600 border-orange-600 text-white shadow-sm'
                  : 'border-slate-200 text-slate-700 hover:border-orange-300 hover:bg-orange-50',
              ].join(' ')}
            >
              <span>Pagar total pendiente</span>
              <span className="tabular-nums">{formatGs(cuentaSeleccionada.saldo_pendiente)}</span>
            </button>

            {/* Monto personalizado */}
            <div>
              <p className="text-sm text-slate-500 mb-2">O ingresá un monto parcial:</p>
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
              {montoEfectivo > pendiente && (
                <p className="text-sm text-red-500 mt-1">
                  El monto no puede superar el saldo pendiente ({formatGs(pendiente)}).
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Método de pago */}
      {cuentaSeleccionada && montoValido && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
              {cuentas.length > 1 ? '3' : '2'} — Método de pago
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
      {cuentaSeleccionada && montoEfectivo > 0 && montoValido && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Resumen</p>
          </div>
          <div className="px-5 py-4 space-y-2">
            <div className="flex justify-between text-base">
              <span className="text-slate-500">Alumno</span>
              <span className="font-semibold text-slate-800">{cuentaSeleccionada.hijo_nombre}</span>
            </div>
            <div className="flex justify-between text-base">
              <span className="text-slate-500">Período</span>
              <span className="font-semibold text-slate-800">
                {MESES[cuentaSeleccionada.mes]} {cuentaSeleccionada.anio}
              </span>
            </div>
            <div className="flex justify-between text-base border-t border-slate-100 pt-2 mt-2">
              <span className="text-slate-500">Monto a pagar</span>
              <span className="text-xl font-bold text-orange-700 tabular-nums">
                {formatGs(montoEfectivo)}
              </span>
            </div>
            {montoEfectivo < pendiente && (
              <div className="flex justify-between text-sm text-slate-400">
                <span>Quedará pendiente</span>
                <span className="tabular-nums">{formatGs(pendiente - montoEfectivo)}</span>
              </div>
            )}
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
        const listo = cuentaSeleccionada && montoValido && (metodoPago === 'ocasional' || cardIdSeleccionado !== null)
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
