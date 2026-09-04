import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { UserPlus, Search, Edit2, Briefcase, ShieldOff, Fingerprint, Users, HardHat, Plus, Pencil, Trash2, Globe, RefreshCw, KeyRound } from 'lucide-react'
import api from '../services/api'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import {
  extractErrorMessage,
  type Usuario, type UsuarioPortal, type Rol, type Empleado, type TabKey,
  ROL_COLOR, ROL_LABEL, ROLES_SISTEMA,
} from './usuarios/shared'
import ModalUsuario from './usuarios/ModalUsuario'
import ModalEmpleado from './usuarios/ModalEmpleado'
import ModalRol from './usuarios/ModalRol'

export default function Usuarios() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<TabKey>('usuarios')

  // ── Usuarios ──────────────────────────────────────────────────────
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [filterRol, setFilterRol] = useState('')
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const searchTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdRef = useRef(0)

  const [modalOpen, setModalOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<Usuario | null>(null)

  // ── Roles (puestos de trabajo) ──────────────────────────────────────
  const [roles, setRoles] = useState<Rol[]>([])

  // ── Portal Padres ─────────────────────────────────────────────────
  const [padres, setPadres] = useState<UsuarioPortal[]>([])
  const [loadingPadres, setLoadingPadres] = useState(false)
  const [totalPadres, setTotalPadres] = useState(0)
  const [pagePadres, setPagePadres] = useState(1)
  const [searchPadres, setSearchPadres] = useState('')
  const [resettingId, setResettingId] = useState<number | null>(null)
  const searchPadresTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  // ── Rol CRUD ──────────────────────────────────────────────────────
  const [rolModal, setRolModal] = useState<{ open: boolean; rol: Rol | null }>({ open: false, rol: null })
  const [deletingRolId, setDeletingRolId] = useState<number | null>(null)

  // ── Load usuarios ─────────────────────────────────────────────────
  const loadUsuarios = useCallback(async (q: string, rol: string, p: number) => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, sin_portal: '1' }
      if (q) params.search = q
      if (rol) params.rol = rol
      const { data } = await api.get('/usuarios/usuarios/', { params })
      if (requestId !== requestIdRef.current) return
      setUsuarios(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (requestId !== requestIdRef.current) return
      toast.error('Error al cargar usuarios')
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
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

  // ── Load roles (puestos de trabajo) ────────────────────────────────
  const loadRoles = useCallback(async () => {
    try {
      const { data } = await api.get('/usuarios/roles/', { params: { page_size: 100 } })
      setRoles(data.results ?? data)
    } catch { /* silent */ }
  }, [])

  useEffect(() => {
    if (tab === 'roles') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadRoles()
    }
  }, [tab, loadRoles])

  // ── Empleados ──────────────────────────────────────────────────────
  const [empleados, setEmpleados] = useState<Empleado[]>([])
  const [loadingEmp, setLoadingEmp] = useState(false)
  const [totalEmp, setTotalEmp] = useState(0)
  const [pageEmp, setPageEmp] = useState(1)
  const [empModalOpen, setEmpModalOpen] = useState(false)
  const [editingEmp, setEditingEmp] = useState<Empleado | null>(null)

  const loadEmpleados = useCallback(async (p: number) => {
    setLoadingEmp(true)
    try {
      const { data } = await api.get('/usuarios/empleados/', {
        params: { page: p, page_size: 15 },
      })
      setEmpleados(data.results ?? [])
      setTotalEmp(data.count ?? 0)
    } catch {
      toast.error('Error al cargar empleados')
    } finally {
      setLoadingEmp(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'empleados') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadEmpleados(1)
      loadRoles()
    }
  }, [tab, loadEmpleados, loadRoles])

  const loadPadres = useCallback(async (q: string, p: number) => {
    setLoadingPadres(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, rol: 'CLIENTE_WEB' }
      if (q) params.search = q
      const { data } = await api.get('/usuarios/usuarios/', { params })
      setPadres(data.results ?? [])
      setTotalPadres(data.count ?? 0)
    } catch {
      toast.error('Error al cargar usuarios del portal')
    } finally {
      setLoadingPadres(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'portal') {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setPagePadres(1)
      loadPadres(searchPadres, 1)
    }
  }, [tab]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (tab !== 'portal') return
    clearTimeout(searchPadresTimer.current)
    searchPadresTimer.current = setTimeout(() => {
      setPagePadres(1)
      loadPadres(searchPadres, 1)
    }, 350)
    return () => clearTimeout(searchPadresTimer.current)
  }, [searchPadres, loadPadres, tab])

  const resetearPassword = useCallback(async (padre: UsuarioPortal) => {
    if (!window.confirm(`¿Resetear contraseña de ${padre.nombre_completo} al CI/RUC ${padre.cliente_ruc_ci}?`)) return
    setResettingId(padre.id_usuario)
    try {
      await api.post(`/usuarios/usuarios/${padre.id_usuario}/resetear-password/`)
      toast.success(`Contraseña reseteada — el padre deberá cambiarla al ingresar`)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setResettingId(null)
    }
  }, [])

  const toggleActivoPadre = useCallback(async (padre: UsuarioPortal) => {
    try {
      await api.patch(`/usuarios/usuarios/${padre.id_usuario}/`, { is_active: !padre.is_active })
      toast.success(padre.is_active ? 'Acceso desactivado' : 'Acceso activado')
      loadPadres(searchPadres, pagePadres)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadPadres, searchPadres, pagePadres])

  const [desactivando2FAId, setDesactivando2FAId] = useState<number | null>(null)

  const desactivar2FA = useCallback(async (padre: UsuarioPortal) => {
    if (!window.confirm(`¿Desactivar la verificación en dos pasos de ${padre.nombre_completo}? Va a tener que configurarla de nuevo en su próximo ingreso.`)) return
    setDesactivando2FAId(padre.id_usuario)
    try {
      await api.post('/usuarios/2fa/desactivar/', { usuario_id: padre.id_usuario })
      toast.success('Verificación en dos pasos desactivada')
      loadPadres(searchPadres, pagePadres)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setDesactivando2FAId(null)
    }
  }, [loadPadres, searchPadres, pagePadres])

  const [desactivandoHuellaId, setDesactivandoHuellaId] = useState<number | null>(null)

  const desactivarHuella = useCallback(async (padre: UsuarioPortal) => {
    if (!window.confirm(`¿Desactivar la huella/Face ID de ${padre.nombre_completo}? Va a tener que registrarla de nuevo en su próximo ingreso.`)) return
    setDesactivandoHuellaId(padre.id_usuario)
    try {
      await api.post('/usuarios/webauthn/desactivar/', { usuario_id: padre.id_usuario })
      toast.success('Huella desactivada')
      loadPadres(searchPadres, pagePadres)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setDesactivandoHuellaId(null)
    }
  }, [loadPadres, searchPadres, pagePadres])

  // ── Eliminar rol ──────────────────────────────────────────────────
  const deleteRol = useCallback(async (rolId: number) => {
    if (!window.confirm('¿Eliminar este rol? Los empleados asignados quedarán sin rol.')) return
    setDeletingRolId(rolId)
    try {
      await api.delete(`/usuarios/roles/${rolId}/`)
      toast.success('Rol eliminado')
      loadRoles()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setDeletingRolId(null)
    }
  }, [loadRoles])

  // ── Toggle activo ─────────────────────────────────────────────────
  const toggleActivo = useCallback(async (u: Usuario) => {
    try {
      await api.patch(`/usuarios/usuarios/${u.id_usuario}/`, { is_active: !u.is_active })
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
          <p className="text-base font-semibold text-slate-800">{r.nombre_completo || `${r.nombre} ${r.apellido}`}</p>
          <p className="text-sm text-slate-400">{r.email}</p>
          {r.rol !== 'CLIENTE_WEB' && (
            <p className="text-xs text-slate-400">CI/RUC: {r.ci_ruc || <span className="text-red-500">sin cargar</span>}</p>
          )}
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
          <Button size="sm" variant="secondary" onClick={() => { setEditingUser(r); setModalOpen(true) }}>
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
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const colsRoles: Column<Rol>[] = [
    {
      title: 'Rol',
      key: 'nombre_rol',
      render: (_, r) => <span className="text-base font-medium text-slate-800">{r.nombre_rol}</span>,
    },
    {
      title: 'Descripción',
      key: 'descripcion',
      render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={r.estado ? 'green' : 'default'}>{r.estado ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 100,
      render: (_, r) => (
        <div className="flex gap-1.5 justify-end">
          <button
            onClick={() => setRolModal({ open: true, rol: r })}
            title="Editar rol"
            className="p-2 rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition-colors cursor-pointer"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => deleteRol(r.id_rol)}
            disabled={deletingRolId === r.id_rol}
            title="Eliminar rol"
            className="p-2 rounded-xl border border-red-200 text-red-500 hover:bg-red-50 transition-colors cursor-pointer disabled:opacity-50"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ]

  const colsEmpleados: Column<Empleado>[] = [
    {
      title: 'Empleado',
      key: 'nombre',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.nombre} {r.apellido}</p>
          <p className="text-sm text-slate-400">{r.email || '—'}</p>
        </div>
      ),
    },
    { title: 'Teléfono', key: 'telefono', render: (_, r) => <span className="text-sm text-slate-600">{r.telefono || '—'}</span> },
    { title: 'Rol', key: 'rol', render: (_, r) => <Badge color="blue">{r.rol_nombre}</Badge> },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={r.estado ? 'green' : 'default'}>{r.estado ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 80,
      render: (_, r) => (
        <Button size="sm" variant="secondary" onClick={() => { setEditingEmp(r); setEmpModalOpen(true) }}>
          <Edit2 className="w-3.5 h-3.5" />
          Editar
        </Button>
      ),
    },
  ]

  const TABS = [
    { key: 'usuarios'  as TabKey, label: 'Usuarios',     icon: Users     },
    { key: 'empleados' as TabKey, label: 'Empleados',    icon: HardHat   },
    { key: 'roles'     as TabKey, label: 'Roles',        icon: Briefcase },
    { key: 'portal'    as TabKey, label: 'Portal Padres', icon: Globe    },
  ]

  const colsPadres: Column<UsuarioPortal>[] = [
    {
      title: 'Padre / Tutor',
      key: 'nombre',
      render: (_, r) => (
        <div>
          <p className="text-base font-semibold text-slate-800">{r.nombre_completo || `${r.nombre} ${r.apellido}`}</p>
          <p className="text-sm text-slate-400 font-mono">{r.cliente_ruc_ci ?? '—'}</p>
        </div>
      ),
    },
    {
      title: 'Email / Acceso',
      key: 'email',
      render: (_, r) => {
        const esSintetico = r.email.endsWith('@portal.tita.local')
        return (
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500 truncate max-w-[180px]">{r.email}</span>
            <span className={`shrink-0 text-xs font-bold px-2 py-0.5 rounded-full ${esSintetico ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}>
              {esSintetico ? 'Sintético' : 'Real'}
            </span>
          </div>
        )
      },
    },
    {
      title: 'Último acceso',
      key: 'ultimo_acceso',
      render: (_, r) => (
        <span className="text-sm text-slate-500">
          {r.ultimo_acceso
            ? new Date(r.ultimo_acceso).toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : <span className="text-slate-300 italic">Nunca ingresó</span>}
        </span>
      ),
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={r.is_active ? 'green' : 'default'}>{r.is_active ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '2FA',
      key: '2fa',
      render: (_, r) => (
        <div className="flex gap-1">
          <Badge color={r.tiene_2fa_activo ? 'green' : 'yellow'}>{r.tiene_2fa_activo ? 'App' : 'Pendiente'}</Badge>
          {r.tiene_webauthn && <Badge color="blue">Huella</Badge>}
        </div>
      ),
    },
    {
      title: '',
      key: 'acciones',
      width: 340,
      render: (_, r) => (
        <div className="flex gap-1.5 justify-end">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => resetearPassword(r)}
            disabled={resettingId === r.id_usuario}
            title="Resetear contraseña al CI/RUC"
          >
            {resettingId === r.id_usuario
              ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              : <KeyRound className="w-3.5 h-3.5" />}
            Resetear
          </Button>
          {r.tiene_2fa_activo && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => desactivar2FA(r)}
              disabled={desactivando2FAId === r.id_usuario}
              title="Desactivar verificación en dos pasos por app (si perdió el celular)"
            >
              {desactivando2FAId === r.id_usuario
                ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                : <ShieldOff className="w-3.5 h-3.5" />}
              2FA
            </Button>
          )}
          {r.tiene_webauthn && (
            <Button
              size="sm"
              variant="secondary"
              onClick={() => desactivarHuella(r)}
              disabled={desactivandoHuellaId === r.id_usuario}
              title="Desactivar huella/Face ID (si perdió el celular)"
            >
              {desactivandoHuellaId === r.id_usuario
                ? <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                : <Fingerprint className="w-3.5 h-3.5" />}
              Huella
            </Button>
          )}
          <Button
            size="sm"
            variant={r.is_active ? 'danger' : 'primary'}
            onClick={() => toggleActivoPadre(r)}
          >
            {r.is_active ? 'Desactivar' : 'Activar'}
          </Button>
        </div>
      ),
    },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('usuarios.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('usuarios.subtitle')}</p>
        </div>
        {tab === 'usuarios' && (
          <Button variant="primary" onClick={() => { setEditingUser(null); setModalOpen(true) }}>
            <UserPlus className="w-4 h-4" />
            {t('usuarios.newUsuario')}
          </Button>
        )}
        {tab === 'empleados' && (
          <Button variant="primary" onClick={() => { setEditingEmp(null); setEmpModalOpen(true) }}>
            <Plus className="w-4 h-4" />
            Nuevo Empleado
          </Button>
        )}
        {tab === 'roles' && (
          <Button variant="primary" onClick={() => setRolModal({ open: true, rol: null })}>
            <Plus className="w-4 h-4" />
            Nuevo Rol
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
                rowKey="id_usuario"
                loading={loading}
                pageSize={15}
                page={page}
                onPageChange={p => { setPage(p); loadUsuarios(search, filterRol, p) }}
                total={total}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Roles tab ────────────────────────────────────────────── */}
      {tab === 'roles' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            <Table
              columns={colsRoles}
              dataSource={roles}
              rowKey="id_rol"
            />
          </div>
        </div>
      )}

      {/* ── Empleados tab ────────────────────────────────────────── */}
      {tab === 'empleados' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            <Table
              columns={colsEmpleados}
              dataSource={empleados}
              rowKey="id_empleado"
              loading={loadingEmp}
              pageSize={15}
              page={pageEmp}
              total={totalEmp}
              onPageChange={p => { setPageEmp(p); loadEmpleados(p) }}
            />
          </div>
        </div>
      )}

      {/* ── Portal Padres tab ──────────────────────────────────── */}
      {tab === 'portal' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-center gap-3">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <input
                placeholder="Nombre o CI/RUC..."
                value={searchPadres}
                onChange={e => setSearchPadres(e.target.value)}
                className={`${inputClass} pl-9`}
              />
            </div>
            <p className="text-sm text-slate-400 shrink-0">{totalPadres} padre{totalPadres !== 1 ? 's' : ''}</p>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={colsPadres}
                dataSource={padres}
                rowKey="id_usuario"
                loading={loadingPadres}
                pageSize={15}
                page={pagePadres}
                total={totalPadres}
                onPageChange={p => { setPagePadres(p); loadPadres(searchPadres, p) }}
              />
            </div>
          </div>
        </>
      )}

      <ModalUsuario
        open={modalOpen}
        editingUser={editingUser}
        onClose={() => setModalOpen(false)}
        onSaved={() => { setPage(1); loadUsuarios(search, filterRol, 1) }}
      />

      <ModalEmpleado
        open={empModalOpen}
        editingEmp={editingEmp}
        roles={roles}
        onClose={() => setEmpModalOpen(false)}
        onSaved={() => loadEmpleados(pageEmp)}
      />

      <ModalRol
        open={rolModal.open}
        rol={rolModal.rol}
        onClose={() => setRolModal({ open: false, rol: null })}
        onSaved={loadRoles}
      />
    </div>
  )
}
