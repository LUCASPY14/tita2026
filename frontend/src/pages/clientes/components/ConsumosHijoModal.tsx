import React, { useState, useEffect, useCallback } from 'react';
import { X, ShoppingBag, Calendar, TrendingDown, CreditCard, AlertCircle, ArrowDownCircle, ArrowUpCircle } from 'lucide-react';
import { Button, Spinner } from '../../../components/common';
import { getReporteConsumosHijo } from '../../../services/reportes.service';
import type { Hijo, Tarjeta, ReporteConsumosHijo, ConsumoHijoDetalle } from '../../../types';

interface ConsumosHijoModalProps {
  hijo: Hijo;
  tarjeta: Tarjeta | null;
  onClose: () => void;
}

const formatGs = (amount: number | string | undefined): string => {
  if (amount === undefined || amount === null) return 'Gs. 0';
  return `Gs. ${Number(amount).toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;
};

const formatFecha = (fechaStr: string): string => {
  const d = new Date(fechaStr);
  return d.toLocaleDateString('es-PY', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

const formatHora = (fechaStr: string): string => {
  const d = new Date(fechaStr);
  return d.toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' });
};

const todayStr = (): string => new Date().toISOString().split('T')[0];
const thirtyDaysAgoStr = (): string => {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return d.toISOString().split('T')[0];
};

// ─── ConsumoRow ──────────────────────────────────────────────────────────────
interface ConsumoRowProps {
  consumo: ConsumoHijoDetalle;
  esRecarga: boolean;
}

const ConsumoRow: React.FC<ConsumoRowProps> = ({ consumo: c, esRecarga }) => {
  const monto = Math.abs(Number(c.monto_consumido));

  return (
    <div
      className={`rounded-lg border px-4 py-3 ${
        esRecarga
          ? 'border-green-200 bg-green-50'
          : 'border-red-100 bg-white'
      }`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {esRecarga ? (
            <ArrowUpCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
          ) : (
            <ArrowDownCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
          )}
          <div className="min-w-0">
            <span className="text-xs text-gray-500">
              {formatFecha(c.fecha_consumo)} · {formatHora(c.fecha_consumo)}
            </span>
            {esRecarga && (
              <p className="text-sm font-medium text-green-700 truncate">
                Recarga de saldo
              </p>
            )}
          </div>
        </div>
        <div className="text-right flex-shrink-0">
          <p className={`font-bold text-sm ${esRecarga ? 'text-green-700' : 'text-red-700'}`}>
            {esRecarga ? '+' : '-'}{formatGs(monto)}
          </p>
          <p className="text-xs text-gray-400">
            Saldo: {formatGs(c.saldo_posterior)}
          </p>
        </div>
      </div>

      {/* Productos (solo para compras) */}
      {!esRecarga && c.productos && c.productos.length > 0 && (
        <div className="mt-2 pl-6 space-y-1">
          {c.productos.map((p, i) => (
            <div key={i} className="flex items-center justify-between text-sm">
              <span className="text-gray-700">
                <span className="font-medium text-gray-900">
                  {Number(p.cantidad) % 1 === 0
                    ? Number(p.cantidad).toFixed(0)
                    : Number(p.cantidad).toString()}×
                </span>{' '}
                {p.descripcion}
              </span>
              <span className="text-gray-500 text-xs ml-2 whitespace-nowrap">
                {formatGs(p.subtotal)}
              </span>
            </div>
          ))}
        </div>
      )}

      {!esRecarga && (!c.productos || c.productos.length === 0) && c.detalle && (
        <p className="mt-1 pl-6 text-xs text-gray-400 italic">{c.detalle}</p>
      )}
    </div>
  );
};
// ─────────────────────────────────────────────────────────────────────────────

const ConsumosHijoModal: React.FC<ConsumosHijoModalProps> = ({ hijo, tarjeta, onClose }) => {
  const [fechaInicio, setFechaInicio] = useState(thirtyDaysAgoStr());
  const [fechaFin, setFechaFin] = useState(todayStr());
  const [reporte, setReporte] = useState<ReporteConsumosHijo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cargarReporte = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getReporteConsumosHijo({
        id_hijo: hijo.id_hijo,
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
      });
      setReporte(data);
    } catch (err: unknown) {
      setError('Error al cargar el reporte de consumos.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [hijo.id_hijo, fechaInicio, fechaFin]);

  useEffect(() => {
    cargarReporte();
  }, [cargarReporte]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-3xl max-h-[90vh] bg-white rounded-xl shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b bg-amber-50">
          <div className="flex items-center gap-3">
            <ShoppingBag className="h-5 w-5 text-amber-600" />
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Consumos de {hijo.nombre} {hijo.apellido}
              </h2>
              {hijo.grado && (
                <p className="text-sm text-gray-500">Grado: {hijo.grado}</p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 items-end px-6 py-4 border-b bg-gray-50">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Desde</label>
            <input
              type="date"
              value={fechaInicio}
              onChange={(e) => setFechaInicio(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Hasta</label>
            <input
              type="date"
              value={fechaFin}
              onChange={(e) => setFechaFin(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
          </div>
          <Button size="sm" onClick={cargarReporte} disabled={loading}>
            {loading ? 'Cargando...' : 'Buscar'}
          </Button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Spinner size="lg" />
              <span className="ml-3 text-gray-600">Cargando consumos...</span>
            </div>
          ) : error ? (
            <div className="flex items-center gap-3 rounded-lg bg-red-50 px-4 py-3 text-red-700">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <p>{error}</p>
            </div>
          ) : !reporte ? null : !reporte.tiene_tarjeta ? (
            <div className="flex flex-col items-center justify-center py-16 text-gray-500">
              <CreditCard className="h-12 w-12 mb-4 text-gray-300" />
              <p className="font-medium">Este alumno no tiene tarjeta asignada.</p>
              <p className="text-sm mt-1">Asigne una tarjeta para registrar consumos.</p>
            </div>
          ) : (
            <>
              {/* Summary Cards */}
              {(() => {
                const soloCompras = reporte.consumos.filter(c => Number(c.monto_consumido) > 0);
                const totalGastado = soloCompras.reduce((sum, c) => sum + Number(c.monto_consumido), 0);
                return (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                    <div className="rounded-lg bg-blue-50 p-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <ShoppingBag className="h-4 w-4 text-blue-600" />
                        <p className="text-xs font-medium text-blue-600">Compras</p>
                      </div>
                      <p className="text-xl font-bold text-blue-900">{soloCompras.length}</p>
                    </div>

                    <div className="rounded-lg bg-red-50 p-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <TrendingDown className="h-4 w-4 text-red-600" />
                        <p className="text-xs font-medium text-red-600">Total Gastado</p>
                      </div>
                      <p className="text-lg font-bold text-red-900">
                        {formatGs(totalGastado)}
                      </p>
                    </div>

                    <div className="rounded-lg bg-green-50 p-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <CreditCard className="h-4 w-4 text-green-600" />
                        <p className="text-xs font-medium text-green-600">Saldo Actual</p>
                      </div>
                      <p className="text-lg font-bold text-green-900">
                        {formatGs(reporte.saldo_actual ?? tarjeta?.saldo_actual)}
                      </p>
                    </div>

                    <div className="rounded-lg bg-gray-100 p-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Calendar className="h-4 w-4 text-gray-600" />
                        <p className="text-xs font-medium text-gray-600">Período</p>
                      </div>
                      <p className="text-xs font-medium text-gray-800">
                        {formatFecha(fechaInicio)} –<br />{formatFecha(fechaFin)}
                      </p>
                    </div>
                  </div>
                );
              })()}

              {/* Tarjeta info */}
              <p className="text-xs text-gray-400 mb-4">
                Tarjeta Nº {reporte.nro_tarjeta}
              </p>

              {/* Table */}
              {reporte.consumos.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-gray-400">
                  <ShoppingBag className="h-10 w-10 mb-3" />
                  <p className="font-medium">Sin consumos en este período</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {reporte.consumos.map((c) => {
                    const esRecarga = Number(c.monto_consumido) < 0;
                    return (
                      <ConsumoRow
                        key={c.id_consumo}
                        consumo={c}
                        esRecarga={esRecarga}
                      />
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-3 border-t bg-gray-50">
          <Button variant="outline" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConsumosHijoModal;
