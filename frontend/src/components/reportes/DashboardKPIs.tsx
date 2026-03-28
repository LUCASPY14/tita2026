/**
 * Dashboard de KPIs Principales
 * 
 * Muestra métricas clave del día actual:
 * - Ventas del día
 * - Recargas del día
 * - Tarjetas activas
 * - Productos bajo stock
 */

import { useEffect, useState, useRef } from 'react';
import { 
  DollarSign, 
  ShoppingCart, 
  Wallet, 
  CreditCard, 
  AlertTriangle,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

import { Card, SkeletonKPI } from '../common';
import reportesService from '../../services/reportes.service';
import type { DashboardKPIs as DashboardKPIsType } from '../../types';

export default function DashboardKPIs() {
  const [kpis, setKpis] = useState<DashboardKPIsType | null>(null);
  const [cargando, setCargando] = useState(true);
  const [ultimaActualizacion, setUltimaActualizacion] = useState<Date>(new Date());
  const [fechaSeleccionada, setFechaSeleccionada] = useState<string>(
    new Date().toISOString().split('T')[0]
  );
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    cargarKPIs();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fechaSeleccionada]);

  // Auto-refresh cada 5 minutos sólo si es el día actual
  useEffect(() => {
    const hoy = new Date().toISOString().split('T')[0];
    if (fechaSeleccionada !== hoy) return;

    intervalRef.current = setInterval(() => {
      cargarKPIs(true);
    }, 5 * 60 * 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fechaSeleccionada]);

  const cargarKPIs = async (silencioso = false) => {
    if (!silencioso) setCargando(true);
    try {
      const data = await reportesService.getKPIsPrincipales(fechaSeleccionada);
      setKpis(data);
      setUltimaActualizacion(new Date());
    } catch (error) {
      console.error('Error cargando KPIs:', error);
      if (!silencioso) toast.error('Error al cargar los KPIs');
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

  if (cargando) {
    return (
      <div className="space-y-6">
        <div className="h-20 animate-pulse rounded-lg bg-gray-100" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map(i => <SkeletonKPI key={i} />)}
        </div>
        <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
      </div>
    );
  }

  if (!kpis) {
    return (
      <Card>
        <p className="text-gray-500 text-center py-8">No hay datos disponibles</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Selector de fecha */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">KPIs del Día</h3>
            <p className="text-sm text-gray-500 mt-1">
              Métricas principales del negocio
            </p>
          </div>
          <div className="flex items-center gap-4">
            <input
              type="date"
              value={fechaSeleccionada}
              onChange={(e) => setFechaSeleccionada(e.target.value)}
              max={new Date().toISOString().split('T')[0]}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex flex-col items-end gap-1">
              <button
                onClick={() => cargarKPIs()}
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

      {/* Grid de KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Ventas del Día */}
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Ventas del Día</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {formatearMoneda(kpis.ventas_del_dia)}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {kpis.cantidad_ventas} {kpis.cantidad_ventas === 1 ? 'venta' : 'ventas'}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <DollarSign className="text-green-600" size={24} />
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">Ticket Promedio</p>
            <p className="text-sm font-medium text-gray-700">
              {formatearMoneda(kpis.ticket_promedio)}
            </p>
          </div>
        </Card>

        {/* Recargas del Día */}
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Recargas del Día</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {formatearMoneda(kpis.recargas_del_dia)}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                {kpis.cantidad_recargas} {kpis.cantidad_recargas === 1 ? 'recarga' : 'recargas'}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Wallet className="text-blue-600" size={24} />
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500">Saldo Total Tarjetas</p>
            <p className="text-sm font-medium text-gray-700">
              {formatearMoneda(kpis.saldo_total_tarjetas)}
            </p>
          </div>
        </Card>

        {/* Tarjetas Activas */}
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tarjetas Activas</p>
              <p className="text-4xl font-bold text-gray-900 mt-2">
                {kpis.tarjetas_activas}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                En circulación
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <CreditCard className="text-purple-600" size={24} />
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 text-green-600">
              <TrendingUp size={16} />
              <span className="text-xs font-medium">Activo</span>
            </div>
          </div>
        </Card>

        {/* Productos Bajo Stock */}
        <Card className={`hover:shadow-lg transition-shadow ${kpis.productos_bajo_stock > 0 ? 'border-orange-200' : ''}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Productos Bajo Stock</p>
              <p className="text-4xl font-bold text-gray-900 mt-2">
                {kpis.productos_bajo_stock}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Requieren reposición
              </p>
            </div>
            <div className={`p-3 rounded-full ${kpis.productos_bajo_stock > 0 ? 'bg-orange-100' : 'bg-gray-100'}`}>
              {kpis.productos_bajo_stock > 0 ? (
                <AlertTriangle className="text-orange-600" size={24} />
              ) : (
                <ShoppingCart className="text-gray-600" size={24} />
              )}
            </div>
          </div>
          {kpis.productos_bajo_stock > 0 && (
            <div className="mt-4 pt-4 border-t border-orange-200">
              <div className="flex items-center gap-2 text-orange-600">
                <AlertTriangle size={16} />
                <span className="text-xs font-medium">Requiere atención</span>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Resumen del día */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Resumen del Día</h3>
            <p className="text-sm text-gray-500 mt-1">
              {new Date(fechaSeleccionada).toLocaleDateString('es-PY', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Total Ingresos</p>
            <p className="text-2xl font-bold text-green-600">
              {formatearMoneda(kpis.ventas_del_dia + kpis.recargas_del_dia)}
            </p>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Total Transacciones</p>
            <p className="text-2xl font-bold text-blue-600">
              {kpis.cantidad_ventas + kpis.cantidad_recargas}
            </p>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-2">Ticket Promedio</p>
            <p className="text-2xl font-bold text-purple-600">
              {formatearMoneda(kpis.ticket_promedio)}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
