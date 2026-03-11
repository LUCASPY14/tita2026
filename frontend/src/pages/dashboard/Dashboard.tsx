import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useAuth } from '../../hooks/useAuth';
import { useDashboard } from '../../hooks/useDashboard';
import { Card, Badge, Button } from '../../components/common';
import {
  TrendingUp,
  Users,
  Package,
  Utensils,
  CreditCard,
  ShoppingCart,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

// ─── Utils ────────────────────────────────────────────────────────────────────

const formatGs = (monto: number) =>
  new Intl.NumberFormat('es-PY', {
    style: 'currency',
    currency: 'PYG',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(monto);

const formatFechaCorta = (fecha: string) => {
  try {
    return format(parseISO(fecha), 'd MMM', { locale: es });
  } catch {
    return fecha;
  }
};

// ─── StatCard ─────────────────────────────────────────────────────────────────

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  icon: React.ElementType;
  color: 'amber' | 'green' | 'blue' | 'purple';
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, icon: Icon, color, loading }) => {
  const isPositive = (change ?? 0) >= 0;

  const colorClasses = {
    amber: 'bg-amber-50 text-amber-600',
    green: 'bg-green-50 text-green-600',
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <Card variant="elevated" padding="lg" hoverable>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          {loading ? (
            <div className="mt-2 h-9 w-32 animate-pulse rounded bg-gray-200" />
          ) : (
            <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
          )}
          {change !== undefined && !loading && (
            <div className={`mt-2 flex items-center gap-1 text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {isPositive ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
              <span>{Math.abs(change).toFixed(1)}%</span>
              <span className="ml-1 text-gray-500">vs semana anterior</span>
            </div>
          )}
        </div>
        <div className={`rounded-lg p-3 ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  );
};

// ─── Tooltip personalizado para el gráfico ────────────────────────────────────

const TooltipVentas = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg text-sm">
      <p className="font-semibold text-gray-700 mb-1">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.name} style={{ color: entry.color }}>
          {entry.name}: {entry.name === 'Ventas (Gs.)' ? formatGs(entry.value) : entry.value}
        </p>
      ))}
    </div>
  );
};

