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
  id: number
  email: string
  nombre: string
  apellido: string
  rol: string
  nombre_completo: string
  is_active: boolean
}

export interface UsuarioForm {
  email: string
  nombre: string
  apellido: string
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

export interface Permiso {
  id: number
  codigo_permiso: string
  nombre: string
  modulo: string
  descripcion: string | null
}

export interface RolPermiso {
  id: number
  id_rol: number
  id_permiso: number
  rol_nombre: string
  permiso_codigo: string
}

export interface Empleado {
  id_empleado: number
  nombre: string
  apellido: string
  email: string | null
  telefono: string | null
  fecha_ingreso: string
  estado: boolean
  id_rol: number
  rol_nombre: string
}

export interface EmpleadoForm {
  nombre: string
  apellido: string
  email: string
  telefono: string
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

export const FORM_INITIAL: UsuarioForm = {
  email: '', nombre: '', apellido: '', rol: 'CAJERO', password: '', is_active: true,
}

export const EMP_FORM_INITIAL: EmpleadoForm = {
  nombre: '', apellido: '', email: '', telefono: '', id_rol: '', estado: true,
}

export type TabKey = 'usuarios' | 'permisos' | 'empleados'
