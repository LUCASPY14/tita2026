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
import Reportes from '../pages/Reportes';
import Notificaciones from '../pages/Notificaciones';
import Configuracion from '../pages/Configuracion';
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
                
                {/* Módulo de Reportes */}
                <Route path="/reportes" element={<Reportes />} />
                
                {/* Módulo de Notificaciones */}
                <Route path="/notificaciones" element={<Notificaciones />} />
                
                {/* Módulo de Configuración */}
                <Route path="/configuracion" element={<Configuracion />} />
              </Routes>
            </MainLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

export default AppRoutes;

