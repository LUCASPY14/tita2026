import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { Check, X } from 'lucide-react'
import cierreCuentasService from '../../services/cierreCuentas'
import { formatDateTime } from '../../lib/format'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import {
  BOLSILLO_LABEL, TIPO_LABEL, esAdmin, extractErrorMessage, formatGs, type Resolucion,
} from './shared'

interface Props {
  anio: number
  rol?: string
  onChanged: () => void
  onAbrir: (cierreId: number) => void
}

export default function TabPendientes({ anio, rol, onChanged, onAbrir }: Props) {
  const [items, setItems] = useState<Resolucion[]>([])
  const [loading, setLoading] = useState(false)
  const [trabajando, setTrabajando] = useState<number | null>(null)
  const [rechazando, setRechazando] = useState<Resolucion | null>(null)
  const [motivo, setMotivo] = useState('')

  const cargar = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await cierreCuentasService.pendientes(anio)
      setItems(data.results ?? [])
    } catch {
      toast.error('Error al cargar las aprobaciones pendientes')
    } finally {
      setLoading(false)
    }
  }, [anio])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargar() }, [cargar])

  const aprobar = async (r: Resolucion) => {
    setTrabajando(r.id_resolucion)
    try {
      const { data } = await cierreCuentasService.aprobar(r.id_resolucion)
      toast.success(`${TIPO_LABEL[r.tipo]} aprobada y ejecutada`)
      if (data.advertencia) toast(data.advertencia, { duration: 9000 })
      await cargar()
      onChanged()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setTrabajando(null)
    }
  }

  const rechazar = async () => {
    if (!rechazando) return
    if (!motivo.trim()) { toast.error('Indicá el motivo del rechazo'); return }
    setTrabajando(rechazando.id_resolucion)
    try {
      await cierreCuentasService.rechazar(rechazando.id_resolucion, motivo.trim())
      toast.success('Solicitud rechazada')
      setRechazando(null)
      setMotivo('')
      await cargar()
      onChanged()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setTrabajando(null)
    }
  }

  if (loading && items.length === 0) return <p className="py-10 text-center text-sm text-slate-400">Cargando...</p>
  if (items.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-400">No hay aprobaciones pendientes.</p>
  }

  return (
    <>
      <ul className="divide-y divide-slate-100">
        {items.map(r => (
          <li key={r.id_resolucion} className="px-6 py-4 flex flex-wrap items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <button
                  className="text-sm font-semibold text-slate-800 hover:underline cursor-pointer"
                  onClick={() => onAbrir(r.cierre)}
                >
                  {r.hijo_nombre}
                </button>
                <span className="text-sm text-slate-600">{TIPO_LABEL[r.tipo]}</span>
                <span className="tabular-nums font-semibold">{formatGs(r.monto)}</span>
                <span className="text-xs text-slate-400">{BOLSILLO_LABEL[r.bolsillo_origen]}</span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Solicitó {r.solicitado_por_nombre} · {formatDateTime(r.fecha_solicitud)}
                {r.metodo_pago && ` · ${r.metodo_pago}`}
                {r.referencia && ` · Ref. ${r.referencia}`}
                {r.motivo && ` · ${r.motivo}`}
              </p>
            </div>
            {esAdmin(rol) ? (
              <div className="flex gap-2">
                <Button size="sm" variant="primary" loading={trabajando === r.id_resolucion} onClick={() => aprobar(r)}>
                  <Check className="w-3.5 h-3.5" />
                  Aprobar
                </Button>
                <Button size="sm" variant="danger" disabled={trabajando !== null} onClick={() => { setRechazando(r); setMotivo('') }}>
                  <X className="w-3.5 h-3.5" />
                  Rechazar
                </Button>
              </div>
            ) : (
              <Badge color="yellow">Pendiente de un administrador</Badge>
            )}
          </li>
        ))}
      </ul>

      <Modal
        open={rechazando !== null}
        title="Rechazar solicitud"
        onOk={rechazar}
        onCancel={() => setRechazando(null)}
        okText="Rechazar"
        confirmLoading={trabajando !== null}
        width={420}
      >
        <div className="space-y-2">
          <p className="text-sm text-slate-600">
            {rechazando && `${TIPO_LABEL[rechazando.tipo]} de ${formatGs(rechazando.monto)} — ${rechazando.hijo_nombre}`}
          </p>
          <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide" htmlFor="cc-rechazo">Motivo *</label>
          <textarea
            id="cc-rechazo" rows={3} value={motivo} onChange={e => setMotivo(e.target.value)}
            className="border border-slate-200 rounded-xl px-3 py-2 text-sm w-full focus:outline-none focus:ring-2 focus:ring-green-500/30"
          />
          <p className="text-xs text-slate-400">Se le avisa a quien la solicitó.</p>
        </div>
      </Modal>
    </>
  )
}
