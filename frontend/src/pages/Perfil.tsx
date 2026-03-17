/**
 * Página de Perfil del Usuario
 * Muestra información del empleado autenticado y permite cambiar contraseña
 */

import React, { useState, useEffect } from 'react';
import {
  Mail,
  Phone,
  MapPin,
  Calendar,
  Shield,
  Key,
  Save,
  Loader2,
  CheckCircle,
  Eye,
  EyeOff,
} from 'lucide-react';
import { useAuthContext } from '../contexts/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';

interface EmpleadoPerfil {
  id_empleado: number;
  nombre: string;
  apellido: string;
  usuario: string;
  email: string;
  telefono: string;
  direccion: string;
  ciudad: string;
  pais: string;
  fecha_ingreso: string;
  estado: boolean;
  rol_nombre: string;
}

const Perfil: React.FC = () => {
  const { user } = useAuthContext();
  const [empleado, setEmpleado] = useState<EmpleadoPerfil | null>(null);
  const [cargando, setCargando] = useState(true);

  // Estado para cambio de contraseña
  const [passwordActual, setPasswordActual] = useState('');
  const [passwordNueva, setPasswordNueva] = useState('');
  const [passwordConfirmar, setPasswordConfirmar] = useState('');
  const [guardandoPassword, setGuardandoPassword] = useState(false);
  const [mostrarActual, setMostrarActual] = useState(false);
  const [mostrarNueva, setMostrarNueva] = useState(false);
  const [mostrarConfirmar, setMostrarConfirmar] = useState(false);

  useEffect(() => {
    cargarPerfil();
  }, []);

  const cargarPerfil = async () => {
    try {
      setCargando(true);
      const response = await api.get('/auth/perfil/');
      setEmpleado(response.data.empleado);
    } catch (error) {
      console.error('Error cargando perfil:', error);
      toast.error('Error al cargar el perfil');
    } finally {
      setCargando(false);
    }
  };

  const handleCambiarPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!passwordActual || !passwordNueva || !passwordConfirmar) {
      toast.error('Completa todos los campos');
      return;
    }

    if (passwordNueva !== passwordConfirmar) {
      toast.error('Las contraseñas nuevas no coinciden');
      return;
    }

    if (passwordNueva.length < 8) {
      toast.error('La contraseña nueva debe tener al menos 8 caracteres');
      return;
    }

    try {
      setGuardandoPassword(true);
      await api.post('/auth/cambiar_password/', {
        password_actual: passwordActual,
        password_nueva: passwordNueva,
      });
      toast.success('Contraseña cambiada exitosamente');
      setPasswordActual('');
      setPasswordNueva('');
      setPasswordConfirmar('');
    } catch (error: any) {
      const mensaje = error?.response?.data?.mensaje || 'Error al cambiar la contraseña';
      toast.error(mensaje);
    } finally {
      setGuardandoPassword(false);
    }
  };

  const formatearFecha = (fecha: string) => {
    if (!fecha) return '—';
    return new Date(fecha).toLocaleDateString('es-PY', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getRolColor = (rol: string) => {
    const colores: Record<string, string> = {
      Administrador: 'bg-purple-100 text-purple-700',
      Gerente: 'bg-blue-100 text-blue-700',
      Cajero: 'bg-green-100 text-green-700',
      Vendedor: 'bg-green-100 text-green-700',
      Empleado: 'bg-gray-100 text-gray-700',
    };
    return colores[rol] || 'bg-gray-100 text-gray-700';
  };

  if (cargando) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Mi Perfil</h1>
        <p className="mt-1 text-sm text-gray-500">
          Información de tu cuenta y configuración de seguridad
        </p>
      </div>

      {/* Tarjeta de información del perfil */}
      <div className="bg-white rounded-xl shadow border border-gray-200 overflow-hidden">
        {/* Banner superior */}
        <div className="h-20 bg-gradient-to-r from-amber-400 to-orange-500" />

        <div className="px-6 pb-6">
          {/* Avatar */}
          <div className="-mt-10 mb-4 flex items-end gap-4">
            <div className="h-20 w-20 rounded-full border-4 border-white bg-amber-500 shadow-md flex items-center justify-center">
              <span className="text-2xl font-bold text-white">
                {empleado
                  ? `${empleado.nombre[0] || ''}${empleado.apellido[0] || ''}`
                  : user?.username?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="mb-1">
              {empleado && (
                <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${getRolColor(empleado.rol_nombre)}`}>
                  <Shield className="h-3 w-3" />
                  {empleado.rol_nombre}
                </span>
              )}
            </div>
          </div>

          {/* Nombre y usuario */}
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900">
              {empleado ? `${empleado.nombre} ${empleado.apellido}` : user?.username || '—'}
            </h2>
            <p className="text-sm text-gray-500">@{empleado?.usuario || user?.username}</p>
          </div>

          {/* Datos del perfil */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <InfoField
              icon={<Mail className="h-4 w-4 text-gray-400" />}
              label="Correo electrónico"
              value={empleado?.email || '—'}
            />
            <InfoField
              icon={<Phone className="h-4 w-4 text-gray-400" />}
              label="Teléfono"
              value={empleado?.telefono || '—'}
            />
            <InfoField
              icon={<MapPin className="h-4 w-4 text-gray-400" />}
              label="Ciudad"
              value={empleado?.ciudad || '—'}
            />
            <InfoField
              icon={<MapPin className="h-4 w-4 text-gray-400" />}
              label="País"
              value={empleado?.pais || '—'}
            />
            <InfoField
              icon={<Calendar className="h-4 w-4 text-gray-400" />}
              label="Fecha de ingreso"
              value={empleado?.fecha_ingreso ? formatearFecha(empleado.fecha_ingreso) : '—'}
            />
            <InfoField
              icon={<CheckCircle className="h-4 w-4 text-gray-400" />}
              label="Estado"
              value={
                <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${empleado?.estado ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {empleado?.estado ? 'Activo' : 'Inactivo'}
                </span>
              }
            />
          </div>
        </div>
      </div>

      {/* Tarjeta de cambio de contraseña */}
      <div className="bg-white rounded-xl shadow border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="rounded-lg bg-amber-50 p-2">
            <Key className="h-5 w-5 text-amber-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Cambiar contraseña</h3>
            <p className="text-sm text-gray-500">Mantén tu cuenta segura con una contraseña fuerte</p>
          </div>
        </div>

        <form onSubmit={handleCambiarPassword} className="space-y-4 max-w-md">
          <PasswordField
            label="Contraseña actual"
            value={passwordActual}
            onChange={setPasswordActual}
            mostrar={mostrarActual}
            onToggle={() => setMostrarActual(v => !v)}
            placeholder="Tu contraseña actual"
          />
          <PasswordField
            label="Nueva contraseña"
            value={passwordNueva}
            onChange={setPasswordNueva}
            mostrar={mostrarNueva}
            onToggle={() => setMostrarNueva(v => !v)}
            placeholder="Mínimo 8 caracteres"
          />
          <PasswordField
            label="Confirmar nueva contraseña"
            value={passwordConfirmar}
            onChange={setPasswordConfirmar}
            mostrar={mostrarConfirmar}
            onToggle={() => setMostrarConfirmar(v => !v)}
            placeholder="Repite la nueva contraseña"
          />

          <button
            type="submit"
            disabled={guardandoPassword}
            className="flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
          >
            {guardandoPassword ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            {guardandoPassword ? 'Guardando...' : 'Cambiar contraseña'}
          </button>
        </form>
      </div>
    </div>
  );
};

// ── Subcomponentes ────────────────────────────────────────────────────────────

interface InfoFieldProps {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}

const InfoField: React.FC<InfoFieldProps> = ({ icon, label, value }) => (
  <div className="flex items-start gap-3">
    <div className="mt-0.5 flex-shrink-0">{icon}</div>
    <div>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">{label}</p>
      <div className="mt-0.5 text-sm text-gray-900">{value}</div>
    </div>
  </div>
);

interface PasswordFieldProps {
  label: string;
  value: string;
  onChange: (v: string) => void;
  mostrar: boolean;
  onToggle: () => void;
  placeholder: string;
}

const PasswordField: React.FC<PasswordFieldProps> = ({
  label, value, onChange, mostrar, onToggle, placeholder,
}) => (
  <div>
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    <div className="relative">
      <input
        type={mostrar ? 'text' : 'password'}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 pr-10 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
      />
      <button
        type="button"
        onClick={onToggle}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
      >
        {mostrar ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  </div>
);

export default Perfil;
