import React, { useState, useEffect } from 'react';
import { Search, Edit, Shield, ToggleLeft, ToggleRight, Trash2, Key, Mail, Phone } from 'lucide-react';
import { Input, Button, Badge, Spinner } from '../../../components/common';
import { usersService, rolesService } from '../../../services/users.service';
import type { Usuario, Rol } from '../../../services/users.service';
import toast from 'react-hot-toast';
import clsx from 'clsx';

interface UserTableProps {
  onEditar: (usuario: Usuario) => void;
  onActualizarLista: () => void;
}

const UserTable: React.FC<UserTableProps> = ({ onEditar, onActualizarLista }) => {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [roles, setRoles] = useState<Rol[]>([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroActivo, setFiltroActivo] = useState<boolean | undefined>(undefined);
  const [filtroRol, setFiltroRol] = useState<number | undefined>(undefined);

  useEffect(() => {
    cargarDatos();
  }, []);

  useEffect(() => {
    // Filtrar clientes cuando cambia la búsqueda o filtros
    if (!cargando) {
      // En este caso simplemente re-renderizamos, el filtrado es en el frontend
      // Si fuera backend pagination, haríamos una nueva petición
    }
  }, [busqueda, filtroActivo, filtroRol]);

  const cargarDatos = async () => {
    setCargando(true);
    try {
      const [usuariosData, rolesData] = await Promise.all([
        usersService.getAll(),
        rolesService.getAll()
      ]);
      setUsuarios(usuariosData);
      setRoles(rolesData);
    } catch (error) {
      console.error('Error al cargar datos:', error);
      toast.error('Error al cargar la lista de usuarios');
    } finally {
      setCargando(false);
    }
  };

  const handleToggleEstado = async (usuario: Usuario) => {
    try {
      if (usuario.activo) {
        await usersService.deactivate(usuario.id_empleado);
        toast.success('Usuario desactivado exitosamente');
      } else {
        await usersService.activate(usuario.id_empleado);
        toast.success('Usuario activado exitosamente');
      }
      cargarDatos();
      onActualizarLista();
    } catch (error) {
      toast.error('Error al cambiar el estado del usuario');
    }
  };

  const handleEliminar = async (usuario: Usuario) => {
    if (!window.confirm(
      `¿Estás seguro de eliminar al usuario ${usuario.nombre} ${usuario.apellido}?\n\n` +
      `Esta acción no se puede deshacer. Considera desactivar el usuario en su lugar.`
    )) {
      return;
    }

    try {
      await usersService.delete(usuario.id_empleado);
      toast.success('Usuario eliminado exitosamente');
      cargarDatos();
      onActualizarLista();
    } catch (error) {
      toast.error('Error al eliminar el usuario');
    }
  };

  const handleResetPassword = async (usuario: Usuario) => {
    const newPassword = prompt(
      `Ingrese la nueva contraseña para ${usuario.nombre} ${usuario.apellido}:`
    );

    if (!newPassword) {
      return;
    }

    if (newPassword.length < 8) {
      toast.error('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    try {
      await usersService.changePassword(usuario.id_empleado, { password: newPassword });
      toast.success('Contraseña actualizada exitosamente');
    } catch (error) {
      toast.error('Error al cambiar la contraseña');
    }
  };

  const getRolBadgeColor = (rolNombre: string): string => {
    const colores: Record<string, string> = {
      'Administrador': 'bg-purple-100 text-purple-700',
      'Gerente': 'bg-blue-100 text-blue-700',
      'Cajero': 'bg-green-100 text-green-700',
      'Empleado': 'bg-gray-100 text-gray-700',
    };
    return colores[rolNombre] || 'bg-gray-100 text-gray-700';
  };

  const usuariosFiltrados = usuarios.filter((usuario) => {
    // Filtro de búsqueda
    if (busqueda) {
      const searchLower = busqueda.toLowerCase();
      const coincide = 
        usuario.nombre.toLowerCase().includes(searchLower) ||
        usuario.apellido.toLowerCase().includes(searchLower) ||
        usuario.usuario.toLowerCase().includes(searchLower) ||
        (usuario.email && usuario.email.toLowerCase().includes(searchLower));
      
      if (!coincide) return false;
    }

    // Filtro de estado activo
    if (filtroActivo !== undefined && usuario.activo !== filtroActivo) {
      return false;
    }

    // Filtro de rol
    if (filtroRol !== undefined && usuario.id_rol !== filtroRol) {
      return false;
    }

    return true;
  });

  const formatearFecha = (fecha: string): string => {
    return new Date(fecha).toLocaleDateString('es-PY', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
        <div className="md:col-span-2">
          <Input
            type="text"
            placeholder="Buscar por nombre, usuario o email..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            leftIcon={<Search className="h-5 w-5 text-gray-400" />}
          />
        </div>

        <div>
          <select
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            value={filtroRol ?? ''}
            onChange={(e) => setFiltroRol(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">Todos los roles</option>
            {roles.map((rol) => (
              <option key={rol.id_rol} value={rol.id_rol}>
                {rol.nombre_rol}
              </option>
            ))}
          </select>
        </div>

        <div className="flex gap-2">
          <Button
            variant={filtroActivo === true ? 'primary' : 'outline'}
            onClick={() => setFiltroActivo(filtroActivo === true ? undefined : true)}
            className="flex-1"
          >
            Activos
          </Button>
          <Button
            variant={filtroActivo === false ? 'primary' : 'outline'}
            onClick={() => setFiltroActivo(filtroActivo === false ? undefined : false)}
            className="flex-1"
          >
            Inactivos
          </Button>
        </div>
      </div>

      {/* Stats rápidas */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-lg bg-gradient-to-br from-purple-50 to-purple-100 p-4">
          <div className="text-sm font-medium text-purple-600">Total Usuarios</div>
          <div className="text-2xl font-bold text-purple-900">{usuarios.length}</div>
        </div>
        <div className="rounded-lg bg-gradient-to-br from-green-50 to-green-100 p-4">
          <div className="text-sm font-medium text-green-600">Activos</div>
          <div className="text-2xl font-bold text-green-900">
            {usuarios.filter(u => u.activo).length}
          </div>
        </div>
        <div className="rounded-lg bg-gradient-to-br from-gray-50 to-gray-100 p-4">
          <div className="text-sm font-medium text-gray-600">Inactivos</div>
          <div className="text-2xl font-bold text-gray-900">
            {usuarios.filter(u => !u.activo).length}
          </div>
        </div>
        <div className="rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 p-4">
          <div className="text-sm font-medium text-blue-600">Filtrados</div>
          <div className="text-2xl font-bold text-blue-900">{usuariosFiltrados.length}</div>
        </div>
      </div>

      {/* Tabla */}
      {cargando ? (
        <div className="flex items-center justify-center py-12">
          <Spinner />
          <span className="ml-2 text-gray-600">Cargando usuarios...</span>
        </div>
      ) : usuariosFiltrados.length === 0 ? (
        <div className="py-12 text-center">
          <p className="text-gray-500">No se encontraron usuarios</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Usuario
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Contacto
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Rol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Ingreso
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Estado
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {usuariosFiltrados.map((usuario) => (
                <tr key={usuario.id_empleado} className="hover:bg-gray-50">
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-white font-semibold">
                        {usuario.nombre.charAt(0)}{usuario.apellido.charAt(0)}
                      </div>
                      <div>
                        <div className="font-medium text-gray-900">
                          {usuario.nombre} {usuario.apellido}
                        </div>
                        <div className="text-sm text-gray-500 flex items-center gap-1">
                          <span>@{usuario.usuario}</span>
                          {usuario.rol_nombre === 'Administrador' && (
                            <Shield className="h-3 w-3 text-purple-600" />
                          )}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {usuario.email && (
                      <div className="flex items-center gap-2 text-sm text-gray-900">
                        <Mail className="h-4 w-4 text-gray-400" />
                        {usuario.email}
                      </div>
                    )}
                    {usuario.telefono && (
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Phone className="h-4 w-4 text-gray-400" />
                        {usuario.telefono}
                      </div>
                    )}
                    {!usuario.email && !usuario.telefono && (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <span
                      className={clsx(
                        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
                        getRolBadgeColor(usuario.rol_nombre || '')
                      )}
                    >
                      {usuario.rol_nombre || 'Sin rol'}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                    {formatearFecha(usuario.fecha_ingreso)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    <Badge variant={usuario.activo ? 'success' : 'danger'}>
                      {usuario.activo ? 'Activo' : 'Inactivo'}
                    </Badge>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => onEditar(usuario)}
                        className="text-amber-600 hover:text-amber-700"
                        title="Editar usuario"
                      >
                        <Edit className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleResetPassword(usuario)}
                        className="text-blue-600 hover:text-blue-700"
                        title="Cambiar contraseña"
                      >
                        <Key className="h-5 w-5" />
                      </button>
                      <button
                        onClick={() => handleToggleEstado(usuario)}
                        className={clsx(
                          'hover:opacity-80',
                          usuario.activo ? 'text-orange-600' : 'text-green-600'
                        )}
                        title={usuario.activo ? 'Desactivar usuario' : 'Activar usuario'}
                      >
                        {usuario.activo ? (
                          <ToggleRight className="h-5 w-5" />
                        ) : (
                          <ToggleLeft className="h-5 w-5" />
                        )}
                      </button>
                      <button
                        onClick={() => handleEliminar(usuario)}
                        className="text-red-600 hover:text-red-700"
                        title="Eliminar usuario"
                      >
                        <Trash2 className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default UserTable;
