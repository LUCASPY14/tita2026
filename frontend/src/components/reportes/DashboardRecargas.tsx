/**
 * Dashboard de Recargas
 * 
 * Muestra análisis de recargas:
 * - Recargas por día
 * - Recargas por método de pago
 * - Comisiones generadas
 * - Tasa de éxito
 */

import { useEffect, useState } from 'react';
import { Wallet, TrendingUp, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

import { Card } from '../common';
import reportesService from '../../services/reportes.service';
import type { DashboardRecargas as DashboardRecargasType } from '../../types';

export default function DashboardRecargas() {
  const [dashboard, setDashboard] = useState<DashboardRecargasType | null>(null);
  const [cargando, setCargando] = useState(true);
  const [diasSeleccionados, setDiasSeleccionados] = useState(7);

  useEffect(() => {
    cargarDashboard();
  }, [diasSeleccionados]);

  const cargarDashboard = async () => {
    setCargando(true);
    try {
      const data = await reportesService.getDashboardRecargas({ dias: diasSeleccionados });
      setDashboard(data);
    } catch (error) {
      console.error('Error cargando dashboard recargas:', error);
      toast.error('Error al cargar el dashboard');
    } finally {
      setCargando(false);
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
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
            <h3 className="text-lg font-medium text-gray-900">Dashboard de Recargas</h3>
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
          </div>
        </div>
      </Card>

      {/* KPIs principales de recargas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Recargas</p>
              <p className="text-2xl font-bold text-gray-900 mt-2">
                {dashboard.total_recargas}
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <Wallet className="text-blue-600" size={24} />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Recargas Exitosas</p>
              <p className="text-2xl font-bold text-green-600 mt-2">
                {dashboard.recargas_exitosas}
              </p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <CheckCircle className="text-green-600" size={24} />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tasa de Éxito</p>
              <p className="text-2xl font-bold text-blue-600 mt-2">
                {dashboard.tasa_exito.toFixed(1)}%
              </p>
            </div>
            <div className="p-3 bg-blue-100 rounded-full">
              <TrendingUp className="text-blue-600" size={24} />
            </div>
          </div>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Comisiones</p>
              <p className="text-xl font-bold text-purple-600 mt-2">
                {formatearMoneda(dashboard.comisiones_generadas)}
              </p>
            </div>
            <div className="p-3 bg-purple-100 rounded-full">
              <TrendingUp className="text-purple-600" size={24} />
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recargas por Día */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-700">Recargas por Día</h4>
          </div>

          <div className="space-y-3">
            {dashboard.recargas_por_dia.slice().reverse().map((recarga, index) => {
              const maxMonto = Math.max(...dashboard.recargas_por_dia.map(r => r.monto_total));
              const porcentaje = (recarga.monto_total / maxMonto) * 100;

              return (
                <div key={index} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">{formatearFecha(recarga.fecha)}</span>
                    <span className="font-medium text-gray-900">{formatearMoneda(recarga.monto_total)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${porcentaje}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{recarga.cantidad_recargas} recargas</span>
                    <span>Comisión: {formatearMoneda(recarga.comision_total)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Recargas por Método de Pago */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-sm font-medium text-gray-700">Recargas por Método de Pago</h4>
          </div>

          <div className="space-y-4">
            {dashboard.recargas_por_metodo.map((metodo, index) => {
              const totalRecargas = dashboard.recargas_por_metodo.reduce((sum, m) => sum + m.monto_total, 0);
              const porcentaje = totalRecargas > 0 ? (metodo.monto_total / totalRecargas) * 100 : 0;

              const colores: Record<string, string> = {
                efectivo: 'bg-green-600',
                tarjeta_pos: 'bg-blue-600',
                transferencia: 'bg-purple-600',
                bancard: 'bg-orange-600'
              };

              const color = colores[metodo.metodo_pago] || 'bg-gray-600';

              return (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 capitalize">
                      {metodo.metodo_pago.replace('_', ' ')}
                    </span>
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
                      {formatearMoneda(metodo.monto_total)}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{metodo.cantidad} recargas</span>
                    <span>Comisión: {formatearMoneda(metodo.comision_total)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </div>

      {/* Análisis de rendimiento */}
      <Card>
        <h4 className="text-sm font-medium text-gray-700 mb-4">Análisis de Rendimiento</h4>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <div className="flex items-center justify-center mb-3">
              <Wallet className="text-blue-600" size={32} />
            </div>
            <p className="text-sm text-gray-600 mb-2">Promedio por Recarga</p>
            <p className="text-2xl font-bold text-blue-600">
              {formatearMoneda(
                dashboard.total_recargas > 0
                  ? dashboard.recargas_por_dia.reduce((sum, r) => sum + r.monto_total, 0) / dashboard.total_recargas
                  : 0
              )}
            </p>
          </div>

          <div className="text-center p-6 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
            <div className="flex items-center justify-center mb-3">
              <CheckCircle className="text-green-600" size={32} />
            </div>
            <p className="text-sm text-gray-600 mb-2">Tasa de Éxito</p>
            <p className="text-2xl font-bold text-green-600">
              {dashboard.tasa_exito.toFixed(1)}%
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {dashboard.recargas_exitosas} de {dashboard.total_recargas} recargas
            </p>
          </div>

          <div className="text-center p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
            <div className="flex items-center justify-center mb-3">
              <TrendingUp className="text-purple-600" size={32} />
            </div>
            <p className="text-sm text-gray-600 mb-2">Comisiones Generadas</p>
            <p className="text-2xl font-bold text-purple-600">
              {formatearMoneda(dashboard.comisiones_generadas)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              En {dashboard.recargas_exitosas} recargas exitosas
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
