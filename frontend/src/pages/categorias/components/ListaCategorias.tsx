import React, { useState, useEffect } from 'react';
import { Search, Edit, Trash2, ToggleLeft, ToggleRight, Tag } from 'lucide-react';
import { productosService } from '../../../services/productos.service';
import { Categoria } from '../../../types';
import { Card, ConfirmDialog, Skeleton, EmptyState } from '../../../components/common';
import { useDebounce } from '../../../hooks/useDebounce';
import toast from 'react-hot-toast';

interface ListaCategoriasProps {
  onEditar: (categoria: Categoria) => void;
  actualizarClave?: number;
}

const ListaCategorias: React.FC<ListaCategoriasProps> = ({ onEditar, actualizarClave }) => {
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroActivo, setFiltroActivo] = useState<boolean | undefined>(true);
  const [categoriaAEliminar, setCategoriaAEliminar] = useState<Categoria | null>(null);

  const busquedaDebounced = useDebounce(busqueda);

  useEffect(() => {
    cargarCategorias();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busquedaDebounced, filtroActivo, actualizarClave]);

  const cargarCategorias = async () => {
    setCargando(true);
    try {
      const params: any = { page_size: 100 };
      if (filtroActivo !== undefined) params.estado = filtroActivo;
      const response = await productosService.getCategorias(params);
      const resultado = response.results ?? (response as any);
      const lista: Categoria[] = Array.isArray(resultado) ? resultado : [];
      const filtradas = busquedaDebounced
        ? lista.filter((c) =>
            c.nombre.toLowerCase().includes(busquedaDebounced.toLowerCase())
          )
        : lista;
      setCategorias(filtradas);
    } catch (error) {
      toast.error('Error al cargar categorías');
      console.error('Error:', error);
    } finally {
      setCargando(false);
    }
  };

  const handleToggleEstado = async (categoria: Categoria) => {
    try {
      await productosService.actualizarCategoria(categoria.id_categoria, {
        estado: !categoria.estado,
      });
      toast.success(
        `Categoría ${!categoria.estado ? 'activada' : 'desactivada'} exitosamente`
      );
      cargarCategorias();
    } catch (error) {
      toast.error('Error al cambiar estado de la categoría');
      console.error('Error:', error);
    }
  };

  const handleEliminar = (categoria: Categoria) => {
    setCategoriaAEliminar(categoria);
  };

  const confirmarEliminar = async () => {
    if (!categoriaAEliminar) return;
    try {
      await productosService.eliminarCategoria(categoriaAEliminar.id_categoria);
      toast.success('Categoría eliminada exitosamente');
      setCategoriaAEliminar(null);
      cargarCategorias();
    } catch (error) {
      toast.error('Error al eliminar categoría. Puede tener productos asociados.');
      console.error('Error:', error);
    }
  };

  if (cargando && categorias.length === 0) {
    return (
      <Card>
        <Skeleton rows={6} cols={4} />
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          {/* Búsqueda */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar categoría..."
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>

          {/* Filtro Estado */}
          <div className="flex gap-2">
            {[
              { label: 'Activas', value: true },
              { label: 'Inactivas', value: false },
              { label: 'Todas', value: undefined },
            ].map(({ label, value }) => (
              <button
                key={label}
                onClick={() => setFiltroActivo(value)}
                className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                  filtroActivo === value
                    ? 'border-amber-600 bg-amber-50 text-amber-700'
                    : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Tabla */}
      <Card>
        {categorias.length === 0 ? (
          <EmptyState
            icon={Tag}
            title="No hay categorías"
            description="No se encontraron categorías con los filtros aplicados."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">#</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Nombre</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Tipo</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Estado</th>
                  <th className="px-4 py-3 text-center font-semibold text-gray-700">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {categorias.map((categoria) => (
                  <tr key={categoria.id_categoria} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500">{categoria.id_categoria}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {categoria.nombre_completo || categoria.nombre}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {categoria.es_categoria_raiz || !categoria.id_categoria_padre
                        ? 'Principal'
                        : 'Subcategoría'}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                          categoria.estado
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {categoria.estado ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => onEditar(categoria)}
                          className="rounded p-1 text-blue-600 hover:bg-blue-50"
                          title="Editar"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleToggleEstado(categoria)}
                          className={`rounded p-1 ${
                            categoria.estado
                              ? 'text-orange-500 hover:bg-orange-50'
                              : 'text-green-600 hover:bg-green-50'
                          }`}
                          title={categoria.estado ? 'Desactivar' : 'Activar'}
                        >
                          {categoria.estado ? (
                            <ToggleRight className="h-4 w-4" />
                          ) : (
                            <ToggleLeft className="h-4 w-4" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEliminar(categoria)}
                          className="rounded p-1 text-red-600 hover:bg-red-50"
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Confirmación eliminar */}
      <ConfirmDialog
        isOpen={!!categoriaAEliminar}
        title="Eliminar categoría"
        message={`¿Estás seguro de que deseas eliminar la categoría "${categoriaAEliminar?.nombre}"? Esta acción no se puede deshacer.`}
        onConfirm={() => { confirmarEliminar(); }}
        onClose={() => setCategoriaAEliminar(null)}
        confirmText="Eliminar"
        variant="danger"
      />
    </div>
  );
};

export default ListaCategorias;
