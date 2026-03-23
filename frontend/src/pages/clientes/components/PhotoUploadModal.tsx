import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, X, Trash2, AlertCircle, CheckCircle, Camera, RefreshCw } from 'lucide-react';
import { Button, Avatar, Spinner, Modal } from '../../../components/common';
import api from '../../../services/api';
import type { Hijo } from '../../../types';

interface PhotoUploadModalProps {
  hijo: Hijo;
  onClose: () => void;
  onPhotoUpdated: (hijoId: number, nuevaFoto: string) => void;
}

type Tab = 'upload' | 'webcam';

const PhotoUploadModal: React.FC<PhotoUploadModalProps> = ({
  hijo,
  onClose,
  onPhotoUpdated
}) => {
  const [tab, setTab] = useState<Tab>('upload');
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [capturedFile, setCapturedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Webcam state
  const [streaming, setStreaming] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setStreaming(false);
  }, []);

  const startCamera = async () => {
    setCameraError(null);
    setPreview(null);
    setCapturedFile(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setStreaming(true);
    } catch (e: any) {
      setCameraError(
        e.name === 'NotAllowedError'
          ? 'Permiso de cÃ¡mara denegado. Habilitalo en la configuraciÃ³n del navegador.'
          : 'No se pudo acceder a la cÃ¡mara. VerificÃ¡ que estÃ© conectada.'
      );
    }
  };

  const capture = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d')!.drawImage(video, 0, 0);
    canvas.toBlob(blob => {
      if (!blob) return;
      const file = new File([blob], `foto_${hijo.id_hijo}_${Date.now()}.jpg`, { type: 'image/jpeg' });
      setCapturedFile(file);
      setPreview(canvas.toDataURL('image/jpeg', 0.9));
      stopStream();
    }, 'image/jpeg', 0.9);
  };

  const retake = () => {
    setPreview(null);
    setCapturedFile(null);
    startCamera();
  };

  // Stop stream when switching tabs or unmounting
  useEffect(() => {
    if (tab !== 'webcam') stopStream();
  }, [tab, stopStream]);

  useEffect(() => () => stopStream(), [stopStream]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setError('Por favor seleccionÃ¡ un archivo de imagen vÃ¡lido');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError('La imagen es muy grande. MÃ¡ximo 5MB permitido');
      return;
    }
    setError(null);
    setSuccess(null);
    setCapturedFile(file);
    const reader = new FileReader();
    reader.onload = e => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    const file = capturedFile ?? fileInputRef.current?.files?.[0];
    if (!file || !preview) {
      setError('SeleccionÃ¡ o capturÃ¡ una imagen primero');
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('foto_perfil', file);
      const response = await api.patch(`/hijos/${hijo.id_hijo}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccess('Foto actualizada correctamente');
      onPhotoUpdated(hijo.id_hijo, response.data.foto_perfil);
      setTimeout(onClose, 1500);
    } catch {
      setError('Error al subir la foto. Intentalo de nuevo.');
    } finally {
      setUploading(false);
    }
  };

  const handleDeletePhoto = async () => {
    if (!hijo.foto_perfil) return;
    if (!window.confirm('Â¿EstÃ¡s seguro de eliminar la foto actual?')) return;
    setDeleting(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('foto_perfil', '');
      await api.patch(`/hijos/${hijo.id_hijo}/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccess('Foto eliminada correctamente');
      onPhotoUpdated(hijo.id_hijo, '');
      setTimeout(onClose, 1500);
    } catch {
      setError('Error al eliminar la foto. Intentalo de nuevo.');
    } finally {
      setDeleting(false);
    }
  };

  const clearPreview = () => {
    setPreview(null);
    setCapturedFile(null);
    setError(null);
    setSuccess(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Modal isOpen onClose={onClose} size="md">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Gestionar Foto</h3>
            <p className="text-sm text-gray-600">{hijo.nombre} {hijo.apellido}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-5">
          {/* Foto Actual */}
          <div className="text-center">
            <label className="block text-sm font-medium text-gray-700 mb-2">Foto Actual</label>
            <div className="flex justify-center mb-3">
              <Avatar src={hijo.foto_perfil} name={`${hijo.nombre} ${hijo.apellido}`} size="xl" />
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

          {/* Tabs */}
          <div className="flex rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => setTab('upload')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
                tab === 'upload'
                  ? 'bg-amber-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Upload className="h-4 w-4" />
              Subir archivo
            </button>
            <button
              onClick={() => setTab('webcam')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium transition-colors ${
                tab === 'webcam'
                  ? 'bg-amber-500 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Camera className="h-4 w-4" />
              Webcam
            </button>
          </div>

          {/* Tab: Subir archivo */}
          {tab === 'upload' && (
            <div>
              {preview ? (
                <div className="text-center">
                  <div className="relative inline-block">
                    <img
                      src={preview}
                      alt="Preview"
                      className="w-32 h-32 rounded-full object-cover border-2 border-amber-300 mx-auto"
                    />
                    <button
                      onClick={clearPreview}
                      className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">Vista previa</p>
                </div>
              ) : (
                <div
                  className="flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md hover:border-amber-400 transition-colors cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="space-y-1 text-center">
                    <Upload className="mx-auto h-10 w-10 text-gray-400" />
                    <div className="text-sm text-gray-600">
                      <span className="font-medium text-amber-600 hover:text-amber-500">
                        Seleccionar archivo
                      </span>
                      <span className="pl-1">o arrastra y suelta</span>
                    </div>
                    <p className="text-xs text-gray-500">PNG, JPG, JPEG hasta 5MB</p>
                  </div>
                </div>
              )}
              <input
                ref={fileInputRef}
                type="file"
                className="sr-only"
                accept="image/*"
                onChange={handleFileSelect}
                disabled={uploading || deleting}
              />
            </div>
          )}

          {/* Tab: Webcam */}
          {tab === 'webcam' && (
            <div className="space-y-3">
              {cameraError && (
                <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  {cameraError}
                </div>
              )}

              {preview ? (
                /* Foto capturada */
                <div className="text-center space-y-3">
                  <div className="relative inline-block">
                    <img
                      src={preview}
                      alt="Captura"
                      className="w-48 h-48 rounded-full object-cover border-2 border-amber-300 mx-auto"
                    />
                  </div>
                  <p className="text-xs text-gray-500">Foto capturada</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={retake}
                    leftIcon={<RefreshCw className="h-4 w-4" />}
                    className="border-gray-300"
                  >
                    Tomar otra
                  </Button>
                </div>
              ) : streaming ? (
                /* Stream activo */
                <div className="text-center space-y-3">
                  <div className="relative rounded-xl overflow-hidden bg-black mx-auto" style={{ maxWidth: 320 }}>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full"
                    />
                    {/* GuÃ­a circular */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="w-48 h-48 rounded-full border-2 border-white border-dashed opacity-60" />
                    </div>
                  </div>
                  <Button
                    onClick={capture}
                    leftIcon={<Camera className="h-4 w-4" />}
                    className="bg-amber-500 hover:bg-amber-600 text-white"
                  >
                    Capturar foto
                  </Button>
                  <canvas ref={canvasRef} className="hidden" />
                </div>
              ) : (
                /* Sin stream */
                <div className="text-center py-6">
                  <Camera className="mx-auto h-12 w-12 text-gray-300 mb-3" />
                  <p className="text-sm text-gray-500 mb-4">
                    UsÃ¡ la webcam para tomar una foto en el momento
                  </p>
                  <Button
                    onClick={startCamera}
                    leftIcon={<Camera className="h-4 w-4" />}
                    className="bg-amber-500 hover:bg-amber-600 text-white"
                  >
                    Activar cÃ¡mara
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Mensajes */}
          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
          {success && (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-500 shrink-0" />
              <span className="text-sm text-green-700">{success}</span>
            </div>
          )}

          {/* Botones */}
          <div className="flex gap-3 pt-4 border-t">
            <Button variant="outline" onClick={onClose} disabled={uploading || deleting} className="flex-1">
              Cancelar
            </Button>
            {preview && (
              <Button
                onClick={handleUpload}
                disabled={uploading || deleting}
                leftIcon={uploading ? <Spinner size="sm" /> : <Upload className="h-4 w-4" />}
                className="flex-1 bg-amber-500 hover:bg-amber-600 text-white"
              >
                {uploading ? 'Subiendo...' : 'Guardar Foto'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default PhotoUploadModal;
