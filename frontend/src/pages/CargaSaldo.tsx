import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  CreditCard, Search, CheckCircle, RefreshCw, History,
  ArrowUp, ArrowDown, X, Wallet, Printer, BookOpen, Banknote, UtensilsCrossed,
} from 'lucide-react'
import api from '../services/api'
import tarjetasService from '../services/tarjetas'
import { METODOS_PAGO as METODOS } from '../constants/mediosPago'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Table, { type Column } from '../components/ui/Table'
import {
  extractErrorMessage, formatGs, formatFecha, abrirRecibo,
  type Tarjeta, type Movimiento, type CargaReciente, type UltimaCarga,
  MONTOS_RAPIDOS, TIPO_COLOR, ESTADO_COLOR,
} from './cargasaldo/shared'
import ModalConfirmarCarga from './cargasaldo/ModalConfirmarCarga'

export default function CargaSaldo() {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  // ── Búsqueda de tarjeta ──────────────────────────────────────────
  const [busqueda, setBusqueda] = useState(() => searchParams.get('tarjeta') ?? '')
  const [tarjeta, setTarjeta] = useState<Tarjeta | null>(null)
  const [buscando, setBuscando] = useState(false)
  const inputBusquedaRef = useRef<HTMLInputElement>(null)
  const limpiarTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  // ── Tipo de saldo a cargar: cantina (tarjeta) o almuerzo (cuenta corriente) ──
  const [tipoSaldo, setTipoSaldo] = useState<'CANTINA' | 'ALMUERZO'>(
    () => (searchParams.get('tipo') === 'ALMUERZO' ? 'ALMUERZO' : 'CANTINA')
  )
  const [saldoAlmuerzo, setSaldoAlmuerzo] = useState<number | null>(null)
  const [ultimaCargaAlmuerzo, setUltimaCargaAlmuerzo] = useState<{
    monto: number; metodo: string; estado: string; hijoNombre: string
  } | null>(null)

  // ── Formulario de carga ──────────────────────────────────────────
  const [tipoCobro, setTipoCobro] = useState<'CONTADO' | 'CREDITO'>('CONTADO')
  const [monto, setMonto] = useState('')
  const [metodo, setMetodo] = useState('EFECTIVO')
  const [referencia, setReferencia] = useState('')
  const [cargando, setCargando] = useState(false)
  const [emitirFacturaCarga, setEmitirFacturaCarga] = useState(false)
  const [nroFacturaCarga, setNroFacturaCarga] = useState('')

  // ── Historial ────────────────────────────────────────────────────
  const [movimientos, setMovimientos] = useState<Movimiento[]>([])
  const [cargas, setCargas] = useState<CargaReciente[]>([])
  const [loadingHistorial, setLoadingHistorial] = useState(false)
  const [historialTab, setHistorialTab] = useState<'movimientos' | 'cargas'>('movimientos')

  // ── Última operación exitosa ─────────────────────────────────────
  const [ultimaCarga, setUltimaCarga] = useState<UltimaCarga | null>(null)

  // ── Confirmar carga pendiente ─────────────────────────────────────
  const [confirmCargaId, setConfirmCargaId] = useState<number | null>(null)

  // ── Cargar historial ─────────────────────────────────────────────
  const cargarHistorial = useCallback(async (nro: string) => {
    setLoadingHistorial(true)
    try {
      const [movRes, cargaRes] = await Promise.all([
        tarjetasService.getMovimientos<Movimiento>(nro, 20),
        tarjetasService.getCargas<CargaReciente>(nro, 20),
      ])
      setMovimientos(movRes.data.results ?? [])
      setCargas(cargaRes.data.results ?? [])
    } catch {
      // historial es secundario, no bloquear
    } finally {
      setLoadingHistorial(false)
    }
  }, [])

  // ── Buscar tarjeta ────────────────────────────────────────────────
  const buscarTarjeta = useCallback(async (overrideQuery?: string) => {
    const q = (overrideQuery ?? busqueda).trim()
    if (!q) { toast.error('Ingresá el número de tarjeta'); return }
    setBuscando(true)
    setTarjeta(null)
    setMovimientos([])
    setCargas([])
    setUltimaCarga(null)
    try {
      const { data } = await tarjetasService.buscar<Tarjeta>(q)
      const found: Tarjeta | undefined = (data.results ?? []).find(
        (t) => t.nro_tarjeta === q || t.codigo_barras === q
      )
      if (!found) { toast.error('Tarjeta no encontrada'); return }
      if (found.estado !== 'ACTIVA') {
        toast.error(`Tarjeta ${found.estado.toLowerCase()} — no se puede recargar`)
        return
      }
      setTarjeta(found)
      cargarHistorial(found.nro_tarjeta)

      if (found.hijo) {
        try {
          const { data } = await api.get('/almuerzos/saldos/', { params: { hijo: found.hijo } })
          const item = (data.results ?? data)[0]
          setSaldoAlmuerzo(item ? Number(item.saldo_actual) : 0)
        } catch {
          setSaldoAlmuerzo(null)
        }
      } else {
        setSaldoAlmuerzo(null)
      }
    } catch {
      toast.error('Error al buscar tarjeta')
    } finally {
      setBuscando(false)
    }
  }, [busqueda, cargarHistorial])

  // Auto-focus al inicio, o búsqueda automática si vino con ?tarjeta= (desde
  // ModoRecreo): disparar la búsqueda sincrónicamente al montar es intencional.
  useEffect(() => {
    const nroPreseleccionado = searchParams.get('tarjeta')
    if (nroPreseleccionado) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      buscarTarjeta(nroPreseleccionado)
    } else {
      inputBusquedaRef.current?.focus()
    }
    return () => clearTimeout(limpiarTimerRef.current)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Realizar carga de saldo de almuerzo (cuenta corriente del hijo) ─────────
  const handleCargarAlmuerzo = useCallback(async () => {
    const montoNum = Number(monto)
    if (!tarjeta) { toast.error('Buscá primero la tarjeta'); return }
    if (!tarjeta.hijo) { toast.error('Esta tarjeta no tiene un alumno asociado'); return }
    if (!montoNum || montoNum <= 0) { toast.error('Ingresá un monto válido'); return }

    const metodoInfo = METODOS.find(m => m.value === metodo)
    if (metodoInfo?.requiere_referencia && !referencia.trim()) {
      toast.error('Ingresá el código de transacción')
      return
    }
    if (metodoInfo?.autoconfirma && emitirFacturaCarga && !nroFacturaCarga.trim()) {
      toast.error('Ingresá el número de factura')
      return
    }

    setCargando(true)
    try {
      const payload: { hijo: number; monto_cargado: number; metodo_pago: string; referencia?: string; nro_factura?: string } = {
        hijo:          tarjeta.hijo,
        monto_cargado: montoNum,
        metodo_pago:   metodo,
        ...(referencia.trim() ? { referencia: referencia.trim() } : {}),
        ...(metodoInfo?.autoconfirma && emitirFacturaCarga && nroFacturaCarga.trim()
          ? { nro_factura: nroFacturaCarga.trim() }
          : {}),
      }

      const { data } = await api.post('/almuerzos/recargas-saldo/', payload)

      const { data: saldoRes } = await api.get('/almuerzos/saldos/', { params: { hijo: tarjeta.hijo } })
      const item = (saldoRes.results ?? saldoRes)[0]
      setSaldoAlmuerzo(item ? Number(item.saldo_actual) : montoNum)

      setUltimaCargaAlmuerzo({
        monto: montoNum,
        metodo,
        estado: data.estado ?? 'CONFIRMADA',
        hijoNombre: tarjeta.hijo_nombre,
      })

      if (metodoInfo?.autoconfirma) {
        toast.success(`Recarga de ${formatGs(montoNum)} confirmada`)
      } else {
        toast.success(`Recarga de ${formatGs(montoNum)} registrada — pendiente de confirmación`)
      }

      setMonto('')
      setReferencia('')
      setEmitirFacturaCarga(false)
      setNroFacturaCarga('')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setCargando(false)
    }
  }, [tarjeta, monto, metodo, referencia, emitirFacturaCarga, nroFacturaCarga])

  // ── Realizar carga de saldo de cantina (tarjeta) ────────────────────────────
  const handleCargar = useCallback(async () => {
    if (tipoSaldo === 'ALMUERZO') { handleCargarAlmuerzo(); return }

    const montoNum = Number(monto)
    if (!tarjeta) { toast.error('Buscá primero la tarjeta'); return }
    if (!montoNum || montoNum <= 0) { toast.error('Ingresá un monto válido'); return }

    const metodoEfectivo = tipoCobro === 'CREDITO' ? 'CUENTA_CORRIENTE' : metodo
    const metodoInfo = METODOS.find(m => m.value === metodoEfectivo)

    if (tipoCobro === 'CONTADO' && metodoInfo?.requiere_referencia && !referencia.trim()) {
      toast.error('Ingresá el código de transacción')
      return
    }
    if (tipoCobro === 'CONTADO' && metodoInfo?.autoconfirma && emitirFacturaCarga && !nroFacturaCarga.trim()) {
      toast.error('Ingresá el número de factura')
      return
    }

    setCargando(true)
    try {
      const cargaPayload: { tarjeta: string; monto_cargado: number; metodo_pago: string; referencia?: string; nro_factura?: string } = {
        tarjeta:       tarjeta.nro_tarjeta,
        monto_cargado: montoNum,
        metodo_pago:   metodoEfectivo,
        ...(referencia.trim() ? { referencia: referencia.trim() } : {}),
        ...(tipoCobro === 'CONTADO' && metodoInfo?.autoconfirma && emitirFacturaCarga && nroFacturaCarga.trim()
          ? { nro_factura: nroFacturaCarga.trim() }
          : {}),
      }

      const { data } = await tarjetasService.crearCarga(cargaPayload)

      const { data: tarjetaActualizada } = await tarjetasService.getByNro<Tarjeta>(tarjeta.nro_tarjeta)
      setTarjeta(tarjetaActualizada)
      cargarHistorial(tarjeta.nro_tarjeta)

      setUltimaCarga({
        monto: montoNum,
        metodo: metodoEfectivo,
        tipoCobro,
        estado: data.estado ?? 'CONFIRMADA',
        tarjeta: tarjetaActualizada,
        fecha: new Date().toISOString(),
      })

      if (tipoCobro === 'CREDITO') {
        toast.success(`Recarga de ${formatGs(montoNum)} acreditada a cuenta corriente`)
      } else if (metodoInfo?.autoconfirma) {
        toast.success(`Recarga de ${formatGs(montoNum)} confirmada`)
      } else {
        toast.success(`Carga de ${formatGs(montoNum)} registrada — pendiente de confirmación`)
      }

      setMonto('')
      setReferencia('')
      setEmitirFacturaCarga(false)
      setNroFacturaCarga('')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setCargando(false)
    }
  }, [tarjeta, monto, metodo, tipoCobro, referencia, emitirFacturaCarga, nroFacturaCarga, cargarHistorial, tipoSaldo, handleCargarAlmuerzo])

  // ── Limpiar y nueva operación ─────────────────────────────────────
  const limpiar = useCallback(() => {
    setTarjeta(null)
    setBusqueda('')
    setMonto('')
    setReferencia('')
    setMetodo('EFECTIVO')
    setTipoCobro('CONTADO')
    setEmitirFacturaCarga(false)
    setNroFacturaCarga('')
    setMovimientos([])
    setCargas([])
    setUltimaCarga(null)
    setTipoSaldo('CANTINA')
    setSaldoAlmuerzo(null)
    setUltimaCargaAlmuerzo(null)
    limpiarTimerRef.current = setTimeout(() => inputBusquedaRef.current?.focus(), 50)
  }, [])

  const metodoSeleccionado = METODOS.find(m => m.value === metodo)
  const saldoCC = Number(tarjeta?.cliente_saldo_cc ?? 0)
  const limiteCC = Number(tarjeta?.cliente_limite_credito ?? 0)
  const mostrarMetodoPago = tipoSaldo === 'ALMUERZO' || tipoCobro === 'CONTADO'

  // ── Columnas historial ────────────────────────────────────────────
  const colsMovimientos: Column<Movimiento>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-400">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <Badge color={TIPO_COLOR[r.tipo] ?? 'default'}>{r.tipo}</Badge>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => {
        const entrada = r.tipo === 'RECARGA' || r.tipo === 'REVERSO'
        return (
          <span className={`tabular-nums font-semibold text-sm flex items-center gap-0.5 ${entrada ? 'text-emerald-700' : 'text-slate-600'}`}>
            {entrada ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {formatGs(r.monto)}
          </span>
        )
      },
    },
    {
      title: 'Saldo resultante',
      key: 'saldo',
      render: (_, r) => (
        <span className={`tabular-nums text-sm font-medium ${Number(r.saldo_resultante) < 0 ? 'text-red-600' : 'text-slate-700'}`}>
          {formatGs(r.saldo_resultante)}
        </span>
      ),
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-sm text-slate-400">{r.descripcion || '—'}</span>,
    },
  ]

  const colsCargas: Column<CargaReciente>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-400">{formatFecha(r.fecha_carga)}</span>,
    },
    {
      title: 'Monto',
      key: 'monto',
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto_cargado)}</span>,
    },
    {
      title: 'Método',
      key: 'metodo',
      render: (_, r) => {
        const label = r.metodo_pago === 'CUENTA_CORRIENTE'
          ? 'Cuenta Corriente'
          : (METODOS.find(m => m.value === r.metodo_pago)?.label ?? r.metodo_pago)
        return <span className="text-sm text-slate-600">{label}</span>
      },
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: '',
      key: 'accion',
      width: 110,
      render: (_, r) => r.estado === 'PENDIENTE' ? (
        <Button size="sm" variant="primary" onClick={() => setConfirmCargaId(r.id)}>
          Confirmar
        </Button>
      ) : null,
    },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">

      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Wallet className="w-6 h-6 text-green-600" />
            {t('cargaSaldo.title')}
          </h1>
          <p className="text-base text-slate-500 mt-0.5">{t('cargaSaldo.subtitle')}</p>
        </div>
        {tarjeta && (
          <button
            onClick={limpiar}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 font-semibold text-sm rounded-xl transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
            {t('cargaSaldo.nueva')}
          </button>
        )}
      </div>

      {/* ── Estado idle: sin tarjeta ── */}
      {!tarjeta && (
        <div className="flex flex-col items-center gap-8 py-10">
          <div className="text-center">
            <div className="w-32 h-32 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6 shadow-sm">
              <CreditCard className="w-16 h-16 text-green-500" />
            </div>
            <p className="text-slate-800 text-4xl font-black">Pasá la tarjeta</p>
            <p className="text-slate-400 text-xl mt-2">o escribí el número y buscá</p>
          </div>

          <div className="w-full max-w-lg">
            <div className="flex gap-3">
              <input
                ref={inputBusquedaRef}
                placeholder="Nro. de tarjeta..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && buscarTarjeta()}
                autoComplete="off"
                className="flex-1 text-center text-3xl font-black tracking-widest py-5 px-6 border-2 rounded-2xl outline-none transition-all duration-150 placeholder:text-slate-300 bg-white border-slate-300 focus:border-green-500 focus:ring-4 focus:ring-green-500/10 text-slate-900 shadow-sm"
              />
              <button
                onClick={() => buscarTarjeta()}
                disabled={buscando}
                className="px-6 bg-green-600 hover:bg-green-500 text-white rounded-2xl flex items-center gap-2 text-lg font-bold transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
              >
                {buscando
                  ? <RefreshCw className="w-5 h-5 animate-spin" />
                  : <Search className="w-5 h-5" />
                }
              </button>
            </div>
            <p className="text-center text-slate-400 text-base mt-2.5 font-medium">
              Enter para buscar
            </p>
          </div>
        </div>
      )}

      {/* ── Con tarjeta: layout 2 columnas ── */}
      {tarjeta && (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

          {/* ── Panel izquierdo: datos + formulario ── */}
          <div className="lg:col-span-2 space-y-5">

            {/* Tarjeta encontrada */}
            <div className="bg-emerald-50 border-2 border-emerald-300 rounded-3xl p-6 shadow-sm">
              <div className="flex items-start justify-between mb-4">
                <div className="w-14 h-14 rounded-full bg-emerald-100 flex items-center justify-center border border-emerald-200">
                  <CreditCard className="w-7 h-7 text-emerald-600" />
                </div>
                <button
                  onClick={limpiar}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-colors cursor-pointer"
                  title="Cambiar tarjeta"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-slate-900 text-3xl font-black leading-tight">{tarjeta.hijo_nombre}</p>
              <p className="text-slate-500 text-lg mt-1">{tarjeta.hijo_grado} · {tarjeta.cliente_nombre}</p>
              <p className="text-slate-400 text-base font-mono mt-1">{tarjeta.nro_tarjeta}</p>
              <div className={`mt-4 pt-4 border-t border-emerald-200 grid gap-3 ${tarjeta.hijo ? 'grid-cols-3' : 'grid-cols-2'}`}>
                <div>
                  <p className="text-slate-500 text-xs font-semibold uppercase tracking-wide">Saldo tarjeta</p>
                  <p className={`text-2xl font-black tabular-nums mt-0.5 ${Number(tarjeta.saldo_disponible) < 0 ? 'text-red-600' : 'text-emerald-700'}`}>
                    {formatGs(tarjeta.saldo_disponible)}
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 text-xs font-semibold uppercase tracking-wide">Saldo CC</p>
                  <p className={`text-2xl font-black tabular-nums mt-0.5 ${saldoCC > 0 ? 'text-orange-600' : 'text-slate-700'}`}>
                    {formatGs(saldoCC)}
                  </p>
                  {saldoCC > 0 && (
                    <p className="text-xs text-orange-500 mt-0.5">deuda pendiente</p>
                  )}
                </div>
                {tarjeta.hijo && (
                  <div>
                    <p className="text-slate-500 text-xs font-semibold uppercase tracking-wide">Saldo almuerzo</p>
                    <p className={`text-2xl font-black tabular-nums mt-0.5 ${saldoAlmuerzo !== null && saldoAlmuerzo < 0 ? 'text-red-600' : 'text-orange-700'}`}>
                      {saldoAlmuerzo === null ? '—' : formatGs(saldoAlmuerzo)}
                    </p>
                    {saldoAlmuerzo !== null && saldoAlmuerzo < 0 && (
                      <p className="text-xs text-red-500 mt-0.5">debe</p>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Formulario de carga */}
            <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 space-y-5">
              <p className="text-slate-800 text-lg font-bold flex items-center gap-2">
                <RefreshCw className="w-5 h-5 text-green-600" />
                Nueva carga
              </p>

              {/* Toggle cantina / almuerzo — solo si la tarjeta tiene un alumno asociado */}
              {tarjeta.hijo && (
                <div>
                  <p className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-2.5">Saldo a cargar</p>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setTipoSaldo('CANTINA')}
                      className={`flex items-center justify-center gap-2 px-3 py-3 rounded-xl text-sm font-bold transition-colors cursor-pointer border-2 ${
                        tipoSaldo === 'CANTINA'
                          ? 'bg-green-600 text-white border-green-600'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-green-400'
                      }`}
                    >
                      <Wallet className="w-4 h-4" />
                      Cantina
                    </button>
                    <button
                      type="button"
                      onClick={() => setTipoSaldo('ALMUERZO')}
                      className={`flex items-center justify-center gap-2 px-3 py-3 rounded-xl text-sm font-bold transition-colors cursor-pointer border-2 ${
                        tipoSaldo === 'ALMUERZO'
                          ? 'bg-orange-600 text-white border-orange-600'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-orange-400'
                      }`}
                    >
                      <UtensilsCrossed className="w-4 h-4" />
                      Almuerzo
                    </button>
                  </div>
                </div>
              )}

              {/* Toggle contado / crédito — solo aplica a saldo de cantina */}
              {tipoSaldo === 'CANTINA' && (
                <div>
                  <p className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-2.5">Tipo de cobro</p>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => { setTipoCobro('CONTADO'); setMetodo('EFECTIVO') }}
                      className={`flex items-center justify-center gap-2 px-3 py-3 rounded-xl text-sm font-bold transition-colors cursor-pointer border-2 ${
                        tipoCobro === 'CONTADO'
                          ? 'bg-green-600 text-white border-green-600'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-green-400'
                      }`}
                    >
                      <Banknote className="w-4 h-4" />
                      Contado
                    </button>
                    <button
                      type="button"
                      onClick={() => setTipoCobro('CREDITO')}
                      className={`flex items-center justify-center gap-2 px-3 py-3 rounded-xl text-sm font-bold transition-colors cursor-pointer border-2 ${
                        tipoCobro === 'CREDITO'
                          ? 'bg-orange-500 text-white border-orange-500'
                          : 'bg-white text-slate-700 border-slate-200 hover:border-orange-400'
                      }`}
                    >
                      <BookOpen className="w-4 h-4" />
                      Crédito CC
                    </button>
                  </div>
                  {tipoCobro === 'CREDITO' && (
                    <div className="mt-2 bg-orange-50 border border-orange-200 rounded-xl px-3 py-2 space-y-0.5">
                      <p className="text-xs text-orange-700 font-semibold">
                        La recarga se acredita a cuenta corriente del responsable.
                      </p>
                      {limiteCC > 0 && (
                        <p className="text-xs text-orange-600">
                          Límite de crédito habilitado: {formatGs(limiteCC)}
                        </p>
                      )}
                      <p className="text-xs text-orange-600">
                        Deuda CC actual: {formatGs(saldoCC)}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Montos rápidos */}
              <div>
                <p className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-2.5">Montos rápidos</p>
                <div className="flex flex-wrap gap-2">
                  {MONTOS_RAPIDOS.map(m => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setMonto(String(m))}
                      className={`px-4 py-2 rounded-xl text-base font-bold transition-colors cursor-pointer ${
                        monto === String(m)
                          ? 'bg-green-600 text-white shadow-sm'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {m.toLocaleString('es-PY')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Monto personalizado */}
              <div>
                <p className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-2">Monto (Gs.) *</p>
                <input
                  type="number"
                  min={1000}
                  step={1000}
                  value={monto}
                  onChange={e => setMonto(e.target.value)}
                  placeholder="0"
                  className="w-full text-center text-3xl font-black tracking-wider py-4 border-2 rounded-2xl outline-none bg-white border-slate-200 focus:border-green-500 focus:ring-4 focus:ring-green-500/10 text-slate-900 placeholder:text-slate-300 transition-all"
                />
              </div>

              {/* Método de pago (contado, o siempre para saldo de almuerzo) */}
              {mostrarMetodoPago && (
                <div>
                  <p className="text-sm font-bold text-slate-500 uppercase tracking-wide mb-2.5">Método de pago</p>
                  <div className="grid grid-cols-2 gap-2">
                    {METODOS.map(m => (
                      <button
                        key={m.value}
                        type="button"
                        onClick={() => { setMetodo(m.value); setReferencia('') }}
                        className={`px-3 py-3 rounded-xl text-sm font-bold text-left transition-colors cursor-pointer border-2 ${
                          metodo === m.value
                            ? 'bg-green-600 text-white border-green-600'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-green-400'
                        }`}
                      >
                        {m.label}
                        {!m.autoconfirma && (
                          <span className={`block text-xs mt-0.5 font-normal ${metodo === m.value ? 'text-green-100' : 'text-slate-400'}`}>
                            queda pendiente
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {mostrarMetodoPago && metodoSeleccionado?.requiere_referencia && (
                <Input
                  label={`Código de transacción${metodoSeleccionado.autoconfirma ? ' *' : ''}`}
                  value={referencia}
                  onChange={e => setReferencia(e.target.value)}
                  placeholder={metodo === 'TRANSFERENCIA' ? 'Nro. de transferencia...' : 'Nro. de comprobante POS...'}
                />
              )}

              {mostrarMetodoPago && metodoSeleccionado?.autoconfirma && (
                <div className="space-y-2">
                  {tipoSaldo === 'CANTINA' && tarjeta?.cliente_modalidad_facturacion === 'MENSUAL' ? (
                    <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 border border-blue-200 rounded-xl">
                      <span className="text-blue-600 text-base">🗓️</span>
                      <span className="text-sm font-semibold text-blue-700">Factura mensual — se acumula para fin de mes</span>
                    </div>
                  ) : (
                    <>
                      <label className="flex items-center gap-2 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={emitirFacturaCarga}
                          onChange={e => { setEmitirFacturaCarga(e.target.checked); setNroFacturaCarga('') }}
                          className="w-4 h-4 rounded accent-green-600"
                        />
                        <span className="text-sm font-semibold text-slate-700">Emitir factura ahora</span>
                      </label>
                      {emitirFacturaCarga && (
                        <input
                          value={nroFacturaCarga}
                          onChange={e => setNroFacturaCarga(e.target.value)}
                          placeholder="001-001-0001234"
                          className="w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150"
                          autoFocus
                        />
                      )}
                    </>
                  )}
                </div>
              )}

              <button
                onClick={handleCargar}
                disabled={cargando}
                className={`w-full py-4 disabled:opacity-50 text-white text-lg font-black rounded-2xl flex items-center justify-center gap-2 transition-colors shadow-sm cursor-pointer ${
                  tipoSaldo === 'ALMUERZO'
                    ? 'bg-orange-600 hover:bg-orange-500'
                    : tipoCobro === 'CREDITO'
                      ? 'bg-orange-500 hover:bg-orange-400'
                      : 'bg-green-600 hover:bg-green-500'
                }`}
              >
                {cargando
                  ? <><RefreshCw className="w-5 h-5 animate-spin" /> Cargando...</>
                  : tipoSaldo === 'ALMUERZO'
                    ? <><UtensilsCrossed className="w-5 h-5" />{metodoSeleccionado?.autoconfirma ? 'Cargar saldo de almuerzo' : 'Registrar recarga pendiente'}</>
                    : tipoCobro === 'CREDITO'
                      ? <><BookOpen className="w-5 h-5" /> Cargar a cuenta corriente</>
                      : <><RefreshCw className="w-5 h-5" />{metodoSeleccionado?.autoconfirma ? 'Cargar saldo' : 'Registrar carga pendiente'}</>
                }
              </button>
            </div>

            {/* Resultado última operación — saldo de almuerzo */}
            {tipoSaldo === 'ALMUERZO' && ultimaCargaAlmuerzo && (
              <div className={`rounded-2xl border-2 p-5 ${
                ultimaCargaAlmuerzo.estado === 'CONFIRMADA'
                  ? 'bg-orange-50 border-orange-300'
                  : 'bg-amber-50 border-amber-300'
              }`}>
                <div className="flex items-center gap-3 mb-2">
                  <CheckCircle className={`w-6 h-6 ${ultimaCargaAlmuerzo.estado === 'CONFIRMADA' ? 'text-orange-600' : 'text-amber-600'}`} />
                  <span className={`text-base font-bold ${ultimaCargaAlmuerzo.estado === 'CONFIRMADA' ? 'text-orange-700' : 'text-amber-700'}`}>
                    {ultimaCargaAlmuerzo.estado === 'CONFIRMADA' ? 'Recarga de almuerzo realizada' : 'Recarga registrada — pendiente'}
                  </span>
                </div>
                <p className="text-3xl font-black tabular-nums text-slate-800">{formatGs(ultimaCargaAlmuerzo.monto)}</p>
                <p className="text-base text-slate-500 mt-0.5">
                  {ultimaCargaAlmuerzo.hijoNombre} · {METODOS.find(m => m.value === ultimaCargaAlmuerzo.metodo)?.label}
                </p>
              </div>
            )}

            {/* Resultado última operación — saldo de cantina */}
            {tipoSaldo === 'CANTINA' && ultimaCarga && (
              <div className={`rounded-2xl border-2 p-5 ${
                ultimaCarga.tipoCobro === 'CREDITO'
                  ? 'bg-orange-50 border-orange-300'
                  : ultimaCarga.estado === 'CONFIRMADA'
                    ? 'bg-emerald-50 border-emerald-300'
                    : 'bg-amber-50 border-amber-300'
              }`}>
                <div className="flex items-center gap-3 mb-2">
                  <CheckCircle className={`w-6 h-6 ${ultimaCarga.tipoCobro === 'CREDITO' ? 'text-orange-600' : ultimaCarga.estado === 'CONFIRMADA' ? 'text-emerald-600' : 'text-amber-600'}`} />
                  <span className={`text-base font-bold ${ultimaCarga.tipoCobro === 'CREDITO' ? 'text-orange-700' : ultimaCarga.estado === 'CONFIRMADA' ? 'text-emerald-700' : 'text-amber-700'}`}>
                    {ultimaCarga.tipoCobro === 'CREDITO'
                      ? 'Carga a cuenta corriente'
                      : ultimaCarga.estado === 'CONFIRMADA'
                        ? 'Carga realizada'
                        : 'Carga registrada — pendiente'
                    }
                  </span>
                </div>
                <p className="text-3xl font-black tabular-nums text-slate-800">{formatGs(ultimaCarga.monto)}</p>
                <p className="text-base text-slate-500 mt-0.5">
                  {ultimaCarga.tipoCobro === 'CREDITO'
                    ? 'Cuenta Corriente (Crédito)'
                    : METODOS.find(m => m.value === ultimaCarga.metodo)?.label
                  }
                </p>
                <button
                  onClick={() => abrirRecibo(ultimaCarga)}
                  className="mt-3 flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 hover:border-slate-400 text-slate-700 text-sm font-semibold rounded-xl transition-colors cursor-pointer"
                >
                  <Printer className="w-4 h-4" />
                  Imprimir recibo
                </button>
              </div>
            )}
          </div>

          {/* ── Panel derecho: historial ── */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
                <History className="w-5 h-5 text-slate-400" />
                <span className="text-base font-bold text-slate-700">Historial — {tarjeta.hijo_nombre}</span>
              </div>
              <div className="border-b border-slate-100 flex">
                {(['movimientos', 'cargas'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setHistorialTab(tab)}
                    className={`px-5 py-3 text-sm font-bold border-b-2 transition-colors cursor-pointer ${
                      historialTab === tab
                        ? 'border-green-600 text-green-700'
                        : 'border-transparent text-slate-500 hover:text-slate-700'
                    }`}
                  >
                    {tab === 'movimientos' ? 'Movimientos' : 'Cargas de saldo'}
                  </button>
                ))}
              </div>
              <div className="p-1">
                {loadingHistorial ? (
                  <div className="py-10 text-center text-slate-400 text-base">Cargando historial...</div>
                ) : historialTab === 'movimientos' ? (
                  <Table columns={colsMovimientos} dataSource={movimientos} rowKey="id" pageSize={8} />
                ) : (
                  <Table columns={colsCargas} dataSource={cargas} rowKey="id" pageSize={8} />
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <ModalConfirmarCarga
        cargaId={confirmCargaId}
        onClose={() => setConfirmCargaId(null)}
        onSaved={async () => {
          if (tarjeta) {
            const { data } = await tarjetasService.getByNro<Tarjeta>(tarjeta.nro_tarjeta)
            setTarjeta(data)
            cargarHistorial(tarjeta.nro_tarjeta)
          }
        }}
      />
    </div>
  )
}
