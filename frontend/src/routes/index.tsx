import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../pages/auth/Login';
import Dashboard from '../pages/dashboard/Dashboard';
import Recargas from '../pages/recargas';
import POS from '../pages/pos';
import Clientes from '../pages/clientes';
import Productos from '../pages/productos';
import Compras from '../pages/compras';
import Almuerzos from '../pages/almuerzos';
import MainLayout from '../layouts/MainLayout';
import ProtectedRoute from './ProtectedRoute';

const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />

      {/* Protected Routes with Layout */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <MainLayout>
              <Routes>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                
                {/* Módulo de Recargas */}
                <Route path="/recargas" element={<Recargas />} />
                
                {/* Módulo de Ventas - POS */}
                <Route path="/ventas" element={<POS />} />
                
                {/* Módulo de Clientes */}
                <Route path="/clientes" element={<Clientes />} />
                
                {/* Módulo de Productos */}
                <Route path="/productos" element={<Productos />} />
                
                {/* Módulo de Compras */}
                <Route path="/compras" element={<Compras />} />
                
                {/* Módulo de Almuerzos */}
                <Route path="/almuerzos" element={<Almuerzos />} />
                
                {/* Placeholder routes - to be implemented */}
                <Route path="/reportes" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Reportes y Estadísticas</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/notificaciones" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Centro de Notificaciones</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/configuracion" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Configuración del Sistema</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
              </Routes>
            </MainLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

export default AppRoutes;

