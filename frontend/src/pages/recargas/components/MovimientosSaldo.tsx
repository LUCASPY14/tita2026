import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, RefreshCw, ChevronLeft, ChevronRight,
  ArrowDownCircle, ArrowUpCircle, CreditCard, Calendar,
} from 'lucide-react';
import { Input, Button, Spinner } from '../../../components/common';
import api from '../../../services/api';
import type { Tarjeta } from '../../../types';

interface ConsumoTarjeta {
  id_consumo: number;
  fecha_consumo: string;
  monto_consumido: string;
  detalle: string | null;
  saldo_anterior: string;
  saldo_posterior: string;
  nro_tarjeta: string;
}

interface Props {
  tarjetaPreseleccionada?: Tarjeta | null;
}

const PAGE_SIZE = 20;

const MovimientosSaldo: React.FC<Props> = ({ tarjetaPreseleccionada }) => {
  const [nroTarjeta, setNroTarjeta] = useState(tarjetaPreseleccionada?.nro_tarjeta ?? '');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [movimientos, setMovimientos] = useState<ConsumoTarjeta[]>([]);
  const [cargando, setCargando] = useState(false);
  const [totalRegistros, setTotalRegistros] = useState(0);
  const [pagina, setPagina] = useState(1);
  const [buscado, setBuscado] = useState(false);

  const cargar = useCallback(async (p = 1) => {
    if (!nroTarjeta.trim()) return;
    setCargando(true);
    setBuscado(true);
    try {
      const params: Record<string, string | number> = {
        nro_tarjeta: nroTarjeta.trim(),
        page: p,
        page_size: PAGE_SIZE,
        ordering: '-fecha_consumo',
      };
      if (fechaDesde) params.fecha_desde = fechaDesde;
      if (fechaHasta) params.fecha_hasta = fechaHasta;

      const response = await api.get('/consumos-tarjeta/', { params });
      setMovimientos(response.data.results ?? response.data);
      setTotalRegistros(response.data.count ?? (response.data.results ?? response.data).length);
    } catch (err) {
      console.error('Error al cargar movimientos:', err);
    } finally {
      setCargando(false);
    }
  }, [nroTarjeta, fechaDesde, fechaHasta]);

  // Auto-load when tarjeta is preselected
  useEffect(() => {
    if (tarjetaPreseleccionada?.nro_tarjeta) {
      setNroTarjeta(tarjetaPreseleccionada.nro_tarjeta);
    }
  }, [tarjetaPreseleccionada]);

  useEffect(() => {
    if (nroTarjeta && nroTarjeta === tarjetaPreseleccionada?.nro_tarjeta) {
      cargar(1);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nroTarjeta]);

  const handleBuscar = (e: React.FormEvent) => {
    e.preventDefault();
    setPagina(1);
    cargar(1);
  };

  const totalPaginas = Math.ceil(totalRegistros / PAGE_SIZE);

  const formatGS = (val: string | number) =>
    `Gs. ${Number(val).toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;

  const formatFecha = (f: string) =>
    new Date(f).toLocaleString('es-PY', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

  const esRecarga = (detalle: string | null) =>
    detalle?.toLowerCase().includes('recarga') || detalle?.toLowerCase().includes('carga');

  return (
    <div className="space-y-4">
      {/* Cabecera si hay tarjeta preseleccionada */}
      {tarjetaPreseleccionada && (
        <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3">
          <CreditCard className="h-5 w-5 text-amber-600 shrink-0" />
          <div>
            <p className="text-sm font-medium text-gray-700">
              Tarjeta: <span className="font-mono font-bold text-amber-700">{tarjetaPreseleccionada.nro_tarjeta}</span>
            </p>
            <p className="text-xs text-gray-500">
              Saldo actual: <span className="font-semibold text-amber-600">
                {formatGS(tarjetaPreseleccionada.saldo_actual)}
              </span>
            </p>
          </div>
        </div>
      )}

      {/* Formulario de búsqueda */}
      <form onSubmit={handleBuscar} className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-48">
          <label className="mb-1 block text-xs font-medium text-gray-600">N° de Tarjeta</label>
          <Input
            type="text"
            placeholder="Ej: T-0001"
            value={nroTarjeta}
            onChange={(e) => setNroTarjeta(e.target.value)}
            leftIcon={<CreditCard className="h-4 w-4 text-gray-400" />}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Desde</label>
          <input
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Hasta</label>
          <input
            type="date"
            value={fechaHasta}
            onChange={(e) => setFechaHasta(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
          />
        </div>
        <Button type="submit" variant="primary" leftIcon={<Search className="h-4 w-4" />}>
          Consultar
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => cargar(pagina)}
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          Actualizar
        </Button>
      </form>

      {/* Estado vacío inicial */}
      {!buscado && !cargando && (
        <div className="rounded-lg border-2 border-dashed border-gray-200 py-16 text-center">
          <CreditCard className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-3 text-gray-500">Ingresá el número de tarjeta para ver los movimientos</p>
        </div>
      )}

      {/* Tabla de movimientos */}
      {buscado && (
        <div className="overflow-hidden rounded-lg border border-gray-200">
          {cargando ? (
            <div className="flex items-center justify-center py-16">
              <Spinner size="lg" />
            </div>
          ) : movimientos.length === 0 ? (
            <div className="py-16 text-center">
              <Calendar className="mx-auto h-12 w-12 text-gray-300" />
              <p className="mt-3 text-gray-500">No hay movimientos para los filtros aplicados</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fecha
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Detalle
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Saldo Anterior
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Movimiento
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Saldo Posterior
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {movimientos.map((mov) => {
                  const esPositivo = esRecarga(mov.detalle);
                  return (
                    <tr key={mov.id_consumo} className="hover:bg-gray-50/60 transition-colors">
                      <td className="px-4 py-3">
                        <p className="text-sm text-gray-700">{formatFecha(mov.fecha_consumo)}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {esPositivo ? (
                            <ArrowUpCircle className="h-4 w-4 text-green-500 shrink-0" />
                          ) : (
                            <ArrowDownCircle className="h-4 w-4 text-red-400 shrink-0" />
                          )}
                          <span className="text-sm text-gray-700">{mov.detalle ?? '—'}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-gray-600">
                        {formatGS(mov.saldo_anterior)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`text-sm font-semibold ${esPositivo ? 'text-green-600' : 'text-red-600'}`}>
                          {esPositivo ? '+' : '-'}{formatGS(mov.monto_consumido)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`text-sm font-bold ${Number(mov.saldo_posterior) < 0 ? 'text-red-600' : 'text-gray-900'}`}>
                          {formatGS(mov.saldo_posterior)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Paginación */}
      {buscado && totalPaginas > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 pt-3">
          <p className="text-sm text-gray-500">
            Mostrando {((pagina - 1) * PAGE_SIZE) + 1}–{Math.min(pagina * PAGE_SIZE, totalRegistros)} de {totalRegistros}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => { const p = pagina - 1; setPagina(p); cargar(p); }}
              disabled={pagina === 1 || cargando}
              className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-600">{pagina} / {totalPaginas}</span>
            <button
              type="button"
              onClick={() => { const p = pagina + 1; setPagina(p); cargar(p); }}
              disabled={pagina === totalPaginas || cargando}
              className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MovimientosSaldo;
