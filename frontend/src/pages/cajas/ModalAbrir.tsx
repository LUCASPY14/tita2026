import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import { extractErrorMessage, type Caja } from './shared'

interface Props {
  open: boolean
  cajas: Caja[]
  onClose: () => void
  onSaved: () => void
}

const inputCls = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors'
const labelCls = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalAbrir({ open, cajas, onClose, onSaved }: Props) {
  const primeraActiva = cajas.find(c => c.activo)
  const [cajaSeleccionada, setCajaSeleccionada] = useState(primeraActiva ? String(primeraActiva.id_caja) : '')
  const [montoInicial, setMontoInicial] = useState('')
  const [abriendo, setAbriendo] = useState(false)
  const abriendoRef = useRef(false)

  const cajaActiva = cajas.find(c => String(c.id_caja) === cajaSeleccionada && c.activo)

  const handleAbrir = async () => {
    if (abriendoRef.current) return
    if (!cajaSeleccionada) { toast.error('Seleccioná una caja'); return }
    abriendoRef.current = true
    setAbriendo(true)
    try {
      await api.post('/contabilidad/cierres-caja/', {
        caja: Number(cajaSeleccionada),
        monto_inicial: Number(montoInicial) || 0,
      }, { timeout: 10000 })
      toast.success('Caja abierta')
      setMontoInicial('')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      abriendoRef.current = false
      setAbriendo(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Abrir Caja"
      onCancel={() => { onClose(); setMontoInicial('') }}
      onOk={handleAbrir}
      okText="Abrir Caja"
      confirmLoading={abriendo}
      width={420}
    >
      <div className="space-y-4">
        <div>
          <label className={labelCls}>Caja</label>
          <select
            value={cajaSeleccionada}
            onChange={e => setCajaSeleccionada(e.target.value)}
            className={inputCls}
          >
            <option value="">Seleccionar caja...</option>
            {cajas.filter(c => c.activo).map(c => (
              <option key={c.id_caja} value={c.id_caja}>{c.nombre}{c.ubicacion ? ` — ${c.ubicacion}` : ''}</option>
            ))}
          </select>
        </div>
        {cajaActiva && (
          <div className="bg-green-50 border border-green-100 rounded-xl px-4 py-2.5">
            <p className="text-sm text-green-700 font-medium">{cajaActiva.nombre}</p>
            {cajaActiva.ubicacion && <p className="text-sm text-green-600 mt-0.5">{cajaActiva.ubicacion}</p>}
          </div>
        )}
        <Input
          label="Monto Inicial (Gs.)"
          type="number"
          placeholder="0"
          value={montoInicial}
          onChange={e => setMontoInicial(e.target.value)}
          min={0}
          step={10000}
        />
      </div>
    </Modal>
  )
}
