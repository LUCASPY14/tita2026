import React, { useState, useEffect } from 'react';
import { Save, X, Eye, EyeOff } from 'lucide-react';
import { Input, Button } from '../../../components/common';
import { usersService, rolesService } from '../../../services/users.service';
import type { Usuario, Rol, CreateUsuarioDto, UpdateUsuarioDto } from '../../../services/users.service';
import toast from 'react-hot-toast';

interface UserFormProps {
  usuario: Usuario | null;
  onGuardado: () => void;
  onCancelar: () => void;
}

const UserForm: React.FC<UserFormProps> = ({ usuario, onGuardado, onCancelar }) => {
  const [guardando, setGuardando] = useState(false);
  const [roles, setRoles] = useState<Rol[]>([]);
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    usuario: '',
    email: '',
    password: '',
    confirmarPassword: '',
    telefono: '',
    direccion: '',
    ciudad: '',
    pais: 'Paraguay',
    id_rol: 0,
    activo: true,
  });

  const [errores, setErrores] = useState<Record<string, string>>({});

  useEffect(() => {
    cargarRoles();
    if (usuario) {
      setFormData({
        nombre: usuario.nombre,
        apellido: usuario.apellido,
        usuario: usuario.usuario,
        email: usuario.email || '',
        password: '',
        confirmarPassword: '',
        telefono: usuario.telefono || '',
        direccion: usuario.direccion || '',
        ciudad: usuario.ciudad || '',
        pais: usuario.pais || 'Paraguay',
        id_rol: usuario.id_rol,
        activo: usuario.activo,
      });
    }
  }, [usuario]);

  const cargarRoles = async () => {
    try {
      const rolesData = await rolesService.getActive();
      setRoles(rolesData);
      
      // Si no hay usuario (crear nuevo) y hay roles, seleccionar el primero
      if (!usuario && rolesData.length > 0 && formData.id_rol === 0) {
        setFormData(prev => ({ ...prev, id_rol: rolesData[0].id_rol }));
      }
    } catch (error) {
      console.error('Error al cargar roles:', error);
      toast.error('Error al cargar los roles');
    }
  };

  const validarFormulario = (): boolean => {
    const nuevosErrores: Record<string, string> = {};

    if (!formData.nombre.trim()) {
      nuevosErrores.nombre = 'El nombre es requerido';
    }

    if (!formData.apellido.trim()) {
      nuevosErrores.apellido = 'El apellido es requerido';
    }

    if (!formData.usuario.trim()) {
      nuevosErrores.usuario = 'El nombre de usuario es requerido';
    } else if (formData.usuario.length < 3) {
      nuevosErrores.usuario = 'El nombre de usuario debe tener al menos 3 caracteres';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.usuario)) {
      nuevosErrores.usuario = 'Solo letras, números y guión bajo';
    }

    if (!formData.email.trim()) {
      nuevosErrores.email = 'El email es requerido';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      nuevosErrores.email = 'Email inválido';
    }

    // Validar password solo si es nuevo usuario o si se ingresó una contraseña
    if (!usuario) {
      if (!formData.password) {
        nuevosErrores.password = 'La contraseña es requerida';
      } else if (formData.password.length < 8) {
        nuevosErrores.password = 'La contraseña debe tener al menos 8 caracteres';
      } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
        nuevosErrores.password = 'Debe contener mayúsculas, minúsculas y números';
      }

      if (formData.password !== formData.confirmarPassword) {
        nuevosErrores.confirmarPassword = 'Las contraseñas no coinciden';
      }
    } else if (formData.password) {
      // Si está editando y quiere cambiar la contraseña
      if (formData.password.length < 8) {
        nuevosErrores.password = 'La contraseña debe tener al menos 8 caracteres';
      } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
        nuevosErrores.password = 'Debe contener mayúsculas, minúsculas y números';
      }

      if (formData.password !== formData.confirmarPassword) {
        nuevosErrores.confirmarPassword = 'Las contraseñas no coinciden';
      }
    }

    if (!formData.id_rol || formData.id_rol === 0) {
      nuevosErrores.id_rol = 'Debe seleccionar un rol';
    }

    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseInt(value) || 0 :
              type === 'checkbox' ? (e.target as HTMLInputElement).checked :
              value,
    }));

    // Limpiar error del campo
    if (errores[name]) {
      setErrores(prev => {
        const nuevos = { ...prev };
        delete nuevos[name];
        return nuevos;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validarFormulario()) {
      toast.error('Por favor, corrija los errores en el formulario');
      return;
    }

    setGuardando(true);
    try {
      if (usuario) {
        // Actualizar usuario existente
        const updateData: UpdateUsuarioDto = {
          nombre: formData.nombre,
          apellido: formData.apellido,
          email: formData.email,
          telefono: formData.telefono || undefined,
          direccion: formData.direccion || undefined,
          ciudad: formData.ciudad || undefined,
          id_rol: formData.id_rol,
          activo: formData.activo,
        };

        await usersService.update(usuario.id_empleado, updateData);

        // Si se proporcionó nueva contraseña, cambiarla
        if (formData.password) {
          await usersService.changePassword(usuario.id_empleado, {
            password: formData.password
          });
        }

        toast.success('Usuario actualizado exitosamente');
      } else {
        // Crear nuevo usuario
        const createData: CreateUsuarioDto = {
          nombre: formData.nombre,
          apellido: formData.apellido,
          usuario: formData.usuario,
          email: formData.email,
          password: formData.password,
          telefono: formData.telefono || undefined,
          direccion: formData.direccion || undefined,
          ciudad: formData.ciudad || undefined,
          pais: formData.pais || undefined,
          id_rol: formData.id_rol,
        };

        await usersService.create(createData);
        toast.success('Usuario creado exitosamente');
      }
      
      onGuardado();
    } catch (error: any) {
      console.error('Error al guardar usuario:', error);
      const mensaje = error.response?.data?.mensaje || 
                     error.response?.data?.detail || 
                     'Error al guardar el usuario';
      toast.error(mensaje);
    } finally {
      setGuardando(false);
    }
  };

  const getRolDescripcion = (idRol: number): string => {
    const rol = roles.find(r => r.id_rol === idRol);
    return rol?.descripcion || '';
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Información Personal */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Información Personal</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Nombre *"
            name="nombre"
            value={formData.nombre}
            onChange={handleChange}
            error={errores.nombre}
            required
            placeholder="Ej: Juan"
          />

          <Input
            label="Apellido *"
            name="apellido"
            value={formData.apellido}
            onChange={handleChange}
            error={errores.apellido}
            required
            placeholder="Ej: Pérez"
          />

          <Input
            label="Nombre de Usuario *"
            name="usuario"
            value={formData.usuario}
            onChange={handleChange}
            error={errores.usuario}
            required
            disabled={!!usuario} // No permitir cambiar el username si está editando
            placeholder="Ej: jperez"
            helperText="Solo letras, números y guión bajo. Mínimo 3 caracteres"
          />

          <Input
            label="Email *"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            error={errores.email}
            required
            placeholder="[email protected]"
          />
        </div>
      </div>

      {/* Credenciales */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">
          {usuario ? 'Cambiar Contraseña (Opcional)' : 'Credenciales de Acceso *'}
        </h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="relative">
            <Input
              label="Contraseña"
              name="password"
              type={mostrarPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleChange}
              error={errores.password}
              required={!usuario}
              placeholder="••••••••"
              helperText={!usuario ? "Mínimo 8 caracteres, incluye mayúsculas, minúsculas y números" : "Dejar en blanco para mantener la actual"}
            />
            <button
              type="button"
              onClick={() => setMostrarPassword(!mostrarPassword)}
              className="absolute right-3 top-8 text-gray-500 hover:text-gray-700"
            >
              {mostrarPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>

          <Input
            label="Confirmar Contraseña"
            name="confirmarPassword"
            type={mostrarPassword ? 'text' : 'password'}
            value={formData.confirmarPassword}
            onChange={handleChange}
            error={errores.confirmarPassword}
            required={!usuario}
            placeholder="••••••••"
          />
        </div>
      </div>

      {/* Información de Contacto */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Información de Contacto</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Teléfono"
            name="telefono"
            type="tel"
            value={formData.telefono}
            onChange={handleChange}
            placeholder="Ej: +595 21 123456"
          />

          <Input
            label="Ciudad"
            name="ciudad"
            value={formData.ciudad}
            onChange={handleChange}
            placeholder="Ej: Asunción"
          />

          <div className="md:col-span-2">
            <Input
              label="Dirección"
              name="direccion"
              value={formData.direccion}
              onChange={handleChange}
              placeholder="Ej: Av. Mariscal López 1234"
            />
          </div>
        </div>
      </div>

      {/* Rol y Permisos */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-gray-900">Rol y Permisos *</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Rol del Usuario *
            </label>
            <select
              name="id_rol"
              value={formData.id_rol}
              onChange={handleChange}
              className={`w-full rounded-lg border ${errores.id_rol ? 'border-red-500' : 'border-gray-300'} px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500`}
              required
            >
              <option value="">Seleccione un rol</option>
              {roles.map((rol) => (
                <option key={rol.id_rol} value={rol.id_rol}>
                  {rol.nombre_rol}
                </option>
              ))}
            </select>
            {errores.id_rol && (
              <p className="mt-1 text-sm text-red-600">{errores.id_rol}</p>
            )}
            {formData.id_rol > 0 && getRolDescripcion(formData.id_rol) && (
              <p className="mt-1 text-sm text-gray-500">
                {getRolDescripcion(formData.id_rol)}
              </p>
            )}
          </div>

          {/* Estado */}
          {usuario && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="activo"
                name="activo"
                checked={formData.activo}
                onChange={handleChange}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="activo" className="text-sm font-medium text-gray-700">
                Usuario activo
              </label>
              <p className="text-xs text-gray-500">
                (Los usuarios inactivos no pueden iniciar sesión)
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Botones de acción */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={onCancelar}
          disabled={guardando}
          leftIcon={<X className="h-5 w-5" />}
        >
          Cancelar
        </Button>

        <Button
          type="submit"
          variant="primary"
          disabled={guardando}
          leftIcon={<Save className="h-5 w-5" />}
        >
          {guardando ? 'Guardando...' : usuario ? 'Actualizar Usuario' : 'Crear Usuario'}
        </Button>
      </div>

      {/* Advertencia de seguridad */}
      {!usuario && (
        <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-4">
          <h4 className="text-sm font-semibold text-yellow-800 mb-2">
            ⚠️ Recordatorio de Seguridad
          </h4>
          <ul className="text-sm text-yellow-700 space-y-1 list-disc list-inside">
            <li>Guarda las credenciales de forma segura</li>
            <li>Comparte la contraseña de forma segura con el usuario</li>
            <li>Recomienda cambiar la contraseña en el primer inicio de sesión</li>
            <li>Asigna el rol apropiado según las responsabilidades</li>
          </ul>
        </div>
      )}
    </form>
  );
};

export default UserForm;