// ─── Dashboard ────────────────────────────────────────────────────────────────

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const {
    kpis,
    dashboardVentas,
    dashboardRecargas,
    cargando,
    cargarKpis,
    cargarDashboardVentas,
    cargarDashboardRecargas,
    refrescarTodo,
  } = useDashboard();

  useEffect(() => {
    cargarKpis();
    cargarDashboardVentas(7);
    cargarDashboardRecargas(7);
  }, [cargarKpis, cargarDashboardVentas, cargarDashboardRecargas]);

  // Preparar datos para gráficos
  const datosVentas = (dashboardVentas?.ventas_por_dia ?? []).map((d) => ({
    fecha: formatFechaCorta(d.fecha),
    'Ventas (Gs.)': d.total_vendido,
    Cantidad: d.cantidad_ventas,
  }));

  const datosRecargas = (dashboardRecargas?.recargas_por_dia ?? []).map((d) => ({
    fecha: formatFechaCorta(d.fecha),
    'Monto (Gs.)': d.monto_total,
    Cantidad: d.cantidad_recargas,
  }));

  const variacionVentas = dashboardVentas?.comparacion_semana_anterior?.variacion_porcentual;

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            ¡Bienvenido, {user?.username || 'Usuario'}! 👋
          </h1>
          <p className="mt-1 text-gray-600 flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            {new Date().toLocaleDateString('es-PY', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <Button
          variant="outline"
          onClick={refrescarTodo}
          leftIcon={<RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} />}
          disabled={cargando}
        >
          Actualizar
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Ventas del Día"
          value={kpis ? formatGs(kpis.ventas_del_dia) : '—'}
          change={variacionVentas}
          icon={TrendingUp}
          color="amber"
          loading={cargando && !kpis}
        />
        <StatCard
          title="Tarjetas Activas"
          value={kpis ? kpis.tarjetas_activas.toLocaleString('es-PY') : '—'}
          icon={Users}
          color="green"
          loading={cargando && !kpis}
        />
        <StatCard
          title="Recargas del Día"
          value={kpis ? formatGs(kpis.recargas_del_dia) : '—'}
          icon={CreditCard}
          color="blue"
          loading={cargando && !kpis}
        />
        <StatCard
          title="Ticket Promedio"
          value={kpis ? formatGs(kpis.ticket_promedio) : '—'}
          icon={Utensils}
          color="purple"
          loading={cargando && !kpis}
        />
      </div>

      {/* Acciones Rápidas */}
      <Card title="Acciones Rápidas" subtitle="Operaciones frecuentes">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Button variant="primary" fullWidth leftIcon={<ShoppingCart className="h-5 w-5" />} onClick={() => navigate('/pos')}>
            Nueva Venta
          </Button>
          <Button variant="secondary" fullWidth leftIcon={<CreditCard className="h-5 w-5" />} onClick={() => navigate('/recargas')}>
            Recargar Tarjeta
          </Button>
          <Button variant="outline" fullWidth leftIcon={<Users className="h-5 w-5" />} onClick={() => navigate('/clientes')}>
            Clientes
          </Button>
          <Button variant="outline" fullWidth leftIcon={<Package className="h-5 w-5" />} onClick={() => navigate('/inventario')}>
            Inventario
          </Button>
        </div>
      </Card>

      {/* Gráficos de tendencia */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Ventas por día */}
        <Card
          title="Tendencia de Ventas"
          subtitle="Últimos 7 días"
          headerAction={
            dashboardVentas?.tendencia && (
              <Badge
                variant={
                  dashboardVentas.tendencia === 'crecimiento'
                    ? 'success'
                    : dashboardVentas.tendencia === 'decrecimiento'
                    ? 'danger'
                    : 'default'
                }
              >
                {dashboardVentas.tendencia === 'crecimiento'
                  ? '↑ Creciendo'
                  : dashboardVentas.tendencia === 'decrecimiento'
                  ? '↓ Bajando'
                  : '→ Estable'}
              </Badge>
            )
          }
        >
          {datosVentas.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-gray-400 text-sm">
              {cargando ? 'Cargando datos...' : 'Sin datos de ventas'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={datosVentas} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorVentas" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="fecha" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip content={<TooltipVentas />} />
                <Area
                  type="monotone"
                  dataKey="Ventas (Gs.)"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  fill="url(#colorVentas)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </Card>

        {/* Recargas por día */}
        <Card title="Tendencia de Recargas" subtitle="Últimos 7 días">
          {datosRecargas.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-gray-400 text-sm">
              {cargando ? 'Cargando datos...' : 'Sin datos de recargas'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={datosRecargas} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="fecha" tick={{ fontSize: 12 }} />
                <YAxis yAxisId="left" tick={{ fontSize: 12 }} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
                <Tooltip content={<TooltipVentas />} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar yAxisId="left" dataKey="Monto (Gs.)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar yAxisId="right" dataKey="Cantidad" fill="#93c5fd" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      {/* Productos con stock bajo */}
      {kpis && kpis.productos_bajo_stock > 0 && (
        <Card
          title="Alerta de Stock"
          subtitle="Productos que requieren reabastecimiento"
          headerAction={
            <Badge variant="warning">
              <AlertTriangle className="mr-1 h-3 w-3 inline" />
              {kpis.productos_bajo_stock} productos
            </Badge>
          }
        >
          <div className="flex items-center justify-between">
            <p className="text-gray-600">
              Hay <strong>{kpis.productos_bajo_stock}</strong> productos por debajo del stock mínimo.
            </p>
            <Button variant="outline" onClick={() => navigate('/inventario')}>
              Ver Inventario
            </Button>
          </div>
        </Card>
      )}

      {/* Resumen del día */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <Card padding="md">
          <p className="text-sm text-gray-500">Ventas de hoy</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {kpis ? kpis.cantidad_ventas : '—'}
          </p>
          <p className="text-xs text-gray-400">transacciones</p>
        </Card>
        <Card padding="md">
          <p className="text-sm text-gray-500">Recargas de hoy</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {kpis ? kpis.cantidad_recargas : '—'}
          </p>
          <p className="text-xs text-gray-400">operaciones</p>
        </Card>
        <Card padding="md">
          <p className="text-sm text-gray-500">Saldo total en tarjetas</p>
          <p className="mt-1 text-2xl font-bold text-gray-900">
            {kpis ? formatGs(kpis.saldo_total_tarjetas) : '—'}
          </p>
          <p className="text-xs text-gray-400">en circulación</p>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
