import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { UserPlus, Search, Edit2, Eye, EyeOff, Shield, Users } from 'lucide-react'
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

interface Rol {
  id_rol: number
  nombre_rol: string
  descripcion: string | null
  estado: boolean
}

interface Permiso {
  id: number
  codigo_permiso: string
  nombre: string
  modulo: string
  descripcion: string | null
}

interface RolPermiso {
  id: number
  id_rol: number
  id_permiso: number
  rol_nombre: string
  permiso_codigo: string
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

type TabKey = 'usuarios' | 'permisos'

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Usuarios() {
  const [tab, setTab] = useState<TabKey>('usuarios')

  // ── Usuarios ──────────────────────────────────────────────────────
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

  // ── Permisos ──────────────────────────────────────────────────────
  const [roles, setRoles] = useState<Rol[]>([])
  const [permisos, setPermisos] = useState<Permiso[]>([])
  const [selectedRolId, setSelectedRolId] = useState<number | null>(null)
  const [rolPermisos, setRolPermisos] = useState<RolPermiso[]>([])
  const [loadingRolPermisos, setLoadingRolPermisos] = useState(false)
  const [togglingPermiso, setTogglingPermiso] = useState<number | null>(null)

  // ── Load usuarios ─────────────────────────────────────────────────
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

  // ── Load roles / permisos ─────────────────────────────────────────
  const loadRoles = useCallback(async () => {
    try {
      const { data } = await api.get('/usuarios/roles/', { params: { page_size: 100 } })
      setRoles(data.results ?? data)
    } catch { /* silent */ }
  }, [])

  const loadPermisosAll = useCallback(async () => {
    try {
      const { data } = await api.get('/usuarios/permisos/', { params: { page_size: 500 } })
      setPermisos(data.results ?? data)
    } catch { /* silent */ }
  }, [])

  const loadRolPermisos = useCallback(async (rolId: number) => {
    setLoadingRolPermisos(true)
    try {
      const { data } = await api.get('/usuarios/roles-permisos/', { params: { id_rol: rolId, page_size: 500 } })
      setRolPermisos(data.results ?? data)
    } catch {
      toast.error('Error al cargar permisos del rol')
    } finally {
      setLoadingRolPermisos(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'permisos') {
      loadRoles()
      loadPermisosAll()
    }
  }, [tab, loadRoles, loadPermisosAll])

  useEffect(() => {
    if (selectedRolId) loadRolPermisos(selectedRolId)
    else setRolPermisos([])
  }, [selectedRolId, loadRolPermisos])

  // ── Toggle permiso ────────────────────────────────────────────────
  const togglePermiso = useCallback(async (permisoId: number, currentlyAssigned: boolean) => {
    if (!selectedRolId) return
    setTogglingPermiso(permisoId)
    try {
      if (currentlyAssigned) {
        const rp = rolPermisos.find(r => r.id_permiso === permisoId)
        if (rp) await api.delete(`/usuarios/roles-permisos/${rp.id}/`)
      } else {
        await api.post('/usuarios/roles-permisos/', { id_rol: selectedRolId, id_permiso: permisoId })
      }
      await loadRolPermisos(selectedRolId)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setTogglingPermiso(null)
    }
  }, [selectedRolId, rolPermisos, loadRolPermisos])

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

  // ── Permisos agrupados por módulo ─────────────────────────────────
  const permisosPorModulo = permisos.reduce<Record<string, Permiso[]>>((acc, p) => {
    if (!acc[p.modulo]) acc[p.modulo] = []
    acc[p.modulo].push(p)
    return acc
  }, {})

  const TABS = [
    { key: 'usuarios' as TabKey, label: 'Usuarios', icon: Users },
    { key: 'permisos' as TabKey, label: 'Roles y Permisos', icon: Shield },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Usuarios</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de usuarios, roles y permisos</p>
        </div>
        {tab === 'usuarios' && (
          <Button variant="primary" onClick={openCreate}>
            <UserPlus className="w-4 h-4" />
            Nuevo Usuario
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Usuarios tab ──────────────────────────────────────────── */}
      {tab === 'usuarios' && (
        <>
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
        </>
      )}

      {/* ── Permisos tab ──────────────────────────────────────────── */}
      {tab === 'permisos' && (
        <div className="space-y-5">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
            <label className={labelClass}>Rol</label>
            <select
              value={selectedRolId ?? ''}
              onChange={e => setSelectedRolId(Number(e.target.value) || null)}
              className={`${inputClass} max-w-xs`}
            >
              <option value="">— Elegí un rol —</option>
              {roles.map(r => (
                <option key={r.id_rol} value={r.id_rol}>{r.nombre_rol}</option>
              ))}
            </select>
          </div>

          {selectedRolId && (
            loadingRolPermisos ? (
              <div className="py-12 text-center text-slate-400 text-sm">Cargando permisos...</div>
            ) : (
              <div className="space-y-3">
                {Object.entries(permisosPorModulo).sort(([a], [b]) => a.localeCompare(b)).map(([modulo, permsInMod]) => (
                  <div key={modulo} className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                    <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/80">
                      <h3 className="text-xs font-bold text-slate-600 uppercase tracking-wider">{modulo}</h3>
                    </div>
                    <div className="divide-y divide-slate-50">
                      {permsInMod.map(p => {
                        const assigned = rolPermisos.some(rp => rp.id_permiso === p.id)
                        const toggling = togglingPermiso === p.id
                        return (
                          <label
                            key={p.id}
                            className="flex items-center justify-between px-5 py-3 hover:bg-slate-50/60 cursor-pointer transition-colors group"
                          >
                            <div className="flex-1 min-w-0 mr-4">
                              <p className="text-sm font-medium text-slate-800 group-hover:text-slate-900">{p.nombre}</p>
                              <p className="text-xs text-slate-400 font-mono mt-0.5">{p.codigo_permiso}</p>
                            </div>
                            <div className={`relative shrink-0 ${toggling ? 'opacity-50 pointer-events-none' : ''}`}>
                              <input
                                type="checkbox"
                                className="sr-only peer"
                                checked={assigned}
                                onChange={() => togglePermiso(p.id, assigned)}
                              />
                              <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
                              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
                            </div>
                          </label>
                        )
                      })}
                    </div>
                  </div>
                ))}
                {permisos.length === 0 && (
                  <div className="text-center py-10 text-slate-400 text-sm">No hay permisos configurados en el sistema.</div>
                )}
              </div>
            )
          )}

          {!selectedRolId && (
            <div className="text-center py-20 text-slate-400">
              <Shield className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p className="text-sm font-medium">Elegí un rol para ver y editar sus permisos</p>
            </div>
          )}
        </div>
      )}

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
