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
import Auditoria from '../pages/Auditoria';
import { UserManagement } from '../pages/usuarios';
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
                {/* Dashboard - Accesible para todos */}
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                
                {/* Módulo de Recargas - Admin, Gerente, Cajero */}
                <Route 
                  path="/recargas" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cajero']}>
                      <Recargas />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Ventas - POS - Admin, Gerente, Cajero */}
                <Route 
                  path="/ventas" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cajero']}>
                      <POS />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Clientes - Admin, Gerente */}
                <Route 
                  path="/clientes" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente']}>
                      <Clientes />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Productos - Admin, Gerente */}
                <Route 
                  path="/productos" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente']}>
                      <Productos />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Compras - Admin, Gerente */}
                <Route 
                  path="/compras" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente']}>
                      <Compras />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Almuerzos - Todos */}
                <Route path="/almuerzos" element={<Almuerzos />} />
                
                {/* Módulo de Reportes - Solo Admin y Gerente */}
                <Route 
                  path="/reportes" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente']}>
                      <Reportes />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Notificaciones - Todos */}
                <Route path="/notificaciones" element={<Notificaciones />} />
                
                {/* Módulo de Configuración - Solo Admin */}
                <Route 
                  path="/configuracion" 
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <Configuracion />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Auditoría - Solo Admin */}
                <Route 
                  path="/admin/auditoria" 
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <Auditoria />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Gestión de Usuarios - Solo Admin */}
                <Route 
                  path="/admin/usuarios" 
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <UserManagement />
                    </ProtectedRoute>
                  } 
                />
              </Routes>
            </MainLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

export default AppRoutes;

