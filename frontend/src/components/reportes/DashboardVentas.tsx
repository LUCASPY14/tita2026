/**
 * Dashboard de Ventas
 * 
 * Muestra análisis de ventas:
 * - Ventas por día (últimos N días)
 * - Ventas por método de pago
 * - Productos más vendidos
 * - Comparación con período anterior
 * - Tendencia
 */

import { useEffect, useState, useRef } from 'react';
import { Calendar, TrendingUp, TrendingDown, Minus, Download, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

import { Card, Skeleton } from '../common';
import reportesService from '../../services/reportes.service';
import type { DashboardVentas as DashboardVentasType } from '../../types';

export default function DashboardVentas() {
  const [dashboard, setDashboard] = useState<DashboardVentasType | null>(null);
  const [cargando, setCargando] = useState(true);
  const [ultimaActualizacion, setUltimaActualizacion] = useState<Date>(new Date());
  const [diasSeleccionados, setDiasSeleccionados] = useState(7);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    cargarDashboard();
  }, [diasSeleccionados]);

  // Auto-refresh cada 5 minutos
  useEffect(() => {
    intervalRef.current = setInterval(() => cargarDashboard(true), 5 * 60 * 1000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [diasSeleccionados]);

  const cargarDashboard = async (silencioso = false) => {
    if (!silencioso) setCargando(true);
    try {
      const data = await reportesService.getDashboardVentas({ dias: diasSeleccionados });
      setDashboard(data);
      setUltimaActualizacion(new Date());
    } catch (error) {
      console.error('Error cargando dashboard ventas:', error);
      if (!silencioso) toast.error('Error al cargar el dashboard');
    } finally {
      if (!silencioso) setCargando(false);
    }
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(valor);
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-PY', {
      month: 'short',
      day: 'numeric'
    });
  };

  if (cargando) {
    return (
      <div className="space-y-6">
        <div className="h-20 animate-pulse rounded-lg bg-gray-100" />
        <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton rows={7} cols={1} />
          <Skeleton rows={4} cols={1} />
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return (
      <Card>
        <p className="text-gray-500 text-center py-8">No hay datos disponibles</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con controles */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Dashboard de Ventas</h3>
            <p className="text-sm text-gray-500 mt-1">
              {dashboard.periodo}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={diasSeleccionados}
              onChange={(e) => setDiasSeleccionados(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={7}>Últimos 7 días</option>
              <option value={15}>Últimos 15 días</option>
              <option value={30}>Últimos 30 días</option>
              <option value={90}>Últimos 90 días</option>
            </select>
            <div className="flex flex-col items-end gap-1">
              <button
                onClick={() => cargarDashboard()}
                className="p-2 text-gray-600 hover:text-blue-600 transition-colors"
                title="Actualizar"
              >
                <RefreshCw size={20} />
              </button>
              <span className="text-xs text-gray-400">
                {ultimaActualizacion.toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* Comparación con período anterior */}
      <Card>
        <h4 className="text-sm font-medium text-gray-700 mb-4">Comparación con Período Anterior</h4>
        
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Período Actual</p>
            <p className="text-xl font-bold text-blue-600">
              {formatearMoneda(dashboard.comparacion_semana_anterior.periodo_actual)}
            </p>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Período Anterior</p>
            <p className="text-xl font-bold text-gray-700">
              {formatearMoneda(dashboard.comparacion_semana_anterior.periodo_anterior)}
            </p>
          </div>

          <div className="text-center p-4 bg-white border rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Variación</p>
            <div className="flex items-center justify-center gap-2">
              {dashboard.tendencia === 'crecimiento' && (
                <TrendingUp className="text-green-600" size={20} />
              )}
              {dashboard.tendencia === 'decrecimiento' && (
                <TrendingDown className="text-red-600" size={20} />
              )}
              {dashboard.tendencia === 'estable' && (
                <Minus className="text-gray-600" size={20} />
              )}
              <p className={`text-xl font-bold ${
                dashboard.tendencia === 'crecimiento' ? 'text-green-600' :
                dashboard.tendencia === 'decrecimiento' ? 'text-red-600' :
                'text-gray-700'
              }`}>
                {dashboard.comparacion_semana_anterior.variacion_porcentual > 0 ? '+' : ''}
                {dashboard.comparacion_semana_anterior.variacion_porcentual.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ventas por Día */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-700">Ventas por Día</h4>
            <Calendar size={16} className="text-gray-400" />
          </div>

          <div className="space-y-3">
            {dashboard.ventas_por_dia.slice().reverse().map((venta, index) => {
              const maxMonto = Math.max(...dashboard.ventas_por_dia.map(v => v.total_vendido));
              const porcentaje = (venta.total_vendido / maxMonto) * 100;

              return (
                <div key={index} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">{formatearFecha(venta.fecha)}</span>
                    <span className="font-medium text-gray-900">{formatearMoneda(venta.total_vendido)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${porcentaje}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    {venta.cantidad_ventas} {venta.cantidad_ventas === 1 ? 'venta' : 'ventas'} · 
                    Promedio: {formatearMoneda(venta.ticket_promedio)}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Ventas por Método de Pago */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-700">Ventas por Método de Pago</h4>
          </div>

          <div className="space-y-4">
            {dashboard.ventas_por_metodo_pago.map((metodo, index) => {
              const totalVentas = dashboard.ventas_por_metodo_pago.reduce((sum, m) => sum + m.total, 0);
              const porcentaje = totalVentas > 0 ? (metodo.total / totalVentas) * 100 : 0;

              const colores: Record<string, string> = {
                efectivo: 'bg-green-600',
                tarjeta: 'bg-blue-600',
                online: 'bg-purple-600',
                credito: 'bg-orange-600'
              };

              const color = colores[metodo.metodo_pago] || 'bg-gray-600';

              return (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 capitalize">{metodo.metodo_pago}</span>
                    <span className="text-sm font-medium text-gray-900">{porcentaje.toFixed(1)}%</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className={`${color} h-2 rounded-full transition-all duration-500`}
                        style={{ width: `${porcentaje}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-700 w-32 text-right">
                      {formatearMoneda(metodo.total)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {metodo.cantidad} {metodo.cantidad === 1 ? 'venta' : 'ventas'}
                  </p>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Productos Más Vendidos */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-medium text-gray-700">Top 10 Productos Más Vendidos</h4>
          <button
            className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center gap-2"
            onClick={() => toast.success('Función de exportación próximamente')}
          >
            <Download size={16} />
            Exportar
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  #
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Código
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Producto
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cantidad
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Vendido
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {dashboard.productos_mas_vendidos.map((producto, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                    {index + 1}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700 font-mono">
                    {producto.id_producto__codigo}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {producto.id_producto__nombre}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                    {producto.cantidad_vendida}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-medium text-green-600">
                    {formatearMoneda(producto.total_vendido)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
