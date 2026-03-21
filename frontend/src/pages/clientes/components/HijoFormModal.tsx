import React, { useState, useEffect, useRef } from 'react';
import { User, Save, X, Camera, CreditCard } from 'lucide-react';
import { Modal, Button, Input, Select, Checkbox, Spinner } from '../../../components/common';
import api from '../../../services/api';
import type { Hijo } from '../../../types';

interface HijoFormModalProps {
  hijo: Hijo | null; // null para crear, objeto para editar
  clienteId: number;
  isEditing: boolean;
  onClose: () => void;
  onSave: () => void;
}

interface Grado {
  id_grado: number;
  nombre_grado: string;
  nivel: number;
  orden_visualizacion: number;
}

const HijoFormModal: React.FC<HijoFormModalProps> = ({
  hijo,
  clienteId,
  isEditing,
  onClose,
  onSave
}) => {
  const [formData, setFormData] = useState({
    nombre: '',
    apellido: '',
    fecha_nacimiento: '',
    grado: '',
    estado: true
  });
  const [grados, setGrados] = useState<Grado[]>([]);
  const [fotoFile, setFotoFile] = useState<File | null>(null);
  const [fotoPreview, setFotoPreview] = useState<string | null>(null);
  const [tarjeta, setTarjeta] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    cargarGrados();
  }, []);

  useEffect(() => {
    if (isEditing && hijo) {
      setFormData({
        nombre: hijo.nombre || '',
        apellido: hijo.apellido || '',
        fecha_nacimiento: hijo.fecha_nacimiento || '',
        grado: hijo.grado || '',
        estado: hijo.estado ?? true
      });
      if (hijo.foto_perfil) {
        setFotoPreview(hijo.foto_perfil);
      }
      cargarTarjeta(hijo.id_hijo);
    }
  }, [hijo, isEditing]);

  const cargarGrados = async () => {
    try {
      const resp = await api.get('/grados/', { params: { page_size: 100 } });
      setGrados(resp.data.results || []);
    } catch (error) {
      console.error('Error al cargar grados:', error);
    }
  };

  const cargarTarjeta = async (idHijo: number) => {
    try {
      const resp = await api.get('/tarjetas/', { params: { id_hijo: idHijo } });
      const results = resp.data.results || resp.data;
      if (results.length > 0) setTarjeta(results[0]);
    } catch {
      // Sin tarjeta asignada
    }
  };

  const gradosOptions = [
    { value: '', label: 'Seleccionar grado' },
    ...grados.map(g => ({ value: g.nombre_grado, label: g.nombre_grado }))
  ];

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.nombre.trim()) newErrors.nombre = 'El nombre es obligatorio';
    if (!formData.apellido.trim()) newErrors.apellido = 'El apellido es obligatorio';
    if (formData.fecha_nacimiento) {
      const fechaNacimiento = new Date(formData.fecha_nacimiento);
      const hoy = new Date();
      if (fechaNacimiento > hoy) newErrors.fecha_nacimiento = 'La fecha de nacimiento no puede ser futura';
      const hace25Anos = new Date();
      hace25Anos.setFullYear(hace25Anos.getFullYear() - 25);
      if (fechaNacimiento < hace25Anos) newErrors.fecha_nacimiento = 'La fecha de nacimiento es muy antigua';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: '' }));
  };

  const handleFotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFotoFile(file);
    const reader = new FileReader();
    reader.onloadend = () => setFotoPreview(reader.result as string);
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setSaving(true);
    try {
      const payload = new FormData();
      payload.append('nombre', formData.nombre);
      payload.append('apellido', formData.apellido);
      payload.append('estado', String(formData.estado));
      payload.append('id_cliente_responsable', String(clienteId));
      if (formData.fecha_nacimiento) payload.append('fecha_nacimiento', formData.fecha_nacimiento);
      if (formData.grado) payload.append('grado', formData.grado);
      if (fotoFile) payload.append('foto_perfil', fotoFile);

      if (isEditing && hijo) {
        await api.patch(`/hijos/${hijo.id_hijo}/`, payload, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      } else {
        await api.post('/hijos/', payload, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
      }
      onSave();
    } catch (error: any) {
      console.error('Error al guardar hijo:', error);
      if (error.response?.data) {
        const backendErrors: Record<string, string> = {};
        Object.entries(error.response.data).forEach(([key, value]) => {
          backendErrors[key] = Array.isArray(value) ? value[0] : (value as string);
        });
        setErrors(backendErrors);
      } else {
        setErrors({ general: 'Error al guardar. IntÃ©ntalo de nuevo.' });
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} size="md">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {isEditing ? 'Editar Hijo' : 'Agregar Nuevo Hijo'}
              </h3>
              <p className="text-sm text-gray-600">
                {isEditing ? 'Modifica la informaciÃ³n del hijo' : 'Completa los datos del nuevo hijo'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {errors.general && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{errors.general}</p>
            </div>
          )}

          {/* Foto de Perfil */}
          <div className="flex flex-col items-center gap-3">
            <div className="relative">
              {fotoPreview ? (
                <img
                  src={fotoPreview}
                  alt="Foto del hijo"
                  className="h-20 w-20 rounded-full object-cover border-2 border-amber-400"
                />
              ) : (
                <div className="h-20 w-20 rounded-full bg-gray-100 flex items-center justify-center border-2 border-dashed border-gray-300">
                  <User className="h-8 w-8 text-gray-400" />
                </div>
              )}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-0 right-0 h-7 w-7 rounded-full bg-amber-500 text-white flex items-center justify-center hover:bg-amber-600 shadow"
                title="Cambiar foto"
              >
                <Camera className="h-4 w-4" />
              </button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleFotoChange}
            />
            <p className="text-xs text-gray-500">Foto del estudiante (opcional)</p>
          </div>

          {/* Nombre y Apellido */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Input
              label="Nombre"
              name="nombre"
              value={formData.nombre}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('nombre', e.target.value)}
              error={errors.nombre}
              placeholder="Ejemplo: Juan"
              required
            />
            <Input
              label="Apellido"
              name="apellido"
              value={formData.apellido}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('apellido', e.target.value)}
              error={errors.apellido}
              placeholder="Ejemplo: PÃ©rez"
              required
            />
          </div>

          {/* Fecha y Grado */}
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <Input
              type="date"
              label="Fecha de Nacimiento"
              name="fecha_nacimiento"
              value={formData.fecha_nacimiento}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleInputChange('fecha_nacimiento', e.target.value)}
              error={errors.fecha_nacimiento}
              max={new Date().toISOString().split('T')[0]}
            />
            <Select
              label="Grado"
              name="grado"
              value={formData.grado}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) => handleInputChange('grado', e.target.value)}
              options={gradosOptions}
              error={errors.grado}
            />
          </div>

          {/* Tarjeta (solo ediciÃ³n) */}
          {isEditing && (
            <div className="p-4 bg-gray-50 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <CreditCard className="h-4 w-4 text-amber-600" />
                <span className="text-sm font-medium text-gray-700">Tarjeta de Uso Exclusivo</span>
              </div>
              {tarjeta ? (
                <div className="text-sm text-gray-600 space-y-1">
                  <p><span className="font-medium">Nro:</span> {tarjeta.nro_tarjeta}</p>
                  <p><span className="font-medium">Saldo:</span> Gs. {Number(tarjeta.saldo_actual).toLocaleString('es-PY')}</p>
                  <p><span className="font-medium">Estado:</span> {tarjeta.estado}</p>
                </div>
              ) : (
                <p className="text-sm text-gray-500">Sin tarjeta asignada. Se puede asignar desde el detalle del cliente.</p>
              )}
            </div>
          )}

          {/* Estado */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="text-sm font-medium text-gray-700">Estado del Hijo</label>
              <p className="text-sm text-gray-500">Determina si el hijo estÃ¡ activo en el sistema</p>
            </div>
            <Checkbox
              checked={formData.estado}
              onChange={(e) => handleInputChange('estado', e.target.checked)}
              label="Activo"
            />
          </div>

          {/* Botones */}
          <div className="flex gap-3 pt-6 border-t">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving} className="flex-1">
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={saving}
              leftIcon={saving ? <Spinner size="sm" /> : <Save className="h-4 w-4" />}
              className="flex-1"
            >
              {saving
                ? (isEditing ? 'Actualizando...' : 'Guardando...')
                : (isEditing ? 'Actualizar Hijo' : 'Guardar Hijo')}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default HijoFormModal;
