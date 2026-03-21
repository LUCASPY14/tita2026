import React, { useState, useEffect } from 'react';
import { Search, Package, Edit, Eye, Trash2, ToggleLeft, ToggleRight, AlertTriangle } from 'lucide-react';
import { productosService } from '../../../services/productos.service';
import { Producto, Categoria } from '../../../types';
import { Card, ConfirmDialog, Skeleton, EmptyState } from '../../../components/common';
import { useDebounce } from '../../../hooks/useDebounce';
import toast from 'react-hot-toast';

interface ListaProductosProps {
  onEditar: (producto: Producto) => void;
  onVerDetalle: (producto: Producto) => void;
}

const ListaProductos: React.FC<ListaProductosProps> = ({ onEditar, onVerDetalle }) => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroActivo, setFiltroActivo] = useState<boolean | undefined>(true);
  const [filtroCategoria, setFiltroCategoria] = useState<number | undefined>();
  const [paginaActual, setPaginaActual] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [productoAEliminar, setProductoAEliminar] = useState<Producto | null>(null);

  const busquedaDebounced = useDebounce(busqueda);

  useEffect(() => {
    cargarCategorias();
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    cargarProductos();
  }, [busquedaDebounced, filtroActivo, filtroCategoria, paginaActual]);

  const cargarCategorias = async () => {
    try {
      const response = await productosService.getCategorias({ estado: true });
      setCategorias(response.results);
    } catch (error) {
      console.error('Error al cargar categorías:', error);
    }
  };

  const cargarProductos = async () => {
    setCargando(true);
    try {
      const params: any = {
        page: paginaActual,
        page_size: 10,
      };

      if (busquedaDebounced) params.search = busquedaDebounced;
      if (filtroActivo !== undefined) params.estado = filtroActivo;
      if (filtroCategoria) params.id_categoria = filtroCategoria;

      const response = await productosService.getProductos(params);
      setProductos(response.results);
      setTotalPaginas(Math.ceil(response.count / 10));
    } catch (error) {
      toast.error('Error al cargar productos');
      console.error('Error:', error);
    } finally {
      setCargando(false);
    }
  };

  const handleToggleEstado = async (producto: Producto) => {
    try {
      await productosService.toggleEstadoProducto(producto.id_producto, !producto.estado);
      toast.success(`Producto ${!producto.estado ? 'activado' : 'desactivado'} exitosamente`);
      cargarProductos();
    } catch (error) {
      toast.error('Error al cambiar estado del producto');
      console.error('Error:', error);
    }
  };

  const handleEliminar = (producto: Producto) => {
    setProductoAEliminar(producto);
  };

  const confirmarEliminar = async () => {
    if (!productoAEliminar) return;
    try {
      await productosService.eliminarProducto(productoAEliminar.id_producto);
      toast.success('Producto eliminado exitosamente');
      setProductoAEliminar(null);
      cargarProductos();
    } catch (error) {
      toast.error('Error al eliminar producto');
      console.error('Error:', error);
    }
  };

  const formatearMoneda = (valor?: number) => {
    if (valor === undefined || valor === null) return 'N/A';
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(valor);
  };

  if (cargando && productos.length === 0) {
    return (
      <Card>
        <Skeleton rows={8} cols={6} />
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filtros */}
      <Card>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          {/* Búsqueda */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por código o descripción..."
                value={busqueda}
                onChange={(e) => {
                  setBusqueda(e.target.value);
                  setPaginaActual(1);
                }}
                className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>
          </div>

          {/* Filtro Categoría */}
          <div>
            <select
              value={filtroCategoria || ''}
              onChange={(e) => {
                setFiltroCategoria(e.target.value ? Number(e.target.value) : undefined);
                setPaginaActual(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              <option value="">Todas las categorías</option>
              {categorias.map((categoria) => (
                <option key={categoria.id_categoria} value={categoria.id_categoria}>
                  {categoria.nombre}
                </option>
              ))}
            </select>
          </div>

          {/* Filtro Estado */}
          <div className="flex gap-2">
            <button
              onClick={() => {
                setFiltroActivo(true);
                setPaginaActual(1);
              }}
              className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                filtroActivo === true
                  ? 'border-green-600 bg-green-50 text-green-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Activos
            </button>
            <button
              onClick={() => {
                setFiltroActivo(false);
                setPaginaActual(1);
              }}
              className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                filtroActivo === false
                  ? 'border-red-600 bg-red-50 text-red-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              Inactivos
            </button>
          </div>
        </div>
      </Card>

      {/* Tabla de Productos */}
      <Card>
        {cargando ? (
          <Skeleton rows={8} cols={6} />
        ) : productos.length === 0 ? (
          <EmptyState
            icon={Package}
            title="No hay productos"
            description={busquedaDebounced || filtroActivo !== undefined || filtroCategoria !== undefined
              ? "No se encontraron productos con los filtros seleccionados"
              : "Comienza agregando tu primer producto al catálogo"}
            action={busquedaDebounced || filtroActivo !== undefined || filtroCategoria !== undefined ? {
              label: "Limpiar filtros",
              onClick: () => {
                setBusqueda('');
                setFiltroActivo(undefined);
                setFiltroCategoria(undefined);
              }
            } : undefined}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Código
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Producto
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Categoría
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Stock
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Precio
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                      Estado
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {productos.map((producto) => (
                    <tr key={producto.id_producto} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {producto.codigo_barra || 'N/A'}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {producto.descripcion}
                        </div>
                        {producto.requiere_reposicion && (
                          <div className="mt-1 flex items-center gap-1 text-xs text-amber-600">
                            <AlertTriangle className="h-3 w-3" />
                            Requiere reposición
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {producto.categoria_nombre || 'Sin categoría'}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {producto.stock_actual !== undefined ? (
                            <>
                              <span className={producto.stock_actual < producto.stock_minimo ? 'text-red-600' : ''}>
                                {producto.stock_actual}
                              </span>
                              {' / '}
                              <span className="text-gray-500">{producto.stock_minimo} mín.</span>
                            </>
                          ) : (
                            'N/A'
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {formatearMoneda(producto.precio)}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span
                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                            producto.estado
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {producto.estado ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => onVerDetalle(producto)}
                            className="rounded p-1 text-blue-600 hover:bg-blue-50"
                            title="Ver detalle"
                          >
                            <Eye className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => onEditar(producto)}
                            className="rounded p-1 text-amber-600 hover:bg-amber-50"
                            title="Editar"
                          >
                            <Edit className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleToggleEstado(producto)}
                            className={`rounded p-1 ${
                              producto.estado
                                ? 'text-gray-600 hover:bg-gray-50'
                                : 'text-green-600 hover:bg-green-50'
                            }`}
                            title={producto.estado ? 'Desactivar' : 'Activar'}
                          >
                            {producto.estado ? (
                              <ToggleRight className="h-5 w-5" />
                            ) : (
                              <ToggleLeft className="h-5 w-5" />
                            )}
                          </button>
                          <button
                            onClick={() => handleEliminar(producto)}
                            className="rounded p-1 text-red-600 hover:bg-red-50"
                            title="Eliminar"
                          >
                            <Trash2 className="h-5 w-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginación */}
            {totalPaginas > 1 && (
              <div className="mt-4 flex items-center justify-between border-t border-gray-200 px-4 py-3">
                <div className="text-sm text-gray-700">
                  Página {paginaActual} de {totalPaginas}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPaginaActual((prev) => Math.max(1, prev - 1))}
                    disabled={paginaActual === 1}
                    className="rounded-lg border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPaginaActual((prev) => Math.min(totalPaginas, prev + 1))}
                    disabled={paginaActual === totalPaginas}
                    className="rounded-lg border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>

      <ConfirmDialog
        isOpen={!!productoAEliminar}
        onClose={() => setProductoAEliminar(null)}
        onConfirm={confirmarEliminar}
        title="Eliminar producto"
        message={productoAEliminar ? `¿Está seguro de eliminar el producto "${productoAEliminar.descripcion}"? Esta acción no se puede deshacer.` : ''}
        confirmText="Eliminar"
      />
    </div>
  );
};

export default ListaProductos;
