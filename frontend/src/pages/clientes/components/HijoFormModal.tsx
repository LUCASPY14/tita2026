import React, { useState, useEffect } from 'react';
import { User, Save, X } from 'lucide-react';
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
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const gradosOptions = [
    { value: '', label: 'Seleccionar grado' },
    { value: 'Maternal', label: 'Maternal' },
    { value: 'Pre-kinder', label: 'Pre-kinder' },
    { value: 'Kinder', label: 'Kinder' },
    { value: '1° Grado', label: '1° Grado' },
    { value: '2° Grado', label: '2° Grado' },
    { value: '3° Grado', label: '3° Grado' },
    { value: '4° Grado', label: '4° Grado' },
    { value: '5° Grado', label: '5° Grado' },
    { value: '6° Grado', label: '6° Grado' },
    { value: '7° Grado', label: '7° Grado' },
    { value: '8° Grado', label: '8° Grado' },
    { value: '9° Grado', label: '9° Grado' },
    { value: '1° Curso', label: '1° Curso' },
    { value: '2° Curso', label: '2° Curso' },
    { value: '3° Curso', label: '3° Curso' }
  ];

  useEffect(() => {
    if (isEditing && hijo) {
      setFormData({
        nombre: hijo.nombre || '',
        apellido: hijo.apellido || '',
        fecha_nacimiento: hijo.fecha_nacimiento || '',
        grado: hijo.grado || '',
        estado: hijo.estado ?? true
      });
    }
  }, [hijo, isEditing]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.nombre.trim()) {
      newErrors.nombre = 'El nombre es obligatorio';
    }

    if (!formData.apellido.trim()) {
      newErrors.apellido = 'El apellido es obligatorio';
    }

    if (formData.fecha_nacimiento) {
      const fechaNacimiento = new Date(formData.fecha_nacimiento);
      const hoy = new Date();
      
      if (fechaNacimiento > hoy) {
        newErrors.fecha_nacimiento = 'La fecha de nacimiento no puede ser futura';
      }
      
      // Validar que no sea muy antigua (más de 25 años)
      const hace25Anos = new Date();
      hace25Anos.setFullYear(hace25Anos.getFullYear() - 25);
      
      if (fechaNacimiento < hace25Anos) {
        newErrors.fecha_nacimiento = 'La fecha de nacimiento es muy antigua';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSaving(true);
    
    try {
      const payload = {
        ...formData,
        id_cliente_responsable: clienteId,
        // Convertir fecha vacía a null
        fecha_nacimiento: formData.fecha_nacimiento || null,
        grado: formData.grado || null
      };

      if (isEditing && hijo) {
        // Actualizar hijo existente
        await api.patch(`/hijos/${hijo.id_hijo}/`, payload);
      } else {
        // Crear nuevo hijo
        await api.post('/hijos/', payload);
      }

      onSave();
    } catch (error: any) {
      console.error('Error al guardar hijo:', error);
      
      // Manejar errores de validación del backend
      if (error.response?.data) {
        const backendErrors: Record<string, string> = {};
        Object.entries(error.response.data).forEach(([key, value]) => {
          if (Array.isArray(value)) {
            backendErrors[key] = value[0];
          } else {
            backendErrors[key] = value as string;
          }
        });
        setErrors(backendErrors);
      } else {
        setErrors({
          general: 'Error al guardar. Inténtalo de nuevo.'
        });
      }
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpiar error específico cuando el usuario comience a escribir
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} size="md">
      <div className="p-6">
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
                {isEditing 
                  ? 'Modifica la información del hijo'
                  : 'Completa los datos del nuevo hijo'
                }
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Error General */}
          {errors.general && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{errors.general}</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {/* Nombre */}
            <Input
              label="Nombre"
              value={formData.nombre}
              onChange={(value) => handleInputChange('nombre', value)}
              error={errors.nombre}
              placeholder="Ejemplo: Juan"
              required
            />

            {/* Apellido */}
            <Input
              label="Apellido"
              value={formData.apellido}
              onChange={(value) => handleInputChange('apellido', value)}
              error={errors.apellido}
              placeholder="Ejemplo: Pérez"
              required
            />
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            {/* Fecha de Nacimiento */}
            <Input
              type="date"
              label="Fecha de Nacimiento"
              value={formData.fecha_nacimiento}
              onChange={(value) => handleInputChange('fecha_nacimiento', value)}
              error={errors.fecha_nacimiento}
              max={new Date().toISOString().split('T')[0]} // No permitir fechas futuras
            />

            {/* Grado */}
            <Select
              label="Grado"
              value={formData.grado}
              onChange={(value) => handleInputChange('grado', value)}
              options={gradosOptions}
              error={errors.grado}
            />
          </div>

          {/* Estado */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="text-sm font-medium text-gray-700">
                Estado del Hijo
              </label>
              <p className="text-sm text-gray-500">
                Determina si el hijo está activo en el sistema
              </p>
            </div>
            <Checkbox
              checked={formData.estado}
              onChange={(checked) => handleInputChange('estado', checked)}
              label="Activo"
            />
          </div>

          {/* Botones de Acción */}
          <div className="flex gap-3 pt-6 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={saving}
              className="flex-1"
            >
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
                : (isEditing ? 'Actualizar Hijo' : 'Guardar Hijo')
              }
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default HijoFormModal;