import React, {useState, useEffect, useRef, useCallback } from 'react';
import { Search, Package, Plus } from 'lucide-react';
import { Input, Select, Spinner, Badge, EmptyState } from '../../../components/common';
import { posService } from '../../../services/pos.service';
import type { Producto, Categoria } from '../../../types';
import { useDebounce } from '../../../hooks/useDebounce';
import toast from 'react-hot-toast';

interface CatalogoProductosProps {
  onAgregarProducto: (producto: Producto, cantidad: number) => void;
}

const CatalogoProductos: React.FC<CatalogoProductosProps> = ({ onAgregarProducto }) => {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [busqueda, setBusqueda] = useState('');
  const [categoriaSeleccionada, setCategoriaSeleccionada] = useState<string>('');
  const [cargando, setCargando] = useState(true);
  const [cargandoCategorias, setCargandoCategorias] = useState(true);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const busquedaDebounced = useDebounce(busqueda);

  useEffect(() => {
    cargarCategorias();
  }, []);

  useEffect(() => {
    cargarProductos();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busquedaDebounced, categoriaSeleccionada]);

  const cargarCategorias = async () => {
    try {
      const response = await posService.getCategorias({
        estado: true,
        page_size: 100,
      });
      setCategorias(response.results || []);
    } catch (error) {
      console.error('Error al cargar categorías:', error);
    } finally {
      setCargandoCategorias(false);
    }
  };

  const cargarProductos = async () => {
    setCargando(true);
    try {
      const params: any = {
        estado: true,
        es_servicio: false,
        page_size: 50,
      };

      if (busquedaDebounced) {
        params.search = busquedaDebounced;
      }

      if (categoriaSeleccionada) {
        params.id_categoria = parseInt(categoriaSeleccionada);
      }

      const response = await posService.getProductos(params);
      setProductos(response.results || []);
    } catch (error) {
      console.error('Error al cargar productos:', error);
      toast.error('Error al cargar productos');
    } finally {
      setCargando(false);
    }
  };

  const getStockBadge = (producto: Producto) => {
    if (producto.stock_actual === null || producto.stock_actual === undefined) return null;
    const stock = producto.stock_actual;
    if (stock <= 0) {
      return <span className="ml-1 inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">Sin stock</span>;
    }
    if (producto.requiere_reposicion) {
      return <span className="ml-1 inline-flex items-center rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">Stock bajo: {stock}</span>;
    }
    return <span className="ml-1 inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-semibold text-green-700">Stock: {stock}</span>;
  };

  const handleAgregar = (producto: Producto) => {
    onAgregarProducto(producto, 1);
    toast.success(`${producto.descripcion} agregado`, { duration: 1200, position: 'bottom-right' });
  };

  // Enter en el buscador: búsqueda inmediata + auto-agrega si hay 1 resultado
  const handleSearchKeyDown = useCallback(async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const query = busqueda.trim();
    if (!query) return;

    try {
      const response = await posService.getProductos({
        estado: true,
        es_servicio: false,
        page_size: 10,
        search: query,
        ...(categoriaSeleccionada ? { id_categoria: parseInt(categoriaSeleccionada) } : {}),
      });
      const resultados: Producto[] = response.results || [];

      if (resultados.length === 1) {
        const p = resultados[0];
        if (p.stock_actual !== undefined && p.stock_actual !== null && p.stock_actual <= 0 && !p.permite_stock_negativo) {
          toast.error(`Sin stock: ${p.descripcion}`);
        } else {
          handleAgregar(p);
          setBusqueda('');
          setProductos([]);
          setTimeout(() => searchInputRef.current?.focus(), 50);
        }
      } else if (resultados.length === 0) {
        toast.error('Producto no encontrado');
      } else {
        // Varios resultados: mostrar lista para selección manual
        setProductos(resultados);
      }
    } catch {
      toast.error('Error al buscar producto');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busqueda, categoriaSeleccionada]);

  const formatearPrecio = (precio?: number): string => {
    if (!precio) return 'Gs. 0';
    return `Gs. ${precio.toLocaleString('es-PY')}`;
  };

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Input
          ref={searchInputRef}
          type="text"
          placeholder="Escanea código o busca por nombre... (Enter para agregar)"
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          onKeyDown={handleSearchKeyDown}
          leftIcon={<Search className="h-5 w-5 text-gray-400" />}
          autoFocus
        />

        <Select
          value={categoriaSeleccionada}
          onChange={(e) => setCategoriaSeleccionada(e.target.value)}
          disabled={cargandoCategorias}
          placeholder="Todas las categorías"
          options={[
            { value: '', label: 'Todas las categorías' },
            ...categorias.map((categoria) => ({
              value: categoria.id_categoria.toString(),
              label: categoria.nombre,
            })),
          ]}
        />
      </div>

      {/* Grid de Productos */}
      {cargando ? (
        <div className="flex items-center justify-center py-12">
          <Spinner />
          <span className="ml-2 text-gray-600">Cargando productos...</span>
        </div>
      ) : productos.length === 0 ? (
        <EmptyState
          icon={Package}
          title={busqueda || categoriaSeleccionada ? 'No se encontraron productos' : 'No hay productos disponibles'}
          description={busqueda || categoriaSeleccionada ? "Intenta con otros filtros" : "Agrega productos al catálogo para comenzar"}
          action={busqueda || categoriaSeleccionada ? {
            label: "Limpiar filtros",
            onClick: () => {
              setBusqueda('');
              setCategoriaSeleccionada('');
            }
          } : undefined}
          size="sm"
        />
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {productos.map((producto) => {
            const sinStock = producto.stock_actual !== undefined && producto.stock_actual !== null && producto.stock_actual <= 0 && !producto.permite_stock_negativo;
            return (
              <button
                key={producto.id_producto}
                type="button"
                onClick={() => !sinStock && handleAgregar(producto)}
                disabled={sinStock}
                className={`group w-full text-left flex items-center justify-between rounded-lg border p-4 transition-all
                  ${sinStock
                    ? 'border-gray-200 bg-gray-50 opacity-50 cursor-not-allowed'
                    : 'border-gray-200 bg-white hover:border-amber-400 hover:bg-amber-50 hover:shadow-md active:scale-[0.98] cursor-pointer'
                  }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-gray-900 truncate">{producto.descripcion}</h4>
                      {producto.codigo_barra && (
                        <p className="mt-0.5 text-xs text-gray-500">Código: {producto.codigo_barra}</p>
                      )}
                      <div className="mt-1">{getStockBadge(producto)}</div>
                    </div>
                    {producto.estado && (
                      <Badge variant="success" size="sm">Activo</Badge>
                    )}
                  </div>
                  <p className="mt-2 text-lg font-bold text-amber-600">
                    {formatearPrecio(producto.precio)}
                  </p>
                </div>

                {/* Indicador visual de agregar */}
                <div className={`ml-4 flex-shrink-0 flex h-9 w-9 items-center justify-center rounded-full transition-colors
                  ${sinStock ? 'bg-gray-200 text-gray-400' : 'bg-gray-100 text-gray-400 group-hover:bg-amber-500 group-hover:text-white'}`}>
                  <Plus className="h-5 w-5" />
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default CatalogoProductos;
