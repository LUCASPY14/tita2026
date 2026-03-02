import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from '../pages/auth/Login';
import Dashboard from '../pages/dashboard/Dashboard';
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
                
                {/* Placeholder routes - to be implemented */}
                <Route path="/recargas" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Módulo de Recargas</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/ventas" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Punto de Venta</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/clientes" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Gestión de Clientes</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/productos" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Gestión de Productos</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/almuerzos" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Menú de Almuerzos</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/reportes" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Reportes y Estadísticas</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/notificaciones" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Centro de Notificaciones</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
                <Route path="/compras" element={<div className="text-center py-12"><h2 className="text-2xl font-bold text-gray-700">Gestión de Compras</h2><p className="text-gray-500 mt-2">Próximamente...</p></div>} />
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

