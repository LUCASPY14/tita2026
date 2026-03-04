import React, { useState } from 'react';
import { Plus, Users } from 'lucide-react';
import { Card, Button } from '../../components/common';
import { UserTable, UserForm } from './components';
import type { Usuario } from '../../services/users.service';

type Vista = 'lista' | 'crear' | 'editar';

const UserManagement: React.FC = () => {
  const [vista, setVista] = useState<Vista>('lista');
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState<Usuario | null>(null);
  const [actualizarLista, setActualizarLista] = useState(0);

  const handleNuevoUsuario = () => {
    setUsuarioSeleccionado(null);
    setVista('crear');
  };

  const handleEditarUsuario = (usuario: Usuario) => {
    setUsuarioSeleccionado(usuario);
    setVista('editar');
  };

  const handleGuardadoExitoso = () => {
    setVista('lista');
    setUsuarioSeleccionado(null);
    setActualizarLista(prev => prev + 1);
  };

  const handleCancelar = () => {
    setVista('lista');
    setUsuarioSeleccionado(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-100 rounded-lg">
            <Users className="h-8 w-8 text-purple-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Gestión de Usuarios</h1>
            <p className="mt-1 text-gray-600">
              Administra usuarios, roles y permisos del sistema
            </p>
          </div>
        </div>

        {vista === 'lista' && (
          <Button
            variant="primary"
            onClick={handleNuevoUsuario}
            leftIcon={<Plus className="h-5 w-5" />}
          >
            Nuevo Usuario
          </Button>
        )}
      </div>

      {/* Vista Lista */}
      {vista === 'lista' && (
        <Card>
          <UserTable
            key={actualizarLista}
            onEditar={handleEditarUsuario}
            onActualizarLista={() => setActualizarLista(prev => prev + 1)}
          />
        </Card>
      )}

      {/* Vista Crear/Editar */}
      {(vista === 'crear' || vista === 'editar') && (
        <div className="space-y-4">
          <Button variant="outline" onClick={handleCancelar}>
            ← Volver a la lista
          </Button>
          
          <Card
            title={vista === 'crear' ? 'Nuevo Usuario' : 'Editar Usuario'}
            subtitle={
              vista === 'editar' && usuarioSeleccionado
                ? `${usuarioSeleccionado.nombre} ${usuarioSeleccionado.apellido} (@${usuarioSeleccionado.usuario})`
                : 'Complete los datos del nuevo usuario'
            }
          >
            <UserForm
              usuario={vista === 'editar' ? usuarioSeleccionado : null}
              onGuardado={handleGuardadoExitoso}
              onCancelar={handleCancelar}
            />
          </Card>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
