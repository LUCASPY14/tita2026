import React, { useState, useRef, useEffect } from 'react';
import { CreditCard, Scan, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { Card } from '../../../components/common';
import api from '../../../services/api';
import type { TarjetaEscaneada } from '../../../types';

interface TarjetaScanInputProps {
  onTarjetaEscaneada: (tarjeta: TarjetaEscaneada) => void;
  disabled?: boolean;
  placeholder?: string;
}

const TarjetaScanInput: React.FC<TarjetaScanInputProps> = ({
  onTarjetaEscaneada,
  disabled = false,
  placeholder = "Escanea la tarjeta del hijo..."
}) => {
  const [codigo, setCodigo] = useState('');
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus al montar el componente
  useEffect(() => {
    if (inputRef.current && !disabled) {
      inputRef.current.focus();
    }
  }, [disabled]);

  // Auto-focus cuando se completa una operación
  useEffect(() => {
    if (success && !scanning) {
      const timer = setTimeout(() => {
        setSuccess(false);
        setCodigo('');
        if (inputRef.current) {
          inputRef.current.focus();
        }
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [success, scanning]);

  const handleScan = async (codigoBarras: string) => {
    if (!codigoBarras.trim() || scanning) return;
    
    setScanning(true);
    setError(null);
    
    try {
      const response = await api.post('/tarjetas/scan/', {
        codigo_barras: codigoBarras.trim()
      });

      if (response.data.error) {
        setError(response.data.error);
        return;
      }

      const { tarjeta, verificacion } = response.data;
      
      // Verificar estado de la tarjeta
      if (!verificacion.estado_ok) {
        setError(`Tarjeta ${tarjeta.estado.toLowerCase()}`);
        return;
      }

      // Crear objeto de tarjeta escaneada
      const tarjetaEscaneada: TarjetaEscaneada = {
        numero: tarjeta.nro_tarjeta,
        hijo: {
          id: tarjeta.id_hijo,
          nombre: tarjeta.hijo_nombre,
          apellido: tarjeta.hijo_apellido,
          foto: tarjeta.hijo_foto,
          fechaFoto: tarjeta.hijo_fecha_foto
        } as any,
        saldo: {
          actual: tarjeta.saldo_actual,
          disponible: verificacion.saldo_disponible,
          alertaBajo: verificacion.alerta_saldo_bajo,
        },
        estado: tarjeta.estado,
        timestamp: new Date(verificacion.timestamp),
        restricciones: verificacion.restricciones || [],
      };

      setSuccess(true);
      onTarjetaEscaneada(tarjetaEscaneada);
      
    } catch (err: any) {
      console.error('Error al escanear tarjeta:', err);
      if (err.response?.status === 404) {
        setError('Tarjeta no encontrada');
      } else if (err.response?.status === 403) {
        setError('Tarjeta bloqueada o inactiva');
      } else {
        setError('Error de conexión. Inténtalo de nuevo.');
      }
    } finally {
      setScanning(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleScan(codigo);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setCodigo(value);
    setError(null);
    
    // Auto-submit cuando se detecta un código completo (generalmente 10+ caracteres)
    if (value.length >= 10 && !scanning) {
      handleScan(value);
    }
  };

  const getStatusIcon = () => {
    if (scanning) {
      return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
    }
    if (success) {
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    }
    if (error) {
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    }
    return <Scan className="h-5 w-5 text-gray-400" />;
  };

  const getInputClasses = () => {
    const baseClasses = "w-full pl-10 pr-10 py-3 text-lg border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200";
    
    if (disabled) {
      return `${baseClasses} bg-gray-100 text-gray-500 cursor-not-allowed`;
    }
    if (scanning) {
      return `${baseClasses} border-blue-300 bg-blue-50`;
    }
    if (success) {
      return `${baseClasses} border-green-300 bg-green-50`;
    }
    if (error) {
      return `${baseClasses} border-red-300 bg-red-50`;
    }
    
    return `${baseClasses} border-gray-300 bg-white hover:border-gray-400`;
  };

  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
            <CreditCard className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Escaneo de Tarjeta
            </h3>
            <p className="text-sm text-gray-600">
              Escanea o ingresa el código de barras de la tarjeta del hijo
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
              <CreditCard className="h-5 w-5 text-gray-400" />
            </div>
            
            <input
              ref={inputRef}
              type="text"
              value={codigo}
              onChange={handleInputChange}
              placeholder={placeholder}
              disabled={disabled || scanning}
              className={getInputClasses()}
              autoComplete="off"
              autoFocus
            />
            
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
              {getStatusIcon()}
            </div>
          </div>

          {/* Mensajes de estado */}
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}
          
          {success && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <CheckCircle className="h-4 w-4" />
              Tarjeta verificada correctamente
            </div>
          )}
          
          {scanning && (
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              Verificando tarjeta...
            </div>
          )}

          {/* Botón manual (opcional, principalmente para testing) */}
          {codigo && !scanning && !success && (
            <button
              type="submit"
              className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Scan className="h-4 w-4" />
              Verificar Tarjeta
            </button>
          )}
        </form>

        {/* Instrucciones */}
        <div className="text-xs text-gray-500 space-y-1">
          <p>• El escaneo se procesa automáticamente</p>
          <p>• Presiona <kbd className="px-1 py-0.5 bg-gray-100 rounded text-gray-700 font-mono">Esc</kbd> para limpiar</p>
          <p>• Asegúrate de que la tarjeta esté activa</p>
        </div>
      </div>
    </Card>
  );
};

export default TarjetaScanInput;