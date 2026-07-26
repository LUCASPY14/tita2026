import { useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { ArrowUpCircle, ArrowDownCircle, ShoppingCart } from 'lucide-react'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import { extractErrorMessage, formatGs, formatDatetime, type CierreCaja, type ArqueoData } from './shared'

interface Props {
  cierre: CierreCaja | null
  onClose: () => void
  onSaved: () => void
}

export default function ModalCerrar({ cierre, onClose, onSaved }: Props) {
  const [arqueoModal, setArqueoModal] = useState<ArqueoData | null>(null)
  const [loadingArqueo, setLoadingArqueo] = useState(false)
  const [montoContado, setMontoContado] = useState('')
  const [montoContadoDebounced, setMontoContadoDebounced] = useState('')
  const [cerrando, setCerrando] = useState(false)
  const cerrandoRef = useRef(false)

  useEffect(() => {
    if (!cierre) return
    setMontoContado('')
    setArqueoModal(null)
    setLoadingArqueo(true)
    api.get(`/contabilidad/cierres-caja/${cierre.id}/arqueo/`, { timeout: 8000 })
      .then(({ data }) => setArqueoModal(data))
      .catch(() => { /* modal se abre igual, sin desglose */ })
      .finally(() => setLoadingArqueo(false))
  }, [cierre])

  useEffect(() => {
    const t = setTimeout(() => setMontoContadoDebounced(montoContado), 400)
    return () => clearTimeout(t)
  }, [montoContado])

  const diferenciaViva = useMemo(() => {
    if (!arqueoModal || !montoContadoDebounced) return null
    return Number(montoContadoDebounced) - arqueoModal.efectivo_esperado
  }, [arqueoModal, montoContadoDebounced])

  const handleCerrar = async () => {
    if (cerrandoRef.current || !cierre) return
    cerrandoRef.current = true
    setCerrando(true)
    try {
      await api.post(`/contabilidad/cierres-caja/${cierre.id}/cerrar/`, {
        monto_contado_fisico: Number(montoContado) || 0,
      }, { timeout: 10000 })
      await onSaved()
      onClose()
      setArqueoModal(null)
      toast.success('Caja cerrada')
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      cerrandoRef.current = false
      setCerrando(false)
    }
  }

  return (
    <Modal
      open={!!cierre}
      title={`Cerrar Caja — ${cierre?.caja_nombre ?? ''}`}
      onCancel={onClose}
      onOk={handleCerrar}
      okText="Confirmar Cierre"
      confirmLoading={cerrando}
      width={500}
    >
      <div className="space-y-4">
        <div className="bg-slate-50 rounded-xl px-4 py-3 space-y-1.5 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-500">Apertura:</span>
            <span className="font-medium text-slate-700">{formatDatetime(cierre?.fecha_apertura)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Monto inicial:</span>
            <span className="font-semibold text-slate-800 tabular-nums">{formatGs(cierre?.monto_inicial)}</span>
          </div>
        </div>

        {loadingArqueo ? (
          <div className="flex items-center gap-2 text-slate-400 text-sm py-2">
            <ShoppingCart className="w-4 h-4 animate-pulse" />
            Cargando arqueo…
          </div>
        ) : arqueoModal ? (
          <div className="border border-slate-200 rounded-xl overflow-hidden text-sm">
            <div className="bg-slate-50 px-4 py-2 font-semibold text-slate-600 text-xs uppercase tracking-wide">
              Desglose de movimientos
            </div>
            <div className="divide-y divide-slate-100">
              {arqueoModal.ingresos_por_medio.map(m => (
                <div key={m.medio} className="flex justify-between px-4 py-2">
                  <span className="text-slate-600 flex items-center gap-1.5">
                    <ArrowUpCircle className="w-3.5 h-3.5 text-green-500" />
                    {m.medio}
                  </span>
                  <span className="font-medium text-green-700 tabular-nums">+{formatGs(m.total)}</span>
                </div>
              ))}
              {arqueoModal.egresos_por_medio.map(m => (
                <div key={m.medio} className="flex justify-between px-4 py-2">
                  <span className="text-slate-600 flex items-center gap-1.5">
                    <ArrowDownCircle className="w-3.5 h-3.5 text-orange-500" />
                    {m.medio}
                  </span>
                  <span className="font-medium text-orange-700 tabular-nums">-{formatGs(m.total)}</span>
                </div>
              ))}
              <div className="flex justify-between px-4 py-2.5 bg-blue-50">
                <span className="font-semibold text-blue-800">Efectivo esperado</span>
                <span className="font-bold text-blue-800 tabular-nums">{formatGs(arqueoModal.efectivo_esperado)}</span>
              </div>
            </div>
          </div>
        ) : null}

        <Input
          label="Monto Contado en Efectivo (Gs.)"
          type="number"
          placeholder="0"
          value={montoContado}
          onChange={e => setMontoContado(e.target.value)}
          min={0}
        />

        {diferenciaViva !== null && (
          <div className={[
            'flex justify-between px-4 py-2.5 rounded-xl text-sm font-semibold',
            diferenciaViva === 0
              ? 'bg-emerald-50 text-emerald-700'
              : diferenciaViva > 0
              ? 'bg-green-50 text-green-700'
              : 'bg-red-50 text-red-700',
          ].join(' ')}>
            <span>Diferencia</span>
            <span className="tabular-nums">
              {diferenciaViva > 0 ? '+' : ''}{formatGs(diferenciaViva)}
            </span>
          </div>
        )}
      </div>
    </Modal>
  )
}
