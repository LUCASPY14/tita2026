import React, { useState, useEffect } from 'react';
import { Shield, ChevronDown, ChevronRight, Check, X, AlertCircle, RefreshCw } from 'lucide-react';
import permisosService from '../../services/permisos.service';
import { usePermissions } from '../../contexts/PermissionsContext';
import type { Permiso, PermisosPorModulo, RolConPermisos } from '../../types';
import toast from 'react-hot-toast';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface Rol {
  id_rol: number;
  nombre_rol: string;
  descripcion?: string;
}

const GestionPermisos: React.FC = () => {
  // Context
  const { hasAdminAccess } = usePermissions();
  
  // Estados
  const [roles, setRoles] = useState<Rol[]>([]);
  const [rolSeleccionado, setRolSeleccionado] = useState<number | null>(null);
  const [permisosPorModulo, setPermisosPorModulo] = useState<PermisosPorModulo>({});
  const [permisosRol, setPermisosRol] = useState<RolConPermisos | null>(null);
  const [modulosExpandidos, setModulosExpandidos] = useState<Set<string>>(new Set());
  const [cargando, setCargando] = useState(false);
  const [procesando, setProcesando] = useState(false);

  // Funciones
  const cargarPermisos = async () => {
    try {
      setCargando(true);
      const data = await permisosService.listarPermisos();
      setPermisosPorModulo(data.permisos_por_modulo);
      // Expandir primer módulo por defecto
      if (Object.keys(data.permisos_por_modulo).length > 0) {
        setModulosExpandidos(new Set([Object.keys(data.permisos_por_modulo)[0]]));
      }
    } catch (error) {
      console.error('Error cargando permisos:', error);
      toast.error('Error al cargar permisos');
    } finally {
      setCargando(false);
    }
  };

  const cargarRoles = async () => {
    try {
      const response = await axios.get(`${API_URL}/roles/`);
      setRoles(response.data.results || response.data);
    } catch (error) {
      console.error('Error cargando roles:', error);
      toast.error('Error al cargar roles');
    }
  };

  const cargarPermisosRol = async (idRol: number) => {
    try {
      const data = await permisosService.obtenerPermisosDeRol(idRol);
      setPermisosRol(data);
    } catch (error) {
      console.error('Error cargando permisos del rol:', error);
      toast.error('Error al cargar permisos del rol');
      setPermisosRol(null);
    }
  };

  const toggleModulo = (modulo: string) => {
    setModulosExpandidos(prev => {
      const nuevos = new Set(prev);
      if (nuevos.has(modulo)) {
        nuevos.delete(modulo);
      } else {
        nuevos.add(modulo);
      }
      return nuevos;
    });
  };

  const rolTienePermiso = (codigoPermiso: string): boolean => {
    if (!permisosRol) return false;
    return permisosRol.permisos.some(p => p.id_permiso__codigo_permiso === codigoPermiso);
  };

  const togglePermiso = async (permiso: Permiso) => {
    if (!rolSeleccionado) return;
    
    try {
      setProcesando(true);
      const tienePermiso = rolTienePermiso(permiso.codigo_permiso);
      
      if (tienePermiso) {
        // Remover permiso
        const resultado = await permisosService.removerPermisoDeRol({
          id_rol: rolSeleccionado,
          codigo_permiso: permiso.codigo_permiso,
        });
        
        if (resultado.success) {
          toast.success(`Permiso removido: ${permiso.nombre}`);
          await cargarPermisosRol(rolSeleccionado);
        } else {
          toast.error(resultado.mensaje || 'Error al remover permiso');
        }
      } else {
        // Asignar permiso
        const resultado = await permisosService.asignarPermisoARol({
          id_rol: rolSeleccionado,
          codigo_permiso: permiso.codigo_permiso,
        });
        
        if (resultado.success) {
          toast.success(`Permiso asignado: ${permiso.nombre}`);
          await cargarPermisosRol(rolSeleccionado);
        } else {
          toast.error(resultado.mensaje || 'Error al asignar permiso');
        }
      }
    } catch (error) {
      console.error('Error toggle permiso:', error);
      toast.error('Error al gestionar permiso');
    } finally {
      setProcesando(false);
    }
  };

  const inicializarPermisos = async () => {
    if (!window.confirm('¿Estás seguro de que quieres inicializar todos los permisos? Esto creará los permisos base del sistema.')) {
      return;
    }
    
    try {
      setProcesando(true);
      const resultado = await permisosService.inicializarPermisos();
      
      if (resultado.success) {
        toast.success(resultado.mensaje || 'Permisos inicializados correctamente');
        await cargarPermisos();
      } else {
        toast.error(resultado.mensaje || 'Error al inicializar permisos');
      }
    } catch (error) {
      console.error('Error inicializando permisos:', error);
      toast.error('Error al inicializar permisos');
    } finally {
      setProcesando(false);
    }
  };

  // Efectos
  useEffect(() => {
    cargarPermisos();
    cargarRoles();
  }, []);

  useEffect(() => {
    if (rolSeleccionado) {
      cargarPermisosRol(rolSeleccionado);
    }
  }, [rolSeleccionado]);

  // Verificar acceso administrativo
  if (!hasAdminAccess()) {
    return (
      <div className="bg-white rounded-lg shadow p-8">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-gray-900 mb-1">Acceso Restringido</h3>
          <p className="text-sm text-gray-600">
            Solo los administradores pueden gestionar permisos del sistema.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Permisos</h1>
          <p className="text-gray-600 mt-1">
            Administra permisos del sistema y asigna a roles
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={cargarPermisos}
            disabled={cargando}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
          <button
            onClick={inicializarPermisos}
            disabled={procesando}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors"
          >
            <Shield className="h-4 w-4" />
            Inicializar Permisos
          </button>
        </div>
      </div>

      {/* Selector de Rol */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Seleccionar Rol</h2>
          <p className="text-gray-600">Elige un rol para ver y gestionar sus permisos</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {roles.map((rol) => (
            <button
              key={rol.id_rol}
              onClick={() => setRolSeleccionado(rol.id_rol)}
              className={`p-4 rounded-lg border-2 transition-all ${
                rolSeleccionado === rol.id_rol
                  ? 'border-amber-500 bg-amber-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-900">{rol.nombre_rol}</h3>
                {rolSeleccionado === rol.id_rol && (
                  <Check className="h-5 w-5 text-amber-500" />
                )}
              </div>
              {rol.descripcion && (
                <p className="text-sm text-gray-600">{rol.descripcion}</p>
              )}
              {permisosRol && rolSeleccionado === rol.id_rol && (
                <span className="inline-block mt-2 px-3 py-1 bg-amber-100 text-amber-800 text-xs rounded-full">
                  {permisosRol.total} permisos
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Lista de Permisos por Módulo */}
      {rolSeleccionado && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Permisos Disponibles</h2>
            <p className="text-gray-600">
              Asignar permisos al rol: {roles.find(r => r.id_rol === rolSeleccionado)?.nombre_rol}
            </p>
          </div>
          <div className="space-y-2">
            {Object.entries(permisosPorModulo).map(([modulo, permisosModulo]) => (
              <div key={modulo} className="border rounded-lg overflow-hidden">
                {/* Header del módulo */}
                <button
                  onClick={() => toggleModulo(modulo)}
                  className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {modulosExpandidos.has(modulo) ? (
                      <ChevronDown className="h-5 w-5 text-gray-600" />
                    ) : (
                      <ChevronRight className="h-5 w-5 text-gray-600" />
                    )}
                    <span className="font-semibold text-gray-900 capitalize">{modulo}</span>
                    <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {permisosModulo.length} permisos
                    </span>
                  </div>
                  <div>
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                      {permisosModulo.filter(p => rolTienePermiso(p.codigo_permiso)).length} asignados
                    </span>
                  </div>
                </button>

                {/* Permisos del módulo */}
                {modulosExpandidos.has(modulo) && (
                  <div className="divide-y">
                    {permisosModulo.map((permiso) => {
                      const tienePermiso = rolTienePermiso(permiso.codigo_permiso);
                      
                      return (
                        <div
                          key={permiso.id}
                          className={`px-4 py-3 flex items-center justify-between hover:bg-gray-50 ${
                            tienePermiso ? 'bg-green-50' : ''
                          }`}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <code className="text-sm font-mono text-gray-600 bg-gray-100 px-2 py-1 rounded">
                                {permiso.codigo_permiso}
                              </code>
                              {tienePermiso && (
                                <Check className="h-4 w-4 text-green-600" />
                              )}
                            </div>
                            <p className="text-sm font-medium text-gray-900 mt-1">
                              {permiso.nombre}
                            </p>
                            {permiso.descripcion && (
                              <p className="text-xs text-gray-500 mt-1">{permiso.descripcion}</p>
                            )}
                          </div>
                          <button
                            onClick={() => togglePermiso(permiso)}
                            disabled={procesando}
                            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                              tienePermiso
                                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                : 'bg-green-100 text-green-700 hover:bg-green-200'
                            } disabled:opacity-50`}
                          >
                            {tienePermiso ? (
                              <>
                                <X className="h-4 w-4 inline mr-1" />
                                Remover
                              </>
                            ) : (
                              <>
                                <Check className="h-4 w-4 inline mr-1" />
                                Asignar
                              </>
                            )}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Estado vacío */}
      {!rolSeleccionado && (
        <div className="bg-white rounded-lg shadow p-12">
          <div className="text-center">
            <Shield className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Selecciona un Rol
            </h3>
            <p className="text-gray-600">
              Selecciona un rol arriba para ver y gestionar sus permisos
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default GestionPermisos;