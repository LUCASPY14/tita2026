import { useCallback, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronRight, RefreshCw, Trash2 } from 'lucide-react'
import api from '../../services/api'
import promocionService, {
  type Decision, type LineaPromocion, type PromocionAnual, type PromocionDetalle,
} from '../../services/promocion'
import { formatDateOnly, formatDateTime } from '../../lib/format'
import Badge, { type BadgeColor } from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage } from '../tarjetas/shared'
import { inputClass, labelClass, type Grado } from './helpers'

const DECISION_LABEL: Record<Decision, string> = {
  PROMUEVE: 'Promueve',
  REPITE: 'Repite',
  CAMBIA: 'Cambia de grado',
  EGRESA: 'Egresa',
  NO_CONTINUA: 'No continúa',
}

const DECISION_COLOR: Record<Decision, BadgeColor> = {
  PROMUEVE: 'green', REPITE: 'orange', CAMBIA: 'blue', EGRESA: 'purple', NO_CONTINUA: 'red',
}

const ORDEN_DECISIONES: Decision[] = ['PROMUEVE', 'REPITE', 'CAMBIA', 'EGRESA', 'NO_CONTINUA']

const selectChica = 'border border-slate-200 rounded-lg px-2 py-1.5 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500'

/** Decisiones que admite un alumno según su grado de origen y si sigue activo. */
function decisionesPosibles(l: Pick<LineaPromocion, 'origen_es_ultimo' | 'hijo_activo'>): Decision[] {
  if (!l.hijo_activo) return ['REPITE', 'EGRESA']
  return l.origen_es_ultimo
    ? ['EGRESA', 'REPITE', 'CAMBIA']
    : ['PROMUEVE', 'REPITE', 'CAMBIA', 'NO_CONTINUA']
}

interface Grupo { id: number | null; nombre: string; lineas: LineaPromocion[] }

function agrupar(lineas: LineaPromocion[]): Grupo[] {
  const grupos: Grupo[] = []
  for (const l of lineas) {
    const ultimo = grupos[grupos.length - 1]
    if (ultimo && ultimo.id === l.grado_origen) ultimo.lineas.push(l)
    else grupos.push({ id: l.grado_origen, nombre: l.grado_origen_nombre ?? 'Sin grado', lineas: [l] })
  }
  return grupos
}

// ── Fila de alumno ───────────────────────────────────────────────────────────

interface FilaProps {
  linea: LineaPromocion
  grados: Grado[]
  editable: boolean
  pendiente: Decision | undefined
  onDecision: (l: LineaPromocion, d: Decision) => void
  onDestino: (l: LineaPromocion, d: Decision, destino: number) => void
  onMotivo: (l: LineaPromocion, motivo: string) => void
}

function FilaAlumno({ linea, grados, editable, pendiente, onDecision, onDestino, onMotivo }: FilaProps) {
  const decision = pendiente ?? linea.decision
  const necesitaDestino = decision === 'PROMUEVE' || decision === 'CAMBIA'
  const sinDestino = necesitaDestino && (pendiente !== undefined || !linea.grado_destino)
  const [motivo, setMotivo] = useState(linea.motivo)
  const pideMotivo = decision === 'REPITE' || decision === 'CAMBIA' || decision === 'NO_CONTINUA'

  return (
    <div className={`flex flex-wrap items-center gap-2 px-4 py-2 border-t border-slate-100 ${sinDestino ? 'bg-amber-50/60' : ''}`}>
      <div className="min-w-[170px] flex-1">
        <span className="text-sm font-medium text-slate-800">{linea.hijo_nombre}</span>
        {!linea.hijo_activo && <Badge color="default" className="ml-2">Dado de baja</Badge>}
      </div>
      {editable ? (
        <>
          <select
            aria-label={`Decisión para ${linea.hijo_nombre}`}
            value={decision}
            onChange={e => onDecision(linea, e.target.value as Decision)}
            className={selectChica}
          >
            {decisionesPosibles(linea).map(d => <option key={d} value={d}>{DECISION_LABEL[d]}</option>)}
          </select>
          {necesitaDestino && (
            <select
              aria-label={`Grado de destino de ${linea.hijo_nombre}`}
              value={pendiente ? '' : (linea.grado_destino ?? '')}
              onChange={e => e.target.value && onDestino(linea, decision, Number(e.target.value))}
              className={`${selectChica} ${sinDestino ? 'border-amber-400' : ''}`}
            >
              <option value="">{sinDestino ? 'Elegir grado…' : '—'}</option>
              {grados.filter(g => g.id_grado !== linea.grado_origen && g.activo).map(g => (
                <option key={g.id_grado} value={g.id_grado}>{g.nombre}</option>
              ))}
            </select>
          )}
          {pideMotivo && !pendiente && (
            <input
              aria-label={`Motivo para ${linea.hijo_nombre}`}
              value={motivo}
              maxLength={500}
              placeholder="Motivo (opcional)"
              onChange={e => setMotivo(e.target.value)}
              onBlur={() => motivo !== linea.motivo && onMotivo(linea, motivo)}
              className={`${selectChica} w-52`}
            />
          )}
        </>
      ) : (
        <div className="flex items-center gap-2">
          <Badge color={DECISION_COLOR[linea.decision]}>{DECISION_LABEL[linea.decision]}</Badge>
          {linea.grado_destino_nombre && <span className="text-sm text-slate-600">→ {linea.grado_destino_nombre}</span>}
          {linea.motivo && <span className="text-xs text-slate-400">{linea.motivo}</span>}
        </div>
      )}
      {editable && sinDestino && (
        <span className="text-xs text-amber-700 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Falta el grado de destino</span>
      )}
    </div>
  )
}

