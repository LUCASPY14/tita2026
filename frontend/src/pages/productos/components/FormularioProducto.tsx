import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import { productosService, ProductoData } from '../../../services/productos.service';
import { Producto, Categoria, UnidadMedida } from '../../../types';
import { Card, Spinner } from '../../../components/common';
import toast from 'react-hot-toast';

interface FormularioProductoProps {
  producto?: Producto | null;
  onGuardado: () => void;
  onCancelar: () => void;
}

const FormularioProducto: React.FC<FormularioProductoProps> = ({
  producto,
  onGuardado,
  onCancelar,
}) => {
  const [formData, setFormData] = useState<ProductoData>({
    codigo_barra: '',
    descripcion: '',
    stock_minimo: 0,
    permite_stock_negativo: false,
    activo: true,
    id_categoria: 0,
    id_impuesto: 1, // IVA 10% por defecto
    id_unidad_medida: undefined,
  });

  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [unidades, setUnidades] = useState<UnidadMedida[]>([]);
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [guardando, setGuardando] = useState(false);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    cargarDatosIniciales();
  }, []);

  useEffect(() => {
    if (producto) {
      setFormData({
        codigo_barra: producto.codigo_barra || '',
        descripcion: producto.descripcion,
        stock_minimo: producto.stock_minimo,
        permite_stock_negativo: producto.permite_stock_negativo,
        activo: producto.activo,
        id_categoria: producto.id_categoria,
        id_impuesto: producto.id_impuesto,
        id_unidad_medida: producto.id_unidad_medida,
      });
    }
  }, [producto]);

  const cargarDatosIniciales = async () => {
    try {
      const [responseCategorias, responseUnidades] = await Promise.all([
        productosService.getCategorias({ activo: true }),
        productosService.getUnidadesMedida(),
      ]);

      setCategorias(responseCategorias.results);
      setUnidades(responseUnidades);
    } catch (error) {
      toast.error('Error al cargar datos iniciales');
      console.error('Error:', error);
    } finally {
      setCargando(false);
    }
  };

  const validarFormulario = (): boolean => {
    const nuevosErrores: Record<string, string> = {};

    if (!formData.descripcion.trim()) {
      nuevosErrores.descripcion = 'La descripción es requerida';
    }

    if (formData.id_categoria === 0) {
      nuevosErrores.id_categoria = 'Debe seleccionar una categoría';
    }

    if (formData.stock_minimo < 0) {
      nuevosErrores.stock_minimo = 'El stock mínimo no puede ser negativo';
    }

    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value, type } = e.target;
    
    setFormData((prev) => ({
      ...prev,
      [name]:
        type === 'checkbox'
          ? (e.target as HTMLInputElement).checked
          : type === 'number'
          ? value === ''
            ? 0
            : Number(value)
          : value,
    }));

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
      if (producto) {
        await productosService.actualizarProducto(producto.id_producto, formData);
        toast.success('Producto actualizado exitosamente');
      } else {
        await productosService.crearProducto(formData);
        toast.success('Producto creado exitosamente');
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
      toast.error(producto ? 'Error al actualizar producto' : 'Error al crear producto');
      console.error('Error:', error);
    } finally {
      setGuardando(false);
    }
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
            {producto ? 'Editar Producto' : 'Nuevo Producto'}
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            {producto
              ? 'Modifica la información del producto'
              : 'Complete los datos del nuevo producto'}
          </p>
        </div>
      </div>

      {/* Formulario */}
      <Card>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Sección 1: Información Básica */}
          <div>
            <h3 className="mb-4 text-lg font-medium text-gray-900">Información Básica</h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Código de Barra */}
              <div>
                <label htmlFor="codigo_barra" className="block text-sm font-medium text-gray-700">
                  Código de Barras
                </label>
                <input
                  type="text"
                  id="codigo_barra"
                  name="codigo_barra"
                  value={formData.codigo_barra}
                  onChange={handleChange}
                  className={`mt-1 block w-full rounded-lg border ${
                    errores.codigo_barra ? 'border-red-500' : 'border-gray-300'
                  } px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500`}
                  placeholder="123456789"
                />
                {errores.codigo_barra && (
                  <p className="mt-1 text-sm text-red-600">{errores.codigo_barra}</p>
                )}
              </div>

              {/* Descripción */}
              <div className="md:col-span-2">
                <label htmlFor="descripcion" className="block text-sm font-medium text-gray-700">
                  Descripción <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="descripcion"
                  name="descripcion"
                  value={formData.descripcion}
                  onChange={handleChange}
                  required
                  className={`mt-1 block w-full rounded-lg border ${
                    errores.descripcion ? 'border-red-500' : 'border-gray-300'
                  } px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500`}
                  placeholder="Nombre del producto"
                />
                {errores.descripcion && (
                  <p className="mt-1 text-sm text-red-600">{errores.descripcion}</p>
                )}
              </div>

              {/* Categoría */}
              <div>
                <label htmlFor="id_categoria" className="block text-sm font-medium text-gray-700">
                  Categoría <span className="text-red-500">*</span>
                </label>
                <select
                  id="id_categoria"
                  name="id_categoria"
                  value={formData.id_categoria}
                  onChange={handleChange}
                  required
                  className={`mt-1 block w-full rounded-lg border ${
                    errores.id_categoria ? 'border-red-500' : 'border-gray-300'
                  } px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500`}
                >
                  <option value={0}>Seleccione una categoría</option>
                  {categorias.map((categoria) => (
                    <option key={categoria.id_categoria} value={categoria.id_categoria}>
                      {categoria.nombre}
                    </option>
                  ))}
                </select>
                {errores.id_categoria && (
                  <p className="mt-1 text-sm text-red-600">{errores.id_categoria}</p>
                )}
              </div>

              {/* Unidad de Medida */}
              <div>
                <label htmlFor="id_unidad_medida" className="block text-sm font-medium text-gray-700">
                  Unidad de Medida
                </label>
                <select
                  id="id_unidad_medida"
                  name="id_unidad_medida"
                  value={formData.id_unidad_medida || ''}
                  onChange={handleChange}
                  className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="">Sin unidad de medida</option>
                  {unidades.map((unidad) => (
                    <option key={unidad.id_unidad_medida} value={unidad.id_unidad_medida}>
                      {unidad.nombre} ({unidad.abreviatura})
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Sección 2: Inventario */}
          <div>
            <h3 className="mb-4 text-lg font-medium text-gray-900">Configuración de Inventario</h3>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {/* Stock Mínimo */}
              <div>
                <label htmlFor="stock_minimo" className="block text-sm font-medium text-gray-700">
                  Stock Mínimo
                </label>
                <input
                  type="number"
                  id="stock_minimo"
                  name="stock_minimo"
                  value={formData.stock_minimo}
                  onChange={handleChange}
                  min="0"
                  step="0.001"
                  className={`mt-1 block w-full rounded-lg border ${
                    errores.stock_minimo ? 'border-red-500' : 'border-gray-300'
                  } px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500`}
                />
                {errores.stock_minimo && (
                  <p className="mt-1 text-sm text-red-600">{errores.stock_minimo}</p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Cantidad mínima antes de generar alerta de reposición
                </p>
              </div>

              {/* Permite Stock Negativo */}
              <div className="flex items-center pt-6">
                <input
                  type="checkbox"
                  id="permite_stock_negativo"
                  name="permite_stock_negativo"
                  checked={formData.permite_stock_negativo}
                  onChange={handleChange}
                  className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                />
                <label htmlFor="permite_stock_negativo" className="ml-2 text-sm text-gray-700">
                  Permite venta sin stock (stock negativo)
                </label>
              </div>

              {/* Estado Activo */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="activo"
                  name="activo"
                  checked={formData.activo}
                  onChange={handleChange}
                  className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                />
                <label htmlFor="activo" className="ml-2 text-sm text-gray-700">
                  Producto activo
                </label>
              </div>
            </div>
          </div>

          {/* Botones de Acción */}
          <div className="flex justify-end gap-3 border-t border-gray-200 pt-6">
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
              disabled={guardando}
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
                  {producto ? 'Actualizar' : 'Crear'} Producto
                </>
              )}
            </button>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default FormularioProducto;
