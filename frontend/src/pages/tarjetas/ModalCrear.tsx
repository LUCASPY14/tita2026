import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import tarjetasService from '../../services/tarjetas'
import clientesService from '../../services/clientes'
import api from '../../services/api'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, type ClienteBasico, type Hijo, type TarjetaForm, type TipoTitular, FORM_INITIAL,
} from './shared'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalCrear({ open, onClose, onSaved }: Props) {
  const [form, setForm] = useState<TarjetaForm>(FORM_INITIAL)
  const [saving, setSaving] = useState(false)
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [clientesSearch, setClientesSearch] = useState('')
  const [clientes, setClientes] = useState<ClienteBasico[]>([])
  const [loadingClientes, setLoadingClientes] = useState(false)
  const clientesTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    if (open && hijos.length === 0) {
      clientesService.getHijos<Hijo>({ activo: true, page_size: 500 })
        .then(({ data }) => setHijos(data.results ?? []))
        .catch(() => toast.error('Error al cargar alumnos'))
    }
  }, [open, hijos.length])

  useEffect(() => {
    if (!open || form.tipoTitular !== 'funcionario') return
    clearTimeout(clientesTimer.current)
    if (!clientesSearch.trim()) { setClientes([]); return }
    clientesTimer.current = setTimeout(() => {
      setLoadingClientes(true)
      api.get<{ results?: ClienteBasico[]; count?: number }>('/clientes/clientes/', {
        params: { search: clientesSearch, activo: true, page_size: 8 },
      })
        .then(({ data }) => setClientes(data.results ?? []))
        .catch(() => setClientes([]))
        .finally(() => setLoadingClientes(false))
    }, 350)
    return () => clearTimeout(clientesTimer.current)
  }, [clientesSearch, open, form.tipoTitular])

  const handleClose = () => {
    setClientesSearch('')
    setClientes([])
    onClose()
  }

  const handleCreate = async () => {
    if (!form.nro_tarjeta) { toast.error('Ingresá el número de tarjeta'); return }
    if (form.tipoTitular === 'alumno' && !form.hijo) {
      toast.error('Seleccioná el estudiante'); return
    }
    if (form.tipoTitular === 'funcionario' && !form.cliente_directo) {
      toast.error('Seleccioná el cliente (docente/funcionario)'); return
    }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        nro_tarjeta: form.nro_tarjeta,
        codigo_barras: form.codigo_barras || null,
        limite_credito: Number(form.limite_credito) || 0,
        permite_saldo_negativo: form.permite_saldo_negativo,
        estado: form.estado,
        fecha_vencimiento: form.fecha_vencimiento || null,
      }
      if (form.tipoTitular === 'alumno') {
        payload.hijo = form.hijo
        payload.cliente_directo = null
      } else {
        payload.hijo = null
        payload.cliente_directo = form.cliente_directo
      }
      await tarjetasService.crear(payload)
      toast.success('Tarjeta creada')
      setForm(FORM_INITIAL)
      setClientesSearch('')
      setClientes([])
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Nueva Tarjeta"
      onOk={handleCreate}
      onCancel={handleClose}
      okText="Crear Tarjeta"
      confirmLoading={saving}
      width={560}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Nro. Tarjeta *</label>
            <input
              value={form.nro_tarjeta}
              onChange={e => setForm(f => ({ ...f, nro_tarjeta: e.target.value }))}
              placeholder="0001234"
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>Código de Barras</label>
            <input
              value={form.codigo_barras}
              onChange={e => setForm(f => ({ ...f, codigo_barras: e.target.value }))}
              placeholder="1234567890"
              className={inputClass}
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Tipo de titular *</label>
          <div className="flex gap-3">
            {(['alumno', 'funcionario'] as TipoTitular[]).map(tipo => (
              <button
                key={tipo}
                type="button"
                onClick={() => setForm(f => ({ ...f, tipoTitular: tipo, hijo: '', cliente_directo: '' }))}
                className={[
                  'flex-1 py-2.5 rounded-xl border-2 text-sm font-bold transition-colors cursor-pointer',
                  form.tipoTitular === tipo
                    ? 'bg-green-600 border-green-600 text-white'
                    : 'bg-white border-slate-300 text-slate-600 hover:border-green-400',
                ].join(' ')}
              >
                {tipo === 'alumno' ? '🎓 Estudiante' : '👤 Docente / Funcionario'}
              </button>
            ))}
          </div>
        </div>

        {form.tipoTitular === 'alumno' ? (
          <div>
            <label className={labelClass}>Estudiante *</label>
            <select
              value={form.hijo}
              onChange={e => setForm(f => ({ ...f, hijo: Number(e.target.value) || '' }))}
              className={inputClass}
            >
              <option value="">Seleccionar estudiante...</option>
              {hijos.map(h => (
                <option key={h.id} value={h.id}>{h.nombre} {h.apellido} — {h.grado}</option>
              ))}
            </select>
          </div>
        ) : (
          <div>
            <label className={labelClass}>Docente / Funcionario *</label>
            <input
              value={clientesSearch}
              onChange={e => { setClientesSearch(e.target.value); setForm(f => ({ ...f, cliente_directo: '' })) }}
              placeholder="Buscar por nombre o cédula..."
              className={inputClass}
            />
            {loadingClientes && (
              <p className="text-xs text-slate-400 mt-1">Buscando...</p>
            )}
            {clientes.length > 0 && !form.cliente_directo && (
              <ul className="border border-slate-200 rounded-xl mt-1 max-h-40 overflow-y-auto">
                {clientes.map(c => (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => { setForm(f => ({ ...f, cliente_directo: c.id })); setClientesSearch(c.nombre_completo) }}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-green-50 cursor-pointer"
                    >
                      <span className="font-semibold text-slate-800">{c.nombre_completo}</span>
                      <span className="text-slate-400 ml-2 text-xs">{c.ruc_ci}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {form.cliente_directo !== '' && (
              <div className="mt-1 flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-1.5">
                <span className="text-green-700 text-sm font-semibold">{clientesSearch}</span>
                <button
                  type="button"
                  onClick={() => { setForm(f => ({ ...f, cliente_directo: '' })); setClientesSearch('') }}
                  className="ml-auto text-slate-400 hover:text-red-500 text-xs cursor-pointer"
                >
                  ✕
                </button>
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelClass}>Límite de Crédito (Gs.)</label>
            <input
              type="number"
              value={form.limite_credito}
              onChange={e => setForm(f => ({ ...f, limite_credito: e.target.value }))}
              placeholder="0"
              min={0}
              step={1000}
              className={inputClass}
            />
          </div>
          <div>
            <label className={labelClass}>Estado inicial</label>
            <select
              value={form.estado}
              onChange={e => setForm(f => ({ ...f, estado: e.target.value }))}
              className={inputClass}
            >
              <option value="ACTIVA">Activa</option>
              <option value="BLOQUEADA">Bloqueada</option>
            </select>
          </div>
        </div>

        <div>
          <label className={labelClass}>Fecha de Vencimiento</label>
          <input
            type="date"
            value={form.fecha_vencimiento}
            onChange={e => setForm(f => ({ ...f, fecha_vencimiento: e.target.value }))}
            className={inputClass}
          />
        </div>

        <label className="flex items-center gap-3 cursor-pointer">
          <div className="relative shrink-0">
            <input
              type="checkbox"
              className="sr-only peer"
              checked={form.permite_saldo_negativo}
              onChange={e => setForm(f => ({ ...f, permite_saldo_negativo: e.target.checked }))}
            />
            <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
            <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
          </div>
          <span className="text-sm text-slate-700">Permite saldo negativo</span>
        </label>
      </div>
    </Modal>
  )
}
