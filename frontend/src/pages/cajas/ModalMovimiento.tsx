import { useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { ArrowUpCircle, ArrowDownCircle } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import { extractErrorMessage, type CierreCaja, type MedioPago } from './shared'

interface Props {
  tipo: 'INGRESO' | 'EGRESO' | null
  miCierre: CierreCaja | null
  mediosPago: MedioPago[]
  onClose: () => void
  onSaved: () => void
}

const inputCls = 'w-full border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors'
const labelCls = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalMovimiento({ tipo, miCierre, mediosPago, onClose, onSaved }: Props) {
  const [movTipo, setMovTipo] = useState<'INGRESO' | 'EGRESO'>('INGRESO')
  const [movMonto, setMovMonto] = useState('')
  const [movMedioPago, setMovMedioPago] = useState('')
  const [movDesc, setMovDesc] = useState('')
  const [movSaving, setMovSaving] = useState(false)
  const movSavingRef = useRef(false)

  const [prevTipo, setPrevTipo] = useState(tipo)
  if (tipo !== prevTipo) {
    setPrevTipo(tipo)
    if (tipo) {
      setMovTipo(tipo)
      setMovMonto('')
      setMovMedioPago(mediosPago[0] ? String(mediosPago[0].id) : '')
      setMovDesc('')
    }
  }

  const handleConfirmar = async () => {
    if (movSavingRef.current || !miCierre) return
    if (!movMonto || Number(movMonto) <= 0) { toast.error('Ingresá un monto válido'); return }
    movSavingRef.current = true
    setMovSaving(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${miCierre.id}/registrar-movimiento/`, {
        tipo: movTipo,
        monto: Number(movMonto),
        medio_pago: movMedioPago ? Number(movMedioPago) : null,
        descripcion: movDesc,
      }, { timeout: 10000 })
      toast.success(`${movTipo === 'INGRESO' ? 'Ingreso' : 'Egreso'} registrado`)
      setMovMonto('')
      setMovDesc('')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      movSavingRef.current = false
      setMovSaving(false)
    }
  }

  return (
    <Modal
      open={tipo !== null}
      title={movTipo === 'INGRESO' ? 'Registrar Ingreso' : 'Registrar Egreso'}
      onCancel={onClose}
      onOk={handleConfirmar}
      okText={movTipo === 'INGRESO' ? 'Registrar Ingreso' : 'Registrar Egreso'}
      confirmLoading={movSaving}
      width={420}
    >
      <div className="space-y-4">
        <div className="flex gap-2">
          {(['INGRESO', 'EGRESO'] as const).map(t => (
            <button
              key={t}
              onClick={() => setMovTipo(t)}
              className={[
                'flex-1 flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-sm font-semibold border transition-colors',
                movTipo === t
                  ? t === 'INGRESO'
                    ? 'bg-green-50 border-green-300 text-green-700'
                    : 'bg-orange-50 border-orange-300 text-orange-700'
                  : 'bg-white border-slate-200 text-slate-500 hover:bg-slate-50',
              ].join(' ')}
            >
              {t === 'INGRESO'
                ? <ArrowUpCircle className="w-4 h-4" />
                : <ArrowDownCircle className="w-4 h-4" />}
              {t === 'INGRESO' ? 'Ingreso' : 'Egreso'}
            </button>
          ))}
        </div>

        <Input
          label="Monto (Gs.)"
          type="number"
          placeholder="0"
          value={movMonto}
          onChange={e => setMovMonto(e.target.value)}
          min={1}
          step={10000}
        />

        <div>
          <label className={labelCls}>Medio de Pago</label>
          <select
            value={movMedioPago}
            onChange={e => setMovMedioPago(e.target.value)}
            className={inputCls}
          >
            <option value="">Sin especificar</option>
            {mediosPago.map(m => <option key={m.id} value={m.id}>{m.descripcion}</option>)}
          </select>
        </div>

        <div>
          <label className={labelCls}>Descripción</label>
          <input
            type="text"
            value={movDesc}
            onChange={e => setMovDesc(e.target.value)}
            placeholder={movTipo === 'INGRESO' ? 'Ej: Fondo de cambio adicional' : 'Ej: Compra de insumos'}
            className={inputCls}
          />
        </div>
      </div>
    </Modal>
  )
}
