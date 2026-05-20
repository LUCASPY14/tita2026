import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import {
  Plus, Search, Users, Edit2, AlertTriangle,
  GraduationCap, Phone, Mail, ShieldAlert, Baby,
} from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Combobox from '../components/ui/Combobox'
import Input from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import Spinner from '../components/ui/Spinner'
import Table, { type Column } from '../components/ui/Table'

const CIUDADES_PY = [
  'Asunción', 'San Lorenzo', 'Luque', 'Capiatá', 'Lambaré',
  'Fernando de la Mora', 'Limpio', 'Ñemby', 'Mariano Roque Alonso',
  'Encarnación', 'Ciudad del Este', 'Pedro Juan Caballero',
  'Concepción', 'Coronel Oviedo', 'Caaguazú', 'Villarrica',
  'Pilar', 'Caazapá', 'San Juan Bautista', 'Villa Hayes',
  'Pozo Colorado', 'Fuerte Olimpo', 'Filadelfia', 'Loma Plata',
  'Minga Guazú', 'Hernandarias', 'Presidente Franco',
]

const RUC_CI_REGEX = /^(\d{6,8}(-\d{1,2})?|\d{1,8}-\d{1}|\d{6,8})$/

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface TipoCliente { id: number; nombre: string; activo: boolean }
interface ListaPrecio { id: number; nombre: string }

interface Cliente {
  id: number
  nombres: string
  apellidos: string
  razon_social: string | null
  ruc_ci: string
  direccion: string | null
  ciudad: string | null
  telefono: string | null
  email: string | null
  limite_credito: string
  activo: boolean
  fecha_registro: string
  lista_precio: number
  tipo_cliente: number
  tipo_cliente_nombre: string
  saldo_cuenta_corriente: string
}

interface ClienteForm {
  nombres: string
  apellidos: string
  razon_social: string
  ruc_ci: string
  direccion: string
  ciudad: string
  telefono: string
  email: string
  limite_credito: string
  activo: boolean
  lista_precio: string
  tipo_cliente: string
}

interface Hijo {
  id: number
  nombre: string
  apellido: string
  fecha_nacimiento: string | null
  grado: string | null
  foto_perfil: string | null
  activo: boolean
  cliente_responsable: number
  cliente_nombre: string
}

interface HijoForm {
  nombre: string
  apellido: string
  fecha_nacimiento: string
  grado: string
  activo: boolean
}

