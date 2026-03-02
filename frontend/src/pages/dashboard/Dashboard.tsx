import React from 'react';
import { useAuth } from '../../hooks/useAuth';
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
  Calendar
} from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  change: number;
  icon: React.ElementType;
  color: 'amber' | 'green' | 'blue' | 'purple';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, icon: Icon, color }) => {
  const isPositive = change >= 0;
  
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
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
          <div className={`mt-2 flex items-center gap-1 text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? (
              <ArrowUpRight className="h-4 w-4" />
            ) : (
              <ArrowDownRight className="h-4 w-4" />
            )}
            <span>{Math.abs(change)}%</span>
            <span className="text-gray-500 ml-1">vs mes anterior</span>
          </div>
        </div>
        <div className={`rounded-lg p-3 ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          ¡Bienvenido, {user?.username || 'Usuario'}! 👋
        </h1>
        <p className="mt-2 text-gray-600">
          Aquí está el resumen de tu cantina hoy
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Ventas del Día"
          value="Gs. 1.250.000"
          change={12.5}
          icon={TrendingUp}
          color="amber"
        />
        <StatCard
          title="Clientes Activos"
          value="145"
          change={8.2}
          icon={Users}
          color="green"
        />
        <StatCard
          title="Productos Vendidos"
          value="324"
          change={-3.1}
          icon={Package}
          color="blue"
        />
        <StatCard
          title="Almuerzos Servidos"
          value="89"
          change={15.8}
          icon={Utensils}
          color="purple"
        />
      </div>

      {/* Quick Actions */}
      <Card title="Acciones Rápidas" subtitle="Operaciones frecuentes">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Button 
            variant="primary" 
            fullWidth 
            leftIcon={<ShoppingCart className="h-5 w-5" />}
          >
            Nueva Venta
          </Button>
          <Button 
            variant="secondary" 
            fullWidth 
            leftIcon={<CreditCard className="h-5 w-5" />}
          >
            Recargar Tarjeta
          </Button>
          <Button 
            variant="outline" 
            fullWidth 
            leftIcon={<Users className="h-5 w-5" />}
          >
            Nuevo Cliente
          </Button>
          <Button 
            variant="outline" 
            fullWidth 
            leftIcon={<Package className="h-5 w-5" />}
          >
            Agregar Producto
          </Button>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Sales */}
        <Card 
          title="Ventas Recientes" 
          subtitle="Últimas 5 transacciones"
          headerAction={
            <Badge variant="primary">Hoy</Badge>
          }
        >
          <div className="space-y-4">
            {[
              { id: '#1234', cliente: 'Juan Pérez', monto: 'Gs. 25.000', hora: '10:30' },
              { id: '#1235', cliente: 'María González', monto: 'Gs. 15.000', hora: '10:45' },
              { id: '#1236', cliente: 'Pedro Ramírez', monto: 'Gs. 35.000', hora: '11:00' },
              { id: '#1237', cliente: 'Ana Silva', monto: 'Gs. 20.000', hora: '11:15' },
              { id: '#1238', cliente: 'Carlos López', monto: 'Gs. 12.000', hora: '11:30' },
            ].map((venta) => (
              <div key={venta.id} className="flex items-center justify-between border-b border-gray-100 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-600">
                    <ShoppingCart className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{venta.cliente}</p>
                    <p className="text-sm text-gray-500">{venta.id} • {venta.hora}</p>
                  </div>
                </div>
                <p className="font-semibold text-gray-900">{venta.monto}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Low Stock Products */}
        <Card 
          title="Productos con Stock Bajo" 
          subtitle="Requieren reabastecimiento"
          headerAction={
            <Badge variant="warning">3 productos</Badge>
          }
        >
          <div className="space-y-4">
            {[
              { nombre: 'Coca Cola 500ml', stock: 5, minimo: 20 },
              { nombre: 'Galletas Oreo', stock: 8, minimo: 15 },
              { nombre: 'Jugo de Naranja', stock: 3, minimo: 10 },
            ].map((producto) => (
              <div key={producto.nombre} className="flex items-center justify-between border-b border-gray-100 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-100 text-yellow-600">
                    <Package className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{producto.nombre}</p>
                    <p className="text-sm text-gray-500">Mínimo: {producto.minimo} unidades</p>
                  </div>
                </div>
                <Badge variant="warning">{producto.stock} restantes</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Today's Menu */}
      <Card 
        title="Menú del Día" 
        subtitle="Almuerzos disponibles"
        headerAction={
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Calendar className="h-4 w-4" />
            <span>{new Date().toLocaleDateString('es-PY', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
          </div>
        }
      >
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { nombre: 'Milanesa con Puré', precio: 'Gs. 15.000', disponible: 25 },
            { nombre: 'Pollo al Horno con Ensalada', precio: 'Gs. 18.000', disponible: 30 },
            { nombre: 'Pasta Bolognesa', precio: 'Gs. 12.000', disponible: 20 },
          ].map((menu) => (
            <div key={menu.nombre} className="rounded-lg border border-gray-200 p-4 transition-colors hover:border-amber-300 hover:bg-amber-50/50">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900">{menu.nombre}</h4>
                  <p className="mt-1 text-sm font-medium text-amber-600">{menu.precio}</p>
                </div>
                <Badge variant="success">{menu.disponible} disponibles</Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default Dashboard;
