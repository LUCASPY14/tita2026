import React, { useState } from 'react';
import { CreditCard, ArrowLeftRight } from 'lucide-react';
import { Card } from '../../components/common';
import { BusquedaHijo, FormularioRecarga, HistorialRecargas, MovimientosSaldo } from './components';
import type { Hijo, Tarjeta } from '../../types';

type Vista = 'recargas' | 'movimientos';

const Recargas: React.FC = () => {
  const [vista, setVista] = useState<Vista>('recargas');
  const [hijoSeleccionado, setHijoSeleccionado] = useState<Hijo | null>(null);
  const [tarjetaSeleccionada, setTarjetaSeleccionada] = useState<Tarjeta | null>(null);
  const [actualizarHistorial, setActualizarHistorial] = useState(0);

  const handleHijoSeleccionado = (hijo: Hijo, tarjeta: Tarjeta) => {
    setHijoSeleccionado(hijo);
    setTarjetaSeleccionada(tarjeta);
  };

  const handleRecargaExitosa = () => {
    setActualizarHistorial(prev => prev + 1);
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

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-gray-100 p-1">
        <button
          type="button"
          onClick={() => setVista('recargas')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            vista === 'recargas'
              ? 'bg-white text-amber-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <CreditCard className="h-4 w-4" />
          Recargas
        </button>
        <button
          type="button"
          onClick={() => setVista('movimientos')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            vista === 'movimientos'
              ? 'bg-white text-amber-700 shadow-sm'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <ArrowLeftRight className="h-4 w-4" />
          Movimientos de Saldo
        </button>
      </div>

      {/* Vista: Recargas */}
      {vista === 'recargas' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Columna izquierda: Búsqueda y Recarga */}
          <div className="space-y-6 lg:col-span-2">
            <Card title="Buscar Hijo" subtitle="Ingresa el nombre o número de tarjeta">
              <BusquedaHijo onHijoSeleccionado={handleHijoSeleccionado} />
            </Card>

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
            <Card title="Recargas Recientes" subtitle="Últimas 10 recargas">
              <HistorialRecargas
                key={actualizarHistorial}
                tarjetaNumero={tarjetaSeleccionada?.nro_tarjeta}
              />
            </Card>
          </div>
        </div>
      )}

      {/* Vista: Movimientos */}
      {vista === 'movimientos' && (
        <Card
          title="Movimientos de Saldo"
          subtitle={
            tarjetaSeleccionada
              ? `Tarjeta: ${tarjetaSeleccionada.nro_tarjeta}`
              : 'Consulta el historial de consumos de cualquier tarjeta'
          }
        >
          <MovimientosSaldo tarjetaPreseleccionada={tarjetaSeleccionada} />
        </Card>
      )}
    </div>
  );
};

export default Recargas;

