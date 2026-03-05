import api from './api';
import { UserRole } from './auth.service';

/**
 * Interface para el modelo de Usuario completo
 */
export interface Usuario {
  id_empleado: number;
  nombre: string;
  apellido: string;
  usuario: string;
  email: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  pais?: string;
  fecha_ingreso: string;
  activo: boolean;
  fecha_baja?: string;
  id_rol: number;
  rol_nombre?: string; // viene del serializer
}

/**
 * Interface para Rol
 */
export interface Rol {
  id_rol: number;
  nombre_rol: string;
  descripcion?: string;
  activo: boolean;
}

/**
 * Interface para crear un nuevo usuario
 */
export interface CreateUsuarioDto {
  nombre: string;
  apellido: string;
  usuario: string;
  email: string;
  password: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  pais?: string;
  id_rol: number;
}

/**
 * Interface para actualizar un usuario
 */
export interface UpdateUsuarioDto {
  nombre?: string;
  apellido?: string;
  email?: string;
  telefono?: string;
  direccion?: string;
  ciudad?: string;
  pais?: string;
  id_rol?: number;
  activo?: boolean;
}

/**
 * Interface para cambiar contraseña
 */
export interface ChangePasswordDto {
  password: string;
}

/**
 * Servicio para gestión de usuarios (empleados)
 */
export const usersService = {
  /**
   * Obtener lista de todos los usuarios
   */
  getAll: async (): Promise<Usuario[]> => {
    const response = await api.get<{count: number; next: string | null; previous: string | null; results: Usuario[]}>('/empleados/');
    return response.data.results;
  },

  /**
   * Obtener usuario por ID
   */
  getById: async (id: number): Promise<Usuario> => {
    const response = await api.get<Usuario>(`/empleados/${id}/`);
    return response.data;
  },

  /**
   * Crear nuevo usuario
   */
  create: async (data: CreateUsuarioDto): Promise<Usuario> => {
    const response = await api.post<{ success: boolean; empleado: Usuario; mensaje: string }>(
      '/empleados/',
      data
    );
    return response.data.empleado;
  },

  /**
   * Actualizar usuario existente
   */
  update: async (id: number, data: UpdateUsuarioDto): Promise<Usuario> => {
    const response = await api.patch<Usuario>(`/empleados/${id}/`, data);
    return response.data;
  },

  /**
   * Desactivar usuario (soft delete)
   */
  deactivate: async (id: number): Promise<Usuario> => {
    const response = await api.patch<Usuario>(`/empleados/${id}/`, {
      activo: false,
      fecha_baja: new Date().toISOString()
    });
    return response.data;
  },

  /**
   * Activar usuario
   */
  activate: async (id: number): Promise<Usuario> => {
    const response = await api.patch<Usuario>(`/empleados/${id}/`, {
      activo: true,
      fecha_baja: null
    });
    return response.data;
  },

  /**
   * Cambiar contraseña de usuario
   */
  changePassword: async (id: number, data: ChangePasswordDto): Promise<void> => {
    await api.post(`/empleados/${id}/cambiar_password/`, data);
  },

  /**
   * Eliminar usuario (hard delete)
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`/empleados/${id}/`);
  },
};

/**
 * Servicio para gestión de roles
 */
export const rolesService = {
  /**
   * Obtener lista de todos los roles
   */
  getAll: async (): Promise<Rol[]> => {
    const response = await api.get<{count: number; next: string | null; previous: string | null; results: Rol[]}>('/roles/');
    return response.data.results;
  },

  /**
   * Obtener roles activos
   */
  getActive: async (): Promise<Rol[]> => {
    const response = await api.get<{count: number; next: string | null; previous: string | null; results: Rol[]}>('/roles/?activo=true');
    return response.data.results;
  },

  /**
   * Obtener rol por ID
   */
  getById: async (id: number): Promise<Rol> => {
    const response = await api.get<Rol>(`/roles/${id}/`);
    return response.data;
  },

  /**
   * Crear nuevo rol
   */
  create: async (data: Omit<Rol, 'id_rol'>): Promise<Rol> => {
    const response = await api.post<Rol>('/roles/', data);
    return response.data;
  },

  /**
   * Actualizar rol existente
   */
  update: async (id: number, data: Partial<Omit<Rol, 'id_rol'>>): Promise<Rol> => {
    const response = await api.patch<Rol>(`/roles/${id}/`, data);
    return response.data;
  },

  /**
   * Eliminar rol
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`/roles/${id}/`);
  },
};

/**
 * Helper para mapear rol del backend a UserRole del frontend
 */
export const mapRolToUserRole = (nombreRol: string): UserRole => {
  const mapping: Record<string, UserRole> = {
    'Administrador': 'admin',
    'Gerente': 'gerente',
    'Cajero': 'cajero',
    'Empleado': 'empleado',
  };
  
  return mapping[nombreRol] || 'empleado';
};

/**
 * Helper para mapear UserRole a nombre de rol
 */
export const mapUserRoleToRolNombre = (role: UserRole): string => {
  const mapping: Record<UserRole, string> = {
    'admin': 'Administrador',
    'gerente': 'Gerente',
    'cajero': 'Cajero',
    'empleado': 'Empleado',
  };
  
  return mapping[role];
};
