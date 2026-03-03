/**
 * Página de Reportes y Estadísticas
 * 
 * Muestra dashboards y reportes del sistema:
 * - KPIs principales
 * - Dashboard de ventas
 * - Dashboard de recargas
 * - Reporte financiero
 * - Reportes personalizados
 */

import { useState } from 'react';
import { BarChart3, TrendingUp, Wallet, FileText } from 'lucide-react';

// Importar componentes (crearemos después)
import  { DashboardKPIs } from '../components/reportes';
import  { DashboardVentas } from '../components/reportes';
import  { DashboardRecargas } from '../components/reportes';
import  { ReportesPersonalizados } from '../components/reportes';

type Vista = 'kpis' | 'ventas' | 'recargas' | 'reportes';

export default function Reportes() {
  const [vista, setVista] = useState<Vista>('kpis');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-800">Reportes y Estadísticas</h1>
        <p className="text-gray-600 mt-1">
          Análisis de ventas, recargas y métricas del negocio
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setVista('kpis')}
            className={`
              flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
              ${vista === 'kpis'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            <BarChart3 size={20} />
            KPIs Principales
          </button>

          <button
            onClick={() => setVista('ventas')}
            className={`
              flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
              ${vista === 'ventas'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            <TrendingUp size={20} />
            Dashboard Ventas
          </button>

          <button
            onClick={() => setVista('recargas')}
            className={`
              flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
              ${vista === 'recargas'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            <Wallet size={20} />
            Dashboard Recargas
          </button>

          <button
            onClick={() => setVista('reportes')}
            className={`
              flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors
              ${vista === 'reportes'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }
            `}
          >
            <FileText size={20} />
            Reportes Personalizados
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="mt-6">
        {vista === 'kpis' && <DashboardKPIs />}
        {vista === 'ventas' && <DashboardVentas />}
        {vista === 'recargas' && <DashboardRecargas />}
        {vista === 'reportes' && <ReportesPersonalizados />}
      </div>
    </div>
  );
}
