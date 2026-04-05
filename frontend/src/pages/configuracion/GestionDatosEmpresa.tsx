/**
 * Página de edición de Datos de Empresa
 * Permite actualizar RUC, razón social, dirección, ciudad, teléfono y email
 * que aparecen en las facturas emitidas.
 */

import React, { useState, useEffect } from 'react';
import { Building2, Save, RefreshCw, AlertTriangle } from 'lucide-react';
import api from '../../services/api';
import toast from 'react-hot-toast';

interface DatosEmpresa {
  id_empresa: number;
  ruc: string;
  razon_social: string;
  direccion: string;
  ciudad: string;
  pais: string;
  telefono: string;
  email: string;
  estado: boolean;
}

const campos: { key: keyof DatosEmpresa; label: string; required?: boolean; placeholder?: string }[] = [
  { key: 'ruc',          label: 'RUC',           required: true,  placeholder: '80000000-0' },
  { key: 'razon_social', label: 'Razón Social',   required: true,  placeholder: 'Nombre legal de la empresa' },
  { key: 'direccion',    label: 'Dirección',      placeholder: 'Calle, número, barrio' },
  { key: 'ciudad',       label: 'Ciudad',         placeholder: 'Asunción' },
  { key: 'pais',         label: 'País',           placeholder: 'Paraguay' },
  { key: 'telefono',     label: 'Teléfono',       placeholder: '+595 21 000000' },
  { key: 'email',        label: 'Email',          placeholder: 'info@empresa.com.py' },
];

const GestionDatosEmpresa: React.FC = () => {
  const [empresa, setEmpresa] = useState<DatosEmpresa | null>(null);
  const [form, setForm]       = useState<Partial<DatosEmpresa>>({});
  const [cargando, setCargando]   = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [modificado, setModificado] = useState(false);

  useEffect(() => { cargar(); }, []);

  const cargar = async () => {
    try {
      setCargando(true);
      const res = await api.get<DatosEmpresa[]>('/datos-empresa/');
      const data = (res.data as unknown as DatosEmpresa[])[0] ?? null;
      setEmpresa(data);
      setForm(data ?? {});
      setModificado(false);
    } catch {
      toast.error('Error al cargar los datos de empresa');
    } finally {
      setCargando(false);
    }
  };

  const handleChange = (key: keyof DatosEmpresa, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }));
    setModificado(true);
  };

  const handleGuardar = async () => {
    if (!empresa) return;
    const ruc = (form.ruc ?? '').trim();
    const razon = (form.razon_social ?? '').trim();
    if (!ruc || !razon) {
      toast.error('RUC y Razón Social son obligatorios');
      return;
    }
    try {
      setGuardando(true);
      await api.patch(`/datos-empresa/${empresa.id_empresa}/`, form);
      toast.success('Datos de empresa actualizados');
      await cargar();
    } catch {
      toast.error('Error al guardar los datos');
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Building2 className="h-7 w-7 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Datos de Empresa</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              Información que aparece en facturas y documentos tributarios
            </p>
          </div>
        </div>
        <button
          onClick={cargar}
          disabled={cargando}
          className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-600 hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 mr-1.5 ${cargando ? 'animate-spin' : ''}`} />
          Recargar
        </button>
      </div>

      {/* Aviso */}
      <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4 flex gap-3">
        <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-yellow-700">
          Estos datos se imprimen en cada factura emitida. Verificá que el RUC y la Razón
          Social coincidan exactamente con el registro ante la SET.
        </p>
      </div>

      {cargando ? (
        <div className="bg-white rounded-lg shadow p-10 text-center text-gray-400">
          Cargando…
        </div>
      ) : !empresa ? (
        <div className="bg-white rounded-lg shadow p-10 text-center text-gray-400">
          No hay datos de empresa configurados.
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow divide-y divide-gray-100">
          <div className="p-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
            {campos.map(({ key, label, required, placeholder }) => (
              <div key={key} className={key === 'razon_social' ? 'sm:col-span-2' : ''}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {label}
                  {required && <span className="text-red-500 ml-0.5">*</span>}
                </label>
                <input
                  type={key === 'email' ? 'email' : 'text'}
                  value={String(form[key] ?? '')}
                  onChange={e => handleChange(key, e.target.value)}
                  placeholder={placeholder}
                  className="block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            ))}
          </div>

          <div className="px-6 py-4 flex items-center justify-between bg-gray-50 rounded-b-lg">
            {modificado && (
              <span className="text-sm text-amber-600 font-medium">Hay cambios sin guardar</span>
            )}
            <div className="ml-auto">
              <button
                onClick={handleGuardar}
                disabled={guardando || !modificado}
                className="inline-flex items-center px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {guardando ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Save className="h-4 w-4 mr-2" />
                )}
                Guardar cambios
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GestionDatosEmpresa;
