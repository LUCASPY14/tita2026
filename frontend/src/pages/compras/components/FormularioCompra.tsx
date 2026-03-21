import React, { useState, useEffect } from 'react';
import { X, Save, Plus, Trash2 } from 'lucide-react';
import { comprasService } from '../../../services/compras.service';
import { productosService } from '../../../services/productos.service';
import { posService } from '../../../services/pos.service';
import { Compra, Proveedor, Producto, CompraData } from '../../../types';
import { Card, Spinner } from '../../../components/common';
import toast from 'react-hot-toast';

interface FormularioCompraProps {
  compra?: Compra | null;
  onGuardado: () => void;
  onCancelar: () => void;
}

interface DetalleForm {
  id_producto: number;
  cantidad: number;
  costo_unitario: number;
  producto_nombre?: string;
}

const FormularioCompra: React.FC<FormularioCompraProps> = ({
  compra,
  onGuardado,
  onCancelar,
}) => {
  const [formData, setFormData] = useState({
    fecha: new Date().toISOString().split('T')[0],
    id_proveedor: 0,
    tipo_pago: 'Contado' as 'Contado' | 'Crédito',
    id_medio_pago: null as number | null,
    nro_factura: '',
    observaciones: '',
  });

  const [detalles, setDetalles] = useState<DetalleForm[]>([]);
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [mediosPago, setMediosPago] = useState<any[]>([]);
  const [productoSeleccionado, setProductoSeleccionado] = useState<number>(0);
  const [cantidadNueva, setCantidadNueva] = useState<string>('1');
  const [costoNuevo, setCostoNuevo] = useState<string>('');
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [guardando, setGuardando] = useState(false);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarDatosIniciales();
  }, []);

  useEffect(() => {
    if (compra) {
      setFormData({
        fecha: compra.fecha.split('T')[0],
        id_proveedor: compra.id_proveedor,
        tipo_pago: (compra.tipo_pago || 'Contado') as 'Contado' | 'Crédito',
        id_medio_pago: compra.id_medio_pago || null,
        nro_factura: compra.nro_factura || '',
        observaciones: compra.observaciones || '',
      });

      if (compra.detalles) {
        setDetalles(
          compra.detalles.map((d) => ({
            id_producto: d.id_producto,
            cantidad: d.cantidad,
            costo_unitario: d.costo_unitario,
            producto_nombre: d.producto_nombre,
          }))
        );
      }
    }
  }, [compra]);

  const cargarDatosIniciales = async () => {
    try {
      const [responseProveedores, responseProductos, responseMediosPago] = await Promise.all([
        comprasService.getProveedores({ estado: true }),
        productosService.getProductos({ estado: true }),
        posService.getMediosPago(),
      ]);

      setProveedores(responseProveedores.results);
      setProductos(responseProductos.results);
      setMediosPago(responseMediosPago);
    } catch (error) {
      toast.error('Error al cargar datos iniciales');
      console.error('Error:', error);
    } finally {
      setCargando(false);
    }
  };

  const agregarDetalle = () => {
    if (productoSeleccionado === 0) {
      toast.error('Seleccione un producto');
      return;
    }

    const cantidad = parseFloat(cantidadNueva);
    const costo = parseFloat(costoNuevo);

    if (isNaN(cantidad) || cantidad <= 0) {
      toast.error('Ingrese una cantidad válida');
      return;
    }

    if (isNaN(costo) || costo <= 0) {
      toast.error('Ingrese un costo válido');
      return;
    }

    // Verificar si el producto ya existe
    if (detalles.some((d) => d.id_producto === productoSeleccionado)) {
      toast.error('El producto ya está en la lista');
      return;
    }

    const producto = productos.find((p) => p.id_producto === productoSeleccionado);

    setDetalles([
      ...detalles,
      {
        id_producto: productoSeleccionado,
        cantidad,
        costo_unitario: costo,
        producto_nombre: producto?.descripcion,
      },
    ]);

    // Limpiar formulario de detalle
    setProductoSeleccionado(0);
    setCantidadNueva('1');
    setCostoNuevo('');
  };

  const eliminarDetalle = (index: number) => {
    setDetalles(detalles.filter((_, i) => i !== index));
  };

  const calcularSubtotal = (detalle: DetalleForm) => {
    return detalle.cantidad * detalle.costo_unitario;
  };

  const calcularTotal = () => {
    return detalles.reduce((sum, d) => sum + calcularSubtotal(d), 0);
  };

  const validarFormulario = (): boolean => {
    const nuevosErrores: Record<string, string> = {};

    if (formData.id_proveedor === 0) {
      nuevosErrores.id_proveedor = 'Debe seleccionar un proveedor';
    }

    if (formData.tipo_pago === 'Contado' && !formData.id_medio_pago) {
      nuevosErrores.id_medio_pago = 'Debe seleccionar un medio de pago para compras al contado';
    }

    if (detalles.length === 0) {
      nuevosErrores.detalles = 'Debe agregar al menos un producto';
    }

    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;

    setFormData((prev) => {
      const newData = {
        ...prev,
        [name]: name === 'id_proveedor' ? Number(value) : value,
      };

      // Si cambia a crédito, limpiar medio de pago
      if (name === 'tipo_pago' && value === 'Crédito') {
        newData.id_medio_pago = null;
      }

      return newData;
    });

    // Limpiar error del campo modificado
    if (errores[name]) {
      setErrores((prev) => {
        const nuevosErrores = { ...prev };
        delete nuevosErrores[name];
        return nuevosErrores;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validarFormulario()) {
      toast.error('Por favor, corrija los errores en el formulario');
      return;
    }

    setGuardando(true);

    try {
      const data: CompraData = {
        ...formData,
        // Si es a crédito, asegurar que id_medio_pago sea null
        id_medio_pago: formData.tipo_pago === 'Crédito' ? null : formData.id_medio_pago,
        detalles: detalles.map((d) => ({
          id_producto: d.id_producto,
          cantidad: d.cantidad,
          costo_unitario: d.costo_unitario,
        })),
      };

      if (compra) {
        await comprasService.actualizarCompra(compra.id_compra, data);
        toast.success('Compra actualizada exitosamente');
      } else {
        await comprasService.crearCompra(data);
        toast.success('Compra creada exitosamente');
      }
      onGuardado();
    } catch (error: any) {
      if (error.response?.data) {
        const apiErrors = error.response.data;
        const nuevosErrores: Record<string, string> = {};

        Object.keys(apiErrors).forEach((key) => {
          if (Array.isArray(apiErrors[key])) {
            nuevosErrores[key] = apiErrors[key][0];
          } else {
            nuevosErrores[key] = apiErrors[key];
          }
        });

        setErrores(nuevosErrores);
      }
      toast.error(compra ? 'Error al actualizar compra' : 'Error al crear compra');
      console.error('Error:', error);
    } finally {
      setGuardando(false);
    }
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(valor);
  };

  if (cargando) {
    return (
      <Card>
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            {compra ? 'Editar Compra' : 'Nueva Compra'}
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            {compra
              ? 'Modifica la información de la compra'
              : 'Complete los datos de la nueva compra'}
          </p>
        </div>
      </div>

      {/* Formulario */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Sección 1: Información General */}
        <Card title="Información General">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {/* Fecha */}
            <div>
              <label htmlFor="fecha" className="block text-sm font-medium text-gray-700">
                Fecha <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                id="fecha"
                name="fecha"
                value={formData.fecha}
                onChange={handleChange}
                required
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>

            {/* Proveedor */}
            <div>
              <label htmlFor="id_proveedor" className="block text-sm font-medium text-gray-700">
                Proveedor <span className="text-red-500">*</span>
              </label>
              <select
                id="id_proveedor"
                name="id_proveedor"
                value={formData.id_proveedor}
                onChange={handleChange}
                required
                className={`mt-1 block w-full rounded-lg border ${
                  errores.id_proveedor ? 'border-red-500' : 'border-gray-300'
                } px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500`}
              >
                <option value={0}>Seleccione un proveedor</option>
                {proveedores.map((proveedor) => (
                  <option key={proveedor.id_proveedor} value={proveedor.id_proveedor}>
                    {proveedor.razon_social}
                  </option>
                ))}
              </select>
              {errores.id_proveedor && (
                <p className="mt-1 text-sm text-red-600">{errores.id_proveedor}</p>
              )}
            </div>

            {/* Tipo de Pago */}
            <div>
              <label htmlFor="tipo_pago" className="block text-sm font-medium text-gray-700">
                Tipo de Pago <span className="text-red-500">*</span>
              </label>
              <select
                id="tipo_pago"
                name="tipo_pago"
                value={formData.tipo_pago}
                onChange={handleChange}
                required
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              >
                <option value="Contado">Contado</option>
                <option value="Crédito">Crédito</option>
              </select>
            </div>

            {/* Medio de Pago - Solo si es Contado */}
            {formData.tipo_pago === 'Contado' && (
              <div>
                <label htmlFor="id_medio_pago" className="block text-sm font-medium text-gray-700">
                  Medio de Pago <span className="text-red-500">*</span>
                </label>
                <select
                  id="id_medio_pago"
                  name="id_medio_pago"
                  value={formData.id_medio_pago || ''}
                  onChange={(e) => {
                    const value = e.target.value ? Number(e.target.value) : null;
                    setFormData((prev) => ({
                      ...prev,
                      id_medio_pago: value,
                    }));
                  }}
                  required={formData.tipo_pago === 'Contado'}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="">Seleccione medio de pago</option>
                  {mediosPago.map((medio) => (
                    <option key={medio.id_medio_pago} value={medio.id_medio_pago}>
                      {medio.descripcion}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Número de Factura */}
            <div>
              <label htmlFor="nro_factura" className="block text-sm font-medium text-gray-700">
                Número de Factura
              </label>
              <input
                type="text"
                id="nro_factura"
                name="nro_factura"
                value={formData.nro_factura}
                onChange={handleChange}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="001-001-0000001"
              />
            </div>

            {/* Observaciones */}
            <div className="md:col-span-3">
              <label htmlFor="observaciones" className="block text-sm font-medium text-gray-700">
                Observaciones
              </label>
              <textarea
                id="observaciones"
                name="observaciones"
                value={formData.observaciones}
                onChange={handleChange}
                rows={3}
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="Notas adicionales sobre la compra..."
              />
            </div>
          </div>
        </Card>

        {/* Sección 2: Productos */}
        <Card title="Productos">
          {/* Agregar Producto */}
          <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50 p-4">
            <h4 className="mb-3 text-sm font-medium text-gray-900">Agregar Producto</h4>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
              <div className="md:col-span-2">
                <select
                  value={productoSeleccionado}
                  onChange={(e) => setProductoSeleccionado(Number(e.target.value))}
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value={0}>Seleccione un producto</option>
                  {productos.map((producto) => (
                    <option key={producto.id_producto} value={producto.id_producto}>
                      {producto.descripcion}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <input
                  type="number"
                  value={cantidadNueva}
                  onChange={(e) => setCantidadNueva(e.target.value)}
                  placeholder="Cantidad"
                  step="0.001"
                  min="0"
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>
              <div>
                <input
                  type="number"
                  value={costoNuevo}
                  onChange={(e) => setCostoNuevo(e.target.value)}
                  placeholder="Costo unitario"
                  step="1"
                  min="0"
                  className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>
              <div>
                <button
                  type="button"
                  onClick={agregarDetalle}
                  className="w-full rounded-lg bg-amber-600 px-4 py-2 text-sm text-white hover:bg-amber-700"
                >
                  <Plus className="mx-auto h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          {errores.detalles && (
            <div className="mb-4 rounded-lg bg-red-50 p-3">
              <p className="text-sm text-red-600">{errores.detalles}</p>
            </div>
          )}

          {/* Tabla de Productos */}
          {detalles.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">
                      Producto
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
                      Cantidad
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
                      Costo Unit.
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">
                      Subtotal
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase text-gray-500">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {detalles.map((detalle, index) => (
                    <tr key={index}>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {detalle.producto_nombre || `Producto #${detalle.id_producto}`}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-gray-900">
                        {detalle.cantidad}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-gray-900">
                        {formatearMoneda(detalle.costo_unitario)}
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-semibold text-gray-900">
                        {formatearMoneda(calcularSubtotal(detalle))}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          type="button"
                          onClick={() => eliminarDetalle(index)}
                          className="rounded p-1 text-red-600 hover:bg-red-50"
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t-2 border-gray-300 bg-gray-50">
                    <td colSpan={3} className="px-4 py-3 text-right text-sm font-bold text-gray-900">
                      TOTAL:
                    </td>
                    <td className="px-4 py-3 text-right text-lg font-bold text-amber-600">
                      {formatearMoneda(calcularTotal())}
                    </td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-gray-500">
              No hay productos agregados. Use el formulario arriba para agregar productos.
            </div>
          )}
        </Card>

        {/* Botones de Acción */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancelar}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <X className="h-4 w-4" />
            Cancelar
          </button>
          <button
            type="submit"
            disabled={guardando || detalles.length === 0}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {guardando ? (
              <>
                <Spinner size="sm" />
                Guardando...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                {compra ? 'Actualizar' : 'Crear'} Compra
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default FormularioCompra;
