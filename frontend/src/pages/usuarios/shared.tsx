import type { BadgeColor } from '../../components/ui/Badge'

export function extractErrorMessage(err: unknown): string {
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

export interface Usuario {
  id_usuario: number
  email: string
  ci_ruc: string | null
  nombre: string
  apellido: string
  rol: string
  nombre_completo: string
  is_active: boolean
  empleado_id: number | null
  empleado_nombre: string | null
}

export interface UsuarioPortal {
  id_usuario: number
  email: string
  nombre: string
  apellido: string
  nombre_completo: string
  is_active: boolean
  cliente_id: number | null
  cliente_ruc_ci: string | null
  ultimo_acceso: string | null
  tiene_2fa_activo: boolean
  tiene_webauthn: boolean
}

export interface UsuarioForm {
  email: string
  ci_ruc: string
  nombre: string
  apellido: string
  rol: string
  password: string
  is_active: boolean
}

export interface OtorgarAccesoForm {
  email: string
  ci_ruc: string
  rol: string
  password: string
  is_active: boolean
}

export interface Rol {
  id_rol: number
  nombre_rol: string
  descripcion: string | null
  estado: boolean
}

export interface Empleado {
  id_empleado: number
  nombre: string
  apellido: string
  email: string | null
  telefono: string | null
  fecha_ingreso: string
  fecha_nacimiento: string | null
  direccion: string | null
  ciudad: number | null
  ciudad_nombre: string | null
  estado: boolean
  id_rol: number
  rol_nombre: string
  usuario_id: number | null
}

export interface EmpleadoForm {
  nombre: string
  apellido: string
  email: string
  telefono: string
  fecha_ingreso: string
  fecha_nacimiento: string
  direccion: string
  ciudad: number | null
  id_rol: number | ''
  estado: boolean
}

export const ROL_COLOR: Record<string, BadgeColor> = {
  ADMIN: 'purple',
  CAJERO: 'blue',
  COCINA: 'orange',
  CLIENTE_WEB: 'green',
}

export const ROL_LABEL: Record<string, string> = {
  ADMIN: 'Administrador',
  SUPERVISOR: 'Supervisor',
  CAJERO: 'Cajero',
  COBRADOR: 'Cobrador',
  COCINA: 'Cocina',
  CLIENTE_WEB: 'Portal Padres',
}

export const ROLES_SISTEMA = [
  { value: 'ADMIN', label: 'Administrador' },
  { value: 'SUPERVISOR', label: 'Supervisor' },
  { value: 'CAJERO', label: 'Cajero' },
  { value: 'COBRADOR', label: 'Cobrador' },
  { value: 'COCINA', label: 'Cocina' },
  { value: 'CLIENTE_WEB', label: 'Portal Padres' },
]

// Roles de permisos para "Otorgar acceso al sistema" desde un Empleado — no
// incluye CLIENTE_WEB, que se vincula a un Cliente, no a un Empleado.
export const ROLES_PERSONAL = ROLES_SISTEMA.filter(r => r.value !== 'CLIENTE_WEB')

export const FORM_INITIAL: UsuarioForm = {
  email: '', ci_ruc: '', nombre: '', apellido: '', rol: 'CLIENTE_WEB', password: '', is_active: true,
}

export const OTORGAR_ACCESO_INITIAL: OtorgarAccesoForm = {
  email: '', ci_ruc: '', rol: 'CAJERO', password: '', is_active: true,
}

export const EMP_FORM_INITIAL: EmpleadoForm = {
  nombre: '', apellido: '', email: '', telefono: '', fecha_ingreso: '', fecha_nacimiento: '',
  direccion: '', ciudad: null, id_rol: '', estado: true,
}

export type TabKey = 'usuarios' | 'empleados' | 'roles' | 'portal'
