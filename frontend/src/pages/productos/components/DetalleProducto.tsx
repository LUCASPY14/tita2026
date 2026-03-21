import React, { useState, useEffect } from 'react';
import { ArrowLeft, Edit, Package, Tag, DollarSign, TrendingUp, AlertCircle, Plus, X, Save } from 'lucide-react';
import { productosService } from '../../../services/productos.service';
import { Producto, PrecioPorLista, ListaPrecio } from '../../../types';
import { Card, Spinner } from '../../../components/common';
import toast from 'react-hot-toast';

interface DetalleProductoProps {
  producto: Producto;
  onEditar: (producto: Producto) => void;
  onVolver: () => void;
}

const DetalleProducto: React.FC<DetalleProductoProps> = ({ producto, onEditar, onVolver }) => {
  const [precios, setPrecios] = useState<PrecioPorLista[]>([]);
  const [listasDisponibles, setListasDisponibles] = useState<ListaPrecio[]>([]);
  const [cargandoPrecios, setCargandoPrecios] = useState(true);
  const [editandoPrecio, setEditandoPrecio] = useState<number | null>(null);
  const [nuevoPrecio, setNuevoPrecio] = useState<string>('');
  const [mostrarFormNuevo, setMostrarFormNuevo] = useState(false);
  const [formNuevo, setFormNuevo] = useState({ id_lista: '', precio_unitario: '' });
  const [guardandoNuevo, setGuardandoNuevo] = useState(false);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    cargarDatos();
  }, [producto.id_producto]);

  const cargarDatos = async () => {
    setCargandoPrecios(true);
    try {
      const [datosPrecios, datosListas] = await Promise.all([
        productosService.getPreciosPorProducto(producto.id_producto),
        productosService.getListasPrecios(),
      ]);
      setPrecios(datosPrecios);
      setListasDisponibles(datosListas);
    } catch (error) {
      console.error('Error al cargar precios:', error);
    } finally {
      setCargandoPrecios(false);
    }
  };

  // Listas que aún no tienen precio para este producto
  const listasConPrecio = new Set(precios.map((p) => p.id_lista));
  const listasSinPrecio = listasDisponibles.filter(
    (l) => !listasConPrecio.has(l.id_lista) && l.estado
  );

  const handleActualizarPrecio = async (idPrecio: number) => {
    const precioNumerico = parseFloat(nuevoPrecio);
    if (isNaN(precioNumerico) || precioNumerico <= 0) {
      toast.error('Ingrese un precio mayor a 0');
      return;
    }
    try {
      await productosService.actualizarPrecio(idPrecio, precioNumerico);
      toast.success('Precio actualizado exitosamente');
      setEditandoPrecio(null);
      setNuevoPrecio('');
      cargarDatos();
    } catch (error) {
      toast.error('Error al actualizar precio');
      console.error('Error:', error);
    }
  };

  const handleCrearPrecio = async () => {
    const precioNumerico = parseFloat(formNuevo.precio_unitario);
    if (!formNuevo.id_lista) {
      toast.error('Seleccione una lista de precios');
      return;
    }
    if (isNaN(precioNumerico) || precioNumerico <= 0) {
      toast.error('Ingrese un precio mayor a 0');
      return;
    }
    setGuardandoNuevo(true);
    try {
      await productosService.crearPrecio({
        id_producto: producto.id_producto,
        id_lista: parseInt(formNuevo.id_lista),
        precio_unitario: precioNumerico,
      });
      toast.success('Precio creado exitosamente');
      setMostrarFormNuevo(false);
      setFormNuevo({ id_lista: '', precio_unitario: '' });
      cargarDatos();
    } catch (error: any) {
      const msg = error.response?.data?.non_field_errors?.[0] ||
                  error.response?.data?.detail ||
                  'Error al crear precio';
      toast.error(msg);
    } finally {
      setGuardandoNuevo(false);
    }
  };

  const iniciarEdicionPrecio = (precio: PrecioPorLista) => {
    setEditandoPrecio(precio.id_precio);
    setNuevoPrecio(precio.precio_unitario.toString());
    setMostrarFormNuevo(false);
  };

  const cancelarEdicion = () => {
    setEditandoPrecio(null);
    setNuevoPrecio('');
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(valor);
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-PY', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onVolver}
            className="rounded-lg border border-gray-300 p-2 hover:bg-gray-50"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Detalle del Producto</h2>
            <p className="mt-1 text-sm text-gray-600">
              Información completa y gestión de precios
            </p>
          </div>
        </div>
        <button
          onClick={() => onEditar(producto)}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
        >
          <Edit className="h-4 w-4" />
          Editar
        </button>
      </div>

      {/* Grid Principal */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Columna Izquierda - Información del Producto */}
        <div className="space-y-6 lg:col-span-2">
          {/* Card Info Principal */}
          <Card title="Información del Producto">
            <div className="space-y-4">
              <div className="flex items-start gap-4 border-b border-gray-200 pb-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
                  <Package className="h-8 w-8 text-amber-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900">{producto.descripcion}</h3>
                  <p className="mt-1 text-sm text-gray-600">
                    Código: {producto.codigo_barra || 'No asignado'}
                  </p>
                  <div className="mt-2">
                    <span
                      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                        producto.estado
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {producto.estado ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Categoría</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {producto.categoria_nombre || 'Sin categoría'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Unidad de Medida</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {producto.unidad_medida_nombre
                      ? `${producto.unidad_medida_nombre} (${producto.unidad_medida_abreviatura})`
                      : 'No especificada'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Stock Mínimo</p>
                  <p className="mt-1 text-sm text-gray-900">{producto.stock_minimo}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Stock Actual</p>
                  <p className="mt-1 text-sm font-semibold text-gray-900">
                    {producto.stock_actual !== undefined ? producto.stock_actual : 'N/A'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 rounded-lg bg-gray-50 p-3">
                <AlertCircle className="h-5 w-5 text-gray-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {producto.permite_stock_negativo
                      ? 'Permite venta sin stock'
                      : 'No permite venta sin stock'}
                  </p>
                  <p className="text-xs text-gray-500">
                    {producto.requiere_reposicion
                      ? '⚠️ El producto requiere reposición'
                      : 'Stock dentro de los niveles normales'}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Card Precios por Lista */}
          <Card>
            {/* Header de la card con botón agregar */}
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold text-gray-900">Precios por Lista</h3>
              {!cargandoPrecios && listasSinPrecio.length > 0 && (
                <button
                  onClick={() => {
                    setMostrarFormNuevo(!mostrarFormNuevo);
                    cancelarEdicion();
                    setFormNuevo({ id_lista: '', precio_unitario: '' });
                  }}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-3 py-1.5 text-xs font-medium text-white hover:bg-amber-600"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Agregar Precio
                </button>
              )}
            </div>

            {/* Formulario nuevo precio */}
            {mostrarFormNuevo && (
              <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
                <h4 className="mb-3 text-sm font-semibold text-amber-800">Nuevo Precio</h4>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Lista de Precios <span className="text-red-500">*</span>
                    </label>
                    <select
                      value={formNuevo.id_lista}
                      onChange={(e) => setFormNuevo((p) => ({ ...p, id_lista: e.target.value }))}
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                    >
                      <option value="">Seleccione...</option>
                      {listasSinPrecio.map((l) => (
                        <option key={l.id_lista} value={l.id_lista}>
                          {l.nombre_lista}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">
                      Precio Unitario (Gs.) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={formNuevo.precio_unitario}
                      onChange={(e) =>
                        setFormNuevo((p) => ({ ...p, precio_unitario: e.target.value }))
                      }
                      placeholder="Ej: 5000"
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleCrearPrecio();
                        if (e.key === 'Escape') setMostrarFormNuevo(false);
                      }}
                    />
                  </div>
                  <div className="flex items-end gap-2">
                    <button
                      onClick={handleCrearPrecio}
                      disabled={guardandoNuevo}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
                    >
                      <Save className="h-4 w-4" />
                      {guardandoNuevo ? 'Guardando...' : 'Guardar'}
                    </button>
                    <button
                      onClick={() => setMostrarFormNuevo(false)}
                      className="rounded-lg border border-gray-300 p-2 hover:bg-gray-100"
                    >
                      <X className="h-4 w-4 text-gray-500" />
                    </button>
                  </div>
                </div>
                <p className="mt-2 text-xs text-amber-700">
                  💡 El precio de venta debe ser mayor al costo de compra del producto.
                </p>
              </div>
            )}

            {cargandoPrecios ? (
              <div className="flex items-center justify-center py-8">
                <Spinner size="md" />
              </div>
            ) : precios.length === 0 && !mostrarFormNuevo ? (
              <div className="py-8 text-center">
                <Tag className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-4 text-sm font-medium text-gray-900">
                  No hay precios configurados
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Este producto aún no tiene precios asignados en ninguna lista
                </p>
                {listasSinPrecio.length > 0 && (
                  <button
                    onClick={() => setMostrarFormNuevo(true)}
                    className="mt-4 inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600"
                  >
                    <Plus className="h-4 w-4" />
                    Agregar primer precio
                  </button>
                )}
              </div>
            ) : precios.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Lista de Precios
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Precio Unitario
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Vigencia
                      </th>
                      <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {precios.map((precio) => (
                      <tr key={precio.id_precio} className="hover:bg-gray-50">
                        <td className="px-4 py-4">
                          <div className="text-sm font-medium text-gray-900">
                            {precio.lista_nombre || `Lista #${precio.id_lista}`}
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          {editandoPrecio === precio.id_precio ? (
                            <input
                              type="number"
                              min="1"
                              value={nuevoPrecio}
                              onChange={(e) => setNuevoPrecio(e.target.value)}
                              className="w-36 rounded border border-amber-400 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                              autoFocus
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleActualizarPrecio(precio.id_precio);
                                else if (e.key === 'Escape') cancelarEdicion();
                              }}
                            />
                          ) : (
                            <div className="text-sm font-semibold text-gray-900">
                              {formatearMoneda(precio.precio_unitario)}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-4">
                          <div className="text-sm text-gray-500">
                            {formatearFecha(precio.fecha_vigencia)}
                          </div>
                        </td>
                        <td className="px-4 py-4 text-center">
                          {editandoPrecio === precio.id_precio ? (
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => handleActualizarPrecio(precio.id_precio)}
                                className="rounded px-2 py-1 text-xs font-medium text-green-600 hover:bg-green-50"
                              >
                                Guardar
                              </button>
                              <button
                                onClick={cancelarEdicion}
                                className="rounded px-2 py-1 text-xs font-medium text-gray-500 hover:bg-gray-100"
                              >
                                Cancelar
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => iniciarEdicionPrecio(precio)}
                              className="rounded p-1 text-amber-600 hover:bg-amber-50"
                              title="Editar precio"
                            >
                              <Edit className="h-4 w-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </Card>
        </div>

        {/* Columna Derecha - Estadísticas */}
        <div className="space-y-6">
          {/* Card Stock */}
          <Card>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-blue-100 p-3">
                  <Package className="h-6 w-6 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Stock Actual</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {producto.stock_actual !== undefined ? producto.stock_actual : 'N/A'}
                  </p>
                </div>
              </div>
              <div className="border-t border-gray-200 pt-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Stock Mínimo:</span>
                  <span className="font-medium text-gray-900">{producto.stock_minimo}</span>
                </div>
                {producto.stock_actual !== undefined && (
                  <div className="mt-2">
                    <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                      <div
                        className={`h-full ${
                          producto.stock_actual < producto.stock_minimo
                            ? 'bg-red-600'
                            : 'bg-green-600'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            (producto.stock_actual / (producto.stock_minimo * 2 || 1)) * 100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Card Resumen Precios */}
          <Card>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-green-100 p-3">
                  <DollarSign className="h-6 w-6 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Precio Promedio</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {precios.length > 0
                      ? formatearMoneda(
                          precios.reduce((sum, p) => sum + p.precio_unitario, 0) / precios.length
                        )
                      : 'N/A'}
                  </p>
                </div>
              </div>
              <div className="border-t border-gray-200 pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Listas configuradas:</span>
                  <span className={`font-medium ${precios.length === 0 ? 'text-red-600' : 'text-gray-900'}`}>
                    {precios.length} / {listasDisponibles.length}
                  </span>
                </div>
                {precios.length > 0 && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Precio más bajo:</span>
                      <span className="font-medium text-gray-900">
                        {formatearMoneda(Math.min(...precios.map((p) => p.precio_unitario)))}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Precio más alto:</span>
                      <span className="font-medium text-gray-900">
                        {formatearMoneda(Math.max(...precios.map((p) => p.precio_unitario)))}
                      </span>
                    </div>
                  </>
                )}
                {precios.length === 0 && (
                  <p className="text-xs text-red-600">
                    ⚠️ Sin precio: el producto no podrá venderse en el POS
                  </p>
                )}
              </div>
            </div>
          </Card>

          {/* Card Estado */}
          <Card>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-amber-100 p-3">
                  <TrendingUp className="h-6 w-6 text-amber-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Estado del Producto</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {producto.estado ? '✓ Activo' : '✗ Inactivo'}
                  </p>
                </div>
              </div>
              <div className="space-y-2 border-t border-gray-200 pt-4 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Stock negativo:</span>
                  <span className="font-medium text-gray-900">
                    {producto.permite_stock_negativo ? 'Sí' : 'No'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Requiere reposición:</span>
                  <span
                    className={`font-medium ${
                      producto.requiere_reposicion ? 'text-red-600' : 'text-green-600'
                    }`}
                  >
                    {producto.requiere_reposicion ? 'Sí' : 'No'}
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DetalleProducto;