interface RestriccionHijo {
  id: number
  hijo: number
  tipo: string
  descripcion: string | null
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'
  activo: boolean
  hijo_nombre: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

function formatGs(value: string | number | null | undefined): string {
  return (Number(value) || 0).toLocaleString('es-PY') + ' Gs.'
}

const SEV_COLOR: Record<string, BadgeColor> = {
  BAJA: 'blue', MEDIA: 'yellow', ALTA: 'orange', CRITICA: 'red',
}
const SEV_LABEL: Record<string, string> = {
  BAJA: 'Baja', MEDIA: 'Media', ALTA: 'Alta', CRITICA: 'Crítica',
}

// ─── ClienteModal ─────────────────────────────────────────────────────────────

const BLANK_CLIENTE: ClienteForm = {
  nombres: '', apellidos: '', razon_social: '', ruc_ci: '',
  direccion: '', ciudad: '', telefono: '', email: '',
  limite_credito: '0', activo: true, lista_precio: '', tipo_cliente: '',
}

interface ClienteModalProps {
  open: boolean
  cliente: Cliente | null
  tiposCliente: TipoCliente[]
  listasPrecios: ListaPrecio[]
  onClose: () => void
  onSaved: () => void
}

function ClienteModal({ open, cliente, tiposCliente, listasPrecios, onClose, onSaved }: ClienteModalProps) {
  const [saving, setSaving] = useState(false)
  const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<ClienteForm>({
    defaultValues: BLANK_CLIENTE,
  })
  const activo = watch('activo')
  const ciudadVal = watch('ciudad')

  useEffect(() => {
    if (!open) return
    reset(cliente
      ? {
          nombres: cliente.nombres,
          apellidos: cliente.apellidos,
          razon_social: cliente.razon_social ?? '',
          ruc_ci: cliente.ruc_ci,
          direccion: cliente.direccion ?? '',
          ciudad: cliente.ciudad ?? '',
          telefono: cliente.telefono ?? '',
          email: cliente.email ?? '',
          limite_credito: cliente.limite_credito,
          activo: cliente.activo,
          lista_precio: String(cliente.lista_precio),
          tipo_cliente: String(cliente.tipo_cliente),
        }
      : BLANK_CLIENTE
    )
  }, [open, cliente, reset])

  const onSubmit = handleSubmit(async (form) => {
    setSaving(true)
    const payload = {
      ...form,
      limite_credito: Number(form.limite_credito) || 0,
      lista_precio: Number(form.lista_precio),
      tipo_cliente: Number(form.tipo_cliente),
    }
    try {
      if (cliente) {
        await api.patch(`/clientes/clientes/${cliente.id}/`, payload)
        toast.success('Cliente actualizado')
      } else {
        await api.post('/clientes/clientes/', payload)
        toast.success('Cliente creado')
      }
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  })

  const selectClass = (hasError?: boolean) => [
    'w-full border rounded-xl px-3 py-2 text-sm text-slate-900 bg-white',
    'focus:outline-none focus:ring-2 transition-colors duration-150',
    hasError
      ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
      : 'border-slate-200 focus:ring-green-500/30 focus:border-green-500',
  ].join(' ')
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title={cliente ? `Editar — ${cliente.apellidos}, ${cliente.nombres}` : 'Nuevo Cliente'}
      onCancel={onClose}
      onOk={onSubmit}
      okText={cliente ? 'Guardar Cambios' : 'Crear Cliente'}
      confirmLoading={saving}
      width={680}
    >
      <div className="space-y-5">
        {/* Datos personales */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Nombres *"
            placeholder="Ej: Juan Carlos"
            error={errors.nombres?.message}
            {...register('nombres', { required: 'El nombre es obligatorio' })}
          />
          <Input
            label="Apellidos *"
            placeholder="Ej: González Pérez"
            error={errors.apellidos?.message}
            {...register('apellidos', { required: 'Los apellidos son obligatorios' })}
          />
          <Input
            label="RUC / CI *"
            placeholder="Ej: 1234567 o 80123456-5"
            error={errors.ruc_ci?.message}
            {...register('ruc_ci', {
              required: 'El RUC/CI es obligatorio',
              pattern: { value: RUC_CI_REGEX, message: 'Formato inválido. Ej: 1234567 o 80123456-5' },
            })}
          />
          <Input
            label="Razón Social"
            placeholder="Solo si es empresa"
            {...register('razon_social')}
          />
          <Input
            label="Teléfono"
            placeholder="+595 981 000 000"
            {...register('telefono')}
          />
          <Input
            label="Email"
            type="email"
            placeholder="cliente@email.com"
            error={errors.email?.message}
            {...register('email', {
              pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Email inválido' },
            })}
          />
          <Input
            label="Dirección"
            placeholder="Calle y número"
            {...register('direccion')}
          />
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Ciudad</label>
            <Combobox
              options={CIUDADES_PY.map(c => ({ value: c, label: c }))}
              value={ciudadVal || undefined}
              onChange={(v) => setValue('ciudad', String(v))}
              filterLocal
              placeholder="Buscar ciudad..."
            />
          </div>
        </div>

        {/* Comercial */}
        <div className="border-t border-slate-100 pt-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className={labelClass}>Tipo de Cliente *</label>
            <select
              className={selectClass(!!errors.tipo_cliente)}
              {...register('tipo_cliente', { required: 'Seleccioná un tipo' })}
            >
              <option value="">Seleccionar...</option>
              {tiposCliente.map(t => (
                <option key={t.id} value={t.id}>{t.nombre}</option>
              ))}
            </select>
            {errors.tipo_cliente && <p className="text-xs text-red-500 mt-0.5">{errors.tipo_cliente.message}</p>}
          </div>
          <div>
            <label className={labelClass}>Lista de Precio *</label>
            <select
              className={selectClass(!!errors.lista_precio)}
              {...register('lista_precio', { required: 'Seleccioná una lista' })}
            >
              <option value="">Seleccionar...</option>
              {listasPrecios.map(l => (
                <option key={l.id} value={l.id}>{l.nombre}</option>
              ))}
            </select>
            {errors.lista_precio && <p className="text-xs text-red-500 mt-0.5">{errors.lista_precio.message}</p>}
          </div>
          <Input
            label="Límite de Crédito (Gs.)"
            type="number"
            min="0"
            step="1000"
            placeholder="0"
            {...register('limite_credito', { min: { value: 0, message: 'Debe ser ≥ 0' } })}
          />
        </div>

        {/* Estado */}
        <div className="flex items-center gap-3 border-t border-slate-100 pt-4">
          <button
            type="button"
            role="switch"
            aria-checked={activo}
            onClick={() => setValue('activo', !activo)}
            className={[
              'relative w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500/30',
              activo ? 'bg-green-500' : 'bg-slate-200',
            ].join(' ')}
          >
            <span
              className={[
                'absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200',
                activo ? 'translate-x-5' : 'translate-x-0',
              ].join(' ')}
            />
          </button>
          <span className="text-sm text-slate-700 font-medium">
            Cliente {activo ? 'activo' : 'inactivo'}
          </span>
        </div>
      </div>
    </Modal>
  )
}

// ─── HijoModal ────────────────────────────────────────────────────────────────

const BLANK_HIJO: HijoForm = {
  nombre: '', apellido: '', fecha_nacimiento: '', grado: '', activo: true,
}

interface HijoModalProps {
  open: boolean
  hijo: Hijo | null
  clienteId: number
  onClose: () => void
  onSaved: () => void
}

function HijoModal({ open, hijo, clienteId, onClose, onSaved }: HijoModalProps) {
  const [form, setForm] = useState<HijoForm>(BLANK_HIJO)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setForm(hijo
      ? {
          nombre: hijo.nombre,
          apellido: hijo.apellido,
          fecha_nacimiento: hijo.fecha_nacimiento ?? '',
          grado: hijo.grado ?? '',
          activo: hijo.activo,
        }
      : BLANK_HIJO
    )
  }, [open, hijo])

