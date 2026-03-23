import React, { useState, useEffect } from 'react';
import { Card, Input, Spinner, EmptyState } from '../../../components/common';
import { Calendar, Clock, User, CheckCircle, XCircle, DollarSign, UtensilsCrossed } from 'lucide-react';
import { almuerzosService } from '../../../services/almuerzos.service';
import toast from 'react-hot-toast';
import type { RegistroConsumoAlmuerzo } from '../../../types';

const HistorialConsumos: React.FC = () => {
  const [registros, setRegistros] = useState<RegistroConsumoAlmuerzo[]>([]);
  const [cargando, setCargando] = useState(false);
  const [filtros, setFiltros] = useState({
    busqueda: '',
    fecha_desde: '',
    fecha_hasta: '',
    estado: '',
    alumno: '',
  });
  const [paginaActual, setPaginaActual] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);

  useEffect(() => {
    cargarRegistros();
  }, [filtros, paginaActual]);

  const cargarRegistros = async () => {
    try {
      setCargando(true);
      const params: any = {
        page: paginaActual,
        page_size: 20,
        ordering: '-fecha_consumo,-hora_registro'
      };

      if (filtros.fecha_desde) params.fecha_desde = filtros.fecha_desde;
      if (filtros.fecha_hasta) params.fecha_hasta = filtros.fecha_hasta;
      if (filtros.estado) params.estado = filtros.estado;
      if (filtros.alumno.trim()) params.search = filtros.alumno.trim();

      const response = await almuerzosService.getRegistros(params);
      setRegistros(response.results || response);
      
      if (response.count) {
        setTotalPaginas(Math.ceil(response.count / 20));
      }
    } catch (error) {
      console.error('Error al cargar registros:', error);
      toast.error('Error al cargar el historial');
    } finally {
      setCargando(false);
    }
  };

  const handleFiltroChange = (campo: string, valor: string) => {
    setFiltros({ ...filtros, [campo]: valor });
    setPaginaActual(1);
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha + 'T00:00:00').toLocaleDateString('es-PY', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      weekday: 'short'
    });
  };

  const formatearHora = (hora: string) => {
    return hora.substring(0, 5); // HH:MM
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0
    }).format(valor);
  };

  const getEstadoBadge = (estado: string) => {
    const badges: Record<string, { bg: string; text: string; icon: any }> = {
      'Confirmado': { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle },
      'Pendiente': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: Clock },
      'Rechazado': { bg: 'bg-red-100', text: 'text-red-800', icon: XCircle }
    };
    return badges[estado] || badges['Pendiente'];
  };

  return (
    <div className="space-y-4">
      <Card>
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Historial de Consumos</h3>
          <p className="text-sm text-gray-600">
            Consulta todos los registros de consumo de almuerzos
          </p>
        </div>

        {/* Filtros */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Buscar Alumno
            </label>
            <Input
              type="text"
              placeholder="Nombre o apellido..."
              value={filtros.alumno}
              onChange={(e) => handleFiltroChange('alumno', e.target.value)}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Fecha Desde
            </label>
            <Input
              type="date"
              value={filtros.fecha_desde}
              onChange={(e) => handleFiltroChange('fecha_desde', e.target.value)}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Fecha Hasta
            </label>
            <Input
              type="date"
              value={filtros.fecha_hasta}
              onChange={(e) => handleFiltroChange('fecha_hasta', e.target.value)}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Estado
            </label>
            <select
              value={filtros.estado}
              onChange={(e) => handleFiltroChange('estado', e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
            >
              <option value="">Todos los estados</option>
              <option value="Confirmado">Confirmado</option>
              <option value="Pendiente">Pendiente</option>
              <option value="Rechazado">Rechazado</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => {
                setFiltros({
                  busqueda: '',
                  fecha_desde: '',
                  fecha_hasta: '',
                  estado: '',
                  alumno: '',
                });
                setPaginaActual(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>

        {/* Tabla de registros */}
        {cargando ? (
          <div className="flex items-center justify-center py-12">
            <Spinner className="h-8 w-8" />
          </div>
        ) : registros.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Fecha y Hora
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Hijo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Tipo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Costo
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Cobrado
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Estado
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {registros.map((registro) => {
                    const badge = getEstadoBadge(registro.estado);
                    const IconoEstado = badge.icon;
                    
                    return (
                      <tr key={registro.id_registro_consumo} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 text-sm">
                            <Calendar className="h-4 w-4 text-gray-400" />
                            <div>
                              <p className="font-medium text-gray-900">
                                {formatearFecha(registro.fecha_consumo)}
                              </p>
                              <div className="flex items-center gap-1 text-gray-500">
                                <Clock className="h-3 w-3" />
                                {formatearHora(registro.hora_registro)}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <User className="h-4 w-4 text-gray-400" />
                            <span className="text-sm font-medium text-gray-900">
                              {registro.hijo_nombre || `Hijo #${registro.id_hijo}`}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {registro.tipo_almuerzo_nombre || 
                           (registro.id_suscripcion ? 'Suscripción' : '-')}
                        </td>
                        <td className="px-6 py-4">
                          {registro.costo_almuerzo && registro.costo_almuerzo > 0 ? (
                            <div className="flex items-center gap-1 text-sm font-semibold text-green-600">
                              <DollarSign className="h-4 w-4" />
                              {formatearMoneda(registro.costo_almuerzo)}
                            </div>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          {registro.ya_cobrado ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
                              <CheckCircle className="h-3 w-3" />
                              Sí
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-800">
                              <XCircle className="h-3 w-3" />
                              No
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${badge.bg} ${badge.text}`}
                          >
                            <IconoEstado className="h-3 w-3" />
                            {registro.estado}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
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
                    onClick={() => setPaginaActual(p => Math.max(1, p - 1))}
                    disabled={paginaActual === 1}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPaginaActual(p => Math.min(totalPaginas, p + 1))}
                    disabled={paginaActual === totalPaginas}
                    className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <EmptyState
            icon={UtensilsCrossed}
            title="Sin registros de consumo"
            description={filtros.fecha_desde || filtros.fecha_hasta || filtros.estado
              ? "Intenta cambiar los filtros"
              : "No hay consumos registrados en el sistema"}
            action={filtros.fecha_desde || filtros.fecha_hasta || filtros.estado || filtros.alumno ? {
              label: "Limpiar filtros",
              onClick: () => {
                setFiltros({ busqueda: '', fecha_desde: '', fecha_hasta: '', estado: '', alumno: '' });
                setPaginaActual(1);
              }
            } : undefined}
            size="sm"
          />
        )}
      </Card>
    </div>
  );
};

export default HistorialConsumos;
