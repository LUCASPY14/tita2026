import React, { useState } from 'react';
import { Search, CreditCard, User, AlertCircle } from 'lucide-react';
import { Input, Button, Spinner, Badge } from '../../../components/common';
import { recargasService } from '../../../services/recargas.service';
import type { Hijo, Tarjeta } from '../../../types';
import toast from 'react-hot-toast';

interface BusquedaHijoProps {
  onHijoSeleccionado: (hijo: Hijo, tarjeta: Tarjeta) => void;
}

const BusquedaHijo: React.FC<BusquedaHijoProps> = ({ onHijoSeleccionado }) => {
  const [busqueda, setBusqueda] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [resultados, setResultados] = useState<Hijo[]>([]);
  const [hijoSeleccionado, setHijoSeleccionado] = useState<Hijo | null>(null);
  const [tarjetaInfo, setTarjetaInfo] = useState<Tarjeta | null>(null);
  const [cargandoTarjeta, setCargandoTarjeta] = useState(false);

  const handleBuscar = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!busqueda.trim()) {
      toast.error('Ingresa un nombre o número de tarjeta');
      return;
    }

    setBuscando(true);
    setResultados([]);
    setHijoSeleccionado(null);
    setTarjetaInfo(null);

    try {
      const response = await recargasService.buscarHijos({
        search: busqueda,
        page_size: 10,
        activo: true,
      });

      setResultados(response.results || []);

      if (response.results?.length === 0) {
        toast.error('No se encontraron hijos');
      }
    } catch (error: any) {
      console.error('Error al buscar:', error);
      toast.error(error.response?.data?.message || 'Error al buscar hijos');
    } finally {
      setBuscando(false);
    }
  };

  const handleSeleccionarHijo = async (hijo: Hijo) => {
    setHijoSeleccionado(hijo);
    setCargandoTarjeta(true);
    setTarjetaInfo(null);

    try {
      const tarjeta = await recargasService.getTarjetaByHijo(hijo.id_hijo);
      
      if (!tarjeta) {
        toast.error('Este hijo no tiene tarjeta asignada');
        setHijoSeleccionado(null);
        return;
      }

      setTarjetaInfo(tarjeta);
      onHijoSeleccionado(hijo, tarjeta);
      toast.success(`Hijo seleccionado: ${hijo.nombre} ${hijo.apellido}`);
      
      // Limpiar resultados después de seleccionar
      setResultados([]);
      setBusqueda('');
      
    } catch (error: any) {
      console.error('Error al obtener tarjeta:', error);
      toast.error('Error al obtener información de la tarjeta');
      setHijoSeleccionado(null);
    } finally {
      setCargandoTarjeta(false);
    }
  };

  const formatearMoneda = (monto: number): string => {
    return `Gs. ${monto.toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;
  };

  const getEstadoBadgeVariant = (estado: string): 'success' | 'warning' | 'danger' | 'info' => {
    switch (estado) {
      case 'Activa':
        return 'success';
      case 'Bloqueada':
        return 'danger';
      case 'Inactiva':
        return 'warning';
      default:
        return 'info';
    }
  };

  return (
    <div className="space-y-4">
      {/* Formulario de Búsqueda */}
      <form onSubmit={handleBuscar} className="flex gap-2">
        <div className="flex-1">
          <Input
            type="text"
            placeholder="Buscar por nombre, apellido o número de tarjeta..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            leftIcon={<Search className="h-5 w-5 text-gray-400" />}
          />
        </div>
        <Button 
          type="submit" 
          variant="primary"
          disabled={buscando || !busqueda.trim()}
        >
          {buscando ? <Spinner size="sm" /> : 'Buscar'}
        </Button>
      </form>

      {/* Resultados de Búsqueda */}
      {resultados.length > 0 && (
        <div className="max-h-64 space-y-2 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-3">
          <p className="text-sm font-medium text-gray-700">
            {resultados.length} resultado{resultados.length !== 1 && 's'} encontrado{resultados.length !== 1 && 's'}
          </p>
          {resultados.map((hijo) => (
            <button
              key={hijo.id_hijo}
              onClick={() => handleSeleccionarHijo(hijo)}
              className="flex w-full items-center gap-3 rounded-lg border border-gray-200 bg-white p-3 text-left transition-colors hover:border-amber-300 hover:bg-amber-50"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                <User className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-900">
                  {hijo.nombre} {hijo.apellido}
                </p>
                <p className="text-sm text-gray-500">
                  {hijo.grado || 'Sin grado asignado'}
                </p>
              </div>
              <div className="text-sm text-amber-600">Seleccionar →</div>
            </button>
          ))}
        </div>
      )}

      {/* Información del Hijo y Tarjeta Seleccionada */}
      {hijoSeleccionado && (
        <div className="rounded-lg border-2 border-amber-300 bg-amber-50/50 p-4">
          {cargandoTarjeta ? (
            <div className="flex items-center justify-center py-8">
              <Spinner />
              <span className="ml-2 text-gray-600">Cargando información de la tarjeta...</span>
            </div>
          ) : tarjetaInfo ? (
            <div className="space-y-4">
              {/* Info Hijo */}
              <div className="flex items-start gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-amber-600 text-white">
                  <User className="h-6 w-6" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">
                    {hijoSeleccionado.nombre} {hijoSeleccionado.apellido}
                  </h3>
                  <p className="text-sm text-gray-600">{hijoSeleccionado.grado || 'Sin grado'}</p>
                </div>
                <Badge variant={getEstadoBadgeVariant(tarjetaInfo.estado)}>
                  {tarjetaInfo.estado}
                </Badge>
              </div>

              {/* Info Tarjeta */}
              <div className="grid grid-cols-1 gap-3 rounded-lg bg-white p-4 md:grid-cols-2">
                <div className="flex items-center gap-2">
                  <CreditCard className="h-5 w-5 text-amber-600" />
                  <div>
                    <p className="text-xs text-gray-500">Número de Tarjeta</p>
                    <p className="font-mono font-medium text-gray-900">{tarjetaInfo.nro_tarjeta}</p>
                  </div>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Saldo Actual</p>
                  <p className="text-lg font-bold text-amber-600">
                    {formatearMoneda(tarjetaInfo.saldo_actual)}
                  </p>
                </div>
                {tarjetaInfo.saldo_alerta && tarjetaInfo.saldo_actual <= tarjetaInfo.saldo_alerta && (
                  <div className="col-span-full flex items-center gap-2 rounded-md bg-yellow-50 p-2 text-sm text-yellow-800">
                    <AlertCircle className="h-4 w-4" />
                    <span>Saldo bajo - Requiere recarga</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="py-4 text-center text-gray-600">
              No se pudo cargar la información de la tarjeta
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BusquedaHijo;
