/**
 * Página de Reportes y Estadísticas
 *
 * Muestra dashboards y reportes del sistema:
 * - KPIs principales
 * - Dashboard de ventas
 * - Dashboard de recargas
 * - Reportes personalizados
 */

import { useState } from 'react';
import { BarChart3, TrendingUp, Wallet, FileText } from 'lucide-react';

import { DashboardKPIs } from '../components/reportes';
import { DashboardVentas } from '../components/reportes';
import { DashboardRecargas } from '../components/reportes';
import { ReportesPersonalizados } from '../components/reportes';

type Vista = 'kpis' | 'ventas' | 'recargas' | 'reportes';

const TAB_ITEMS: { id: Vista; label: string; Icon: React.ElementType }[] = [
  { id: 'kpis',     label: 'KPIs Principales',       Icon: BarChart3 },
  { id: 'ventas',   label: 'Dashboard Ventas',        Icon: TrendingUp },
  { id: 'recargas', label: 'Dashboard Recargas',      Icon: Wallet },
  { id: 'reportes', label: 'Reportes Personalizados', Icon: FileText },
];

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
        <nav className="-mb-px flex space-x-8" aria-label="Pestañas de reportes">
          {TAB_ITEMS.map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => setVista(id)}
              className={[
                'flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors',
                vista === id
                  ? 'border-amber-500 text-amber-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              ].join(' ')}
              aria-current={vista === id ? 'page' : undefined}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div>
        {vista === 'kpis'     && <DashboardKPIs />}
        {vista === 'ventas'   && <DashboardVentas />}
        {vista === 'recargas' && <DashboardRecargas />}
        {vista === 'reportes' && <ReportesPersonalizados />}
      </div>
    </div>
  );
}
