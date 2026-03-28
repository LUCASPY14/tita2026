import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Spinner } from '../../../components/common';
import { Plus, Edit, Trash2, User } from 'lucide-react';
import { almuerzosService } from '../../../services/almuerzos.service';
import { recargasService } from '../../../services/recargas.service';
import toast from 'react-hot-toast';
import type { SuscripcionAlmuerzo, PlanAlmuerzo, Hijo } from '../../../types';

const GestionSuscripciones: React.FC = () => {
  const [suscripciones, setSuscripciones] = useState<SuscripcionAlmuerzo[]>([]);
  const [planes, setPlanes] = useState<PlanAlmuerzo[]>([]);
  const [hijos, setHijos] = useState<Hijo[]>([]);
  const [cargando, setCargando] = useState(false);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [suscripcionEditando, setSuscripcionEditando] = useState<SuscripcionAlmuerzo | null>(null);
  const [filtroEstado, setFiltroEstado] = useState<string>('');
  const [busquedaHijo, setBusquedaHijo] = useState('');
  const [formData, setFormData] = useState({
    id_hijo: 0,
    id_plan_almuerzo: 0,
    fecha_inicio: '',
    fecha_fin: '',
    estado: 'Activa'
  });
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    cargarSuscripciones();
    cargarPlanes();
    cargarHijos();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtroEstado]);

  const cargarSuscripciones = async () => {
    try {
      setCargando(true);
      const params: any = filtroEstado ? { estado: filtroEstado } : {};
      const response = await almuerzosService.getSuscripciones(params);
      setSuscripciones(response.results || response);
    } catch (error) {
      console.error('Error al cargar suscripciones:', error);
      toast.error('Error al cargar las suscripciones');
    } finally {
      setCargando(false);
    }
  };

  const cargarPlanes = async () => {
    try {
      const response = await almuerzosService.getPlanes({ estado: true });
      setPlanes(response.results || response);
    } catch (error) {
      console.error('Error al cargar planes:', error);
    }
  };

  const cargarHijos = async () => {
    try {
      const response = await recargasService.buscarHijos({ estado: true });
      setHijos(response.results || response);
    } catch (error) {
      console.error('Error al cargar hijos:', error);
    }
  };

  const handleNuevo = () => {
    const hoy = new Date().toISOString().split('T')[0];
    setFormData({
      id_hijo: 0,
      id_plan_almuerzo: 0,
      fecha_inicio: hoy,
      fecha_fin: '',
      estado: 'Activa'
    });
    setSuscripcionEditando(null);
    setMostrarFormulario(true);
  };

  const handleEditar = (suscripcion: SuscripcionAlmuerzo) => {
    setFormData({
      id_hijo: suscripcion.id_hijo,
      id_plan_almuerzo: suscripcion.id_plan_almuerzo,
      fecha_inicio: suscripcion.fecha_inicio,
      fecha_fin: suscripcion.fecha_fin || '',
      estado: suscripcion.estado
    });
    setSuscripcionEditando(suscripcion);
    setMostrarFormulario(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.id_hijo === 0) {
      toast.error('Selecciona un hijo');
      return;
    }

    if (formData.id_plan_almuerzo === 0) {
      toast.error('Selecciona un plan');
      return;
    }

    setGuardando(true);
    try {
      const data = {
        id_hijo: formData.id_hijo,
        id_plan_almuerzo: formData.id_plan_almuerzo,
        fecha_inicio: formData.fecha_inicio,
        fecha_fin: formData.fecha_fin || undefined,
        estado: formData.estado
      };

      if (suscripcionEditando) {
        await almuerzosService.actualizarSuscripcion(suscripcionEditando.id_suscripcion, data);
        toast.success('Suscripción actualizada exitosamente');
      } else {
        await almuerzosService.crearSuscripcion(data);
        toast.success('Suscripción creada exitosamente');
      }

      setMostrarFormulario(false);
      cargarSuscripciones();
    } catch (error: any) {
      console.error('Error al guardar suscripción:', error);
      toast.error(error.response?.data?.error || 'Error al guardar la suscripción');
    } finally {
      setGuardando(false);
    }
  };

  const handleEliminar = async (suscripcion: SuscripcionAlmuerzo) => {
    if (!window.confirm('¿Estás seguro de eliminar esta suscripción?')) {
      return;
    }

    try {
      await almuerzosService.eliminarSuscripcion(suscripcion.id_suscripcion);
      toast.success('Suscripción eliminada exitosamente');
      cargarSuscripciones();
    } catch (error) {
      console.error('Error al eliminar suscripción:', error);
      toast.error('Error al eliminar la suscripción');
    }
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha + 'T00:00:00').toLocaleDateString('es-PY', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  const getEstadoBadge = (estado: string) => {
    const badges: Record<string, { bg: string; text: string }> = {
      'Activa': { bg: 'bg-green-100', text: 'text-green-800' },
      'Pendiente': { bg: 'bg-yellow-100', text: 'text-yellow-800' },
      'Finalizada': { bg: 'bg-gray-100', text: 'text-gray-800' },
      'Cancelada': { bg: 'bg-red-100', text: 'text-red-800' }
    };
    return badges[estado] || badges['Pendiente'];
  };

  const hijosFiltrados = busquedaHijo
    ? hijos.filter(h => 
        `${h.nombre} ${h.apellido}`.toLowerCase().includes(busquedaHijo.toLowerCase())
      )
    : hijos;

  if (mostrarFormulario) {
    return (
      <Card 
        title={suscripcionEditando ? 'Editar Suscripción' : 'Nueva Suscripción'}
        subtitle="Completa los datos de la suscripción"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Hijo *
              </label>
              <div className="space-y-2">
                <Input
                  type="text"
                  placeholder="Buscar hijo..."
                  value={busquedaHijo}
                  onChange={(e) => setBusquedaHijo(e.target.value)}
                />
                <select
                  value={formData.id_hijo}
                  onChange={(e) => setFormData({ ...formData, id_hijo: Number(e.target.value) })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                  required
                >
                  <option value={0}>Seleccione un hijo...</option>
                  {hijosFiltrados.map((hijo) => (
                    <option key={hijo.id_hijo} value={hijo.id_hijo}>
                      {hijo.nombre} {hijo.apellido}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Plan de Almuerzo *
              </label>
              <select
                value={formData.id_plan_almuerzo}
                onChange={(e) => setFormData({ ...formData, id_plan_almuerzo: Number(e.target.value) })}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                required
              >
                <option value={0}>Seleccione un plan...</option>
                {planes.map((plan) => (
                  <option key={plan.id_plan_almuerzo} value={plan.id_plan_almuerzo}>
                    {plan.nombre_plan} - Gs. {plan.precio_mensual.toLocaleString()}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Fecha de Inicio *
              </label>
              <Input
                type="date"
                value={formData.fecha_inicio}
                onChange={(e) => setFormData({ ...formData, fecha_inicio: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Fecha de Fin
              </label>
              <Input
                type="date"
                value={formData.fecha_fin}
                onChange={(e) => setFormData({ ...formData, fecha_fin: e.target.value })}
              />
            </div>

            <div className="col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Estado *
              </label>
              <select
                value={formData.estado}
                onChange={(e) => setFormData({ ...formData, estado: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                required
              >
                <option value="Activa">Activa</option>
                <option value="Pendiente">Pendiente</option>
                <option value="Finalizada">Finalizada</option>
                <option value="Cancelada">Cancelada</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 border-t pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => setMostrarFormulario(false)}
              disabled={guardando}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={guardando}
              className="flex-1"
            >
              {guardando ? (
                <>
                  <Spinner className="h-4 w-4" />
                  Guardando...
                </>
              ) : (
                <>
                  {suscripcionEditando ? 'Actualizar' : 'Crear'} Suscripción
                </>
              )}
            </Button>
          </div>
        </form>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Suscripciones de Almuerzo</h3>
            <p className="text-sm text-gray-600">
              Gestiona las suscripciones de los hijos a planes de almuerzo
            </p>
          </div>
          <Button onClick={handleNuevo}>
            <Plus className="h-4 w-4" />
            Nueva Suscripción
          </Button>
        </div>

        {/* Filtros */}
        <div className="mb-4 flex gap-4">
          <select
            value={filtroEstado}
            onChange={(e) => setFiltroEstado(e.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
          >
            <option value="">Todos los estados</option>
            <option value="Activa">Activa</option>
            <option value="Pendiente">Pendiente</option>
            <option value="Finalizada">Finalizada</option>
            <option value="Cancelada">Cancelada</option>
          </select>
        </div>

        {cargando ? (
          <div className="flex items-center justify-center py-12">
            <Spinner className="h-8 w-8" />
          </div>
        ) : suscripciones.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Hijo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Fecha Inicio
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Fecha Fin
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {suscripciones.map((suscripcion) => {
                  const badge = getEstadoBadge(suscripcion.estado);
                  return (
                    <tr key={suscripcion.id_suscripcion} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="font-medium text-gray-900">
                            {suscripcion.hijo_nombre || `Hijo #${suscripcion.id_hijo}`}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {suscripcion.plan_nombre || `Plan #${suscripcion.id_plan_almuerzo}`}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {formatearFecha(suscripcion.fecha_inicio)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {suscripcion.fecha_fin ? formatearFecha(suscripcion.fecha_fin) : '-'}
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${badge.bg} ${badge.text}`}
                        >
                          {suscripcion.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditar(suscripcion)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Editar"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleEliminar(suscripcion)}
                            className="text-red-600 hover:text-red-800"
                            title="Eliminar"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center">
            <p className="text-gray-500">No hay suscripciones registradas</p>
            <Button onClick={handleNuevo} className="mt-4">
              <Plus className="h-4 w-4" />
              Crear Primera Suscripción
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default GestionSuscripciones;
