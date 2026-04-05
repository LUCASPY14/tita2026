/**
 * Página de Configuración del Sistema
 * Gestión de configuraciones generales del sistema
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Settings, RefreshCw, AlertTriangle, Building2, CreditCard, Percent, Mail, Clock, ExternalLink } from 'lucide-react';
import { PanelConfiguracion } from '../components/configuracion';
import configuracionService from '../services/configuracion.service';
import { ConfiguracionSistema } from '../types';
import toast from 'react-hot-toast';

type TabType = 'configuracion';

const QUICK_LINKS = [
  { to: '/configuracion/datos-empresa',      icon: Building2,  label: 'Datos de Empresa',      desc: 'RUC, razón social, dirección' },
  { to: '/configuracion/medios-pago',         icon: CreditCard, label: 'Medios de Pago',         desc: 'Efectivo, tarjetas, transferencias' },
  { to: '/configuracion/impuestos',           icon: Percent,    label: 'Impuestos',              desc: 'IVA 10%, IVA 5%, Exenta' },
  { to: '/configuracion/plantillas-email',    icon: Mail,       label: 'Plantillas Email',       desc: 'Asunto y cuerpo HTML/texto' },
  { to: '/configuracion/tareas-programadas',  icon: Clock,      label: 'Tareas Programadas',     desc: 'Celery Beat — horarios y estado' },
];

const Configuracion: React.FC = () => {
  const [tabActiva] = useState<TabType>('configuracion');
  const [configuracionesPorCategoria, setConfiguracionesPorCategoria] = useState<Record<string, ConfiguracionSistema[]>>({});
  const [cargando, setCargando] = useState(true);
  const [categoriaExpandida, setCategoriaExpandida] = useState<string | null>(null);

  useEffect(() => {
    cargarConfiguraciones();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cargarConfiguraciones = async () => {
    try {
      setCargando(true);
      const data = await configuracionService.getConfiguracionesPorCategoria();
      setConfiguracionesPorCategoria(data);
      
      // Expandir primera categoría por defecto
      const categorias = Object.keys(data);
      if (categorias.length > 0 && !categoriaExpandida) {
        setCategoriaExpandida(categorias[0]);
      }
    } catch (error) {
      console.error('Error cargando configuraciones:', error);
      toast.error('Error al cargar las configuraciones');
    } finally {
      setCargando(false);
    }
  };

  const handleConfiguracionActualizada = () => {
    cargarConfiguraciones();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Configuración del Sistema
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Administra las configuraciones generales del sistema
            </p>
          </div>
          
          <button
            onClick={cargarConfiguraciones}
            disabled={cargando}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${cargando ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>
      </div>

      {/* Accesos rápidos a páginas de configuración */}
      <div className="mb-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Tablas paramétricas
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {QUICK_LINKS.map(({ to, icon: Icon, label, desc }) => (
            <Link
              key={to}
              to={to}
              className="flex items-start gap-3 p-4 bg-white border border-gray-200 rounded-lg hover:border-blue-400 hover:shadow-sm transition-all group"
            >
              <Icon className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0 group-hover:text-blue-600" />
              <div className="min-w-0">
                <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700 flex items-center gap-1">
                  {label}
                  <ExternalLink className="h-3 w-3 opacity-0 group-hover:opacity-100 transition-opacity" />
                </p>
                <p className="text-xs text-gray-500 mt-0.5 truncate">{desc}</p>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Advertencia para configuraciones sensibles */}
      <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex">
          <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">
              Advertencia
            </h3>
            <div className="mt-1 text-sm text-yellow-700">
              <p>
                Algunas configuraciones pueden requerir reiniciar el sistema para aplicar los cambios.
                Modifica solo si sabes qué estás haciendo.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            <button
              className="group inline-flex items-center py-4 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm"
            >
              <Settings className="-ml-0.5 mr-2 h-5 w-5 text-blue-500" />
              Configuración General
            </button>
          </nav>
        </div>

        {/* Panel de Configuración */}
        <div className="p-6">
          {tabActiva === 'configuracion' && (
            <PanelConfiguracion
              configuracionesPorCategoria={configuracionesPorCategoria}
              cargando={cargando}
              categoriaExpandida={categoriaExpandida}
              onCategoriaExpandir={setCategoriaExpandida}
              onConfiguracionActualizada={handleConfiguracionActualizada}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Configuracion;
