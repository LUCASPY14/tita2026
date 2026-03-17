import React, { useState, useRef } from 'react';
import { Camera, Upload, X, Trash2, Eye, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, Button, Avatar, Spinner, Modal } from '../../../components/common';
import api from '../../../services/api';
import type { Hijo } from '../../../types';

interface PhotoUploadModalProps {
  hijo: Hijo;
  onClose: () => void;
  onPhotoUpdated: (hijoId: number, nuevaFoto: string) => void;
}

const PhotoUploadModal: React.FC<PhotoUploadModalProps> = ({
  hijo,
  onClose,
  onPhotoUpdated
}) => {
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
      setError('Por favor selecciona un archivo de imagen válido');
      return;
    }

    // Validar tamaño (máximo 5MB)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setError('La imagen es muy grande. Máximo 5MB permitido');
      return;
    }

    setError(null);
    setSuccess(null);

    // Crear preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    if (!fileInputRef.current?.files?.[0] || !preview) {
      setError('Selecciona una imagen primero');
      return;
    }

    const file = fileInputRef.current.files[0];
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('foto_perfil', file);

      const response = await api.patch(`/hijos/${hijo.id_hijo}/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess('Foto actualizada correctamente');
      onPhotoUpdated(hijo.id_hijo, response.data.foto_perfil);
      
      setTimeout(() => {
        onClose();
      }, 1500);
      
    } catch (error) {
      console.error('Error al subir foto:', error);
      setError('Error al subir la foto. Inténtalo de nuevo.');
    } finally {
      setUploading(false);
    }
  };

  const handleDeletePhoto = async () => {
    if (!hijo.foto_perfil) return;
    
    if (!window.confirm('¿Estás seguro de eliminar la foto actual?')) {
      return;
    }

    setDeleting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('foto_perfil', ''); // Enviar string vacío para eliminar

      await api.patch(`/hijos/${hijo.id_hijo}/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setSuccess('Foto eliminada correctamente');
      onPhotoUpdated(hijo.id_hijo, '');
      
      setTimeout(() => {
        onClose();
      }, 1500);
      
    } catch (error) {
      console.error('Error al eliminar foto:', error);
      setError('Error al eliminar la foto. Inténtalo de nuevo.');
    } finally {
      setDeleting(false);
    }
  };

  const handleClearPreview = () => {
    setPreview(null);
    setError(null);
    setSuccess(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} size="md">
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Gestionar Foto
            </h3>
            <p className="text-sm text-gray-600">
              {hijo.nombre} {hijo.apellido}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-6">
          {/* Foto Actual */}
          <div className="text-center">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Foto Actual
              </label>
              <div className="flex justify-center">
                <Avatar
                  src={hijo.foto_perfil}
                  alt={`${hijo.nombre} ${hijo.apellido}`}
                  size="2xl"
                  fallback={
                    <div className="text-gray-400">
                      <Camera className="h-12 w-12" />
                    </div>
                  }
                />
              </div>
            </div>
            
            {hijo.foto_perfil && (
              <Button
                variant="outline"
                size="sm"
                color="danger"
                onClick={handleDeletePhoto}
                disabled={deleting || uploading}
                leftIcon={deleting ? <Spinner size="sm" /> : <Trash2 className="h-4 w-4" />}
              >
                {deleting ? 'Eliminando...' : 'Eliminar Foto Actual'}
              </Button>
            )}
          </div>

          {/* Preview de Nueva Foto */}
          {preview && (
            <div className="text-center">
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nueva Foto (Preview)
                </label>
                <div className="flex justify-center">
                  <div className="relative">
                    <img
                      src={preview}
                      alt="Preview"
                      className="w-32 h-32 rounded-full object-cover border-2 border-gray-200"
                    />
                    <button
                      onClick={handleClearPreview}
                      className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Selector de Archivo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Subir Nueva Foto
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-gray-400 transition-colors">
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label className="relative cursor-pointer bg-white rounded-md font-medium text-amber-600 hover:text-amber-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-amber-500">
                    <span>{preview ? 'Cambiar archivo' : 'Seleccionar archivo'}</span>
                    <input
                      ref={fileInputRef}
                      type="file"
                      className="sr-only"
                      accept="image/*"
                      onChange={handleFileSelect}
                      disabled={uploading || deleting}
                    />
                  </label>
                  <p className="pl-1">o arrastra y suelta</p>
                </div>
                <p className="text-xs text-gray-500">PNG, JPG, JPEG hasta 5MB</p>
              </div>
            </div>
          </div>

          {/* Mensajes de Estado */}
          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}

          {success && (
            <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-sm text-green-700">{success}</span>
            </div>
          )}

          {/* Botones de Acción */}
          <div className="flex gap-3 pt-4 border-t">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={uploading || deleting}
              className="flex-1"
            >
              Cancelar
            </Button>
            
            {preview && (
              <Button
                onClick={handleUpload}
                disabled={uploading || deleting}
                leftIcon={uploading ? <Spinner size="sm" /> : <Upload className="h-4 w-4" />}
                className="flex-1"
              >
                {uploading ? 'Subiendo...' : 'Subir Foto'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default PhotoUploadModal;