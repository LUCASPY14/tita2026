import React from 'react';
import { User, CreditCard, AlertTriangle, DollarSign, Camera } from 'lucide-react';
import { Card } from '../../../components/common';
import type { TarjetaEscaneada } from '../../../types';

interface HijoCardProps {
  tarjeta: TarjetaEscaneada;
  onCerrar?: () => void;
  showDetails?: boolean;
  compactMode?: boolean;
}

const HijoCard: React.FC<HijoCardProps> = ({
  tarjeta,
  onCerrar,
  showDetails = true,
  compactMode = false
}) => {
  const { hijo, saldo, numero, estado } = tarjeta;
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const formatDateTime = (date: Date) => {
    return new Intl.DateTimeFormat('es-PY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getSaldoColor = () => {
    if (saldo.alertaBajo) return 'text-red-600 bg-red-50';
    if (saldo.disponible < 10000) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getSaldoIcon = () => {
    if (saldo.alertaBajo) return <AlertTriangle className="h-4 w-4" />;
    return <DollarSign className="h-4 w-4" />;
  };

  return (
    <Card className={`${compactMode ? 'p-4' : 'p-6'} relative overflow-hidden`}>
      {/* Cerrar */}
      {onCerrar && (
        <button
          onClick={onCerrar}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          ×
        </button>
      )}

      {/* Header */}
      <div className="flex items-start gap-4">
        {/* Foto del hijo */}
        <div className="relative">
          <div className="w-16 h-16 rounded-full overflow-hidden bg-gray-100 border-2 border-blue-200">
            {hijo.foto ? (
              <img
                src={hijo.foto}
                alt={`${hijo.nombre} ${hijo.apellido}`}
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback si la imagen no carga
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling?.classList.remove('hidden');
                }}
              />
            ) : null}
            
            {/* Fallback avatar */}
            <div className={`w-full h-full flex items-center justify-center ${hijo.foto ? 'hidden' : ''}`}>
              <User className="h-8 w-8 text-gray-400" />
            </div>
          </div>
          
          {/* Indicador de foto */}
          {hijo.foto && (
            <div className="absolute -bottom-1 -right-1 bg-green-500 rounded-full p-1">
              <Camera className="h-3 w-3 text-white" />
            </div>
          )}
        </div>

        {/* Información del hijo */}
        <div className="flex-1 min-w-0">
          <h3 className="text-xl font-bold text-gray-900 truncate">
            {hijo.nombre} {hijo.apellido}
          </h3>
          
          <div className="mt-1 flex items-center gap-2 text-sm text-gray-600">
            <CreditCard className="h-4 w-4" />
            <span className="font-mono">{numero}</span>
            
            {/* Estado de la tarjeta */}
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              estado === 'ACTIVA' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}>
              {estado}
            </span>
          </div>

          {/* Información del saldo */}
          <div className={`mt-3 inline-flex items-center gap-2 px-3 py-2 rounded-lg ${getSaldoColor()}`}>
            {getSaldoIcon()}
            <div>
              <p className="text-sm font-medium">
                Saldo: {formatCurrency(saldo.disponible)}
              </p>
              {saldo.alertaBajo && (
                <p className="text-xs">Saldo bajo - Recarga recomendada</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Detalles adicionales */}
      {showDetails && !compactMode && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">Saldo actual</p>
              <p className="font-semibold">{formatCurrency(saldo.actual)}</p>
            </div>
            
            <div>
              <p className="text-gray-600">Saldo disponible</p>
              <p className="font-semibold">{formatCurrency(saldo.disponible)}</p>
            </div>
            
            {hijo.fechaFoto && (
              <div>
                <p className="text-gray-600">Foto actualizada</p>
                <p className="text-xs text-gray-500">
                  {new Date(hijo.fechaFoto).toLocaleDateString('es-PY')}
                </p>
              </div>
            )}
            
            <div>
              <p className="text-gray-600">Verificado</p>
              <p className="text-xs text-gray-500">
                {formatDateTime(tarjeta.timestamp)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Indicador de verificación */}
      <div className="absolute top-2 left-2 w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
    </Card>
  );
};

export default HijoCard;