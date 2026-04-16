import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import LoadingSpinner from '../components/common/LoadingSpinner';
import MainLayout from '../layouts/MainLayout';
import ProtectedRoute from './ProtectedRoute';
import PortalRoute from './PortalRoute';

// Lazy-loaded pages (code splitting — reduces initial bundle from ~1.2MB)
const Login = React.lazy(() => import('../pages/auth/Login'));
const Verify2FA = React.lazy(() => import('../pages/auth/Verify2FA'));
const RecuperarPassword = React.lazy(() => import('../pages/auth/RecuperarPassword'));
const DashboardMejorado = React.lazy(() => import('../pages/dashboard/DashboardMejorado'));
const Recargas = React.lazy(() => import('../pages/recargas'));
const POS = React.lazy(() => import('../pages/pos'));
const Ventas = React.lazy(() => import('../pages/ventas'));
const Clientes = React.lazy(() => import('../pages/clientes'));
const Productos = React.lazy(() => import('../pages/productos'));
const Compras = React.lazy(() => import('../pages/compras'));
const Proveedores = React.lazy(() => import('../pages/compras/Proveedores'));
const Cobros = React.lazy(() => import('../pages/cobros/Cobros'));
const Almuerzos = React.lazy(() => import('../pages/almuerzos'));
const Reportes = React.lazy(() => import('../pages/Reportes'));
const Inventario = React.lazy(() => import('../pages/inventario/Inventario'));
const Notificaciones = React.lazy(() => import('../pages/Notificaciones'));
const Configuracion = React.lazy(() => import('../pages/Configuracion'));
const Auditoria = React.lazy(() => import('../pages/Auditoria'));
const GestionPermisos = React.lazy(() => import('../pages/permisos'));
const UserManagement = React.lazy(() =>
  import('../pages/usuarios').then(m => ({ default: m.UserManagement }))
);
const Categorias = React.lazy(() => import('../pages/categorias'));
const Perfil = React.lazy(() => import('../pages/Perfil'));
const GestionCaja = React.lazy(() => import('../pages/caja/GestionCaja'));
const GestionTimbrado = React.lazy(() => import('../pages/timbrado/GestionTimbrado'));
const ColaFacturacion = React.lazy(() => import('../pages/facturacion/ColaFacturacion'));
const HistorialFacturas = React.lazy(() => import('../pages/facturacion/HistorialFacturas'));
const GestionDatosEmpresa = React.lazy(() => import('../pages/configuracion/GestionDatosEmpresa'));
const GestionMediosPago = React.lazy(() => import('../pages/configuracion/GestionMediosPago'));
const GestionImpuestos = React.lazy(() => import('../pages/configuracion/GestionImpuestos'));
const GestionPlantillasEmail = React.lazy(() => import('../pages/configuracion/GestionPlantillasEmail'));
const GestionTareasProgramadas = React.lazy(() => import('../pages/configuracion/GestionTareasProgramadas'));
const GestionPaises = React.lazy(() => import('../pages/configuracion/GestionPaises'));
const GestionCiudades = React.lazy(() => import('../pages/configuracion/GestionCiudades'));
const GestionCondicionesVenta = React.lazy(() => import('../pages/configuracion/GestionCondicionesVenta'));
const LoginPortal = React.lazy(() => import('../pages/portal/LoginPortal'));
const DashboardPortal = React.lazy(() => import('../pages/portal/DashboardPortal'));
const PWAConfigPage = React.lazy(() => import('../pages/PWAConfigPage'));

