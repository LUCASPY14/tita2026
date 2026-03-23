/**
 * CuentaCorrienteAlmuerzos
 * Reporte de cuenta corriente de almuerzos por hijo/cliente,
 * SEPARADO del saldo de cantina/POS.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Input, Spinner } from '../../../components/common';
import { Search, FileText, CheckCircle, Clock, AlertCircle, DollarSign, Receipt } from 'lucide-react';
import { almuerzosService } from '../../../services/almuerzos.service';
import ReciboCobro from './ReciboCobro';
import { recargasService } from '../../../services/recargas.service';
import toast from 'react-hot-toast';
import type { Hijo } from '../../../types';

interface CuentaMensual {
  id_cuenta: number;
  id_hijo: number;
  hijo_nombre: string;
  anio: number;
  mes: number;
  cantidad_almuerzos: number;
  monto_total: string;
  monto_pagado: string;
  forma_cobro: string;
  forma_pago: string;
  comprobante_pago: string;
  fecha_pago: string | null;
  estado: string;
  fecha_generacion: string;
  fecha_actualizacion: string;
  observaciones: string | null;
}

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const ESTADO_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  pendiente: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-800', icon: <Clock className="h-3 w-3" /> },
  validacion_pendiente: { label: 'Validación pendiente', color: 'bg-blue-100 text-blue-800', icon: <AlertCircle className="h-3 w-3" /> },
  pagado: { label: 'Pagado', color: 'bg-green-100 text-green-800', icon: <CheckCircle className="h-3 w-3" /> },
  parcial: { label: 'Parcial', color: 'bg-orange-100 text-orange-800', icon: <DollarSign className="h-3 w-3" /> },
  anulado: { label: 'Anulado', color: 'bg-gray-100 text-gray-500', icon: null },
};

const CuentaCorrienteAlmuerzos: React.FC = () => {
  const hoy = new Date();
  const [anio, setAnio] = useState(hoy.getFullYear());
  const [mes, setMes] = useState(hoy.getMonth() + 1);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [cuentas, setCuentas] = useState<CuentaMensual[]>([]);
  const [cargando, setCargando] = useState(false);
  const [busquedaHijo, setBusquedaHijo] = useState('');
  const [hijoBuscado, setHijoBuscado] = useState<Hijo | null>(null);

  // Modal de pago
  const [cuentaPago, setCuentaPago] = useState<CuentaMensual | null>(null);
  const [formPago, setFormPago] = useState({
    forma_pago: '',
    comprobante_pago: '',
    fecha_pago: hoy.toISOString().split('T')[0],
    monto_pagado: '',
    estado: 'pagado',
    observaciones: '',
  });
  const [guardandoPago, setGuardandoPago] = useState(false);
  const [reciboData, setReciboData] = useState<any>(null);

  const cargarCuentas = useCallback(async () => {
    try {
      setCargando(true);
      const params: any = { anio, mes, page_size: 100 };
      if (filtroEstado) params.estado = filtroEstado;
      if (hijoBuscado) params.id_hijo = hijoBuscado.id_hijo;
      const response = await almuerzosService.getCuentasMensuales(params);
      setCuentas(response.results || response);
    } catch (error) {
      console.error('Error al cargar cuentas:', error);
      toast.error('Error al cargar las cuentas corrientes');
    } finally {
      setCargando(false);
    }
  }, [anio, mes, filtroEstado, hijoBuscado]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { cargarCuentas(); }, [anio, mes, filtroEstado, hijoBuscado]);

  const handleBuscarHijo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!busquedaHijo.trim()) { setHijoBuscado(null); return; }
    try {
      const resp = await recargasService.buscarHijos({ search: busquedaHijo });
      const lista = resp.results || resp;
      if (lista.length > 0) {
        setHijoBuscado(lista[0]);
        toast.success(`Filtrando por: ${lista[0].nombre} ${lista[0].apellido}`);
      } else {
        toast.error('No se encontró ningún alumno con ese nombre');
      }
    } catch {
      toast.error('Error en la búsqueda');
    }
  };

  const handleRegistrarPago = async () => {
    if (!cuentaPago) return;
    if (!formPago.forma_pago) { toast.error('Selecciona la forma de pago'); return; }
    const monto = parseFloat(formPago.monto_pagado);
    if (!formPago.monto_pagado || monto <= 0) { toast.error('Ingresa el monto pagado'); return; }

    setGuardandoPago(true);
    try {
      const nuevoMontoPagado = parseFloat(cuentaPago.monto_pagado) + monto;
      const nuevoEstado = formPago.estado === 'validacion_pendiente'
        ? 'validacion_pendiente'
        : nuevoMontoPagado >= parseFloat(cuentaPago.monto_total)
          ? 'pagado'
          : 'parcial';

      await almuerzosService.actualizarCuenta(cuentaPago.id_cuenta, {
        forma_pago: formPago.forma_pago,
        comprobante_pago: formPago.comprobante_pago,
        fecha_pago: formPago.fecha_pago || undefined,
        monto_pagado: nuevoMontoPagado,
        estado: nuevoEstado,
        observaciones: formPago.observaciones || undefined,
      });
      toast.success('Pago registrado correctamente');
      const idParaRecibo = cuentaPago.id_cuenta;
      const estadoFinal = nuevoEstado;
      setCuentaPago(null);
      cargarCuentas();
      if (estadoFinal !== 'validacion_pendiente') {
        try {
          const datos = await almuerzosService.getReciboPago(idParaRecibo);
          setReciboData(datos);
        } catch { /* recibo no disponible */ }
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Error al registrar el pago');
    } finally {
      setGuardandoPago(false);
    }
  };

  const handleValidarPago = async (cuenta: CuentaMensual) => {
    if (!window.confirm(`¿Confirmar y validar el pago de ${cuenta.hijo_nombre}?`)) return;
    try {
      await almuerzosService.actualizarCuenta(cuenta.id_cuenta, { estado: 'pagado' });
      toast.success('Pago validado');
      cargarCuentas();
    } catch {
      toast.error('Error al validar el pago');
    }
  };

  const handleVerRecibo = async (idCuenta: number) => {
    try {
      const datos = await almuerzosService.getReciboPago(idCuenta);
      setReciboData(datos);
    } catch {
      toast.error('No hay recibo disponible para esta cuenta');
    }
  };

  const formatearMoneda = (valor: string | number) =>
    new Intl.NumberFormat('es-PY', { style: 'currency', currency: 'PYG', minimumFractionDigits: 0 }).format(Number(valor));

  // Totales del período
  const totalAlmuerzos = cuentas.reduce((s, c) => s + c.cantidad_almuerzos, 0);
  const totalFacturado = cuentas.reduce((s, c) => s + parseFloat(c.monto_total), 0);
  const totalCobrado = cuentas.reduce((s, c) => s + parseFloat(c.monto_pagado), 0);
  const totalPendiente = totalFacturado - totalCobrado;

  return (
    <div className="space-y-6">
      {/* Filtros */}
      <Card>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Año</label>
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none"
              value={anio}
              onChange={(e) => setAnio(Number(e.target.value))}
            >
              {[2024, 2025, 2026, 2027].map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Mes</label>
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none"
              value={mes}
              onChange={(e) => setMes(Number(e.target.value))}
            >
              {MESES.map((m, i) => (
                <option key={i + 1} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Estado</label>
            <select
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none"
              value={filtroEstado}
              onChange={(e) => setFiltroEstado(e.target.value)}
            >
              <option value="">Todos</option>
              <option value="pendiente">Pendiente</option>
              <option value="validacion_pendiente">Validación pendiente</option>
              <option value="pagado">Pagado</option>
              <option value="parcial">Parcial</option>
              <option value="anulado">Anulado</option>
            </select>
          </div>
          <form onSubmit={handleBuscarHijo} className="flex gap-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Buscar alumno</label>
              <Input
                type="text"
                placeholder="Nombre o apellido..."
                value={busquedaHijo}
                onChange={(e) => { setBusquedaHijo(e.target.value); if (!e.target.value) setHijoBuscado(null); }}
                className="w-48"
              />
            </div>
            <div className="pt-5">
              <Button type="submit" variant="secondary" size="sm">
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </form>
          {hijoBuscado && (
            <div className="pt-5">
              <Button variant="outline" size="sm" onClick={() => { setHijoBuscado(null); setBusquedaHijo(''); }}>
                Limpiar filtro
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Resumen del período */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {[
          { label: 'Total almuerzos', value: totalAlmuerzos, tipo: 'cantidad' },
          { label: 'Total facturado', value: formatearMoneda(totalFacturado), tipo: 'monto' },
          { label: 'Total cobrado', value: formatearMoneda(totalCobrado), tipo: 'cobrado' },
          { label: 'Saldo pendiente', value: formatearMoneda(totalPendiente), tipo: 'pendiente' },
        ].map(({ label, value, tipo }) => (
          <Card key={label}>
            <p className="text-xs text-gray-500">{label}</p>
            <p className={`mt-1 text-xl font-bold ${tipo === 'pendiente' && totalPendiente > 0 ? 'text-red-600' : tipo === 'cobrado' ? 'text-green-600' : 'text-gray-900'}`}>
              {value}
            </p>
            <p className="text-xs text-gray-400">
              {MESES[mes - 1]} {anio}
            </p>
          </Card>
        ))}
      </div>

      {/* Tabla de cuentas */}
      <Card
        title={`Cuenta corriente de almuerzos — ${MESES[mes - 1]} ${anio}`}
        subtitle="Independiente del saldo de cantina/POS"
      >
        {cargando ? (
          <div className="flex justify-center py-8"><Spinner size="lg" /></div>
        ) : cuentas.length === 0 ? (
          <p className="py-8 text-center text-gray-500">
            No hay registros para {MESES[mes - 1]} {anio}
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Alumno</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-500">Almuerzos</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Total</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Pagado</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-500">Saldo</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-500">Estado</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Pago</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-500">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {cuentas.map((cuenta) => {
                  const saldo = parseFloat(cuenta.monto_total) - parseFloat(cuenta.monto_pagado);
                  const cfg = ESTADO_CONFIG[cuenta.estado] || { label: cuenta.estado, color: 'bg-gray-100 text-gray-600', icon: null };
                  return (
                    <tr key={cuenta.id_cuenta} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{cuenta.hijo_nombre}</td>
                      <td className="px-4 py-3 text-center text-gray-700">{cuenta.cantidad_almuerzos}</td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-900">
                        {formatearMoneda(cuenta.monto_total)}
                      </td>
                      <td className="px-4 py-3 text-right text-green-700">
                        {formatearMoneda(cuenta.monto_pagado)}
                      </td>
                      <td className={`px-4 py-3 text-right font-semibold ${saldo > 0 ? 'text-red-600' : 'text-gray-400'}`}>
                        {formatearMoneda(saldo)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${cfg.color}`}>
                          {cfg.icon}
                          {cfg.label}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">
                        {cuenta.forma_pago && <span className="capitalize">{cuenta.forma_pago}</span>}
                        {cuenta.fecha_pago && <> · {new Date(cuenta.fecha_pago + 'T00:00:00').toLocaleDateString('es-PY')}</>}
                        {cuenta.comprobante_pago && (
                          <div className="mt-0.5 truncate max-w-[140px]" title={cuenta.comprobante_pago}>
                            {cuenta.comprobante_pago}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {cuenta.estado !== 'pagado' && cuenta.estado !== 'anulado' && (
                            <button
                              onClick={() => {
                                setCuentaPago(cuenta);
                                setFormPago({
                                  forma_pago: '',
                                  comprobante_pago: '',
                                  fecha_pago: hoy.toISOString().split('T')[0],
                                  monto_pagado: String(
                                    parseFloat(cuenta.monto_total) - parseFloat(cuenta.monto_pagado)
                                  ),
                                  estado: 'pagado',
                                  observaciones: '',
                                });
                              }}
                              className="rounded bg-green-100 px-2 py-1 text-xs text-green-700 hover:bg-green-200"
                            >
                              Registrar pago
                            </button>
                          )}
                          {cuenta.estado === 'validacion_pendiente' && (
                            <button
                              onClick={() => handleValidarPago(cuenta)}
                              className="rounded bg-blue-100 px-2 py-1 text-xs text-blue-700 hover:bg-blue-200"
                            >
                              Validar
                            </button>
                          )}
                          <button
                            onClick={() => {
                              // Ver detalle de consumos del mes
                              const url = `/almuerzos?tab=historial&hijo=${cuenta.id_hijo}&mes=${cuenta.mes}&anio=${cuenta.anio}`;
                              window.open(url, '_blank');
                            }}
                            className="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
                          >
                            <FileText className="h-3 w-3" />
                          </button>
                          {Number(cuenta.monto_pagado) > 0 && (
                            <button
                              onClick={() => handleVerRecibo(cuenta.id_cuenta)}
                              className="rounded bg-purple-100 px-2 py-1 text-xs text-purple-700 hover:bg-purple-200"
                              title="Ver recibo de cobro"
                            >
                              <Receipt className="h-3 w-3" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Modal de registro de pago */}
      {cuentaPago && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h3 className="mb-1 text-lg font-semibold text-gray-900">Registrar pago</h3>
            <p className="mb-4 text-sm text-gray-500">
              {cuentaPago.hijo_nombre} · {MESES[cuentaPago.mes - 1]} {cuentaPago.anio}
            </p>

            <div className="mb-4 rounded-lg bg-gray-50 p-3 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Total:</span><span className="font-semibold">{formatearMoneda(cuentaPago.monto_total)}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Ya pagado:</span><span className="text-green-600">{formatearMoneda(cuentaPago.monto_pagado)}</span></div>
              <div className="flex justify-between border-t pt-1"><span className="text-gray-700 font-medium">Saldo pendiente:</span><span className="font-bold text-red-600">{formatearMoneda(parseFloat(cuentaPago.monto_total) - parseFloat(cuentaPago.monto_pagado))}</span></div>
            </div>

            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Forma de pago *</label>
                <select
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={formPago.forma_pago}
                  onChange={(e) => setFormPago((p) => ({ ...p, forma_pago: e.target.value }))}
                >
                  <option value="">Seleccionar...</option>
                  <option value="efectivo">Efectivo</option>
                  <option value="transferencia">Transferencia bancaria</option>
                  <option value="online">Pago online</option>
                  <option value="debito_automatico">Débito automático</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Monto pagado (Gs) *</label>
                  <Input
                    type="number"
                    min="1"
                    value={formPago.monto_pagado}
                    onChange={(e) => setFormPago((p) => ({ ...p, monto_pagado: e.target.value }))}
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Fecha de pago</label>
                  <Input
                    type="date"
                    value={formPago.fecha_pago}
                    onChange={(e) => setFormPago((p) => ({ ...p, fecha_pago: e.target.value }))}
                  />
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Comprobante / Referencia
                </label>
                <Input
                  type="text"
                  placeholder="Nro. de transferencia, URL, etc."
                  value={formPago.comprobante_pago}
                  onChange={(e) => setFormPago((p) => ({ ...p, comprobante_pago: e.target.value }))}
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Estado del pago</label>
                <select
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={formPago.estado}
                  onChange={(e) => setFormPago((p) => ({ ...p, estado: e.target.value }))}
                >
                  <option value="pagado">Confirmado (pagado)</option>
                  <option value="validacion_pendiente">Pendiente de validación</option>
                </select>
                <p className="mt-1 text-xs text-gray-400">
                  "Pendiente de validación": para pagos online que requieren confirmación del administrador.
                </p>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Observaciones</label>
                <Input
                  type="text"
                  value={formPago.observaciones}
                  onChange={(e) => setFormPago((p) => ({ ...p, observaciones: e.target.value }))}
                  placeholder="Notas adicionales..."
                />
              </div>
            </div>

            <div className="mt-5 flex gap-3">
              <Button variant="primary" onClick={handleRegistrarPago} disabled={guardandoPago} className="flex-1">
                {guardandoPago ? <Spinner size="sm" /> : 'Guardar pago'}
              </Button>
              <Button variant="secondary" onClick={() => setCuentaPago(null)} className="flex-1">
                Cancelar
              </Button>
            </div>
          </div>
        </div>
      )}
      {reciboData && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#fff', overflowY: 'auto' }}>
          <ReciboCobro data={reciboData} onClose={() => setReciboData(null)} />
        </div>
      )}
    </div>
  );
};

export default CuentaCorrienteAlmuerzos;
