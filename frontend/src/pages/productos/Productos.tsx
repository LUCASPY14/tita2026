import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { ListaProductos, FormularioProducto, DetalleProducto } from './components';
import type { Producto } from '../../types';

type Vista = 'lista' | 'crear' | 'editar' | 'detalle';

const Productos: React.FC = () => {
  const [vista, setVista] = useState<Vista>('lista');
  const [productoSeleccionado, setProductoSeleccionado] = useState<Producto | null>(null);
  const [actualizarLista, setActualizarLista] = useState(0);

  const handleNuevoProducto = () => {
    setProductoSeleccionado(null);
    setVista('crear');
  };

  const handleEditarProducto = (producto: Producto) => {
    setProductoSeleccionado(producto);
    setVista('editar');
  };

  const handleVerDetalle = (producto: Producto) => {
    setProductoSeleccionado(producto);
    setVista('detalle');
  };

  const handleGuardadoExitoso = () => {
    setVista('lista');
    setProductoSeleccionado(null);
    setActualizarLista(prev => prev + 1);
  };

  const handleCancelar = () => {
    setVista('lista');
    setProductoSeleccionado(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      {vista === 'lista' && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Gestión de Productos</h1>
            <p className="mt-2 text-gray-600">
              Administra el catálogo de productos, categorías y precios
            </p>
          </div>
          <button
            onClick={handleNuevoProducto}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-white hover:bg-amber-700 transition-colors"
          >
            <Plus className="h-5 w-5" />
            Nuevo Producto
          </button>
        </div>
      )}

      {/* Vista Lista */}
      {vista === 'lista' && (
        <ListaProductos
          key={actualizarLista}
          onEditar={handleEditarProducto}
          onVerDetalle={handleVerDetalle}
        />
      )}

      {/* Vista Crear/Editar */}
      {(vista === 'crear' || vista === 'editar') && (
        <FormularioProducto
          producto={productoSeleccionado}
          onGuardado={handleGuardadoExitoso}
          onCancelar={handleCancelar}
        />
      )}

      {/* Vista Detalle */}
      {vista === 'detalle' && productoSeleccionado && (
        <DetalleProducto
          producto={productoSeleccionado}
          onEditar={handleEditarProducto}
          onVolver={handleCancelar}
        />
      )}
    </div>
  );
};

export default Productos;
