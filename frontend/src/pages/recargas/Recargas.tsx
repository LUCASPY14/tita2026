import React, { useState } from 'react';
import { Card } from '../../components/common';
import { BusquedaHijo, FormularioRecarga, HistorialRecargas } from './components';
import type { Hijo, Tarjeta } from '../../types';

const Recargas: React.FC = () => {
  const [hijoSeleccionado, setHijoSeleccionado] = useState<Hijo | null>(null);
  const [tarjetaSeleccionada, setTarjetaSeleccionada] = useState<Tarjeta | null>(null);
  const [actualizarHistorial, setActualizarHistorial] = useState(0);

  const handleHijoSeleccionado = (hijo: Hijo, tarjeta: Tarjeta) => {
    setHijoSeleccionado(hijo);
    setTarjetaSeleccionada(tarjeta);
  };

  const handleRecargaExitosa = () => {
    // Actualizar historial y limpiar selección
    setActualizarHistorial(prev => prev + 1);
    // Opcional: Mantener el hijo seleccionado para otra recarga
    // setHijoSeleccionado(null);
    // setTarjetaSeleccionada(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Recargas de Tarjeta</h1>
        <p className="mt-2 text-gray-600">
          Gestiona las recargas de saldo de las tarjetas estudiantiles
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Columna izquierda: Búsqueda y Recarga */}
        <div className="space-y-6 lg:col-span-2">
          {/* Búsqueda de Hijo */}
          <Card title="Buscar Hijo" subtitle="Ingresa el nombre o número de tarjeta">
            <BusquedaHijo onHijoSeleccionado={handleHijoSeleccionado} />
          </Card>

          {/* Formulario de Recarga */}
          {hijoSeleccionado && tarjetaSeleccionada && (
            <Card 
              title="Registrar Recarga" 
              subtitle={`Hijo: ${hijoSeleccionado.nombre} ${hijoSeleccionado.apellido}`}
            >
              <FormularioRecarga
                hijo={hijoSeleccionado}
                tarjeta={tarjetaSeleccionada}
                onRecargaExitosa={handleRecargaExitosa}
              />
            </Card>
          )}

          {/* Mensaje cuando no hay hijo seleccionado */}
          {!hijoSeleccionado && (
            <Card>
              <div className="py-12 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
                  <svg
                    className="h-8 w-8 text-amber-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                    />
                  </svg>
                </div>
                <h3 className="mt-4 text-lg font-medium text-gray-900">
                  Selecciona un hijo
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Busca y selecciona un hijo para procesar una recarga de tarjeta
                </p>
              </div>
            </Card>
          )}
        </div>

        {/* Columna derecha: Historial */}
        <div className="lg:col-span-1">
          <Card 
            title="Recargas Recientes" 
            subtitle="Últimas 10 recargas"
          >
            <HistorialRecargas 
              key={actualizarHistorial}
              tarjetaNumero={tarjetaSeleccionada?.nro_tarjeta}
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Recargas;
