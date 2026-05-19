import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { UserPlus, Search, Edit2, Eye, EyeOff } from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import Modal from '../components/ui/Modal'

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

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Usuario {
  id: number
  email: string
  nombre: string
  apellido: string
  rol: string
  nombre_completo: string
  is_active: boolean
}

interface UsuarioForm {
  email: string
  nombre: string
  apellido: string
  rol: string
  password: string
  is_active: boolean
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ROL_COLOR: Record<string, BadgeColor> = {
  ADMIN: 'purple',
  CAJERO: 'blue',
  COCINA: 'orange',
  CLIENTE_WEB: 'green',
}

const ROL_LABEL: Record<string, string> = {
  ADMIN: 'Administrador',
  CAJERO: 'Cajero',
  COCINA: 'Cocina',
  CLIENTE_WEB: 'Portal Padres',
}

const FORM_INITIAL: UsuarioForm = {
  email: '', nombre: '', apellido: '', rol: 'CAJERO', password: '', is_active: true,
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [filterRol, setFilterRol] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const [modalOpen, setModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<Usuario | null>(null)
  const [form, setForm] = useState<UsuarioForm>(FORM_INITIAL)
  const [showPassword, setShowPassword] = useState(false)
  const [saving, setSaving] = useState(false)

  // ── Load ─────────────────────────────────────────────────────────
  const loadUsuarios = useCallback(async (q: string, rol: string, p: number) => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15 }
      if (q) params.search = q
      if (rol) params.rol = rol
      const { data } = await api.get('/usuarios/usuarios/', { params })
      setUsuarios(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      toast.error('Error al cargar usuarios')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(searchTimer.current)
    searchTimer.current = setTimeout(() => {
      setPage(1)
      loadUsuarios(search, filterRol, 1)
    }, 350)
    return () => clearTimeout(searchTimer.current)
  }, [search, filterRol, loadUsuarios])

  useEffect(() => {
    loadUsuarios(search, filterRol, page)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  // ── Open modal ────────────────────────────────────────────────────
  const openCreate = useCallback(() => {
    setEditingUser(null)
    setForm(FORM_INITIAL)
    setShowPassword(false)
    setModalOpen(true)
  }, [])

  const openEdit = useCallback((u: Usuario) => {
    setEditingUser(u)
    setForm({
      email: u.email,
      nombre: u.nombre,
      apellido: u.apellido,
      rol: u.rol,
      password: '',
      is_active: u.is_active,
    })
    setShowPassword(false)
    setModalOpen(true)
  }, [])

  // ── Save ──────────────────────────────────────────────────────────
  const handleSave = useCallback(async () => {
    if (!form.email || !form.nombre) { toast.error('Completá email y nombre'); return }
    if (!editingUser && form.password.length < 6) { toast.error('La contraseña debe tener mínimo 6 caracteres'); return }
    setSaving(true)
    try {
      const payload: Record<string, unknown> = {
        email: form.email,
        nombre: form.nombre,
        apellido: form.apellido,
        rol: form.rol,
        is_active: form.is_active,
      }
      if (form.password) payload.password = form.password

      if (editingUser) {
        await api.patch(`/usuarios/usuarios/${editingUser.id}/`, payload)
        toast.success('Usuario actualizado')
      } else {
        await api.post('/usuarios/usuarios/', payload)
        toast.success('Usuario creado')
      }
      setModalOpen(false)
      setPage(1)
      loadUsuarios(search, filterRol, 1)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }, [form, editingUser, search, filterRol, loadUsuarios])

  // ── Toggle activo ─────────────────────────────────────────────────
  const toggleActivo = useCallback(async (u: Usuario) => {
    try {
      await api.patch(`/usuarios/usuarios/${u.id}/`, { is_active: !u.is_active })
      toast.success(u.is_active ? 'Usuario desactivado' : 'Usuario activado')
      loadUsuarios(search, filterRol, page)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [search, filterRol, page, loadUsuarios])

  // ── Columns ──────────────────────────────────────────────────────
  const columns: Column<Usuario>[] = [
    {
      title: 'Usuario',
      key: 'usuario',
      render: (_, r) => (
        <div>
          <p className="text-sm font-semibold text-slate-800">{r.nombre_completo || `${r.nombre} ${r.apellido}`}</p>
          <p className="text-xs text-slate-400">{r.email}</p>
        </div>
      ),
    },
    {
      title: 'Rol',
      key: 'rol',
      render: (_, r) => <Badge color={ROL_COLOR[r.rol] ?? 'default'}>{ROL_LABEL[r.rol] ?? r.rol}</Badge>,
    },
    {
      title: 'Estado',
      key: 'activo',
      render: (_, r) => <Badge color={r.is_active ? 'green' : 'default'}>{r.is_active ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 160,
      render: (_, r) => (
        <div className="flex gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => openEdit(r)}>
            <Edit2 className="w-3.5 h-3.5" />
            Editar
          </Button>
          <Button
            size="sm"
            variant={r.is_active ? 'danger' : 'primary'}
            onClick={() => toggleActivo(r)}
          >
            {r.is_active ? 'Desactivar' : 'Activar'}
          </Button>
        </div>
      ),
    },
  ]

  // ── Styles ────────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const ROLES_SISTEMA = [
    { value: 'ADMIN', label: 'Administrador' },
    { value: 'CAJERO', label: 'Cajero' },
    { value: 'COCINA', label: 'Cocina' },
    { value: 'CLIENTE_WEB', label: 'Portal Padres' },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Usuarios</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de usuarios y roles del sistema</p>
        </div>
        <Button variant="primary" onClick={openCreate}>
          <UserPlus className="w-4 h-4" />
          Nuevo Usuario
        </Button>
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[200px]">
          <label className={labelClass}>Buscar</label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            <input
              placeholder="Nombre, email..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className={`${inputClass} pl-9`}
            />
          </div>
        </div>
        <div>
          <label className={labelClass}>Rol</label>
          <select
            value={filterRol}
            onChange={e => { setFilterRol(e.target.value); setPage(1) }}
            className={`${inputClass} w-auto`}
          >
            <option value="">Todos</option>
            {ROLES_SISTEMA.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table
            columns={columns}
            dataSource={usuarios}
            rowKey="id"
            loading={loading}
            pageSize={15}
            page={page}
            onPageChange={setPage}
            total={total}
          />
        </div>
      </div>

      {/* ── Create/Edit modal ──────────────────────────────────────── */}
      <Modal
        open={modalOpen}
        title={editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        okText={editingUser ? 'Guardar' : 'Crear'}
        confirmLoading={saving}
        width={500}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nombre *</label>
              <input
                value={form.nombre}
                onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))}
                placeholder="Juan"
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Apellido</label>
              <input
                value={form.apellido}
                onChange={e => setForm(f => ({ ...f, apellido: e.target.value }))}
                placeholder="García"
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label className={labelClass}>Email *</label>
            <input
              type="email"
              value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              placeholder="usuario@cantina.com"
              className={inputClass}
            />
          </div>

          <div>
            <label className={labelClass}>Rol</label>
            <select value={form.rol} onChange={e => setForm(f => ({ ...f, rol: e.target.value }))} className={inputClass}>
              {ROLES_SISTEMA.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>

          <div>
            <label className={labelClass}>
              {editingUser ? 'Nueva Contraseña (dejar vacío para no cambiar)' : 'Contraseña *'}
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                placeholder={editingUser ? 'Nueva contraseña...' : 'Mínimo 6 caracteres'}
                className={`${inputClass} pr-10`}
              />
              <button
                type="button"
                onClick={() => setShowPassword(s => !s)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative shrink-0">
              <input type="checkbox" className="sr-only peer" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} />
              <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
            </div>
            <span className="text-sm text-slate-700">Usuario activo</span>
          </label>
        </div>
      </Modal>
    </div>
  )
}
