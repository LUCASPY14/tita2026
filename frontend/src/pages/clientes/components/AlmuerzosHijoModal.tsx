import React, { useState, useEffect, useCallback } from 'react';
import { X, UtensilsCrossed, Calendar, CheckCircle, XCircle, Clock, TrendingUp } from 'lucide-react';
import { Spinner } from '../../../components/common';
import { almuerzosService } from '../../../services/almuerzos.service';
import type { Hijo, Tarjeta, RegistroConsumoAlmuerzo, CuentaAlmuerzoMensual } from '../../../types';

interface AlmuerzosHijoModalProps {
  hijo: Hijo;
  tarjeta: Tarjeta | null;
  onClose: () => void;
}

const formatGs = (v: number | undefined) =>
  `Gs. ${Number(v ?? 0).toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;

const formatFecha = (s: string) =>
  new Date(s + 'T00:00:00').toLocaleDateString('es-PY', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

const hoy = () => new Date().toISOString().split('T')[0];
const hace30 = () => {
  const d = new Date();
  d.setDate(d.getDate() - 30);
  return d.toISOString().split('T')[0];
};

const MESES = [
  'Enero','Febrero','Marzo','Abril','Mayo','Junio',
  'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre',
];

const AlmuerzosHijoModal: React.FC<AlmuerzosHijoModalProps> = ({ hijo, tarjeta, onClose }) => {
  const [tab, setTab] = useState<'registros' | 'cuentas'>('registros');

  // ── Registros ──────────────────────────────────────────────
  const [registros, setRegistros] = useState<RegistroConsumoAlmuerzo[]>([]);
  const [cargandoReg, setCargandoReg] = useState(false);
  const [desde, setDesde] = useState(hace30());
  const [hasta, setHasta] = useState(hoy());

  // ── Cuentas mensuales ──────────────────────────────────────
  const [cuentas, setCuentas] = useState<CuentaAlmuerzoMensual[]>([]);
  const [cargandoCuentas, setCargandoCuentas] = useState(false);

  const cargarRegistros = useCallback(async () => {
    setCargandoReg(true);
    try {
      const resp = await almuerzosService.getRegistrosPorHijo(hijo.id_hijo, desde, hasta);
      setRegistros(resp.results || resp);
    } catch (e) {
      console.error(e);
    } finally {
      setCargandoReg(false);
    }
  }, [hijo.id_hijo, desde, hasta]);

  const cargarCuentas = useCallback(async () => {
    setCargandoCuentas(true);
    try {
      const resp = await almuerzosService.getCuentasMensuales({ id_hijo: hijo.id_hijo });
      const lista: CuentaAlmuerzoMensual[] = resp.results || resp;
      // Ordenar del más reciente al más antiguo
      lista.sort((a, b) => b.anio - a.anio || b.mes - a.mes);
      setCuentas(lista);
    } catch (e) {
      console.error(e);
    } finally {
      setCargandoCuentas(false);
    }
  }, [hijo.id_hijo]);

  useEffect(() => { cargarRegistros(); }, [cargarRegistros]);
  useEffect(() => { if (tab === 'cuentas') cargarCuentas(); }, [tab, cargarCuentas]);

  // ── Summary stats ──────────────────────────────────────────
  const totalAlmuerzos = registros.length;
  const totalCobrado = registros
    .filter((r) => r.ya_cobrado)
    .reduce((s, r) => s + (r.costo_almuerzo || 0), 0);
  const segundosServicios = registros.filter((r) => !r.ya_cobrado).length;

  // ── Cuentas badge ─────────────────────────────────────────
  const estadoBadge = (estado: string) => {
    const m: Record<string, string> = {
      Pendiente: 'bg-yellow-100 text-yellow-800',
      Pagada: 'bg-green-100 text-green-800',
      Parcial: 'bg-blue-100 text-blue-800',
    };
    return m[estado] || 'bg-gray-100 text-gray-700';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="flex w-full max-w-2xl flex-col rounded-xl bg-white shadow-2xl" style={{ maxHeight: '90vh' }}>
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100">
              <UtensilsCrossed className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Almuerzos — {hijo.nombre} {hijo.apellido}
              </h3>
              <p className="text-sm text-gray-500">
                {hijo.grado ? `${hijo.grado} · ` : ''}
                {tarjeta ? `Tarjeta: ${tarjeta.nro_tarjeta}` : 'Sin tarjeta'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b px-6 pt-3">
          {(['registros', 'cuentas'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`rounded-t-lg px-4 py-2 text-sm font-medium transition-colors ${
                tab === t
                  ? 'border-b-2 border-amber-500 text-amber-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t === 'registros' ? 'Registros de Consumo' : 'Facturación Mensual'}
            </button>
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">

          {/* ── TAB: Registros ─────────────────────────────── */}
          {tab === 'registros' && (
            <div className="space-y-4">
              {/* Summary cards */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-amber-50 p-3 text-center">
                  <p className="text-2xl font-bold text-amber-700">{totalAlmuerzos}</p>
                  <p className="text-xs text-amber-600">Registros</p>
                </div>
                <div className="rounded-lg bg-green-50 p-3 text-center">
                  <p className="text-2xl font-bold text-green-700">{totalAlmuerzos - segundosServicios}</p>
                  <p className="text-xs text-green-600">1er Servicio</p>
                </div>
                <div className="rounded-lg bg-orange-50 p-3 text-center">
                  <p className="text-2xl font-bold text-orange-600">{segundosServicios}</p>
                  <p className="text-xs text-orange-500">2do Servicio</p>
                </div>
              </div>

              {/* Monto total cobrado */}
              {totalCobrado > 0 && (
                <div className="flex items-center gap-2 rounded-lg bg-blue-50 px-4 py-2 text-sm">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                  <span className="text-blue-700">
                    Total acumulado en el período:{' '}
                    <span className="font-bold">{formatGs(totalCobrado)}</span>
                  </span>
                </div>
              )}

              {/* Filtros de fecha */}
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="mb-1 block text-xs font-medium text-gray-600">Desde</label>
                  <input
                    type="date"
                    value={desde}
                    onChange={(e) => setDesde(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-amber-500 focus:outline-none"
                  />
                </div>
                <div className="flex-1">
                  <label className="mb-1 block text-xs font-medium text-gray-600">Hasta</label>
                  <input
                    type="date"
                    value={hasta}
                    onChange={(e) => setHasta(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-amber-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Lista de registros */}
              {cargandoReg ? (
                <div className="flex justify-center py-8">
                  <Spinner className="h-8 w-8" />
                </div>
              ) : registros.length === 0 ? (
                <div className="py-10 text-center text-sm text-gray-500">
                  <UtensilsCrossed className="mx-auto mb-2 h-8 w-8 text-gray-300" />
                  <p>Sin registros en el período seleccionado</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {registros.map((r) => (
                    <div
                      key={r.id_registro_consumo}
                      className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3"
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                            r.ya_cobrado
                              ? 'bg-green-100 text-green-700'
                              : 'bg-orange-100 text-orange-600'
                          }`}
                        >
                          {r.ya_cobrado ? '1°' : '2°'}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {formatFecha(r.fecha_consumo)}
                          </p>
                          <div className="flex items-center gap-1 text-xs text-gray-500">
                            <Clock className="h-3 w-3" />
                            {r.hora_registro.substring(0, 5)}
                            {r.tipo_almuerzo_nombre && (
                              <span className="ml-2 text-gray-400">· {r.tipo_almuerzo_nombre}</span>
                            )}
                            {r.id_suscripcion && !r.tipo_almuerzo_nombre && (
                              <span className="ml-2 text-purple-500">· Plan mensual</span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 text-right">
                        {r.ya_cobrado ? (
                          <span className="text-sm font-semibold text-green-700">
                            {r.costo_almuerzo ? formatGs(r.costo_almuerzo) : 'Plan'}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">Sin costo</span>
                        )}
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                            r.estado === 'Confirmado'
                              ? 'bg-green-100 text-green-700'
                              : r.estado === 'Pendiente'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {r.estado === 'Confirmado' ? (
                            <CheckCircle className="h-3 w-3" />
                          ) : (
                            <XCircle className="h-3 w-3" />
                          )}
                          {r.estado}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── TAB: Cuentas mensuales ─────────────────────── */}
          {tab === 'cuentas' && (
            <div className="space-y-3">
              {cargandoCuentas ? (
                <div className="flex justify-center py-8">
                  <Spinner className="h-8 w-8" />
                </div>
              ) : cuentas.length === 0 ? (
                <div className="py-10 text-center text-sm text-gray-500">
                  <Calendar className="mx-auto mb-2 h-8 w-8 text-gray-300" />
                  <p>Sin facturación registrada</p>
                </div>
              ) : (
                cuentas.map((c) => (
                  <div
                    key={c.id_cuenta}
                    className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-4 py-3"
                  >
                    <div>
                      <p className="font-medium text-gray-900">
                        {MESES[c.mes - 1]} {c.anio}
                      </p>
                      <p className="text-xs text-gray-500">
                        {c.cantidad_almuerzos} almuerzo{c.cantidad_almuerzos !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-4 text-right">
                      <div>
                        <p className="text-sm font-semibold text-gray-900">{formatGs(c.monto_total)}</p>
                        {c.monto_pagado > 0 && (
                          <p className="text-xs text-green-600">
                            Pagado: {formatGs(c.monto_pagado)}
                          </p>
                        )}
                        {c.monto_total - c.monto_pagado > 0 && (
                          <p className="text-xs text-red-500">
                            Saldo: {formatGs(c.monto_total - c.monto_pagado)}
                          </p>
                        )}
                      </div>
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${estadoBadge(c.estado)}`}>
                        {c.estado}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-3 text-right">
          <button
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlmuerzosHijoModal;
