import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Spinner } from '../../../components/common';
import { Plus, Edit, Trash2, Tag, CheckCircle } from 'lucide-react';
import { almuerzosService } from '../../../services/almuerzos.service';
import type { PrecioAlmuerzoData } from '../../../services/almuerzos.service';
import toast from 'react-hot-toast';

interface PrecioAlmuerzo {
  id_precio: number;
  precio_unitario: string;
  fecha_inicio_vigencia: string;
  fecha_fin_vigencia: string | null;
  descripcion: string;
  activo: boolean;
  fecha_creacion: string;
}

const GestionPrecios: React.FC = () => {
  const [precios, setPrecios] = useState<PrecioAlmuerzo[]>([]);
  const [precioActual, setPrecioActual] = useState<PrecioAlmuerzo | null>(null);
  const [cargando, setCargando] = useState(false);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [precioEditando, setPrecioEditando] = useState<PrecioAlmuerzo | null>(null);
  const [guardando, setGuardando] = useState(false);

  const hoy = new Date().toISOString().split('T')[0];

  const [formData, setFormData] = useState<{
    precio_unitario: string;
    fecha_inicio_vigencia: string;
    fecha_fin_vigencia: string;
    descripcion: string;
    activo: boolean;
  }>({
    precio_unitario: '',
    fecha_inicio_vigencia: hoy,
    fecha_fin_vigencia: '',
    descripcion: '',
    activo: true,
  });

  useEffect(() => {
    cargarPrecios();
  }, []);

  const cargarPrecios = async () => {
    try {
      setCargando(true);
      const [historial, actual] = await Promise.all([
        almuerzosService.getPrecios({ ordering: '-fecha_inicio_vigencia', page_size: 50 }),
        almuerzosService.getPrecioActual(),
      ]);
      setPrecios(historial.results || historial);
      setPrecioActual(actual?.id_precio ? actual : null);
    } catch (error) {
      console.error('Error al cargar precios:', error);
      toast.error('Error al cargar el historial de precios');
    } finally {
      setCargando(false);
    }
  };

  const handleNuevo = () => {
    setFormData({
      precio_unitario: '',
      fecha_inicio_vigencia: hoy,
      fecha_fin_vigencia: '',
      descripcion: '',
      activo: true,
    });
    setPrecioEditando(null);
    setMostrarFormulario(true);
  };

  const handleEditar = (precio: PrecioAlmuerzo) => {
    setFormData({
      precio_unitario: precio.precio_unitario,
      fecha_inicio_vigencia: precio.fecha_inicio_vigencia,
      fecha_fin_vigencia: precio.fecha_fin_vigencia || '',
      descripcion: precio.descripcion || '',
      activo: precio.activo,
    });
    setPrecioEditando(precio);
    setMostrarFormulario(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const valor = parseFloat(formData.precio_unitario);
    if (!formData.precio_unitario || valor <= 0) {
      toast.error('El precio debe ser mayor a 0');
      return;
    }
    if (!formData.fecha_inicio_vigencia) {
      toast.error('La fecha de inicio de vigencia es requerida');
      return;
    }

    setGuardando(true);
    try {
      const data: PrecioAlmuerzoData = {
        precio_unitario: valor,
        fecha_inicio_vigencia: formData.fecha_inicio_vigencia,
        fecha_fin_vigencia: formData.fecha_fin_vigencia || null,
        descripcion: formData.descripcion,
        activo: formData.activo,
      };

      if (precioEditando) {
        await almuerzosService.actualizarPrecio(precioEditando.id_precio, data);
        toast.success('Precio actualizado exitosamente');
      } else {
        await almuerzosService.crearPrecio(data);
        toast.success('Nuevo precio registrado');
      }

      setMostrarFormulario(false);
      cargarPrecios();
    } catch (error: any) {
      console.error('Error al guardar precio:', error);
      toast.error(error.response?.data?.error || 'Error al guardar el precio');
    } finally {
      setGuardando(false);
    }
  };

  const handleEliminar = async (precio: PrecioAlmuerzo) => {
    if (!window.confirm(`¿Eliminar este registro de precio (Gs ${formatearMoneda(parseFloat(precio.precio_unitario))})?`)) return;
    try {
      await almuerzosService.eliminarPrecio(precio.id_precio);
      toast.success('Precio eliminado');
      cargarPrecios();
    } catch {
      toast.error('No se puede eliminar — tiene registros de consumo asociados');
    }
  };

  const formatearMoneda = (valor: number) =>
    new Intl.NumberFormat('es-PY', { style: 'currency', currency: 'PYG', minimumFractionDigits: 0 }).format(valor);

  const formatearFecha = (fecha: string) =>
    new Date(fecha + 'T00:00:00').toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric' });

  if (mostrarFormulario) {
    return (
      <Card
        title={precioEditando ? 'Editar Precio' : 'Nuevo Precio de Almuerzo'}
        subtitle="Define el precio unitario y su período de vigencia"
      >
        <form onSubmit={handleSubmit} className="space-y-4 max-w-lg">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Precio por almuerzo (Gs) *
            </label>
            <Input
              type="number"
              value={formData.precio_unitario}
              onChange={(e) => setFormData((p) => ({ ...p, precio_unitario: e.target.value }))}
              placeholder="Ej: 25000"
              min="1"
              step="500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Vigencia desde *
              </label>
              <Input
                type="date"
                value={formData.fecha_inicio_vigencia}
                onChange={(e) => setFormData((p) => ({ ...p, fecha_inicio_vigencia: e.target.value }))}
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Vigencia hasta <span className="text-gray-400">(vacío = sin vencimiento)</span>
              </label>
              <Input
                type="date"
                value={formData.fecha_fin_vigencia}
                onChange={(e) => setFormData((p) => ({ ...p, fecha_fin_vigencia: e.target.value }))}
                min={formData.fecha_inicio_vigencia}
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Descripción / Motivo
            </label>
            <Input
              type="text"
              value={formData.descripcion}
              onChange={(e) => setFormData((p) => ({ ...p, descripcion: e.target.value }))}
              placeholder="Ej: Ajuste por inflación 2026"
              maxLength={200}
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="activo"
              checked={formData.activo}
              onChange={(e) => setFormData((p) => ({ ...p, activo: e.target.checked }))}
              className="h-4 w-4 rounded border-gray-300 text-amber-600"
            />
            <label htmlFor="activo" className="text-sm text-gray-700">Precio activo</label>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" variant="primary" disabled={guardando}>
              {guardando ? <Spinner size="sm" /> : precioEditando ? 'Actualizar' : 'Guardar precio'}
            </Button>
            <Button type="button" variant="secondary" onClick={() => setMostrarFormulario(false)}>
              Cancelar
            </Button>
          </div>
        </form>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Precio actual vigente */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-amber-100 p-3">
              <Tag className="h-6 w-6 text-amber-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Precio unitario vigente hoy</p>
              <p className="text-3xl font-bold text-amber-600">
                {precioActual
                  ? formatearMoneda(parseFloat(precioActual.precio_unitario))
                  : 'Sin configurar'}
              </p>
              {precioActual && (
                <p className="text-xs text-gray-400 mt-1">
                  Desde: {formatearFecha(precioActual.fecha_inicio_vigencia)}
                  {precioActual.fecha_fin_vigencia && (
                    <> · Hasta: {formatearFecha(precioActual.fecha_fin_vigencia)}</>
                  )}
                  {precioActual.descripcion && <> · {precioActual.descripcion}</>}
                </p>
              )}
            </div>
          </div>
          <Button variant="primary" onClick={handleNuevo}>
            <Plus className="mr-2 h-4 w-4" />
            Nuevo precio
          </Button>
        </div>
      </Card>

      {/* Historial de precios */}
      <Card title="Historial de precios" subtitle="Todos los precios registrados con su período de vigencia">
        {cargando ? (
          <div className="flex justify-center py-8">
            <Spinner size="lg" />
          </div>
        ) : precios.length === 0 ? (
          <p className="py-6 text-center text-gray-500">No hay precios registrados</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Precio (Gs)</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Vigencia desde</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Vigencia hasta</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Descripción</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Estado</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {precios.map((precio) => {
                  const esVigente = precioActual?.id_precio === precio.id_precio;
                  return (
                    <tr key={precio.id_precio} className={esVigente ? 'bg-amber-50' : ''}>
                      <td className="px-4 py-3 font-semibold text-gray-900">
                        {formatearMoneda(parseFloat(precio.precio_unitario))}
                        {esVigente && (
                          <CheckCircle className="ml-2 inline h-4 w-4 text-green-500" />
                        )}
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        {formatearFecha(precio.fecha_inicio_vigencia)}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {precio.fecha_fin_vigencia ? formatearFecha(precio.fecha_fin_vigencia) : '—'}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{precio.descripcion || '—'}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                            precio.activo
                              ? 'bg-green-100 text-green-700'
                              : 'bg-gray-100 text-gray-500'
                          }`}
                        >
                          {precio.activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditar(precio)}
                            className="rounded p-1 text-blue-600 hover:bg-blue-50"
                            title="Editar"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          {!esVigente && (
                            <button
                              onClick={() => handleEliminar(precio)}
                              className="rounded p-1 text-red-500 hover:bg-red-50"
                              title="Eliminar"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
};

export default GestionPrecios;
