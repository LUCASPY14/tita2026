import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Spinner } from '../../../components/common';
import { Plus, Edit, Trash2, ToggleLeft, ToggleRight } from 'lucide-react';
import { almuerzosService } from '../../../services/almuerzos.service';
import toast from 'react-hot-toast';
import type { PlanAlmuerzo } from '../../../types';

const GestionPlanes: React.FC = () => {
  const [planes, setPlanes] = useState<PlanAlmuerzo[]>([]);
  const [cargando, setCargando] = useState(false);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [planEditando, setPlanEditando] = useState<PlanAlmuerzo | null>(null);
  const [formData, setFormData] = useState({
    nombre_plan: '',
    descripcion: '',
    precio_mensual: '',
    tipo_plan: 'sin_limite' as 'cantidad' | 'sin_limite',
    cantidad_almuerzos_mes: '' as string | number,
    limite_credito_mensual: '' as string | number,
    dias_semana_incluidos: '',
    estado: true
  });
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    cargarPlanes();
  }, []);

  const cargarPlanes = async () => {
    try {
      setCargando(true);
      const response = await almuerzosService.getPlanes();
      setPlanes(response.results || response);
    } catch (error) {
      console.error('Error al cargar planes:', error);
      toast.error('Error al cargar los planes');
    } finally {
      setCargando(false);
    }
  };

  const handleNuevo = () => {
    setFormData({
      nombre_plan: '',
      descripcion: '',
      precio_mensual: '',
      tipo_plan: 'sin_limite',
      cantidad_almuerzos_mes: '',
      limite_credito_mensual: '',
      dias_semana_incluidos: '',
      estado: true
    });
    setPlanEditando(null);
    setMostrarFormulario(true);
  };

  const handleEditar = (plan: PlanAlmuerzo) => {
    setFormData({
      nombre_plan: plan.nombre_plan,
      descripcion: plan.descripcion || '',
      precio_mensual: plan.precio_mensual.toString(),
      tipo_plan: (plan as any).tipo_plan || 'sin_limite',
      cantidad_almuerzos_mes: (plan as any).cantidad_almuerzos_mes ?? '',
      limite_credito_mensual: (plan as any).limite_credito_mensual ?? '',
      dias_semana_incluidos: plan.dias_semana_incluidos,
      estado: plan.estado
    });
    setPlanEditando(plan);
    setMostrarFormulario(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.nombre_plan.trim()) {
      toast.error('El nombre del plan es requerido');
      return;
    }

    if (!formData.precio_mensual || parseFloat(formData.precio_mensual) <= 0) {
      toast.error('El precio debe ser mayor a 0');
      return;
    }

    setGuardando(true);
    try {
      const data: any = {
        nombre_plan: formData.nombre_plan,
        descripcion: formData.descripcion || undefined,
        precio_mensual: parseFloat(formData.precio_mensual),
        tipo_plan: formData.tipo_plan,
        cantidad_almuerzos_mes:
          formData.tipo_plan === 'cantidad' && formData.cantidad_almuerzos_mes !== ''
            ? parseInt(String(formData.cantidad_almuerzos_mes))
            : null,
        limite_credito_mensual:
          formData.limite_credito_mensual !== ''
            ? parseFloat(String(formData.limite_credito_mensual))
            : null,
        dias_semana_incluidos: formData.dias_semana_incluidos,
        estado: formData.estado
      };

      if (planEditando) {
        await almuerzosService.actualizarPlan(planEditando.id_plan_almuerzo, data);
        toast.success('Plan actualizado exitosamente');
      } else {
        await almuerzosService.crearPlan(data);
        toast.success('Plan creado exitosamente');
      }

      setMostrarFormulario(false);
      cargarPlanes();
    } catch (error: any) {
      console.error('Error al guardar plan:', error);
      toast.error(error.response?.data?.error || 'Error al guardar el plan');
    } finally {
      setGuardando(false);
    }
  };

  const handleToggleEstado = async (plan: PlanAlmuerzo) => {
    try {
      await almuerzosService.toggleEstadoPlan(plan.id_plan_almuerzo, !plan.estado);
      toast.success(`Plan ${!plan.estado ? 'activado' : 'desactivado'}`);
      cargarPlanes();
    } catch (error) {
      console.error('Error al cambiar estado:', error);
      toast.error('Error al cambiar el estado');
    }
  };

  const handleEliminar = async (plan: PlanAlmuerzo) => {
    if (!window.confirm(`¿Estás seguro de eliminar el plan "${plan.nombre_plan}"?`)) {
      return;
    }

    try {
      await almuerzosService.eliminarPlan(plan.id_plan_almuerzo);
      toast.success('Plan eliminado exitosamente');
      cargarPlanes();
    } catch (error) {
      console.error('Error al eliminar plan:', error);
      toast.error('Error al eliminar el plan');
    }
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0
    }).format(valor);
  };

  if (mostrarFormulario) {
    return (
      <Card 
        title={planEditando ? 'Editar Plan' : 'Nuevo Plan de Almuerzo'}
        subtitle="Completa los datos del plan"
      >
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Nombre del Plan *
              </label>
              <Input
                type="text"
                placeholder="Ej: Plan Mensual Completo"
                value={formData.nombre_plan}
                onChange={(e) => setFormData({ ...formData, nombre_plan: e.target.value })}
                required
              />
            </div>

            <div className="col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Descripción
              </label>
              <textarea
                rows={3}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                placeholder="Descripción del plan..."
                value={formData.descripcion}
                onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Precio Mensual (Gs.) *
              </label>
              <Input
                type="number"
                step="1"
                min="0"
                placeholder="0"
                value={formData.precio_mensual}
                onChange={(e) => setFormData({ ...formData, precio_mensual: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Días Incluidos
              </label>
              <Input
                type="text"
                placeholder="Ej: Lunes a Viernes"
                value={formData.dias_semana_incluidos}
                onChange={(e) => setFormData({ ...formData, dias_semana_incluidos: e.target.value })}
              />
            </div>

            <div className="col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Tipo de suscripción *
              </label>
              <select
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                value={formData.tipo_plan}
                onChange={(e) => setFormData({ ...formData, tipo_plan: e.target.value as 'cantidad' | 'sin_limite', cantidad_almuerzos_mes: '' })}
              >
                <option value="sin_limite">Mensual sin límite (cuenta corriente)</option>
                <option value="cantidad">Mensual con cantidad de almuerzos</option>
              </select>
              <p className="mt-1 text-xs text-gray-500">
                {formData.tipo_plan === 'sin_limite'
                  ? 'Se registra cada consumo y al cierre del mes se factura el total.'
                  : 'El plan incluye un máximo de almuerzos por mes incluidos en el precio mensual.'}
              </p>
            </div>

            {formData.tipo_plan === 'cantidad' && (
              <div className="col-span-2">
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Cantidad de almuerzos incluidos por mes *
                </label>
                <Input
                  type="number"
                  min="1"
                  max="31"
                  placeholder="Ej: 20"
                  value={formData.cantidad_almuerzos_mes}
                  onChange={(e) => setFormData({ ...formData, cantidad_almuerzos_mes: e.target.value })}
                  required={formData.tipo_plan === 'cantidad'}
                />
              </div>
            )}

            <div className="col-span-2">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Límite de crédito mensual (Gs) — opcional
              </label>
              <Input
                type="number"
                min="0"
                step="1000"
                placeholder="Dejar vacío para sin límite"
                value={formData.limite_credito_mensual}
                onChange={(e) => setFormData({ ...formData, limite_credito_mensual: e.target.value })}
              />
              <p className="mt-1 text-xs text-gray-500">
                Si se define, el sistema bloqueará nuevos registros cuando el saldo pendiente supere este monto.
              </p>
            </div>

            <div className="col-span-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.estado}
                  onChange={(e) => setFormData({ ...formData, estado: e.target.checked })}
                  className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
                />
                <span className="text-sm font-medium text-gray-700">Plan activo</span>
              </label>
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
                  {planEditando ? 'Actualizar' : 'Crear'} Plan
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
            <h3 className="text-lg font-semibold text-gray-900">Planes de Almuerzo</h3>
            <p className="text-sm text-gray-600">
              Gestiona los planes mensuales disponibles
            </p>
          </div>
          <Button onClick={handleNuevo}>
            <Plus className="h-4 w-4" />
            Nuevo Plan
          </Button>
        </div>

        {cargando ? (
          <div className="flex items-center justify-center py-12">
            <Spinner className="h-8 w-8" />
          </div>
        ) : planes.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Plan
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Días Incluidos
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Tipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Precio Mensual
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
                {planes.map((plan) => (
                  <tr key={plan.id_plan_almuerzo} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{plan.nombre_plan}</p>
                        {plan.descripcion && (
                          <p className="text-sm text-gray-500">{plan.descripcion}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {plan.dias_semana_incluidos || '-'}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                        (plan as any).tipo_plan === 'cantidad'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-purple-100 text-purple-700'
                      }`}>
                        {(plan as any).tipo_plan === 'cantidad'
                          ? `Fijo (${(plan as any).cantidad_almuerzos_mes ?? '?'} alm/mes)`
                          : 'Cta. Corriente'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-green-600">
                        {formatearMoneda(plan.precio_mensual)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                          plan.estado
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {plan.estado ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditar(plan)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Editar"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleToggleEstado(plan)}
                          className={plan.estado ? 'text-amber-600 hover:text-amber-800' : 'text-green-600 hover:text-green-800'}
                          title={plan.estado ? 'Desactivar' : 'Activar'}
                        >
                          {plan.estado ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}
                        </button>
                        <button
                          onClick={() => handleEliminar(plan)}
                          className="text-red-600 hover:text-red-800"
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
        ) : (
          <div className="py-12 text-center">
            <p className="text-gray-500">No hay planes registrados</p>
            <Button onClick={handleNuevo} className="mt-4">
              <Plus className="h-4 w-4" />
              Crear Primer Plan
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default GestionPlanes;
