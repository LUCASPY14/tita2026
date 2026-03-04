/**
 * Dashboard Principal Mejorado
 * Panel de control con KPIs en tiempo real y análisis de tendencias
 */

import React, { useEffect, useState } from 'react';
import {
  Users,
  ShoppingCart,
  CreditCard,
  Package,
  AlertTriangle,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
} from 'lucide-react';
import { Card, Button, Badge } from '../../components/common';
import { useDashboard } from '../../hooks/useDashboard';
import { useAuthContext } from '../../contexts/AuthContext';
import dashboardService from '../../services/dashboard.service';

const Dashboard: React.FC = () => {
  const { user } = useAuthContext();
  const {
    kpis,
    dashboardVentas,
    cargando,
    error,
    cargarDashboardVentas,
    cambiarDiasAnalisis,
    refrescarTodo,
  } = useDashboard();

  const [periodoSeleccionado, setPeriodoSeleccionado] = useState<7 | 15 | 30>(7);

  useEffect(() => {
    cargarDashboardVentas(periodoSeleccionado);
  }, [periodoSeleccionado, cargarDashboardVentas]);

  const handleCambioPeriodo = (dias: 7 | 15 | 30) => {
    setPeriodoSeleccionado(dias);
    cambiarDiasAnalisis(dias);
  };

  const formatearMoneda = (monto: number) => {
    return dashboardService.formatearMoneda(monto);
  };

  const formatearPorcentaje = (valor: number) => {
    return dashboardService.formatearPorcentaje(valor);
  };

  const obtenerIconoTendencia = (variacion: number) => {
    if (variacion > 0) return <ArrowUpRight className="h-4 w-4 text-green-600" />;
    if (variacion < 0) return <ArrowDownRight className="h-4 w-4 text-red-600" />;
    return <span className="text-gray-600">→</span>;
  };

  const obtenerColorTendencia = (variacion: number) => {
    if (variacion > 0) return 'text-green-600';
    if (variacion < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            ¡Bienvenido, {user?.username || 'Usuario'}! 👋
          </h1>
          <p className="mt-1 text-gray-600">
            Panel de control - {new Date().toLocaleDateString('es-PY', { 
              weekday: 'long', 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </p>
        </div>

        <div className="flex gap-2">
          {/* Selector de período */}
          <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg p-1">
            <button
              onClick={() => handleCambioPeriodo(7)}
              className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                periodoSeleccionado === 7
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              7 días
            </button>
            <button
              onClick={() => handleCambioPeriodo(15)}
              className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                periodoSeleccionado === 15
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              15 días
            </button>
            <button
              onClick={() => handleCambioPeriodo(30)}
              className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
                periodoSeleccionado === 30
                  ? 'bg-purple-100 text-purple-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              30 días
            </button>
          </div>

          <Button
            variant="outline"
            onClick={refrescarTodo}
            disabled={cargando}
            leftIcon={<RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} />}
          >
            Actualizar
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2 text-red-800">
          <AlertTriangle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      )}

      {/* KPIs Principales */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {/* Ventas del Día */}
        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-amber-700">Ventas del Día</p>
              <p className="mt-2 text-3xl font-bold text-amber-900">
                {kpis ? formatearMoneda(kpis.ventas_del_dia) : '-'}
              </p>
              <p className="mt-1 text-sm text-amber-600">
                {kpis ? `${kpis.cantidad_ventas} transacciones` : 'Cargando...'}
              </p>
            </div>
            <div className="p-3 bg-amber-200 rounded-lg">
              <ShoppingCart className="h-6 w-6 text-amber-700" />
            </div>
          </div>
        </Card>

        {/* Recargas del Día */}
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-green-700">Recargas del Día</p>
              <p className="mt-2 text-3xl font-bold text-green-900">
                {kpis ? formatearMoneda(kpis.recargas_del_dia) : '-'}
              </p>
              <p className="mt-1 text-sm text-green-600">
                {kpis ? `${kpis.cantidad_recargas} recargas` : 'Cargando...'}
              </p>
            </div>
            <div className="p-3 bg-green-200 rounded-lg">
              <CreditCard className="h-6 w-6 text-green-700" />
            </div>
          </div>
        </Card>

        {/* Tarjetas Activas */}
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-blue-700">Tarjetas Activas</p>
              <p className="mt-2 text-3xl font-bold text-blue-900">
                {kpis ? kpis.tarjetas_activas.toLocaleString() : '-'}
              </p>
              <p className="mt-1 text-sm text-blue-600">
                {kpis ? formatearMoneda(kpis.saldo_total_tarjetas) : 'Saldo total'}
              </p>
            </div>
            <div className="p-3 bg-blue-200 rounded-lg">
              <Users className="h-6 w-6 text-blue-700" />
            </div>
          </div>
        </Card>

        {/* Ticket Promedio */}
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-purple-700">Ticket Promedio</p>
              <p className="mt-2 text-3xl font-bold text-purple-900">
                {kpis ? formatearMoneda(kpis.ticket_promedio) : '-'}
              </p>
              {kpis && kpis.productos_bajo_stock > 0 && (
                <div className="mt-1 flex items-center gap-1 text-sm text-orange-600">
                  <AlertTriangle className="h-4 w-4" />
                  <span>{kpis.productos_bajo_stock} productos bajo stock</span>
                </div>
              )}
            </div>
            <div className="p-3 bg-purple-200 rounded-lg">
              <Wallet className="h-6 w-6 text-purple-700" />
            </div>
          </div>
        </Card>
      </div>

      {/* Análisis de Tendencias */}
      {dashboardVentas && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Comparación con Período Anterior */}
          <Card title="Comparación de Rendimiento" subtitle={`Últimos ${periodoSeleccionado} días`}>
            <div className="space-y-4">
              <div className="flex items-center justify-between py-3 border-b border-gray-100">
                <div>
                  <p className="text-sm font-medium text-gray-600">Período Actual</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatearMoneda(dashboardVentas.comparacion_semana_anterior.periodo_actual)}
                  </p>
                </div>
                <Badge
                  className={
                    dashboardVentas.tendencia === 'crecimiento'
                      ? 'bg-green-100 text-green-800'
                      : dashboardVentas.tendencia === 'decrecimiento'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }
                >
                  {dashboardVentas.tendencia === 'crecimiento'
                    ? 'Crecimiento'
                    : dashboardVentas.tendencia === 'decrecimiento'
                    ? 'Decrecimiento'
                    : 'Estable'}
                </Badge>
              </div>

              <div className="flex items-center justify-between py-3 border-b border-gray-100">
                <div>
                  <p className="text-sm font-medium text-gray-600">Período Anterior</p>
                  <p className="text-xl font-bold text-gray-900">
                    {formatearMoneda(dashboardVentas.comparacion_semana_anterior.periodo_anterior)}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium text-gray-600">Variación</p>
                  <div className="flex items-center gap-2 mt-1">
                    {obtenerIconoTendencia(dashboardVentas.comparacion_semana_anterior.variacion_porcentual)}
                    <span className={`text-xl font-bold ${obtenerColorTendencia(dashboardVentas.comparacion_semana_anterior.variacion_porcentual)}`}>
                      {formatearPorcentaje(Math.abs(dashboardVentas.comparacion_semana_anterior.variacion_porcentual))}
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-600">Diferencia</p>
                  <p className={`text-lg font-bold ${obtenerColorTendencia(dashboardVentas.comparacion_semana_anterior.periodo_actual - dashboardVentas.comparacion_semana_anterior.periodo_anterior)}`}>
                    {formatearMoneda(dashboardVentas.comparacion_semana_anterior.periodo_actual - dashboardVentas.comparacion_semana_anterior.periodo_anterior)}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Productos Más Vendidos */}
          <Card 
            title="Productos Más Vendidos" 
            subtitle={`Top 5 - Últimos ${periodoSeleccionado} días`}
            headerAction={
              <Badge variant="primary">
                <Package className="inline h-3 w-3 mr-1" />
                {dashboardVentas.productos_mas_vendidos.length} productos
              </Badge>
            }
          >
            <div className="space-y-3">
              {dashboardVentas.productos_mas_vendidos.slice(0, 5).map((producto, index) => (
                <div
                  key={producto.id_producto__codigo}
                  className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex items-center justify-center w-8 h-8 bg-purple-100 rounded-full">
                      <span className="text-sm font-bold text-purple-600">#{index + 1}</span>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{producto.id_producto__nombre}</p>
                      <p className="text-xs text-gray-500">{producto.id_producto__codigo}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">
                      {producto.cantidad_vendida} unidades
                    </p>
                    <p className="text-sm text-gray-600">
                      {formatearMoneda(producto.total_vendido)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Métodos de Pago */}
      {dashboardVentas && dashboardVentas.ventas_por_metodo_pago.length > 0 && (
        <Card title="Distribución por Método de Pago" subtitle={`Últimos ${periodoSeleccionado} días`}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {dashboardVentas.ventas_por_metodo_pago.map((metodo) => (
              <div
                key={metodo.metodo_pago}
                className="p-4 bg-gray-50 rounded-lg border border-gray-200"
              >
                <p className="text-sm font-medium text-gray-600 capitalize">
                  {metodo.metodo_pago}
                </p>
                <p className="mt-1 text-2xl font-bold text-gray-900">
                  {formatearMoneda(metodo.total)}
                </p>
                <p className="mt-0.5 text-sm text-gray-600">
                  {metodo.cantidad} transacciones
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
