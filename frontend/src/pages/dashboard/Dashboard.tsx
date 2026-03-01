import React from 'react';
import { useAuth } from '@hooks/useAuth';
import Button from '@components/common/Button';

interface StatCardProps {
  title: string;
  value: string | number;
  label: string;
  icon?: React.ReactNode;
  color?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, label, icon, color = 'primary' }) => {
  return (
    <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-600 text-sm font-medium">{title}</h3>
        {icon && <div className={`text-${color}-600`}>{icon}</div>}
      </div>
      <p className={`text-3xl font-bold text-${color}-600 mb-1`}>{value}</p>
      <p className="text-gray-500 text-sm">{label}</p>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const { user, logout } = useAuth();

  const handleLogout = (): void => {
    logout();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-500">Cantina Tita</p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">
                Bienvenido, <span className="font-semibold">{user?.username || 'Usuario'}</span>
              </span>
              <Button 
                variant="danger" 
                onClick={handleLogout}
                className="!px-4 !py-2"
              >
                Cerrar Sesión
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Ventas del Día"
            value="Gs. 0"
            label="Total vendido hoy"
            color="primary"
          />
          <StatCard
            title="Clientes"
            value="0"
            label="Total registrados"
            color="green"
          />
          <StatCard
            title="Productos"
            value="0"
            label="En inventario"
            color="yellow"
          />
          <StatCard
            title="Almuerzos"
            value="0"
            label="Servidos hoy"
            color="purple"
          />
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Acciones Rápidas</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="primary" fullWidth>
              📝 Nueva Venta
            </Button>
            <Button variant="secondary" fullWidth>
              👥 Nuevo Cliente
            </Button>
            <Button variant="success" fullWidth>
              📦 Nuevo Producto
            </Button>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Actividad Reciente</h2>
          <div className="text-center text-gray-500 py-8">
            <p>No hay actividad reciente</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
