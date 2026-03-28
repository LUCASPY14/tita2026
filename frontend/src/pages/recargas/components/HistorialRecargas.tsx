import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, AlertCircle, Banknote, CreditCard } from 'lucide-react';
import { Spinner, Badge } from '../../../components/common';
import { recargasService } from '../../../services/recargas.service';
import type { CargaSaldo } from '../../../types';

interface HistorialRecargasProps {
  tarjetaNumero?: string;
}

const HistorialRecargas: React.FC<HistorialRecargasProps> = ({ tarjetaNumero }) => {
  const [recargas, setRecargas] = useState<CargaSaldo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    cargarHistorial();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tarjetaNumero]);

  const cargarHistorial = async () => {
    setCargando(true);
    setError(null);

    try {
      const params: any = {
        page_size: 10,
      };

      if (tarjetaNumero) {
        params.nro_tarjeta = tarjetaNumero;
      }

      const response = await recargasService.getRecargas(params);
      setRecargas(response.results || []);
    } catch (error: any) {
      console.error('Error al cargar historial:', error);
      setError('Error al cargar el historial de recargas');
    } finally {
      setCargando(false);
    }
  };

  const formatearMoneda = (monto: number): string => {
    return `Gs. ${monto.toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;
  };

  const formatearFecha = (fecha: string): string => {
    const date = new Date(fecha);
    return date.toLocaleDateString('es-PY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getEstadoInfo = (estado: string): { icon: React.ReactNode; variant: 'success' | 'warning' | 'danger' | 'info'; label: string } => {
    switch (estado) {
      case 'Confirmada':
        return {
          icon: <CheckCircle className="h-4 w-4" />,
          variant: 'success',
          label: 'Confirmada',
        };
      case 'Pendiente':
        return {
          icon: <Clock className="h-4 w-4" />,
          variant: 'warning',
          label: 'Pendiente',
        };
      case 'Rechazada':
        return {
          icon: <XCircle className="h-4 w-4" />,
          variant: 'danger',
          label: 'Rechazada',
        };
      case 'Cancelada':
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          variant: 'danger',
          label: 'Cancelada',
        };
      default:
        return {
          icon: <Clock className="h-4 w-4" />,
          variant: 'info',
          label: estado,
        };
    }
  };

  const getMetodoPagoIcon = (metodo?: string) => {
    switch (metodo) {
      case 'efectivo':
        return <Banknote className="h-4 w-4 text-green-600" />;
      case 'tarjeta_pos':
        return <CreditCard className="h-4 w-4 text-blue-600" />;
      default:
        return <CreditCard className="h-4 w-4 text-gray-600" />;
    }
  };

  if (cargando) {
    return (
      <div className="flex items-center justify-center py-8">
        <Spinner />
        <span className="ml-2 text-gray-600">Cargando historial...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-center">
        <AlertCircle className="mx-auto h-8 w-8 text-red-600" />
        <p className="mt-2 text-sm text-red-800">{error}</p>
      </div>
    );
  }

  if (recargas.length === 0) {
    return (
      <div className="py-8 text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gray-100">
          <Clock className="h-6 w-6 text-gray-400" />
        </div>
        <p className="mt-2 text-sm text-gray-600">
          {tarjetaNumero ? 'No hay recargas para esta tarjeta' : 'No hay recargas registradas'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {recargas.map((recarga) => {
        const estadoInfo = getEstadoInfo(recarga.estado);
        
        return (
          <div
            key={recarga.id_carga}
            className="rounded-lg border border-gray-200 bg-white p-3 transition-shadow hover:shadow-md"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  {getMetodoPagoIcon(recarga.metodo_pago)}
                  <p className="font-semibold text-gray-900">
                    {formatearMoneda(recarga.monto_cargado)}
                  </p>
                  <Badge variant={estadoInfo.variant} size="sm">
                    {estadoInfo.label}
                  </Badge>
                </div>
                
                {recarga.hijo_nombre && (
                  <p className="mt-1 text-xs text-gray-600">
                    {recarga.hijo_nombre}
                  </p>
                )}
                
                <p className="mt-1 text-xs text-gray-500">
                  {formatearFecha(recarga.fecha_carga)}
                </p>
                
                {recarga.referencia && (
                  <p className="mt-1 text-xs text-gray-500">
                    Ref: {recarga.referencia}
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default HistorialRecargas;
