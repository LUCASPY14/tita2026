import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  UtensilsCrossed, CheckCircle2, XCircle, AlertCircle,
  ChevronRight, Loader2, Wallet, RefreshCw, Clock,
} from 'lucide-react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'

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
  const [iniciando, setIniciando]   = useState(false)

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
      window.location.href = data.redirect_url
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al iniciar el pago'
      toast.error(msg)
      setIniciando(false)
    }
  }, [cuentaSeleccionada, montoValido, montoEfectivo, iniciando])

  const handleNuevoPago = () => {
    setSearchParams({})
    setMontoCustom('')
    cargarCuentas()
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
            Al presionar «Ir a pagar», serás redirigido a la plataforma segura de Bancard
            donde ingresarás tu CI, número de tarjeta (Visa o Mastercard), vencimiento y CVV.
            Cantina Tita no almacena datos de tarjeta.
          </p>
        </div>
      </div>

      {/* Botón principal */}
      <button
        type="button"
        onClick={handlePagar}
        disabled={!cuentaSeleccionada || !montoValido || iniciando}
        className={[
          'w-full flex items-center justify-center gap-3 py-4 rounded-2xl',
          'text-lg font-bold transition-all',
          cuentaSeleccionada && montoValido && !iniciando
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
    </div>
  )
}