  function setText(field: keyof HijoForm) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm(prev => ({ ...prev, [field]: e.target.value }))
  }

  async function handleSave() {
    if (!form.nombre || !form.apellido) {
      toast.error('Nombre y apellido son obligatorios')
      return
    }
    setSaving(true)
    const payload = {
      ...form,
      fecha_nacimiento: form.fecha_nacimiento || null,
      grado: form.grado || null,
      cliente_responsable: clienteId,
    }
    try {
      if (hijo) {
        await api.patch(`/clientes/hijos/${hijo.id}/`, payload)
        toast.success('Estudiante actualizado')
      } else {
        await api.post('/clientes/hijos/', payload)
        toast.success('Estudiante registrado')
      }
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
      title={hijo ? 'Editar Estudiante' : 'Nuevo Estudiante'}
      onCancel={onClose}
      onOk={handleSave}
      okText={hijo ? 'Guardar Cambios' : 'Registrar'}
      confirmLoading={saving}
      width={460}
    >
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Input label="Nombre *" value={form.nombre} onChange={setText('nombre')} placeholder="Juan" />
          <Input label="Apellido *" value={form.apellido} onChange={setText('apellido')} placeholder="García" />
          <Input label="Grado" value={form.grado} onChange={setText('grado')} placeholder="Ej: 5° Primaria A" />
          <Input label="Fecha de Nacimiento" type="date" value={form.fecha_nacimiento} onChange={setText('fecha_nacimiento')} />
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            role="switch"
            aria-checked={form.activo}
            onClick={() => setForm(prev => ({ ...prev, activo: !prev.activo }))}
            className={[
              'relative w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500/30',
              form.activo ? 'bg-green-500' : 'bg-slate-200',
            ].join(' ')}
          >
            <span
              className={[
                'absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200',
                form.activo ? 'translate-x-5' : 'translate-x-0',
              ].join(' ')}
            />
          </button>
          <span className="text-sm text-slate-700 font-medium">
            Estudiante {form.activo ? 'activo' : 'inactivo'}
          </span>
        </div>
      </div>
    </Modal>
  )
}

// ─── HijosModal ───────────────────────────────────────────────────────────────

