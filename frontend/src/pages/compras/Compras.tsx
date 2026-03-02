import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { ListaCompras, FormularioCompra, DetalleCompra } from './components';
import type { Compra } from '../../types';

type Vista = 'lista' | 'crear' | 'editar' | 'detalle';

const Compras: React.FC = () => {
  const [vista, setVista] = useState<Vista>('lista');
  const [compraSeleccionada, setCompraSeleccionada] = useState<Compra | null>(null);
  const [actualizarLista, setActualizarLista] = useState(0);

  const handleNuevaCompra = () => {
    setCompraSeleccionada(null);
    setVista('crear');
  };

  const handleEditarCompra = (compra: Compra) => {
    setCompraSeleccionada(compra);
    setVista('editar');
  };

  const handleVerDetalle = (compra: Compra) => {
    setCompraSeleccionada(compra);
    setVista('detalle');
  };

  const handleGuardadoExitoso = () => {
    setVista('lista');
    setCompraSeleccionada(null);
    setActualizarLista(prev => prev + 1);
  };

  const handleCancelar = () => {
    setVista('lista');
    setCompraSeleccionada(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      {vista === 'lista' && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Gestión de Compras</h1>
            <p className="mt-2 text-gray-600">
              Administra las compras a proveedores y control de inventario
            </p>
          </div>
          <button
            onClick={handleNuevaCompra}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-white hover:bg-amber-700 transition-colors"
          >
            <Plus className="h-5 w-5" />
            Nueva Compra
          </button>
        </div>
      )}

      {/* Vista Lista */}
      {vista === 'lista' && (
        <ListaCompras
          key={actualizarLista}
          onEditar={handleEditarCompra}
          onVerDetalle={handleVerDetalle}
        />
      )}

      {/* Vista Crear/Editar */}
      {(vista === 'crear' || vista === 'editar') && (
        <FormularioCompra
          compra={compraSeleccionada}
          onGuardado={handleGuardadoExitoso}
          onCancelar={handleCancelar}
        />
      )}

      {/* Vista Detalle */}
      {vista === 'detalle' && compraSeleccionada && (
        <DetalleCompra
          compra={compraSeleccionada}
          onEditar={handleEditarCompra}
          onVolver={handleCancelar}
        />
      )}
    </div>
  );
};

export default Compras;
