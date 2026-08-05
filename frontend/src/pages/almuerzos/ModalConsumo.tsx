import { useCallback, useState } from 'react'
import { CheckCircle, Search, X } from 'lucide-react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, formatGs, todayISO, type Hijo, type TarjetaBusqueda, type TipoAlmuerzo } from './shared'

interface Props {
  open: boolean
  hijos: Hijo[]
  tiposAlmuerzo: TipoAlmuerzo[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalConsumo({ open, hijos, tiposAlmuerzo, onClose, onSaved }: Props) {
  const [tarjetaSearch, setTarjetaSearch] = useState('')
  const [tarjeta, setTarjeta] = useState<TarjetaBusqueda | null>(null)
  const [tarjetaBuscando, setTarjetaBuscando] = useState(false)
  const [hijoId, setHijoId] = useState<number | ''>('')
  const [tipoAlmuerzoId, setTipoAlmuerzoId] = useState<string | null>(null)
  const [fechaConsumo, setFechaConsumo] = useState(todayISO())
  const [registrando, setRegistrando] = useState(false)

  const tiposActivos = tiposAlmuerzo.filter(t => t.activo)
  const predeterminado = tiposActivos.find(t => t.es_predeterminado)
  const tipoSeleccionado = tipoAlmuerzoId ?? (predeterminado ? String(predeterminado.id) : '')

  const buscarTarjeta = useCallback(async (nro?: string) => {
    const searchValue = nro ?? tarjetaSearch.trim()
    if (!searchValue) { toast.error('Ingresá un número de tarjeta'); return }
    setTarjetaBuscando(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: searchValue }, timeout: 6000 })
      const found = (data.results ?? []).find((t: TarjetaBusqueda) => t.nro_tarjeta === searchValue)
      if (!found) { toast.error('Tarjeta no encontrada'); return }
      if (found.estado !== 'ACTIVA') { toast.error(`Tarjeta ${found.estado}`); return }
      setTarjeta(found)
      const h = hijos.find(x => `${x.nombre} ${x.apellido}` === found.hijo_nombre || x.nombre_completo === found.hijo_nombre)
      if (h) setHijoId(h.id)
      toast.success(found.hijo_nombre)
    } catch {
      toast.error('Error al buscar tarjeta')
    } finally {
      setTarjetaBuscando(false)
      setTarjetaSearch('')
    }
  }, [tarjetaSearch, hijos])

  const handleRegistrar = useCallback(async () => {
    if (!hijoId) { toast.error('Seleccioná un estudiante'); return }
    if (!tarjeta) { toast.error('Buscá la tarjeta del estudiante'); return }
    const h = hijos.find(x => x.id === Number(hijoId))
    if (h) {
      const coincide = tarjeta.hijo_nombre === `${h.nombre} ${h.apellido}` || tarjeta.hijo_nombre === h.nombre_completo
      if (!coincide) { toast.error('La tarjeta no pertenece al estudiante seleccionado'); return }
    }
    setRegistrando(true)
    try {
      const payload: Record<string, unknown> = {
        hijo: hijoId,
        fecha_consumo: fechaConsumo,
        nro_tarjeta: tarjeta.nro_tarjeta,
      }
      if (tipoSeleccionado) payload.tipo_almuerzo = Number(tipoSeleccionado)
      await api.post('/almuerzos/registros-consumo/', payload)
      toast.success('Consumo registrado')
      setTarjeta(null)
      setTarjetaSearch('')
      setHijoId('')
      setTipoAlmuerzoId(null)
      setFechaConsumo(todayISO())
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setRegistrando(false)
    }
  }, [hijoId, tarjeta, hijos, fechaConsumo, tipoSeleccionado, onSaved, onClose])

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title="Registrar Consumo de Almuerzo"
      onOk={handleRegistrar}
      onCancel={() => { setTarjeta(null); setTarjetaSearch(''); onClose() }}
      okText="Registrar"
      confirmLoading={registrando}
      width={480}
    >
      <div className="space-y-4">
        <div className="bg-slate-50 rounded-xl p-4">
          <label className={labelClass}>Tarjeta del Estudiante</label>
          <div className="flex gap-2">
            <input
              placeholder="Nro. tarjeta"
              value={tarjetaSearch}
              onChange={e => setTarjetaSearch(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') { const v = e.currentTarget.value.trim(); if (v) buscarTarjeta(v) } }}
              className="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
            />
            <Button size="sm" variant="secondary" loading={tarjetaBuscando} onClick={() => buscarTarjeta()}>
              <Search className="w-3.5 h-3.5" />
              Buscar
            </Button>
          </div>
          {tarjeta && (
            <div className="mt-2 flex items-center gap-2 bg-green-50 rounded-lg px-3 py-2">
              <CheckCircle className="w-4 h-4 text-green-600 shrink-0" />
              <span className="text-sm font-medium text-green-800">{tarjeta.hijo_nombre}</span>
              <span className="text-xs text-green-600 ml-auto">Saldo: {formatGs(tarjeta.saldo_actual)}</span>
              <button onClick={() => { setTarjeta(null); setTarjetaSearch('') }} className="text-slate-400 hover:text-red-500 cursor-pointer">
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        <div>
          <label htmlFor="consumo-estudiante" className={labelClass}>Estudiante *</label>
          <select
            id="consumo-estudiante"
            value={hijoId}
            onChange={e => setHijoId(Number(e.target.value) || '')}
            className={inputClass}
            disabled={!!tarjeta}
          >
            <option value="">Seleccionar...</option>
            {hijos.map(h => (
              <option key={h.id} value={h.id}>
                {h.nombre_completo ?? `${h.nombre} ${h.apellido}`} — {h.grado}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="consumo-tipo-almuerzo" className={labelClass}>Tipo de Almuerzo (opcional)</label>
          <select
            id="consumo-tipo-almuerzo"
            value={tipoSeleccionado}
            onChange={e => setTipoAlmuerzoId(e.target.value)}
            className={inputClass}
          >
            <option value="">Sin especificar</option>
            {tiposActivos.map(t => (
              <option key={t.id} value={t.id}>{t.nombre}{t.es_predeterminado ? ' (predeterminado)' : ''} — {formatGs(t.precio_unitario)}</option>
            ))}
          </select>
        </div>

        <div>
          <label className={labelClass}>Fecha</label>
          <input
            type="date"
            value={fechaConsumo}
            onChange={e => setFechaConsumo(e.target.value)}
            className={inputClass}
          />
        </div>
      </div>
    </Modal>
  )
}
