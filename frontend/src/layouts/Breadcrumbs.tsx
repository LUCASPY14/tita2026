import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
  name: string;
  path?: string;
}

// Mapeo de rutas a nombres amigables
const routeNames: Record<string, string> = {
  dashboard: 'Dashboard',
  recargas: 'Recargas',
  ventas: 'Punto de Venta',
  clientes: 'Clientes',
  productos: 'Productos',
  almuerzos: 'Almuerzos',
  reportes: 'Reportes',
  notificaciones: 'Notificaciones',
  compras: 'Compras',
  configuracion: 'Configuración',
  perfil: 'Mi Perfil',
  nuevo: 'Nuevo',
  editar: 'Editar',
  detalle: 'Detalle',
};

const Breadcrumbs: React.FC = () => {
  const location = useLocation();
  
  // Generar breadcrumbs desde la ruta actual
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const paths = location.pathname.split('/').filter(Boolean);
    
    // Si estamos en home/dashboard, no mostrar breadcrumbs
    if (paths.length === 0 || (paths.length === 1 && paths[0] === 'dashboard')) {
      return [];
    }

    const breadcrumbs: BreadcrumbItem[] = [
      { name: 'Inicio', path: '/dashboard' }
    ];

    let currentPath = '';
    paths.forEach((path, index) => {
      currentPath += `/${path}`;
      const isLast = index === paths.length - 1;
      
      // Si es un número (ID), usar el nombre del paso anterior + ID
      if (!isNaN(Number(path))) {
        breadcrumbs[breadcrumbs.length - 1].name = `${breadcrumbs[breadcrumbs.length - 1].name} #${path}`;
        breadcrumbs[breadcrumbs.length - 1].path = isLast ? undefined : currentPath;
      } else {
        breadcrumbs.push({
          name: routeNames[path] || path.charAt(0).toUpperCase() + path.slice(1),
          path: isLast ? undefined : currentPath,
        });
      }
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  // No renderizar si no hay breadcrumbs
  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <nav className="flex items-center gap-2 px-6 py-3 text-sm bg-gray-50 border-b border-gray-200">
      <Link
        to="/dashboard"
        className="text-gray-500 hover:text-gray-700 transition-colors"
        title="Inicio"
      >
        <Home className="h-4 w-4" />
      </Link>

      {breadcrumbs.map((breadcrumb, index) => (
        <React.Fragment key={index}>
          <ChevronRight className="h-4 w-4 text-gray-400" />
          
          {breadcrumb.path ? (
            <Link
              to={breadcrumb.path}
              className="text-gray-600 hover:text-gray-900 transition-colors font-medium"
            >
              {breadcrumb.name}
            </Link>
          ) : (
            <span className="text-gray-900 font-semibold">
              {breadcrumb.name}
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
};

export default Breadcrumbs;
