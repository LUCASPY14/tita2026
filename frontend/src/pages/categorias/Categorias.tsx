import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { ListaCategorias, FormularioCategoria } from './components';
import type { Categoria } from '../../types';

type Vista = 'lista' | 'crear' | 'editar';

const Categorias: React.FC = () => {
  const [vista, setVista] = useState<Vista>('lista');
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState<Categoria | null>(null);
  const [actualizarLista, setActualizarLista] = useState(0);

  const handleNuevaCategoria = () => {
    setCategoriaSeleccionada(null);
    setVista('crear');
  };

  const handleEditarCategoria = (categoria: Categoria) => {
    setCategoriaSeleccionada(categoria);
    setVista('editar');
  };

  const handleGuardadoExitoso = () => {
    setVista('lista');
    setCategoriaSeleccionada(null);
    setActualizarLista((prev) => prev + 1);
  };

  const handleCancelar = () => {
    setVista('lista');
    setCategoriaSeleccionada(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      {vista === 'lista' && (
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Categorías de Productos</h1>
            <p className="mt-2 text-gray-600">
              Administrá las categorías para organizar el catálogo de productos
            </p>
          </div>
          <button
            onClick={handleNuevaCategoria}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-white hover:bg-amber-700 transition-colors"
          >
            <Plus className="h-5 w-5" />
            Nueva Categoría
          </button>
        </div>
      )}

      {/* Vista Lista */}
      {vista === 'lista' && (
        <ListaCategorias
          onEditar={handleEditarCategoria}
          actualizarClave={actualizarLista}
        />
      )}

      {/* Vista Crear / Editar */}
      {(vista === 'crear' || vista === 'editar') && (
        <>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCancelar}
              className="text-sm text-amber-600 hover:underline"
            >
              ← Volver a Categorías
            </button>
          </div>
          <FormularioCategoria
            categoria={categoriaSeleccionada}
            onGuardado={handleGuardadoExitoso}
            onCancelar={handleCancelar}
          />
        </>
      )}
    </div>
  );
};

export default Categorias;