// ── Grupo por grado de origen ────────────────────────────────────────────────

interface GrupoProps {
  grupo: Grupo
  grados: Grado[]
  editable: boolean
  pendientes: Record<number, Decision>
  onDecision: FilaProps['onDecision']
  onDestino: FilaProps['onDestino']
  onMotivo: FilaProps['onMotivo']
  onMasiva: (grado: number, decision: Decision, destino: number | null) => Promise<void>
}

function GrupoGrado({ grupo, grados, editable, pendientes, onDecision, onDestino, onMotivo, onMasiva }: GrupoProps) {
  const hayProblemas = grupo.lineas.some(l => l.problema)
  const [abierto, setAbierto] = useState(hayProblemas)
  const [masDecision, setMasDecision] = useState<Decision>('PROMUEVE')
  const [masDestino, setMasDestino] = useState('')
  const [aplicando, setAplicando] = useState(false)

  const conteo = useMemo(() => {
    const c: Partial<Record<Decision, number>> = {}
    for (const l of grupo.lineas) c[l.decision] = (c[l.decision] ?? 0) + 1
    return c
  }, [grupo.lineas])

  const esUltimo = grupo.lineas[0]?.origen_es_ultimo ?? false
  const opcionesMasivas: Decision[] = esUltimo ? ['EGRESA', 'REPITE'] : ['PROMUEVE', 'REPITE', 'NO_CONTINUA']
  const decisionMasiva = opcionesMasivas.includes(masDecision) ? masDecision : opcionesMasivas[0]
  const muestraDestino = decisionMasiva === 'PROMUEVE'

  const aplicar = async () => {
    if (grupo.id === null) return
    setAplicando(true)
    try {
      await onMasiva(grupo.id, decisionMasiva, muestraDestino && masDestino ? Number(masDestino) : null)
    } finally {
      setAplicando(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
      <button
        type="button"
        onClick={() => setAbierto(a => !a)}
        aria-expanded={abierto}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 cursor-pointer"
      >
        {abierto ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
        <span className="font-semibold text-slate-800">{grupo.nombre}</span>
        <span className="text-sm text-slate-400">{grupo.lineas.length} alumno(s)</span>
        <span className="flex gap-1.5 flex-wrap ml-auto">
          {ORDEN_DECISIONES.filter(d => conteo[d]).map(d => (
            <Badge key={d} color={DECISION_COLOR[d]}>{conteo[d]} {DECISION_LABEL[d].toLowerCase()}</Badge>
          ))}
          {hayProblemas && <Badge color="yellow">Faltan destinos</Badge>}
        </span>
      </button>
      {abierto && (
        <>
          {editable && (
            <div className="flex flex-wrap items-center gap-2 px-4 py-2.5 bg-slate-50 border-t border-slate-100">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Todo el grado:</span>
              <select
                aria-label={`Decisión para todo ${grupo.nombre}`}
                value={decisionMasiva}
                onChange={e => setMasDecision(e.target.value as Decision)}
                className={selectChica}
              >
                {opcionesMasivas.map(d => <option key={d} value={d}>{DECISION_LABEL[d]}</option>)}
              </select>
              {muestraDestino && (
                <select
                  aria-label={`Destino para todo ${grupo.nombre}`}
                  value={masDestino}
                  onChange={e => setMasDestino(e.target.value)}
                  className={selectChica}
                >
                  <option value="">Grado siguiente configurado</option>
                  {grados.filter(g => g.id_grado !== grupo.id && g.activo).map(g => (
                    <option key={g.id_grado} value={g.id_grado}>{g.nombre}</option>
                  ))}
                </select>
              )}
              <Button size="sm" variant="secondary" onClick={aplicar} loading={aplicando}>Aplicar a todos</Button>
            </div>
          )}
          {grupo.lineas.map(l => (
            <FilaAlumno
              key={l.id_promocion_alumno}
              linea={l} grados={grados} editable={editable}
              pendiente={pendientes[l.id_promocion_alumno]}
              onDecision={onDecision} onDestino={onDestino} onMotivo={onMotivo}
            />
          ))}
        </>
      )}
    </div>
  )
}

// ── Pestaña ──────────────────────────────────────────────────────────────────

export default function TabPromocionAnual() {
  const anioActual = new Date().getFullYear()
  const [anio, setAnio] = useState(anioActual)
  const [promocion, setPromocion] = useState<PromocionDetalle | null>(null)
  const [existentes, setExistentes] = useState<PromocionAnual[]>([])
  const [grados, setGrados] = useState<Grado[]>([])
  const [loading, setLoading] = useState(false)
  const [ocupado, setOcupado] = useState(false)
  // Alumnos cuya decisión requiere elegir destino antes de poder guardarse.
  const [pendientes, setPendientes] = useState<Record<number, Decision>>({})
  const [confirmar, setConfirmar] = useState(false)
  const [entendido, setEntendido] = useState(false)
  const [descartar, setDescartar] = useState(false)

  const cargar = useCallback(async (a: number) => {
    setLoading(true)
    try {
      const [{ data: lista }, { data: gr }] = await Promise.all([
        promocionService.listar(),
        api.get('/clientes/grados/', { params: { page_size: 100 } }),
      ])
      setGrados(gr.results ?? gr ?? [])
      setExistentes(lista.results ?? [])
      const propia = (lista.results ?? []).find((p: PromocionAnual) => p.anio === a)
      if (propia) {
        const { data } = await promocionService.detalle(propia.id_promocion)
        setPromocion(data)
      } else {
        setPromocion(null)
      }
      setPendientes({})
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargar(anio) }, [cargar, anio])

  const ejecutar = useCallback(async (fn: () => Promise<PromocionDetalle | null>, ok?: string) => {
    setOcupado(true)
    try {
      const data = await fn()
      if (data) setPromocion(data)
      if (ok) toast.success(ok)
      return data
    } catch (err) {
      toast.error(extractErrorMessage(err))
      return null
    } finally {
      setOcupado(false)
    }
  }, [])

  const generar = () => ejecutar(async () => (await promocionService.generar(anio)).data, 'Borrador preparado')
  const refrescar = () => ejecutar(async () => {
    const { data } = await promocionService.refrescar(promocion!.id_promocion)
    toast(data.agregados ? `${data.agregados} alumno(s) agregados` : 'No hay alumnos nuevos')
    return data
  })

  const guardarLinea = useCallback(async (l: LineaPromocion, decision: Decision, destino?: number | null, motivo?: string) => {
    if (!promocion) return
    const datos: { decision: Decision; grado_destino?: number | null; motivo?: string } = { decision }
    if (destino !== undefined) datos.grado_destino = destino
    if (motivo !== undefined) datos.motivo = motivo
    const data = await ejecutar(async () => (await promocionService.actualizarLinea(promocion.id_promocion, l.id_promocion_alumno, datos)).data)
    if (data) setPendientes(p => Object.fromEntries(Object.entries(p).filter(([id]) => Number(id) !== l.id_promocion_alumno)))
  }, [promocion, ejecutar])

  const cambiarDecision = useCallback((l: LineaPromocion, decision: Decision) => {
    if (decision === 'PROMUEVE') {
      const destino = l.grado_destino && l.grado_destino !== l.grado_origen ? l.grado_destino : l.origen_siguiente
      if (destino) guardarLinea(l, decision, destino)
      else setPendientes(p => ({ ...p, [l.id_promocion_alumno]: decision }))
    } else if (decision === 'CAMBIA') {
      if (l.decision === 'CAMBIA' && l.grado_destino) return
      setPendientes(p => ({ ...p, [l.id_promocion_alumno]: decision }))
    } else {
      guardarLinea(l, decision)
    }
  }, [guardarLinea])

  const cambiarMasiva = useCallback(async (grado: number, decision: Decision, destino: number | null) => {
    if (!promocion) return
    const data = await ejecutar(async () => (await promocionService.actualizarGrupo(promocion.id_promocion, {
      grado_origen: grado, decision, ...(destino ? { grado_destino: destino } : {}),
    })).data)
    if (!data?.resultado) return
    const { actualizadas, omitidas } = data.resultado
    if (omitidas.length) toast.error(`${actualizadas} actualizados, ${omitidas.length} omitidos: ${omitidas[0].hijo} — ${omitidas[0].motivo}`)
    else toast.success(`${actualizadas} alumno(s) actualizados`)
    setPendientes({})
  }, [promocion, ejecutar])

  const aplicar = useCallback(async () => {
    if (!promocion) return
    const data = await ejecutar(async () => (await promocionService.aplicar(promocion.id_promocion)).data, 'Promoción aplicada')
    if (data) { setConfirmar(false); setEntendido(false); cargar(anio) }
  }, [promocion, ejecutar, cargar, anio])

  const descartarBorrador = useCallback(async () => {
    if (!promocion) return
    setOcupado(true)
    try {
      await promocionService.descartar(promocion.id_promocion)
      toast.success('Borrador descartado')
      setDescartar(false)
      cargar(anio)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setOcupado(false)
    }
  }, [promocion, cargar, anio])

  const grupos = useMemo(() => agrupar(promocion?.lineas ?? []), [promocion])
  const req = promocion?.requisitos
  const editable = promocion?.estado === 'BORRADOR'
  const aplicadas = existentes.filter(p => p.estado === 'APLICADA')

  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-100 rounded-2xl px-5 py-4 text-sm text-slate-700 space-y-1.5">
        <p>
          <strong>Promoción anual:</strong> al terminar el año lectivo cada alumno pasa al grado siguiente. Podés preparar el
          borrador desde el inicio de diciembre y ajustar caso por caso (repite, cambia de grado, egresa o no continúa).
        </p>
        <p>
          Se aplica <strong>una sola vez</strong> y recién después del cierre del año lectivo. Los que egresan o no continúan se dan de baja
          y pasan al cierre de cuentas. Una vez aplicada no se deshace: los casos puntuales se corrigen editando al alumno.
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className={labelClass} htmlFor="promo-anio">Año que termina</label>
          <input
            id="promo-anio" type="number" min={2020} max={2100} value={anio}
            onChange={e => setAnio(Number(e.target.value))}
            className={`${inputClass} w-32`}
          />
        </div>
        {aplicadas.length > 0 && (
          <p className="text-sm text-slate-500 pb-2">
            Ya aplicadas: {aplicadas.map(p => `${p.anio} → ${p.anio + 1}`).join(', ')}
          </p>
        )}
      </div>

      {loading && <p className="text-sm text-slate-500">Cargando…</p>}

      {!loading && !promocion && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-8 text-center space-y-3">
          <p className="text-slate-700">No hay un borrador de promoción para {anio} → {anio + 1}.</p>
          <p className="text-sm text-slate-500">Se crea con una decisión sugerida por alumno; podés ajustarla antes de aplicarla.</p>
          <Button variant="primary" onClick={generar} loading={ocupado}>Preparar borrador {anio}</Button>
        </div>
      )}

      {promocion && req && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg font-semibold text-slate-800">Promoción {promocion.anio} → {promocion.anio + 1}</h2>
              <Badge color={editable ? 'yellow' : 'green'}>{editable ? 'Borrador' : 'Aplicada'}</Badge>
              <span className="text-sm text-slate-500">{promocion.total_alumnos} alumno(s)</span>
              {!editable && promocion.fecha_aplicacion && (
                <span className="text-sm text-slate-500">
                  Aplicada el {formatDateTime(promocion.fecha_aplicacion)}{promocion.aplicada_por_nombre ? ` por ${promocion.aplicada_por_nombre}` : ''}
                </span>
              )}
              {editable && (
                <div className="flex gap-2 ml-auto">
                  <Button size="sm" variant="secondary" onClick={refrescar} disabled={ocupado}>
                    <RefreshCw className="w-3.5 h-3.5" /> Buscar alumnos nuevos
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => setDescartar(true)} disabled={ocupado}>
                    <Trash2 className="w-3.5 h-3.5" /> Descartar borrador
                  </Button>
                </div>
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              {ORDEN_DECISIONES.filter(d => req.resumen[d]).map(d => (
                <Badge key={d} color={DECISION_COLOR[d]}>{req.resumen[d]} {DECISION_LABEL[d].toLowerCase()}</Badge>
              ))}
            </div>

            {editable && req.errores.length > 0 && (
              <ul className="space-y-1" aria-label="Pendientes para aplicar">
                {req.errores.map(e => (
                  <li key={e} className="flex items-start gap-2 text-sm text-red-700">
                    <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {e}
                  </li>
                ))}
              </ul>
            )}
            {editable && req.avisos.map(a => (
              <p key={a} className="flex items-start gap-2 text-sm text-amber-700">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" /> {a}
              </p>
            ))}
            {editable && req.puede_aplicar && (
              <p className="flex items-center gap-2 text-sm text-green-700">
                <CheckCircle2 className="w-4 h-4" /> Todo listo para aplicar.
              </p>
            )}
            {editable && (
              <Button variant="primary" disabled={!req.puede_aplicar || ocupado} onClick={() => setConfirmar(true)}>
                Aplicar promoción
              </Button>
            )}
            {editable && !req.puede_aplicar && req.errores.length === 0 && (
              <p className="text-xs text-slate-500">Se habilita el {formatDateOnly(req.habilitada_desde)}.</p>
            )}
          </div>

          <div className="space-y-3">
            {grupos.map(g => (
              <GrupoGrado
                key={g.id ?? 'sin'}
                grupo={g} grados={grados} editable={!!editable} pendientes={pendientes}
                onDecision={cambiarDecision}
                onDestino={(l, d, destino) => guardarLinea(l, d, destino)}
                onMotivo={(l, motivo) => guardarLinea(l, l.decision, undefined, motivo)}
                onMasiva={cambiarMasiva}
              />
            ))}
          </div>
        </>
      )}

      <Modal
        open={confirmar}
        title="Aplicar promoción anual"
        onOk={() => (entendido ? aplicar() : toast.error('Marcá la casilla para confirmar'))}
        onCancel={() => { setConfirmar(false); setEntendido(false) }}
        okText="Aplicar promoción"
        confirmLoading={ocupado}
        width={480}
      >
        {req && (
          <div className="space-y-3 text-sm text-slate-700">
            <p>Se van a actualizar los grados de <strong>{promocion?.total_alumnos}</strong> alumno(s):</p>
            <ul className="list-disc pl-5 space-y-0.5">
              {ORDEN_DECISIONES.filter(d => req.resumen[d]).map(d => (
                <li key={d}><strong>{req.resumen[d]}</strong> {DECISION_LABEL[d].toLowerCase()}</li>
              ))}
            </ul>
            <p>
              Quienes egresan o no continúan se dan de baja y se abre su cierre de cuentas. Cada cambio queda en el historial del alumno.
              No se puede deshacer.
            </p>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={entendido} onChange={e => setEntendido(e.target.checked)} />
              Revisé el borrador y quiero aplicarlo
            </label>
            {!entendido && <p className="text-xs text-slate-400">Marcá la casilla para continuar.</p>}
          </div>
        )}
      </Modal>

      <Modal
        open={descartar}
        title="Descartar borrador"
        onOk={descartarBorrador}
        onCancel={() => setDescartar(false)}
        okText="Descartar"
        confirmLoading={ocupado}
        width={420}
      >
        <p className="text-sm text-slate-700">
          Se pierden las decisiones cargadas en el borrador de {promocion?.anio}. Los alumnos no se modifican.
        </p>
      </Modal>
    </div>
  )
}
