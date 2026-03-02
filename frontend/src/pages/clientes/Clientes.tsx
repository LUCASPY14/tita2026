import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { Card, Button } from '../../components/common';
import { ListaClientes, FormularioCliente, DetalleCliente } from './components';
import type { Cliente } from '../../types';

type Vista = 'lista' | 'crear' | 'editar' | 'detalle';

const Clientes: React.FC = () => {
  const [vista, setVista] = useState<Vista>('lista');
  const [clienteSeleccionado, setClienteSeleccionado] = useState<Cliente | null>(null);
  const [actualizarLista, setActualizarLista] = useState(0);

  const handleNuevoCliente = () => {
    setClienteSeleccionado(null);
    setVista('crear');
  };

  const handleEditarCliente = (cliente: Cliente) => {
    setClienteSeleccionado(cliente);
    setVista('editar');
  };

  const handleVerDetalle = (cliente: Cliente) => {
    setClienteSeleccionado(cliente);
    setVista('detalle');
  };

  const handleGuardadoExitoso = () => {
    setVista('lista');
    setClienteSeleccionado(null);
    setActualizarLista(prev => prev + 1);
  };

  const handleCancelar = () => {
    setVista('lista');
    setClienteSeleccionado(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestión de Clientes</h1>
          <p className="mt-2 text-gray-600">
            Administra la información de tus clientes
          </p>
        </div>

        {vista === 'lista' && (
          <Button
            variant="primary"
            onClick={handleNuevoCliente}
            leftIcon={<Plus className="h-5 w-5" />}
          >
            Nuevo Cliente
          </Button>
        )}
      </div>

      {/* Vista Lista */}
      {vista === 'lista' && (
        <Card>
          <ListaClientes
            key={actualizarLista}
            onEditar={handleEditarCliente}
            onVerDetalle={handleVerDetalle}
          />
        </Card>
      )}

      {/* Vista Crear/Editar */}
      {(vista === 'crear' || vista === 'editar') && (
        <Card
          title={vista === 'crear' ? 'Nuevo Cliente' : 'Editar Cliente'}
          subtitle={vista === 'editar' && clienteSeleccionado ? 
            `${clienteSeleccionado.nombres} ${clienteSeleccionado.apellidos}` : 
            'Complete los datos del cliente'}
        >
          <FormularioCliente
            cliente={vista === 'editar' ? clienteSeleccionado : null}
            onGuardado={handleGuardadoExitoso}
            onCancelar={handleCancelar}
          />
        </Card>
      )}

      {/* Vista Detalle */}
      {vista === 'detalle' && clienteSeleccionado && (
        <>
          <div className="mb-4">
            <Button
              variant="outline"
              onClick={handleCancelar}
            >
              ← Volver a la lista
            </Button>
          </div>
          <DetalleCliente
            cliente={clienteSeleccionado}
            onEditar={handleEditarCliente}
          />
        </>
      )}
    </div>
  );
};

export default Clientes;
