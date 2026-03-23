import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw, ChevronLeft, ChevronRight, FileText,
  DollarSign, Users, AlertCircle, Receipt, Printer,
} from 'lucide-react';
import { Button, Spinner, Badge } from '../../../components/common';
import { almuerzosService } from '../../../services/almuerzos.service';
import toast from 'react-hot-toast';
import ReciboCobro from './ReciboCobro';
import FacturaImpresa from './FacturaImpresa';

interface CuentaMensual {
  id_cuenta: number;
  anio: number;
  mes: number;
  cantidad_almuerzos: number;
  monto_total: string;
  forma_cobro: string;
  monto_pagado: string;
  estado: string;
  fecha_generacion: string;
  fecha_actualizacion: string;
  observaciones: string | null;
  id_hijo: number;
  hijo_nombre: string | null;
}

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

const FacturacionMensual: React.FC = () => {
  const hoy = new Date();
  const [anio, setAnio] = useState(hoy.getFullYear());
  const [mes, setMes] = useState(hoy.getMonth() + 1);
  const [estado, setEstado] = useState('');
  const [cuentas, setCuentas] = useState<CuentaMensual[]>([]);
  const [cargando, setCargando] = useState(true);
  const [totalRegistros, setTotalRegistros] = useState(0);
  const [pagina, setPagina] = useState(1);

  // Documentos para imprimir
  const [reciboData, setReciboData] = useState<any>(null);
  const [facturaData, setFacturaData] = useState<any>(null);
  const [procesando, setProcesando] = useState<number | null>(null);

  const PAGE_SIZE = 20;

  const cargar = useCallback(async (p = 1) => {
    setCargando(true);
    try {
      const params: Record<string, string | number> = {
        anio,
        mes,
        page: p,
        page_size: PAGE_SIZE,
      };
      if (estado) params.estado = estado;
      const data = await almuerzosService.getCuentasMensuales(params as any);
      setCuentas(data.results ?? data);
      setTotalRegistros(data.count ?? (data.results ?? data).length);
    } catch (err) {
      console.error('Error al cargar facturación mensual:', err);
    } finally {
      setCargando(false);
    }
  }, [anio, mes, estado]);

  useEffect(() => {
    setPagina(1);
    cargar(1);
  }, [anio, mes, estado]);

  const totalPaginas = Math.ceil(totalRegistros / PAGE_SIZE);

  const handleVerRecibo = async (idCuenta: number) => {
    setProcesando(idCuenta);
    try {
      const data = await almuerzosService.getReciboPago(idCuenta);
      setReciboData(data);
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Error al obtener el recibo de cobro';
      toast.error(msg);
    } finally {
      setProcesando(null);
    }
  };

  const handleGenerarFactura = async (idCuenta: number) => {
    setProcesando(idCuenta);
    try {
      const data = await almuerzosService.generarFactura(idCuenta);
      setFacturaData(data);
      if (data.es_nueva) {
        toast.success('Factura generada exitosamente');
        cargar(pagina); // recargar para mostrar nro_comprobante en tabla
      } else {
        toast('Mostrando factura ya emitida', { icon: 'ℹ️' });
      }
    } catch (err: any) {
      const msg = err?.response?.data?.error || 'Error al generar la factura';
      toast.error(msg);
    } finally {
      setProcesando(null);
    }
  };

  const formatGS = (val: string | number) =>
    `Gs. ${Number(val).toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;

  const saldo = (cuenta: CuentaMensual) =>
    Number(cuenta.monto_total) - Number(cuenta.monto_pagado);

  const getEstadoBadge = (estado: string) => {
    switch (estado.toLowerCase()) {
      case 'pagado':
        return <Badge variant="success">Pagado</Badge>;
      case 'pendiente':
        return <Badge variant="warning">Pendiente</Badge>;
      case 'parcial':
        return <Badge variant="info">Parcial</Badge>;
      case 'anulado':
        return <Badge variant="default">Anulado</Badge>;
      default:
        return <Badge variant="default">{estado}</Badge>;
    }
  };

  // Resumen totales de la vista actual
  const totalMonto = cuentas.reduce((s, c) => s + Number(c.monto_total), 0);
  const totalPagado = cuentas.reduce((s, c) => s + Number(c.monto_pagado), 0);
  const totalSaldo = totalMonto - totalPagado;
  const pendientesCount = cuentas.filter(c => c.estado.toLowerCase() === 'pendiente').length;

  return (
    <>
      {/* Overlays de impresión */}
      {reciboData && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#fff', overflowY: 'auto' }}>
          <ReciboCobro data={reciboData} onClose={() => setReciboData(null)} />
        </div>
      )}
      {facturaData && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#fff', overflowY: 'auto' }}>
          <FacturaImpresa data={facturaData} onClose={() => setFacturaData(null)} />
        </div>
      )}

    <div className="space-y-4">
      {/* Filtros */}
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Año</label>
          <select
            value={anio}
            onChange={(e) => setAnio(Number(e.target.value))}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
          >
            {Array.from({ length: 5 }, (_, i) => hoy.getFullYear() - i).map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Mes</label>
          <select
            value={mes}
            onChange={(e) => setMes(Number(e.target.value))}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
          >
            {MESES.map((nombre, idx) => (
              <option key={idx + 1} value={idx + 1}>{nombre}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-gray-600">Estado</label>
          <select
            value={estado}
            onChange={(e) => setEstado(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
          >
            <option value="">Todos</option>
            <option value="pendiente">Pendiente</option>
            <option value="pagado">Pagado</option>
            <option value="parcial">Parcial</option>
            <option value="anulado">Anulado</option>
          </select>
        </div>

        <Button
          type="button"
          variant="secondary"
          onClick={() => cargar(pagina)}
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          Actualizar
        </Button>
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
          <Users className="h-7 w-7 text-amber-500 shrink-0" />
          <div>
            <p className="text-xs text-gray-500">Alumnos</p>
            <p className="text-xl font-bold text-gray-800">{totalRegistros}</p>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
          <FileText className="h-7 w-7 text-blue-500 shrink-0" />
          <div>
            <p className="text-xs text-gray-500">Total facturado</p>
            <p className="text-lg font-bold text-blue-700">{formatGS(totalMonto)}</p>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
          <DollarSign className="h-7 w-7 text-green-500 shrink-0" />
          <div>
            <p className="text-xs text-gray-500">Total cobrado</p>
            <p className="text-lg font-bold text-green-700">{formatGS(totalPagado)}</p>
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
          <AlertCircle className="h-7 w-7 text-red-400 shrink-0" />
          <div>
            <p className="text-xs text-gray-500">Saldo pendiente</p>
            <p className="text-lg font-bold text-red-600">{formatGS(totalSaldo)}</p>
            {pendientesCount > 0 && (
              <p className="text-xs text-red-400">{pendientesCount} sin cobrar</p>
            )}
          </div>
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-hidden rounded-lg border border-gray-200">
        {cargando ? (
          <div className="flex items-center justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : cuentas.length === 0 ? (
          <div className="py-16 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-3 text-gray-500">
              No hay cuentas de almuerzo para {MESES[mes - 1]} {anio}
            </p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Alumno
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Almuerzos
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monto Total
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cobrado
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Saldo
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Forma de Cobro
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {cuentas.map((cuenta) => {
                const saldoRestante = saldo(cuenta);
                return (
                  <tr key={cuenta.id_cuenta} className="hover:bg-amber-50/40 transition-colors">
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-gray-800">
                        {cuenta.hijo_nombre ?? `Alumno #${cuenta.id_hijo}`}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center justify-center rounded-full bg-amber-100 px-2.5 py-0.5 text-sm font-semibold text-amber-800">
                        {cuenta.cantidad_almuerzos}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900 text-sm">
                      {formatGS(cuenta.monto_total)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm text-green-700 font-medium">
                      {formatGS(cuenta.monto_pagado)}
                    </td>
                    <td className="px-4 py-3 text-right text-sm">
                      <span className={saldoRestante > 0 ? 'font-semibold text-red-600' : 'text-gray-400'}>
                        {saldoRestante > 0 ? formatGS(saldoRestante) : '—'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs text-gray-600 capitalize">{cuenta.forma_cobro}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {getEstadoBadge(cuenta.estado)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        {(cuenta as any).nro_comprobante && (
                          <span className="text-xs font-mono text-blue-600 mr-0.5">
                            {(cuenta as any).nro_comprobante}
                          </span>
                        )}
                        <button
                          type="button"
                          onClick={() => handleVerRecibo(cuenta.id_cuenta)}
                          disabled={procesando === cuenta.id_cuenta || Number(cuenta.monto_pagado) <= 0}
                          title="Recibo de cobro"
                          className="rounded p-1.5 text-green-600 hover:bg-green-50 disabled:opacity-40 transition-colors"
                        >
                          {procesando === cuenta.id_cuenta
                            ? <Spinner className="h-4 w-4" />
                            : <Receipt className="h-4 w-4" />}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleGenerarFactura(cuenta.id_cuenta)}
                          disabled={procesando === cuenta.id_cuenta}
                          title={(cuenta as any).nro_comprobante ? 'Ver factura emitida' : 'Generar factura'}
                          className="rounded p-1.5 text-blue-600 hover:bg-blue-50 disabled:opacity-40 transition-colors"
                        >
                          <Printer className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Paginación */}
      {totalPaginas > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 pt-3">
          <p className="text-sm text-gray-500">
            Mostrando {((pagina - 1) * PAGE_SIZE) + 1}–{Math.min(pagina * PAGE_SIZE, totalRegistros)} de {totalRegistros}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => { setPagina(p => p - 1); cargar(pagina - 1); }}
              disabled={pagina === 1 || cargando}
              className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-600">{pagina} / {totalPaginas}</span>
            <button
              type="button"
              onClick={() => { setPagina(p => p + 1); cargar(pagina + 1); }}
              disabled={pagina === totalPaginas || cargando}
              className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
    </>
  );
};

export default FacturacionMensual;
