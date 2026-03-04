/**
 * Página de Auditoría del Sistema
 * Visualización y filtrado de logs de operaciones con estadísticas
 */

import React, { useState, useEffect } from 'react';
import {
  Shield,
  Search,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  User,
  Activity,
  AlertCircle,
  CheckCircle,
  XCircle,
  Eye,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Card, Button, Badge } from '../components/common';
import { useAuditoria } from '../hooks/useAuditoria';
import { format } from 'date-fns';
import { es } from 'date-fns/locale';

const Auditoria: React.FC = () => {
  const {
    logs,
    estadisticas,
    cargando,
    error,
    totalRegistros,
    paginaActual,
    totalPaginas,
    cargarEstadisticas,
    aplicarFiltros,
    cambiarPagina,
    limpiarFiltros,
    refrescar,
  } = useAuditoria();

  // Estados locales para formulario de filtros
  const [mostrarFiltros, setMostrarFiltros] = useState(false);
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [busqueda, setBusqueda] = useState('');
  const [tipoUsuario, setTipoUsuario] = useState('');
  const [operacion, setOperacion] = useState('');
  const [resultado, setResultado] = useState('');
  const [tabla, setTabla] = useState('');

  // Cargar estadísticas al montar
  useEffect(() => {
    cargarEstadisticas();
  }, [cargarEstadisticas]);

  // Handlers
  const handleAplicarFiltros = () => {
    const nuevosFiltros: any = {};
    
    if (fechaDesde) nuevosFiltros.fecha_desde = fechaDesde;
    if (fechaHasta) nuevosFiltros.fecha_hasta = fechaHasta;
    if (busqueda) nuevosFiltros.search = busqueda;
    if (tipoUsuario) nuevosFiltros.tipo_usuario = tipoUsuario;
    if (operacion) nuevosFiltros.operacion = operacion;
    if (resultado) nuevosFiltros.resultado = resultado;
    if (tabla) nuevosFiltros.tabla_afectada = tabla;
    
    aplicarFiltros(nuevosFiltros);
  };

  const handleLimpiarFiltros = () => {
    setFechaDesde('');
    setFechaHasta('');
    setBusqueda('');
    setTipoUsuario('');
    setOperacion('');
    setResultado('');
    setTabla('');
    limpiarFiltros();
  };

  const handleExportar = () => {
    // TODO: Implementar exportación a CSV/Excel
    console.log('Exportar logs');
  };

  // Utilidades de renderizado
  const getResultadoIcon = (resultado: string) => {
    switch (resultado) {
      case 'EXITO':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'ERROR':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'BLOQUEADO':
        return <AlertCircle className="h-4 w-4 text-orange-600" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getResultadoBadgeClass = (resultado: string) => {
    switch (resultado) {
      case 'EXITO':
        return 'bg-green-100 text-green-800';
      case 'ERROR':
        return 'bg-red-100 text-red-800';
      case 'BLOQUEADO':
        return 'bg-orange-100 text-orange-800';
      case 'DENEGADO':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatearFecha = (fecha: string) => {
    return format(new Date(fecha), "dd/MM/yyyy HH:mm:ss", { locale: es });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-purple-100 rounded-lg">
            <Shield className="h-8 w-8 text-purple-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Auditoría del Sistema</h1>
            <p className="mt-1 text-gray-600">
              Registro completo de operaciones y actividad de usuarios
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={refrescar}
            leftIcon={<RefreshCw className="h-4 w-4" />}
            disabled={cargando}
          >
            Recargar
          </Button>
          <Button
            variant="secondary"
            onClick={handleExportar}
            leftIcon={<Download className="h-4 w-4" />}
          >
            Exportar
          </Button>
        </div>
      </div>

      {/* Estadísticas */}
      {estadisticas && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600">Total Operaciones</p>
                <p className="text-2xl font-bold text-blue-900">
                  {estadisticas.total_registros.toLocaleString()}
                </p>
              </div>
              <Activity className="h-10 w-10 text-blue-600 opacity-50" />
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-green-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600">Operaciones Exitosas</p>
                <p className="text-2xl font-bold text-green-900">
                  {estadisticas.operaciones_por_resultado.find(r => r.resultado === 'EXITO')?.total.toLocaleString() || '0'}
                </p>
              </div>
              <CheckCircle className="h-10 w-10 text-green-600 opacity-50" />
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-orange-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600">Usuarios Activos</p>
                <p className="text-2xl font-bold text-orange-900">
                  {estadisticas.usuarios_mas_activos.length}
                </p>
              </div>
              <User className="h-10 w-10 text-orange-600 opacity-50" />
            </div>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-purple-100">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600">Tablas Modificadas</p>
                <p className="text-2xl font-bold text-purple-900">
                  {estadisticas.tablas_mas_modificadas.length}
                </p>
              </div>
              <Eye className="h-10 w-10 text-purple-600 opacity-50" />
            </div>
          </Card>
        </div>
      )}

      {/* Filtros y Búsqueda */}
      <Card>
        <div className="space-y-4">
          {/* Barra de búsqueda */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por usuario, IP, descripción..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAplicarFiltros()}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <Button
              variant="primary"
              onClick={handleAplicarFiltros}
              leftIcon={<Search className="h-4 w-4" />}
            >
              Buscar
            </Button>
            <Button
              variant="outline"
              onClick={() => setMostrarFiltros(!mostrarFiltros)}
              leftIcon={<Filter className="h-4 w-4" />}
            >
              Filtros
            </Button>
          </div>

          {/* Panel de filtros avanzados */}
          {mostrarFiltros && (
            <div className="pt-4 border-t border-gray-200">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Fecha desde */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Calendar className="inline h-4 w-4 mr-1" />
                    Fecha Desde
                  </label>
                  <input
                    type="date"
                    value={fechaDesde}
                    onChange={(e) => setFechaDesde(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Fecha hasta */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    <Calendar className="inline h-4 w-4 mr-1" />
                    Fecha Hasta
                  </label>
                  <input
                    type="date"
                    value={fechaHasta}
                    onChange={(e) => setFechaHasta(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Tipo de usuario */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tipo de Usuario
                  </label>
                  <select
                    value={tipoUsuario}
                    onChange={(e) => setTipoUsuario(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">Todos</option>
                    <option value="Empleado">Empleado</option>
                    <option value="Cliente">Cliente</option>
                    <option value="Sistema">Sistema</option>
                  </select>
                </div>

                {/* Operación */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Operación
                  </label>
                  <select
                    value={operacion}
                    onChange={(e) => setOperacion(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">Todas</option>
                    <option value="LOGIN">Inicio de sesión</option>
                    <option value="LOGOUT">Cierre de sesión</option>
                    <option value="CREATE">Creación</option>
                    <option value="UPDATE">Modificación</option>
                    <option value="DELETE">Eliminación</option>
                    <option value="VIEW">Consulta</option>
                    <option value="EXPORT">Exportación</option>
                  </select>
                </div>

                {/* Resultado */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Resultado
                  </label>
                  <select
                    value={resultado}
                    onChange={(e) => setResultado(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  >
                    <option value="">Todos</option>
                    <option value="EXITO">Exitoso</option>
                    <option value="ERROR">Error</option>
                    <option value="BLOQUEADO">Bloqueado</option>
                    <option value="DENEGADO">Denegado</option>
                  </select>
                </div>

                {/* Tabla afectada */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tabla Afectada
                  </label>
                  <input
                    type="text"
                    placeholder="ej: empleados, ventas..."
                    value={tabla}
                    onChange={(e) => setTabla(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              {/* Botones de acción de filtros */}
              <div className="flex justify-end gap-2 mt-4">
                <Button variant="outline" onClick={handleLimpiarFiltros}>
                  Limpiar filtros
                </Button>
                <Button variant="primary" onClick={handleAplicarFiltros}>
                  Aplicar filtros
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Tabla de logs */}
      <Card
        title="Registros de Auditoría"
        subtitle={`${totalRegistros.toLocaleString()} registros encontrados`}
      >
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Fecha/Hora
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usuario
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Operación
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tabla
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Descripción
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Resultado
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {cargando ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-2" />
                    Cargando registros...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No se encontraron registros
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id_auditoria} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {formatearFecha(log.fecha_operacion)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{log.usuario}</div>
                      <div className="text-xs text-gray-500">{log.tipo_usuario}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {log.tipo_operacion_display || log.operacion}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                      {log.tabla_afectada || '-'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                      {log.descripcion || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getResultadoIcon(log.resultado)}
                        <Badge className={getResultadoBadgeClass(log.resultado)}>
                          {log.resultado_display || log.resultado}
                        </Badge>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {totalPaginas > 1 && (
          <div className="mt-4 flex items-center justify-between border-t border-gray-200 pt-4">
            <div className="text-sm text-gray-700">
              Mostrando página {paginaActual} de {totalPaginas}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => cambiarPagina(paginaActual - 1)}
                disabled={paginaActual === 1 || cargando}
                leftIcon={<ChevronLeft className="h-4 w-4" />}
              >
                Anterior
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => cambiarPagina(paginaActual + 1)}
                disabled={paginaActual === totalPaginas || cargando}
                rightIcon={<ChevronRight className="h-4 w-4" />}
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default Auditoria;
