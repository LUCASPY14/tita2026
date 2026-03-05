import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle, Clock, AlertTriangle, RefreshCw, User } from 'lucide-react';
import { Spinner, Badge, ConfirmDialog } from '../../../components/common';
import { recargasService } from '../../../services/recargas.service';
import type { CargaSaldo } from '../../../types';
import toast from 'react-hot-toast';

const METODO_LABELS: Record<string, string> = {
  efectivo: 'Efectivo',
  tarjeta_pos: 'Tarjeta POS',
  transferencia: 'Transferencia',
  bancard: 'Bancard',
};

const AprobacionRecargas: React.FC = () => {
  const [recargas, setRecargas] = useState<CargaSaldo[]>([]);
  const [cargando, setCargando] = useState(true);
  const [aprobandoId, setAprobandoId] = useState<number | null>(null);
  const [recargaAConfirmar, setRecargaAConfirmar] = useState<CargaSaldo | null>(null);

  const cargarPendientes = useCallback(async () => {
    setCargando(true);
    try {
      const response = await recargasService.getRecargas({
        estado: 'pendiente_validacion',
        page_size: 50,
      });
      setRecargas(response.results || []);
    } catch (error) {
      console.error('Error al cargar recargas pendientes:', error);
      toast.error('Error al cargar recargadas pendientes');
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarPendientes();
  }, [cargarPendientes]);

  const handleAprobar = (recarga: CargaSaldo) => {
    setRecargaAConfirmar(recarga);
  };

  const confirmarAprobacion = async () => {
    const recarga = recargaAConfirmar;
    if (!recarga) return;
    setRecargaAConfirmar(null);
    setAprobandoId(recarga.id_carga);
    try {
      await recargasService.aprobarRecarga(recarga.id_carga, 1);
      toast.success(`Recarga de Gs. ${recarga.monto_cargado.toLocaleString('es-PY')} aprobada`);
      setRecargas(prev => prev.filter(r => r.id_carga !== recarga.id_carga));
    } catch (error: any) {
      console.error('Error al aprobar recarga:', error);
      toast.error(error.response?.data?.detail || 'Error al aprobar la recarga');
    } finally {
      setAprobandoId(null);
    }
  };

  const formatearMoneda = (valor: number) =>
    `Gs. ${valor.toLocaleString('es-PY')}`;

  const formatearFecha = (fecha: string) =>
    new Date(fecha).toLocaleString('es-PY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Recargas Pendientes de Aprobación</h3>
          <p className="text-sm text-gray-500">
            {recargas.length === 0 ? 'No hay recargas en espera' : `${recargas.length} recarga${recargas.length !== 1 ? 's' : ''} esperando aprobación`}
          </p>
        </div>
        <button
          type="button"
          onClick={cargarPendientes}
          disabled={cargando}
          className="flex items-center gap-2 rounded-lg bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Content */}
      {cargando ? (
        <div className="flex items-center justify-center py-16">
          <Spinner className="h-8 w-8" />
        </div>
      ) : recargas.length === 0 ? (
        <div className="rounded-xl border border-green-200 bg-green-50 py-12 text-center">
          <CheckCircle className="mx-auto mb-3 h-12 w-12 text-green-400" />
          <p className="font-medium text-green-800">¡Todo al día!</p>
          <p className="mt-1 text-sm text-green-600">No hay recargas pendientes de aprobación.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {recargas.map((recarga) => (
            <div
              key={recarga.id_carga}
              className="rounded-xl border border-amber-200 bg-white p-4 shadow-sm"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                {/* Info */}
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-gray-400" />
                    <span className="font-semibold text-gray-900">
                      {recarga.hijo_nombre || recarga.cliente_nombre || `Tarjeta ${recarga.nro_tarjeta}`}
                    </span>
                    <Badge variant="warning">
                      <Clock className="mr-1 h-3 w-3" />
                      Pendiente
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-3 text-sm text-gray-500">
                    <span>Tarjeta: <strong className="text-gray-700">{recarga.nro_tarjeta}</strong></span>
                    <span>Método: <strong className="text-gray-700">{METODO_LABELS[recarga.metodo_pago ?? ''] || recarga.metodo_pago || '—'}</strong></span>
                    <span>Fecha: <strong className="text-gray-700">{formatearFecha(recarga.fecha_carga)}</strong></span>
                    {recarga.referencia && (
                      <span>Ref.: <strong className="text-gray-700">{recarga.referencia}</strong></span>
                    )}
                  </div>
                </div>

                {/* Amount + Action */}
                <div className="flex items-center gap-4 sm:flex-col sm:items-end sm:gap-2">
                  <span className="text-lg font-bold text-amber-700">
                    {formatearMoneda(recarga.monto_cargado)}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleAprobar(recarga)}
                    disabled={aprobandoId === recarga.id_carga}
                    className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-green-700 disabled:opacity-50"
                  >
                    {aprobandoId === recarga.id_carga ? (
                      <Spinner className="h-4 w-4" />
                    ) : (
                      <CheckCircle className="h-4 w-4" />
                    )}
                    {aprobandoId === recarga.id_carga ? 'Aprobando...' : 'Aprobar'}
                  </button>
                </div>
              </div>

              {/* Comprobante */}
              {recarga.numero_comprobante && (
                <div className="mt-3 flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-500" />
                  Comprobante: {recarga.numero_comprobante}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        isOpen={!!recargaAConfirmar}
        onClose={() => setRecargaAConfirmar(null)}
        onConfirm={confirmarAprobacion}
        title="Confirmar aprobación"
        message={recargaAConfirmar ? `¿Aprobar la recarga de ${formatearMoneda(recargaAConfirmar.monto_cargado)} para ${recargaAConfirmar.hijo_nombre || recargaAConfirmar.cliente_nombre || `Tarjeta ${recargaAConfirmar.nro_tarjeta}`}?` : ''}
        confirmText="Aprobar"
        cancelText="Cancelar"
        variant="success"
      />
    </div>
  );
};

export default AprobacionRecargas;
