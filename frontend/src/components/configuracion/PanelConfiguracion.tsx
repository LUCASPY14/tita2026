/**
 * Componente Panel de Configuración
 * Muestra y gestiona las configuraciones del sistema agrupadas por categoría
 */

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Settings,
  Bell,
  Shield,
  CreditCard,
  Link,
  Server,
  Palette,
  Mail,
  Save,
  RotateCcw,
  AlertCircle,
} from 'lucide-react';
import { ConfiguracionSistema } from '../../types';
import configuracionService from '../../services/configuracion.service';
import toast from 'react-hot-toast';
import Button from '../common/Button';

interface PanelConfiguracionProps {
  configuracionesPorCategoria: Record<string, ConfiguracionSistema[]>;
  cargando: boolean;
  categoriaExpandida: string | null;
  onCategoriaExpandir: (categoria: string | null) => void;
  onConfiguracionActualizada: () => void;
}

const PanelConfiguracion: React.FC<PanelConfiguracionProps> = ({
  configuracionesPorCategoria,
  cargando,
  categoriaExpandida,
  onCategoriaExpandir,
  onConfiguracionActualizada,
}) => {
  const [editando, setEditando] = useState<number | null>(null);
  const [valorTemporal, setValorTemporal] = useState<string>('');
  const [guardando, setGuardando] = useState<number | null>(null);

  const getIconoCategoria = (categoria: string) => {
    const iconos: Record<string, React.ComponentType<any>> = {
      general: Settings,
      notificaciones: Bell,
      seguridad: Shield,
      pagos: CreditCard,
      integraciones: Link,
      sistema: Server,
      ui: Palette,
      email: Mail,
    };
    return iconos[categoria.toLowerCase()] || Settings;
  };

  const iniciarEdicion = (config: ConfiguracionSistema) => {
    setEditando(config.id_config);
    setValorTemporal(config.valor);
  };

  const cancelarEdicion = () => {
    setEditando(null);
    setValorTemporal('');
  };

  const guardarConfiguracion = async (config: ConfiguracionSistema) => {
    // Validar valor
    const validacion = configuracionService.validarValorConfig(config, valorTemporal);
    if (!validacion.valido) {
      toast.error(validacion.error || 'Valor inválido');
      return;
    }

    try {
      setGuardando(config.id_config);
      await configuracionService.actualizarConfiguracion(config.id_config, {
        valor: valorTemporal,
      });
      toast.success('Configuración actualizada exitosamente');
      setEditando(null);
      setValorTemporal('');
      onConfiguracionActualizada();
    } catch (error) {
      console.error('Error actualizando configuración:', error);
      toast.error('Error al actualizar la configuración');
    } finally {
      setGuardando(null);
    }
  };

  const resetearConfiguracion = async (config: ConfiguracionSistema) => {
    if (!window.confirm('¿Estás seguro de resetear esta configuración a su valor por defecto?')) {
      return;
    }

    try {
      setGuardando(config.id_config);
      await configuracionService.resetearConfiguracion(config.id_config);
      toast.success('Configuración reseteada exitosamente');
      onConfiguracionActualizada();
    } catch (error) {
      console.error('Error reseteando configuración:', error);
      toast.error('Error al resetear la configuración');
    } finally {
      setGuardando(null);
    }
  };

  const renderCampoEdicion = (config: ConfiguracionSistema) => {
    const estaEditando = editando === config.id_config;

    if (!estaEditando) {
      return (
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900">
            {configuracionService.formatearValorConfig(config)}
          </span>
          {!config.solo_superuser && (
            <button
              onClick={() => iniciarEdicion(config)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              Editar
            </button>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-2">
        {config.tipo === 'boolean' ? (
          <select
            value={valorTemporal}
            onChange={(e) => setValorTemporal(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="true">Sí</option>
            <option value="false">No</option>
          </select>
        ) : config.valores_permitidos && Array.isArray(config.valores_permitidos) ? (
          <select
            value={valorTemporal}
            onChange={(e) => setValorTemporal(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {config.valores_permitidos.map((valor) => (
              <option key={valor} value={valor}>
                {valor}
              </option>
            ))}
          </select>
        ) : config.tipo === 'json' ? (
          <textarea
            value={valorTemporal}
            onChange={(e) => setValorTemporal(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
        ) : (
          <input
            type={config.tipo === 'password' ? 'password' : config.tipo === 'number' ? 'number' : 'text'}
            value={valorTemporal}
            onChange={(e) => setValorTemporal(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        )}

        <div className="flex gap-2">
          <Button
            onClick={() => guardarConfiguracion(config)}
            isLoading={guardando === config.id_config}
            variant="primary"
            size="sm"
          >
            <Save className="h-4 w-4 mr-1" />
            Guardar
          </Button>
          <Button
            onClick={cancelarEdicion}
            variant="outline"
            size="sm"
          >
            Cancelar
          </Button>
          <Button
            onClick={() => resetearConfiguracion(config)}
            variant="outline"
            size="sm"
          >
            <RotateCcw className="h-4 w-4 mr-1" />
            Reset
          </Button>
        </div>
      </div>
    );
  };

  if (cargando) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const categorias = Object.keys(configuracionesPorCategoria);

  if (categorias.length === 0) {
    return (
      <div className="text-center py-12">
        <Settings className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">
          No hay configuraciones
        </h3>
        <p className="mt-1 text-sm text-gray-500">
          No se encontraron configuraciones del sistema
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {categorias.map((categoria) => {
        const Icono = getIconoCategoria(categoria);
        const configs = configuracionesPorCategoria[categoria];
        const estaExpandida = categoriaExpandida === categoria;

        return (
          <div key={categoria} className="border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => onCategoriaExpandir(estaExpandida ? null : categoria)}
              className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${configuracionService.getColorCategoria(categoria)}`}>
                  <Icono className="h-5 w-5" />
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-medium text-gray-900 capitalize">
                    {categoria}
                  </h3>
                  <p className="text-xs text-gray-500">
                    {configs.length} configuracion{configs.length !== 1 ? 'es' : ''}
                  </p>
                </div>
              </div>
              {estaExpandida ? (
                <ChevronDown className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-gray-400" />
              )}
            </button>

            {estaExpandida && (
              <div className="divide-y divide-gray-200">
                {configs.map((config) => (
                  <div key={config.id_config} className="p-4 hover:bg-gray-50">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-sm font-medium text-gray-900">
                            {config.clave}
                          </h4>
                          {config.requerido && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                              Requerido
                            </span>
                          )}
                          {config.solo_superuser && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                              Solo Admin
                            </span>
                          )}
                          {config.requiere_reinicio && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-800">
                              Reinicio
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{config.descripcion}</p>
                        
                        {renderCampoEdicion(config)}
                        
                        <div className="mt-2 text-xs text-gray-500">
                          <p>Tipo: {config.tipo} | Por defecto: {config.valor_defecto}</p>
                          {config.updated_at && (
                            <p className="mt-1">
                              Última actualización: {configuracionService.formatearFecha(config.updated_at)}
                            </p>
                          )}
                        </div>
                      </div>

                      {editando !== config.id_config && config.requiere_reinicio && (
                        <div className="flex-shrink-0">
                          <AlertCircle className="h-5 w-5 text-orange-500" />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default PanelConfiguracion;
