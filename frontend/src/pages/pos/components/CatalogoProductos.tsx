import React, {useState, useEffect } from 'react';
import { Search, Plus, Package } from 'lucide-react';
import { Input, Button, Select, Spinner, Badge, EmptyState } from '../../../components/common';
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

  const busquedaDebounced = useDebounce(busqueda);

  useEffect(() => {
    cargarCategorias();
  }, []);

  useEffect(() => {
    cargarProductos();
  }, [busquedaDebounced, categoriaSeleccionada]);

  const cargarCategorias = async () => {
    try {
      const response = await posService.getCategorias({
        activo: true,
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
        activo: true,
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
    toast.success(`${producto.descripcion} agregado al carrito`);
  };

  const formatearPrecio = (precio?: number): string => {
    if (!precio) return 'Gs. 0';
    return `Gs. ${precio.toLocaleString('es-PY')}`;
  };

  return (
    <div className="space-y-4">
      {/* Filtros */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <Input
          type="text"
          placeholder="Buscar por nombre o código..."
          value={busqueda}
          onChange={(e) => setBusqueda(e.target.value)}
          leftIcon={<Search className="h-5 w-5 text-gray-400" />}
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
          {productos.map((producto) => (
            <div
              key={producto.id_producto}
              className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 transition-shadow hover:shadow-md"
            >
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{producto.descripcion}</h4>
                    {producto.codigo_barra && (
                      <p className="mt-1 text-xs text-gray-500">Código: {producto.codigo_barra}</p>
                    )}
                    <div className="mt-1">{getStockBadge(producto)}</div>
                  </div>
                  {producto.activo && (
                    <Badge variant="success" size="sm">
                      Activo
                    </Badge>
                  )}
                </div>
                <p className="mt-2 text-lg font-bold text-amber-600">
                  {formatearPrecio(producto.precio)}
                </p>
              </div>

              <Button
                variant="primary"
                onClick={() => handleAgregar(producto)}
                leftIcon={<Plus className="h-4 w-4" />}
                className="ml-4"
                disabled={producto.stock_actual !== undefined && producto.stock_actual !== null && producto.stock_actual <= 0 && !producto.permite_stock_negativo}
              >
                Agregar
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CatalogoProductos;
