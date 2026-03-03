import React, { useState } from 'react';
import { 
  RegistroConsumo, 
  GestionPlanes, 
  GestionSuscripciones,
  HistorialConsumos 
} from './components';

type Vista = 'registro' | 'planes' | 'suscripciones' | 'historial';

const Almuerzos: React.FC = () => {
  const [vista, setVista] = useState<Vista>('registro');
  const [actualizarHistorial, setActualizarHistorial] = useState(0);

  const handleRegistroExitoso = () => {
    // Actualizar historial después de un registro exitoso
    setActualizarHistorial(prev => prev + 1);
  };

  const tabs = [
    { id: 'registro' as Vista, label: 'Registro de Consumo', icon: '🍽️' },
    { id: 'planes' as Vista, label: 'Planes de Almuerzo', icon: '📋' },
    { id: 'suscripciones' as Vista, label: 'Suscripciones', icon: '👥' },
    { id: 'historial' as Vista, label: 'Historial', icon: '📊' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Gestión de Almuerzos</h1>
        <p className="mt-2 text-gray-600">
          Administra el servicio de almuerzos, planes y consumos diarios
        </p>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setVista(tab.id)}
              className={`
                whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium transition-colors
                ${
                  vista === tab.id
                    ? 'border-amber-500 text-amber-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div>
        {vista === 'registro' && (
          <RegistroConsumo 
            onRegistroExitoso={handleRegistroExitoso}
            actualizarClave={actualizarHistorial}
          />
        )}

        {vista === 'planes' && (
          <GestionPlanes />
        )}

        {vista === 'suscripciones' && (
          <GestionSuscripciones />
        )}

        {vista === 'historial' && (
          <HistorialConsumos key={actualizarHistorial} />
        )}
      </div>
    </div>
  );
};

export default Almuerzos;
