import React, { useState, useEffect } from 'react';
import { Save, X } from 'lucide-react';
import { productosService, CategoriaData } from '../../../services/productos.service';
import { Categoria } from '../../../types';
import { Card } from '../../../components/common';
import toast from 'react-hot-toast';

interface FormularioCategoriaProps {
  categoria?: Categoria | null;
  onGuardado: () => void;
  onCancelar: () => void;
}

const FormularioCategoria: React.FC<FormularioCategoriaProps> = ({
  categoria,
  onGuardado,
  onCancelar,
}) => {
  const [formData, setFormData] = useState<CategoriaData>({
    nombre: '',
    estado: true,
    id_categoria_padre: undefined,
  });
  const [categoriasPadre, setCategoriasPadre] = useState<Categoria[]>([]);
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    cargarCategoriasPadre();
  }, []);

  useEffect(() => {
    if (categoria) {
      setFormData({
        nombre: categoria.nombre,
        estado: categoria.estado,
        id_categoria_padre: categoria.id_categoria_padre,
      });
    }
  }, [categoria]);

  const cargarCategoriasPadre = async () => {
    try {
      const response = await productosService.getCategorias({ estado: true });
      const lista = response.results ?? (response as any);
      setCategoriasPadre(Array.isArray(lista) ? lista : []);
    } catch (error) {
      console.error('Error al cargar categorías padre:', error);
    }
  };

  const validar = (): boolean => {
    const nuevosErrores: Record<string, string> = {};
    if (!formData.nombre.trim()) {
      nuevosErrores.nombre = 'El nombre es requerido';
    }
    setErrores(nuevosErrores);
    return Object.keys(nuevosErrores).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validar()) return;

    setGuardando(true);
    try {
      const datos: CategoriaData = {
        nombre: formData.nombre.trim(),
        estado: formData.estado,
        id_categoria_padre: formData.id_categoria_padre || undefined,
      };

      if (categoria) {
        await productosService.actualizarCategoria(categoria.id_categoria, datos);
        toast.success('Categoría actualizada exitosamente');
      } else {
        await productosService.crearCategoria(datos);
        toast.success('Categoría creada exitosamente');
      }
      onGuardado();
    } catch (error: any) {
      const mensaje =
        error?.response?.data?.nombre?.[0] ||
        error?.response?.data?.detail ||
        'Error al guardar la categoría';
      toast.error(mensaje);
      console.error('Error:', error);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">
          {categoria ? 'Editar Categoría' : 'Nueva Categoría'}
        </h2>
        <button onClick={onCancelar} className="rounded p-1 text-gray-500 hover:bg-gray-100">
          <X className="h-5 w-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Nombre */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nombre <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.nombre}
            onChange={(e) => setFormData((prev) => ({ ...prev, nombre: e.target.value }))}
            className={`w-full rounded-lg border px-3 py-2 focus:outline-none focus:ring-1 focus:ring-amber-500 ${
              errores.nombre ? 'border-red-500' : 'border-gray-300 focus:border-amber-500'
            }`}
            placeholder="Ej: Bebidas, Snacks, Lácteos..."
          />
          {errores.nombre && (
            <p className="mt-1 text-xs text-red-600">{errores.nombre}</p>
          )}
        </div>

        {/* Categoría padre */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Categoría padre (opcional)
          </label>
          <select
            value={formData.id_categoria_padre ?? ''}
            onChange={(e) =>
              setFormData((prev) => ({
                ...prev,
                id_categoria_padre: e.target.value ? Number(e.target.value) : undefined,
              }))
            }
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
          >
            <option value="">— Sin categoría padre (principal) —</option>
            {categoriasPadre
              .filter((c) => !categoria || c.id_categoria !== categoria.id_categoria)
              .map((c) => (
                <option key={c.id_categoria} value={c.id_categoria}>
                  {c.nombre}
                </option>
              ))}
          </select>
        </div>

        {/* Estado */}
        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="estado"
            checked={formData.estado}
            onChange={(e) => setFormData((prev) => ({ ...prev, estado: e.target.checked }))}
            className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
          />
          <label htmlFor="estado" className="text-sm font-medium text-gray-700">
            Categoría activa
          </label>
        </div>

        {/* Botones */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={guardando}
            className="inline-flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2 text-white hover:bg-amber-700 disabled:opacity-50 transition-colors"
          >
            <Save className="h-4 w-4" />
            {guardando ? 'Guardando...' : 'Guardar'}
          </button>
          <button
            type="button"
            onClick={onCancelar}
            className="rounded-lg border border-gray-300 px-4 py-2 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
        </div>
      </form>
    </Card>
  );
};

export default FormularioCategoria;