interface HijosModalProps {
  open: boolean
  cliente: Cliente | null
  onClose: () => void
}

function HijosModal({ open, cliente, onClose }: HijosModalProps) {
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [restricciones, setRestricciones] = useState<Record<number, RestriccionHijo[]>>({})
  const [loading, setLoading] = useState(false)
  const [hijoModal, setHijoModal] = useState<{ open: boolean; hijo: Hijo | null }>({ open: false, hijo: null })
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const loadHijos = useCallback(async () => {
    if (!cliente) return
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/hijos/', { params: { cliente_responsable: cliente.id } })
      const list: Hijo[] = data.results ?? data
      setHijos(list)
      const rest: Record<number, RestriccionHijo[]> = {}
      await Promise.all(
        list.map(async (h) => {
          const { data: rd } = await api.get('/clientes/restricciones/', { params: { hijo: h.id } })
          rest[h.id] = rd.results ?? rd
        })
      )
      setRestricciones(rest)
    } catch {
      toast.error('Error al cargar estudiantes')
    } finally {
      setLoading(false)
    }
  }, [cliente])

  useEffect(() => {
    if (open) {
      setExpandedId(null)
      loadHijos()
    }
  }, [open, loadHijos])

  async function toggleActivo(h: Hijo) {
    try {
      await api.patch(`/clientes/hijos/${h.id}/`, { activo: !h.activo })
      toast.success(h.activo ? 'Estudiante desactivado' : 'Estudiante activado')
      loadHijos()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }

  function maxSeveridad(rests: RestriccionHijo[]): BadgeColor {
    const active = rests.filter(r => r.activo)
    if (active.some(r => r.severidad === 'CRITICA')) return 'red'
    if (active.some(r => r.severidad === 'ALTA')) return 'orange'
    if (active.some(r => r.severidad === 'MEDIA')) return 'yellow'
    if (active.some(r => r.severidad === 'BAJA')) return 'blue'
    return 'default'
  }

  return (
    <>
      <Modal
        open={open}
        title={`Estudiantes — ${cliente?.apellidos ?? ''}, ${cliente?.nombres ?? ''}`}
        onCancel={onClose}
        footer={null}
        width={620}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-500">
              {hijos.length} estudiante{hijos.length !== 1 ? 's' : ''} registrado{hijos.length !== 1 ? 's' : ''}
            </p>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setHijoModal({ open: true, hijo: null })}
            >
              <Plus className="w-3.5 h-3.5" />
              Agregar
            </Button>
          </div>

          {loading ? (
            <Spinner className="py-10" />
          ) : hijos.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Baby className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Sin estudiantes registrados</p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100 -mx-6 px-6">
              {hijos.map((hijo) => {
                const rests = restricciones[hijo.id] ?? []
                const activeRests = rests.filter(r => r.activo)
                const isExpanded = expandedId === hijo.id

                return (
                  <li key={hijo.id} className="py-3.5">
                    <div className="flex items-start gap-3">
                      {/* Avatar */}
                      <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center shrink-0 mt-0.5">
                        {hijo.foto_perfil ? (
                          <img
                            src={hijo.foto_perfil}
                            alt=""
                            className="w-9 h-9 rounded-full object-cover"
                          />
                        ) : (
                          <span className="text-blue-700 font-bold text-sm">
                            {hijo.nombre[0]}{hijo.apellido[0]}
                          </span>
                        )}
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-semibold text-slate-800">
                            {hijo.apellido}, {hijo.nombre}
                          </span>
                          <Badge color={hijo.activo ? 'green' : 'red'}>
                            {hijo.activo ? 'Activo' : 'Inactivo'}
                          </Badge>
                          {activeRests.length > 0 && (
                            <Badge color={maxSeveridad(activeRests)}>
                              <ShieldAlert className="w-3 h-3 mr-1 inline-block" />
                              {activeRests.length} restricción{activeRests.length !== 1 ? 'es' : ''}
                            </Badge>
                          )}
                        </div>
                        {hijo.grado && (
                          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                            <GraduationCap className="w-3 h-3 shrink-0" />
                            {hijo.grado}
                          </p>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-1 shrink-0">
                        {activeRests.length > 0 && (
                          <button
                            onClick={() => setExpandedId(isExpanded ? null : hijo.id)}
                            className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                          >
                            <AlertTriangle className="w-3 h-3" />
                            {isExpanded ? 'Ocultar' : 'Ver'}
                          </button>
                        )}
                        <button
                          onClick={() => setHijoModal({ open: true, hijo })}
                          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => toggleActivo(hijo)}
                          className={[
                            'px-2 py-1 text-xs font-medium rounded-lg transition-colors',
                            hijo.activo
                              ? 'text-slate-400 hover:text-red-600 hover:bg-red-50'
                              : 'text-slate-400 hover:text-green-600 hover:bg-green-50',
                          ].join(' ')}
                          title={hijo.activo ? 'Desactivar' : 'Activar'}
                        >
                          {hijo.activo ? 'Desactivar' : 'Activar'}
                        </button>
                      </div>
                    </div>

                    {/* Restricciones expandidas */}
                    {isExpanded && activeRests.length > 0 && (
                      <div className="mt-2.5 ml-12 space-y-1.5">
                        {activeRests.map((r) => (
                          <div
                            key={r.id}
                            className="flex items-start gap-2.5 bg-orange-50 border border-orange-100 rounded-xl px-3 py-2"
                          >
                            <Badge color={SEV_COLOR[r.severidad]} className="shrink-0 mt-0.5">
                              {SEV_LABEL[r.severidad]}
                            </Badge>
                            <div className="text-xs">
                              <p className="font-semibold text-slate-700">{r.tipo}</p>
                              {r.descripcion && (
                                <p className="text-slate-500 mt-0.5">{r.descripcion}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}

          {/* Footer */}
          <div className="pt-3 border-t border-slate-100 flex justify-end">
            <Button variant="secondary" onClick={onClose}>Cerrar</Button>
          </div>
        </div>
      </Modal>

      <HijoModal
        open={hijoModal.open}
        hijo={hijoModal.hijo}
        clienteId={cliente?.id ?? 0}
        onClose={() => setHijoModal({ open: false, hijo: null })}
        onSaved={loadHijos}
      />
    </>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

const PAGE_SIZE = 20

export default function Clientes() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [tiposCliente, setTiposCliente] = useState<TipoCliente[]>([])
  const [listasPrecios, setListasPrecios] = useState<ListaPrecio[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [filterActivo, setFilterActivo] = useState('')
  const [filterTipo, setFilterTipo] = useState('')

  const [clienteModal, setClienteModal] = useState<{ open: boolean; cliente: Cliente | null }>({
    open: false, cliente: null,
  })
  const [hijosModal, setHijosModal] = useState<{ open: boolean; cliente: Cliente | null }>({
    open: false, cliente: null,
  })

  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  useEffect(() => {
    api.get('/clientes/tipos-cliente/').then(({ data }) => setTiposCliente(data.results ?? data)).catch(() => {})
    api.get('/productos/listas-precio/').then(({ data }) => setListasPrecios(data.results ?? data)).catch(() => {})
  }, [])

  const loadClientes = useCallback(async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, page_size: PAGE_SIZE }
      if (search) params.search = search
      if (filterActivo) params.activo = filterActivo
      if (filterTipo) params.tipo_cliente = filterTipo
      const { data } = await api.get('/clientes/clientes/', { params })
      setClientes(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      toast.error('Error al cargar clientes')
    } finally {
      setLoading(false)
    }
  }, [page, search, filterActivo, filterTipo])

  useEffect(() => {
    loadClientes()
  }, [loadClientes])

  function handleSearchChange(value: string) {
    setSearchInput(value)
    clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => {
      setPage(1)
      setSearch(value)
    }, 350)
  }

  function handleFilterChange(setter: (v: string) => void) {
    return (e: React.ChangeEvent<HTMLSelectElement>) => {
      setter(e.target.value)
      setPage(1)
    }
  }

  const columns = useMemo<Column<Cliente>[]>(() => [
    {
      title: 'RUC / CI',
      key: 'ruc_ci',
      dataIndex: 'ruc_ci',
      render: (v) => (
        <span className="font-mono text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-lg">
          {v as string}
        </span>
      ),
    },
    {
      title: 'Cliente',
      key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-sm font-semibold text-slate-800">{r.apellidos}, {r.nombres}</p>
          {r.tipo_cliente_nombre && (
            <p className="text-xs text-slate-400 mt-0.5">{r.tipo_cliente_nombre}</p>
          )}
        </div>
      ),
    },
    {
      title: 'Contacto',
      key: 'contacto',
      render: (_, r) => (
        <div className="space-y-0.5 text-xs text-slate-500">
          {r.telefono && (
            <div className="flex items-center gap-1">
              <Phone className="w-3 h-3 shrink-0" />
              {r.telefono}
            </div>
          )}
          {r.email && (
            <div className="flex items-center gap-1">
              <Mail className="w-3 h-3 shrink-0" />
              {r.email}
            </div>
          )}
          {!r.telefono && !r.email && <span className="text-slate-300">—</span>}
        </div>
      ),
    },
    {
      title: 'Saldo CC',
      key: 'saldo',
      render: (_, r) => {
        const saldo = Number(r.saldo_cuenta_corriente) || 0
        return (
          <span className={[
            'tabular-nums text-sm font-semibold',
            saldo > 0 ? 'text-red-600' : 'text-emerald-700',
          ].join(' ')}>
            {saldo > 0 ? '+' : ''}{formatGs(saldo)}
          </span>
        )
      },
    },
    {
      title: 'Límite Créd.',
      key: 'limite',
      render: (_, r) => (
        <span className="tabular-nums text-sm text-slate-600">{formatGs(r.limite_credito)}</span>
      ),
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => (
        <Badge color={r.activo ? 'green' : 'red'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>
      ),
    },
    {
      title: '',
      key: 'acciones',
      render: (_, r) => (
        <div className="flex items-center gap-1.5 justify-end">
          <button
            onClick={() => setHijosModal({ open: true, cliente: r })}
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          >
            <Users className="w-3.5 h-3.5" />
            Hijos
          </button>
          <button
            onClick={() => setClienteModal({ open: true, cliente: r })}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Editar cliente"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ], [])

  const stats = useMemo(() => ({
    activos: clientes.filter(c => c.activo).length,
    conDeuda: clientes.filter(c => (Number(c.saldo_cuenta_corriente) || 0) > 0).length,
  }), [clientes])

  const selectClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'

  return (
    <div className="p-4 md:p-6 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Clientes</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de clientes y sus estudiantes</p>
        </div>
        <Button variant="primary" onClick={() => setClienteModal({ open: true, cliente: null })}>
          <Plus className="w-4 h-4" />
          Nuevo Cliente
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total', value: total, color: 'text-slate-900' },
          { label: 'Activos', value: stats.activos, color: 'text-green-600' },
          { label: 'Con Deuda', value: stats.conDeuda, color: 'text-red-600' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
            <p className={`text-2xl font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex flex-wrap gap-3 items-center">
        <div className="flex-1 min-w-48 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            className="w-full border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-sm text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
            placeholder="Buscar por nombre, apellido o RUC/CI..."
            value={searchInput}
            onChange={e => handleSearchChange(e.target.value)}
          />
        </div>
        <select value={filterActivo} onChange={handleFilterChange(setFilterActivo)} className={selectClass}>
          <option value="">Todos los estados</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
        <select value={filterTipo} onChange={handleFilterChange(setFilterTipo)} className={selectClass}>
          <option value="">Todos los tipos</option>
          {tiposCliente.map(t => (
            <option key={t.id} value={t.id}>{t.nombre}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden p-1">
        <Table
          columns={columns}
          dataSource={clientes}
          rowKey="id"
          loading={loading}
          pageSize={PAGE_SIZE}
          page={page}
          onPageChange={setPage}
          total={total}
        />
      </div>

      {/* Modals */}
      <ClienteModal
        open={clienteModal.open}
        cliente={clienteModal.cliente}
        tiposCliente={tiposCliente}
        listasPrecios={listasPrecios}
        onClose={() => setClienteModal({ open: false, cliente: null })}
        onSaved={loadClientes}
      />
      <HijosModal
        open={hijosModal.open}
        cliente={hijosModal.cliente}
        onClose={() => setHijosModal({ open: false, cliente: null })}
      />
    </div>
  )
}