const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<LoadingSpinner size="lg" />}>
    <Routes>
      {/* Portal de Clientes — rutas independientes del sistema de empleados */}
      <Route path="/portal/login" element={<LoginPortal />} />
      <Route
        path="/portal/dashboard"
        element={
          <PortalRoute>
            <DashboardPortal />
          </PortalRoute>
        }
      />
      <Route path="/portal" element={<Navigate to="/portal/login" replace />} />

      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/verificar-2fa" element={<Verify2FA />} />
      <Route path="/recuperar-password" element={<RecuperarPassword />} />

      {/* Protected Routes with Layout */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <MainLayout>
              <Routes>
                {/* Dashboard - Accesible para todos */}
                <Route path="/dashboard" element={<DashboardMejorado />} />
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                
                {/* Módulo de Recargas - Admin, Gerente, Cajero, Cobrador */}
                <Route 
                  path="/recargas" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cajero', 'cobrador']}>
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

                {/* Gestión de Ventas - Historial y seguimiento - Admin, Gerente, Cobrador */}
                <Route 
                  path="/ventas/gestion" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cobrador']}>
                      <Ventas />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Clientes - Admin, Gerente, Cobrador */}
                <Route 
                  path="/clientes" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cobrador']}>
                      <Clientes />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Productos - Admin, Gerente, Supervisor, Compras */}
                <Route 
                  path="/productos" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'supervisor', 'compras']}>
                      <Productos />
                    </ProtectedRoute>
                  } 
                />

                {/* Módulo de Categorías - Admin, Gerente, Supervisor, Compras */}
                <Route
                  path="/categorias"
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'supervisor', 'compras']}>
                      <Categorias />
                    </ProtectedRoute>
                  }
                />
                
                {/* Módulo de Compras - Admin, Gerente, Compras */}
                <Route 
                  path="/compras" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'compras']}>
                      <Compras />
                    </ProtectedRoute>
                  } 
                />

                {/* Módulo de Cobros - Admin, Gerente, Cajero */}
                <Route 
                  path="/cobros" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cajero']}>
                      <Cobros />
                    </ProtectedRoute>
                  } 
                />

                {/* Módulo de Proveedores - Admin, Gerente, Compras */}
                <Route 
                  path="/proveedores" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'compras']}>
                      <Proveedores />
                    </ProtectedRoute>
                  } 
                />

                {/* Módulo de Inventario - Admin, Gerente, Compras */}
                <Route 
                  path="/inventario" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'compras']}>
                      <Inventario />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Almuerzos - Admin, Gerente, Cajero */}
                <Route 
                  path="/almuerzos" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cajero']}>
                      <Almuerzos />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Reportes - Admin, Gerente, Compras */}
                <Route 
                  path="/reportes" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'compras']}>
                      <Reportes />
                    </ProtectedRoute>
                  } 
                />
                
                {/* Módulo de Notificaciones - Todos */}
                <Route path="/notificaciones" element={<Notificaciones />} />
                
                {/* Perfil de usuario */}
                <Route path="/perfil" element={<Perfil />} />
                
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
                
                {/* Módulo de Gestión de Permisos - Solo Admin */}
                <Route 
                  path="/admin/permisos" 
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionPermisos />
                    </ProtectedRoute>
                  } 
                />

                {/* Módulo de Caja - Admin, Gerente, Cajero */}
                <Route 
                  path="/caja" 
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'gerente', 'cajero']}>
                      <GestionCaja />
                    </ProtectedRoute>
                  } 
                />

                {/* Facturación física – Cola e impresión (PC central, Admin + Cajero) */}
                <Route
                  path="/facturacion"
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'cajero']}>
                      <ColaFacturacion />
                    </ProtectedRoute>
                  }
                />

                {/* Historial de facturas emitidas */}
                <Route
                  path="/facturacion/historial"
                  element={
                    <ProtectedRoute requiredRoles={['admin', 'cajero']}>
                      <HistorialFacturas />
                    </ProtectedRoute>
                  }
                />

                {/* Módulo de Timbrado / Documentos Tributarios - Solo Admin */}
                <Route 
                  path="/timbrado" 
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionTimbrado />
                    </ProtectedRoute>
                  } 
                />

                {/* Configuración: tablas paramétricas */}
                <Route
                  path="/configuracion/datos-empresa"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionDatosEmpresa />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/configuracion/medios-pago"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionMediosPago />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/configuracion/impuestos"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionImpuestos />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/configuracion/plantillas-email"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionPlantillasEmail />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/configuracion/tareas-programadas"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionTareasProgramadas />
                    </ProtectedRoute>
                  }
                />

                {/* Catálogos geográficos y comerciales - Solo Admin */}
                <Route
                  path="/configuracion/paises"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionPaises />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/configuracion/ciudades"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionCiudades />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/configuracion/condiciones-venta"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <GestionCondicionesVenta />
                    </ProtectedRoute>
                  }
                />

                {/* Configuración: PWA - Solo Admin */}
                <Route
                  path="/configuracion/pwa"
                  element={
                    <ProtectedRoute requiredRoles={['admin']}>
                      <PWAConfigPage />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </MainLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
    </Suspense>
  );
};

export default AppRoutes;

