import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Printer, CheckCircle2, Clock, XCircle } from 'lucide-react'
import cierreCuentasService from '../../services/cierreCuentas'
import { useAuthStore } from '../../store/authStore'
import { formatDateTime } from '../../lib/format'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import { imprimirComprobante } from './comprobante'
import {
  BOLSILLO_LABEL, ESTADO_CIERRE_COLOR, ESTADO_CIERRE_LABEL, ESTADO_RES_COLOR, METODOS_COBRO, METODOS_DEVOLUCION,
  TIPO_LABEL, esAdmin, extractErrorMessage, formatGs, montoMaximo, opcionesResolucion, saldoDe,
  type Bolsillo, type CierreDetalle, type Resolucion, type TipoResolucion,
} from './shared'

interface Props {
  /** El padre monta el modal solo con un expediente abierto: cada apertura arranca limpia. */
  cierreId: number
  onClose: () => void
  onChanged: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 w-full disabled:bg-slate-50 disabled:text-slate-400'
const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1'

const otroBolsillo = (b: Bolsillo): Bolsillo => (b === 'CANTINA' ? 'ALMUERZO' : 'CANTINA')

function TarjetaSaldo({ titulo, actual, inicial }: { titulo: string; actual: number; inicial: string | number }) {
  const estado = actual < 0 ? 'Deuda' : actual > 0 ? 'A favor' : 'Sin saldo'
  const color = actual < 0 ? 'text-red-600' : actual > 0 ? 'text-emerald-700' : 'text-slate-400'
  return (
    <div className="bg-slate-50 rounded-xl px-4 py-3">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{titulo}</p>
      <p className={`text-xl font-bold tabular-nums mt-0.5 ${color}`}>{formatGs(actual)}</p>
      <p className="text-xs text-slate-400 mt-0.5">{estado} · al abrir: {formatGs(inicial)}</p>
    </div>
  )
}

function IconoEstado({ estado }: { estado: Resolucion['estado'] }) {
  if (estado === 'EJECUTADA') return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
  if (estado === 'RECHAZADA') return <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
  return <Clock className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
}

export default function ModalCierre({ cierreId, onClose, onChanged }: Props) {
  const rol = useAuthStore(s => s.user?.rol)
  const [detalle, setDetalle] = useState<CierreDetalle | null>(null)
  const [loading, setLoading] = useState(false)

  const [bolsillo, setBolsillo] = useState<Bolsillo>('CANTINA')
  const [tipo, setTipo] = useState<TipoResolucion | ''>('')
  const [monto, setMonto] = useState('')
  const [bolsilloDestino, setBolsilloDestino] = useState<Bolsillo>('CANTINA')
  const [hermano, setHermano] = useState('')
  const [metodo, setMetodo] = useState('EFECTIVO')
  const [referencia, setReferencia] = useState('')
  const [motivo, setMotivo] = useState('')
  const [saving, setSaving] = useState(false)

  const [cerrando, setCerrando] = useState(false)
  const [motivoCierre, setMotivoCierre] = useState('')

  const elegirTipo = useCallback((d: CierreDetalle, b: Bolsillo, t: TipoResolucion | '') => {
    setBolsillo(b)
    setTipo(t)
    setMonto(t ? String(montoMaximo(d, b, t)) : '')
    setBolsilloDestino(t === 'COMPENSACION' ? otroBolsillo(b) : b)
    setHermano('')
    setMetodo('EFECTIVO')
    setReferencia('')
    setMotivo('')
  }, [])

  const cargar = useCallback(async (id: number) => {
    setLoading(true)
    try {
      const { data } = await cierreCuentasService.detalle(id)
      setDetalle(data)
      // Por defecto: el bolsillo con saldo (deuda primero) y su primera acción disponible.
      const conSaldo = (['CANTINA', 'ALMUERZO'] as Bolsillo[]).filter(b => saldoDe(data, b) !== 0)
      const b = conSaldo.find(x => saldoDe(data, x) < 0) ?? conSaldo[0] ?? 'CANTINA'
      const ops = opcionesResolucion(data, b, rol, data.hermanos)
      elegirTipo(data, b, ops[0]?.tipo ?? '')
    } catch {
      toast.error('Error al cargar el expediente')
    } finally {
      setLoading(false)
    }
  }, [rol, elegirTipo])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargar(cierreId) }, [cierreId, cargar])

  const cerrado = detalle?.estado === 'RESUELTO' || detalle?.estado === 'CERRADO_CON_SALDO'
  const opciones = detalle ? opcionesResolucion(detalle, bolsillo, rol, detalle.hermanos) : []
  const opcion = opciones.find(o => o.tipo === tipo)
  const maximo = detalle && tipo ? montoMaximo(detalle, bolsillo, tipo) : 0
  const conMedio = tipo === 'COBRO' || tipo === 'DEVOLUCION'
  const metodos = tipo === 'DEVOLUCION' ? METODOS_DEVOLUCION : METODOS_COBRO

  const registrar = async () => {
    if (!detalle || !tipo) return
    const m = Number(monto)
    if (!m || m <= 0) { toast.error('Ingresá el monto'); return }
    if (m > maximo) { toast.error(`El monto máximo es ${formatGs(maximo)}`); return }
    if (tipo === 'TRASPASO_HERMANO' && !hermano) { toast.error('Elegí el hermano que recibe el saldo'); return }
    if (conMedio && metodo === 'TRANSFERENCIA' && !referencia.trim()) { toast.error('Ingresá la referencia de la transferencia'); return }
    if (tipo === 'CONDONACION' && motivo.trim().length < 10) { toast.error('La condonación requiere un motivo (mínimo 10 caracteres)'); return }

    setSaving(true)
    try {
      const { data } = await cierreCuentasService.registrar(detalle.id_cierre_cuenta, {
        tipo, bolsillo_origen: bolsillo, monto: m,
        ...(tipo === 'COMPENSACION' || tipo === 'TRASPASO_HERMANO' ? { bolsillo_destino: bolsilloDestino } : {}),
        ...(tipo === 'TRASPASO_HERMANO' ? { hijo_destino: Number(hermano) } : {}),
        ...(conMedio ? { metodo_pago: metodo, referencia: referencia.trim() } : {}),
        ...(motivo.trim() ? { motivo: motivo.trim() } : {}),
      })
      if (data.resolucion.estado === 'SOLICITADA') {
        toast.success('Solicitud enviada: queda pendiente de aprobación de un administrador')
      } else {
        toast.success(`${TIPO_LABEL[tipo]} registrada`)
      }
      if (data.advertencia) toast(data.advertencia, { duration: 9000 })
      await cargar(detalle.id_cierre_cuenta)
      onChanged()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const cerrarConSaldo = async () => {
    if (!detalle) return
    if (!motivoCierre.trim()) { toast.error('Indicá el motivo del cierre'); return }
    setSaving(true)
    try {
      await cierreCuentasService.cerrarConSaldo(detalle.id_cierre_cuenta, motivoCierre.trim())
      toast.success('Expediente cerrado con saldo pendiente')
      setCerrando(false)
      setMotivoCierre('')
      await cargar(detalle.id_cierre_cuenta)
      onChanged()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open
      title={detalle ? `Cierre de cuentas ${detalle.anio} — ${detalle.hijo_nombre}` : 'Cierre de cuentas'}
      onCancel={onClose}
      width={860}
      footer={<Button variant="secondary" onClick={onClose}>Cerrar</Button>}
    >
      {loading && !detalle && <p className="py-10 text-center text-sm text-slate-400">Cargando expediente...</p>}
      {detalle && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
            <Badge color={ESTADO_CIERRE_COLOR[detalle.estado]}>{ESTADO_CIERRE_LABEL[detalle.estado]}</Badge>
            {!detalle.hijo_activo && <Badge color="default">Dado de baja</Badge>}
            <span>{detalle.hijo_grado ?? 'Sin grado'}</span>
            <span className="text-slate-300">·</span>
            <span>Responsable: <strong className="text-slate-800">{detalle.cliente_nombre}</strong></span>
            <span className="text-slate-300">·</span>
            <span className="font-mono">{detalle.nro_tarjeta || 'Sin tarjeta'}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <TarjetaSaldo titulo="Cantina (tarjeta)" actual={detalle.saldo_cantina_actual} inicial={detalle.saldo_cantina_inicial} />
            <TarjetaSaldo titulo="Almuerzo" actual={detalle.saldo_almuerzo_actual} inicial={detalle.saldo_almuerzo_inicial} />
          </div>

          {detalle.estado === 'CERRADO_CON_SALDO' && (
            <div className="rounded-xl bg-orange-50 border border-orange-200 px-4 py-3 text-sm text-orange-800">
              Cerrado con saldo pendiente el {formatDateTime(detalle.fecha_cierre)}. Motivo: {detalle.motivo_cierre}
            </div>
          )}

          {!cerrado && (
            <section className="border border-slate-200 rounded-2xl p-4 space-y-4" aria-label="Nueva resolución">
              <h3 className="text-sm font-semibold text-slate-800">Nueva resolución</h3>

              <div className="flex flex-wrap gap-2">
                {(['CANTINA', 'ALMUERZO'] as Bolsillo[]).map(b => (
                  <button
                    key={b}
                    type="button"
                    onClick={() => elegirTipo(detalle, b, opcionesResolucion(detalle, b, rol, detalle.hermanos)[0]?.tipo ?? '')}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
                      bolsillo === b ? 'bg-green-50 border-green-500 text-green-700' : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {BOLSILLO_LABEL[b]} · {formatGs(saldoDe(detalle, b))}
                  </button>
                ))}
              </div>

              {opciones.length === 0 ? (
                <p className="text-sm text-slate-400">
                  {saldoDe(detalle, bolsillo) === 0
                    ? 'Este bolsillo no tiene saldo para resolver.'
                    : 'Tu rol solo permite cobrar deudas; un supervisor o administrador resuelve los saldos a favor.'}
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className={labelClass} htmlFor="cc-tipo">Acción</label>
                    <select
                      id="cc-tipo" className={inputClass} value={tipo}
                      onChange={e => elegirTipo(detalle, bolsillo, e.target.value as TipoResolucion)}
                    >
                      {opciones.map(o => (
                        <option key={o.tipo} value={o.tipo}>{o.label}{o.pideAprobacion ? ' (requiere aprobación)' : ''}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className={labelClass} htmlFor="cc-monto">Monto (Gs.) — máx. {formatGs(maximo)}</label>
                    <div className="flex gap-2">
                      <input
                        id="cc-monto" type="number" min={1} max={maximo} value={monto}
                        onChange={e => setMonto(e.target.value)} className={inputClass}
                      />
                      <Button size="sm" variant="secondary" onClick={() => setMonto(String(maximo))}>Todo</Button>
                    </div>
                  </div>

                  {tipo === 'TRASPASO_HERMANO' && (
                    <>
                      <div>
                        <label className={labelClass} htmlFor="cc-hermano">Hermano que recibe</label>
                        <select id="cc-hermano" className={inputClass} value={hermano} onChange={e => setHermano(e.target.value)}>
                          <option value="">Elegí un hermano...</option>
                          {detalle.hermanos.map(h => (
                            <option key={h.id_hijo} value={h.id_hijo}>{h.nombre_completo}{h.grado ? ` — ${h.grado}` : ''}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className={labelClass} htmlFor="cc-destino">Lo recibe en</label>
                        <select id="cc-destino" className={inputClass} value={bolsilloDestino} onChange={e => setBolsilloDestino(e.target.value as Bolsillo)}>
                          <option value="CANTINA">Cantina (tarjeta)</option>
                          <option value="ALMUERZO">Almuerzo</option>
                        </select>
                      </div>
                    </>
                  )}

                  {tipo === 'COMPENSACION' && (
                    <p className="sm:col-span-2 text-sm text-slate-600">
                      El saldo a favor de {BOLSILLO_LABEL[bolsillo]} se aplica a la deuda de {BOLSILLO_LABEL[otroBolsillo(bolsillo)]}.
                    </p>
                  )}

                  {conMedio && (
                    <>
                      <div>
                        <label className={labelClass} htmlFor="cc-metodo">{tipo === 'COBRO' ? 'Medio de cobro' : 'Forma de devolución'}</label>
                        <select id="cc-metodo" className={inputClass} value={metodo} onChange={e => setMetodo(e.target.value)}>
                          {metodos.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
                        </select>
                      </div>
                      {metodo === 'TRANSFERENCIA' && (
                        <div>
                          <label className={labelClass} htmlFor="cc-ref">Referencia *</label>
                          <input id="cc-ref" value={referencia} onChange={e => setReferencia(e.target.value)} className={inputClass} placeholder="Nro. de transferencia" />
                        </div>
                      )}
                    </>
                  )}

                  {(tipo === 'CONDONACION' || tipo === 'DEVOLUCION' || tipo === 'TRASLADO_CC') && (
                    <div className="sm:col-span-2">
                      <label className={labelClass} htmlFor="cc-motivo">Motivo{tipo === 'CONDONACION' ? ' * (mínimo 10 caracteres)' : ''}</label>
                      <textarea id="cc-motivo" rows={2} value={motivo} onChange={e => setMotivo(e.target.value)} className={inputClass} />
                    </div>
                  )}
                </div>
              )}

              {opcion?.pideAprobacion && (
                <p className="text-sm rounded-lg bg-amber-50 border border-amber-200 text-amber-800 px-3 py-2">
                  Esta acción queda pendiente: un administrador debe aprobarla antes de que se mueva el saldo.
                </p>
              )}
              {tipo === 'DEVOLUCION' && metodo === 'EFECTIVO' && esAdmin(rol) && (
                <p className="text-xs text-slate-500">La devolución en efectivo sale de tu caja: necesitás tener una caja abierta.</p>
              )}

              {opciones.length > 0 && (
                <div className="flex justify-end">
                  <Button variant="primary" onClick={registrar} loading={saving}>
                    {opcion?.pideAprobacion ? 'Solicitar aprobación' : 'Registrar'}
                  </Button>
                </div>
              )}
            </section>
          )}

          <section aria-label="Historial">
            <h3 className="text-sm font-semibold text-slate-800 mb-3">Historial de resoluciones</h3>
            {detalle.resoluciones.length === 0 ? (
              <p className="text-sm text-slate-400">Todavía no se tomó ninguna resolución.</p>
            ) : (
              <ol className="space-y-3">
                {detalle.resoluciones.map(r => (
                  <li key={r.id_resolucion} className="flex gap-3 border-l-2 border-slate-100 pl-3">
                    <IconoEstado estado={r.estado} />
                    <div className="flex-1 min-w-0 text-sm">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-semibold text-slate-800">{TIPO_LABEL[r.tipo]}</span>
                        <span className="tabular-nums font-semibold">{formatGs(r.monto)}</span>
                        <span className="text-slate-400">{BOLSILLO_LABEL[r.bolsillo_origen]}</span>
                        <Badge color={ESTADO_RES_COLOR[r.estado]}>{r.estado_display}</Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Solicitó {r.solicitado_por_nombre} · {formatDateTime(r.fecha_solicitud)}
                        {r.decidido_por_nombre && <> · {r.estado === 'RECHAZADA' ? 'Rechazó' : 'Autorizó'} {r.decidido_por_nombre}</>}
                      </p>
                      {(r.hijo_destino_nombre || r.metodo_pago || r.referencia || r.motivo || r.motivo_rechazo) && (
                        <p className="text-xs text-slate-500 mt-0.5">
                          {[
                            r.hijo_destino_nombre && `A ${r.hijo_destino_nombre}`,
                            r.metodo_pago,
                            r.referencia && `Ref. ${r.referencia}`,
                            r.motivo,
                            r.motivo_rechazo && `Rechazo: ${r.motivo_rechazo}`,
                          ].filter(Boolean).join(' · ')}
                        </p>
                      )}
                    </div>
                    {r.estado === 'EJECUTADA' && (
                      <Button size="sm" variant="secondary" onClick={() => imprimirComprobante(detalle, r)}>
                        <Printer className="w-3.5 h-3.5" />
                        Comprobante
                      </Button>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>

          {!cerrado && esAdmin(rol) && (
            <section className="border-t border-slate-100 pt-4">
              {!cerrando ? (
                <Button variant="secondary" size="sm" onClick={() => setCerrando(true)}>
                  Cerrar con saldo pendiente
                </Button>
              ) : (
                <div className="space-y-2">
                  <label className={labelClass} htmlFor="cc-motivo-cierre">Motivo del cierre con saldo pendiente</label>
                  <textarea
                    id="cc-motivo-cierre" rows={2} value={motivoCierre}
                    onChange={e => setMotivoCierre(e.target.value)} className={inputClass}
                    placeholder="Ej.: la familia se retiró del país; deuda no cobrable"
                  />
                  <p className="text-xs text-slate-500">Los saldos no se modifican: quedan registrados y reportados.</p>
                  <div className="flex gap-2">
                    <Button variant="primary" size="sm" onClick={cerrarConSaldo} loading={saving}>Confirmar cierre</Button>
                    <Button variant="secondary" size="sm" onClick={() => setCerrando(false)}>Cancelar</Button>
                  </div>
                </div>
              )}
            </section>
          )}
        </div>
      )}
    </Modal>
  )
}
