import React, { useState, useEffect } from 'react';
import { User, Plus, Edit, Camera, Trash2 } from 'lucide-react';
import { Card, Button, Avatar, Badge, Spinner } from '../../../components/common';
import { PhotoUploadModal, HijoFormModal } from '../components';
import api from '../../../services/api';
import type { Hijo } from '../../../types';

interface ListaHijosProps {
  clienteId: number;
  clienteNombre: string;
}

const ListaHijos: React.FC<ListaHijosProps> = ({ clienteId, clienteNombre }) => {
  const [hijos, setHijos] = useState<Hijo[]>([]);
  const [loading, setLoading] = useState(true);
  const [photoModalOpen, setPhotoModalOpen] = useState(false);
  const [hijoFormModalOpen, setHijoFormModalOpen] = useState(false);
  const [hijoSeleccionado, setHijoSeleccionado] = useState<Hijo | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    cargarHijos();
  }, [clienteId]);

  const cargarHijos = async () => {
    try {
      setLoading(true);
      const response = await api.get('/hijos/', {
        params: { id_cliente_responsable: clienteId }
      });
      setHijos(response.data?.results || response.data || []);
    } catch (error) {
      console.error('Error al cargar hijos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEditarHijo = (hijo: Hijo) => {
    setHijoSeleccionado(hijo);
    setIsEditing(true);
    setHijoFormModalOpen(true);
  };

  const handleNuevoHijo = () => {
    setHijoSeleccionado(null);
    setIsEditing(false);
    setHijoFormModalOpen(true);
  };

  const handleGestionarFoto = (hijo: Hijo) => {
    setHijoSeleccionado(hijo);
    setPhotoModalOpen(true);
  };

  const handleEliminarHijo = async (hijo: Hijo) => {
    if (window.confirm(`¿Estás seguro de eliminar a ${hijo.nombre} ${hijo.apellido}?`)) {
      try {
        await api.delete(`/hijos/${hijo.id_hijo}/`);
        cargarHijos(); // Recargar lista
      } catch (error) {
        console.error('Error al eliminar hijo:', error);
        alert('Error al eliminar el hijo');
      }
    }
  };

  const handleHijoGuardado = () => {
    setHijoFormModalOpen(false);
    setHijoSeleccionado(null);
    cargarHijos(); // Recargar lista
  };

  const handleFotoActualizada = (hijoId: number, nuevaFoto: string) => {
    setHijos(prev => prev.map(hijo => 
      hijo.id_hijo === hijoId ? { ...hijo, foto_perfil: nuevaFoto } : hijo
    ));
    setPhotoModalOpen(false);
    setHijoSeleccionado(null);
  };

  const calcularEdad = (fechaNacimiento?: string): number | null => {
    if (!fechaNacimiento) return null;
    const hoy = new Date();
    const nacimiento = new Date(fechaNacimiento);
    let edad = hoy.getFullYear() - nacimiento.getFullYear();
    const mes = hoy.getMonth() - nacimiento.getMonth();
    if (mes < 0 || (mes === 0 && hoy.getDate() < nacimiento.getDate())) {
      edad--;
    }
    return edad;
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
          <span className="ml-3 text-gray-600">Cargando hijos...</span>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900">
              Hijos de {clienteNombre}
            </h3>
            <p className="text-sm text-gray-600">
              Gestiona la información y fotos de los hijos
            </p>
          </div>
          <Button
            onClick={handleNuevoHijo}
            leftIcon={<Plus className="h-4 w-4" />}
          >
            Agregar Hijo
          </Button>
        </div>

        {hijos.length === 0 ? (
          <div className="text-center py-12">
            <User className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No hay hijos registrados</p>
            <Button
              variant="outline"
              onClick={handleNuevoHijo}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              Agregar Primer Hijo
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {hijos.map((hijo) => {
              const edad = calcularEdad(hijo.fecha_nacimiento);
              
              return (
                <div
                  key={hijo.id_hijo}
                  className="bg-gray-50 rounded-lg p-6 border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <div className="flex items-start gap-4 mb-4">
                    <div className="relative">
                      <Avatar
                        src={hijo.foto_perfil}
                        alt={`${hijo.nombre} ${hijo.apellido}`}
                        name={`${hijo.nombre} ${hijo.apellido}`}
                        size="lg"
                      />
                      
                      <button
                        onClick={() => handleGestionarFoto(hijo)}
                        className="absolute -bottom-1 -right-1 bg-blue-500 hover:bg-blue-600 text-white rounded-full p-1.5 transition-colors"
                        title="Gestionar foto"
                      >
                        <Camera className="h-3 w-3" />
                      </button>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 truncate">
                        {hijo.nombre} {hijo.apellido}
                      </h4>
                      <div className="mt-1 space-y-1">
                        {edad && (
                          <p className="text-sm text-gray-600">
                            {edad} año{edad !== 1 ? 's' : ''}
                          </p>
                        )}
                        {hijo.grado && (
                          <p className="text-sm text-gray-600">
                            Grado: {hijo.grado}
                          </p>
                        )}
                      </div>
                      <div className="mt-2">
                        <Badge variant={hijo.estado ? 'success' : 'danger'}>
                          {hijo.estado ? 'Activo' : 'Inactivo'}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEditarHijo(hijo)}
                      leftIcon={<Edit className="h-3 w-3" />}
                      className="flex-1"
                    >
                      Editar
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      color="danger"
                      onClick={() => handleEliminarHijo(hijo)}
                      leftIcon={<Trash2 className="h-3 w-3" />}
                      className="flex-1"
                    >
                      Eliminar
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      {/* Modals */}
      {photoModalOpen && hijoSeleccionado && (
        <PhotoUploadModal
          hijo={hijoSeleccionado}
          onClose={() => {
            setPhotoModalOpen(false);
            setHijoSeleccionado(null);
          }}
          onPhotoUpdated={handleFotoActualizada}
        />
      )}

      {hijoFormModalOpen && (
        <HijoFormModal
          hijo={hijoSeleccionado}
          clienteId={clienteId}
          isEditing={isEditing}
          onClose={() => {
            setHijoFormModalOpen(false);
            setHijoSeleccionado(null);
          }}
          onSave={handleHijoGuardado}
        />
      )}
    </div>
  );
};

export default ListaHijos;