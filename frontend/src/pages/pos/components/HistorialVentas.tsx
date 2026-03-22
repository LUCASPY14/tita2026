import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, Filter, RefreshCw, Eye, Calendar, TrendingUp,
  ChevronLeft, ChevronRight, DollarSign, ShoppingBag, Banknote,
} from 'lucide-react';
import { Input, Button, Spinner, Badge, EmptyState } from '../../../components/common';
import { posService } from '../../../services/pos.service';
import type { Venta, MedioPago } from '../../../types';

const ESTADOS_PAGO = ['Pendiente', 'Parcial', 'Pagado'] as const;
const TIPOS_VENTA = ['Contado', 'Credito'] as const;

const HistorialVentas: React.FC = () => {
  const [ventas, setVentas] = useState<Venta[]>([]);
  const [cargando, setCargando] = useState(true);
  const [totalRegistros, setTotalRegistros] = useState(0);
  const [paginaActual, setPaginaActual] = useState(1);
  const PAGE_SIZE = 15;

  // Filtros
  const [busqueda, setBusqueda] = useState('');
  const [estadoPago, setEstadoPago] = useState('');
  const [tipoVenta, setTipoVenta] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  const [ventaDetalle, setVentaDetalle] = useState<Venta | null>(null);
  const [mostrarFiltros, setMostrarFiltros] = useState(false);

  // Estado para registro de pago
  const [ventaPago, setVentaPago] = useState<Venta | null>(null);
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([]);
  const [montoPago, setMontoPago] = useState('');
  const [medioPagoId, setMedioPagoId] = useState('');
  const [refPagoPos, setRefPagoPos] = useState('');
  const [refPgTransf, setRefPgTransf] = useState('');
  const [bancoEmisor, setBancoEmisor] = useState('');
  const [procesandoPago, setProcesandoPago] = useState(false);
  const [errorPago, setErrorPago] = useState('');

  const cargarVentas = useCallback(async (pagina = 1, resetear = false) => {
    setCargando(true);
    try {
      const params: any = {
        page: pagina,
        page_size: PAGE_SIZE,
        ordering: '-fecha',
      };
      if (estadoPago) params.estado_pago = estadoPago;
      if (tipoVenta) params.tipo_venta = tipoVenta;
      if (fechaDesde) params.fecha_desde = fechaDesde;
      if (fechaHasta) params.fecha_hasta = fechaHasta;
      if (busqueda.trim()) params.search = busqueda.trim();

      const response = await posService.getVentas(params);
      setVentas(response.results || []);
      setTotalRegistros(response.count || 0);
      if (resetear) setPaginaActual(1);
    } catch (error) {
      console.error('Error al cargar ventas:', error);
    } finally {
      setCargando(false);
    }
  }, [estadoPago, tipoVenta, fechaDesde, fechaHasta, busqueda]);

  useEffect(() => {
    cargarVentas(paginaActual);
  }, [paginaActual, cargarVentas]);

  useEffect(() => {
    posService.getMediosPago().then(setMediosPago).catch(() => {});
  }, []);

  const abrirModalPago = (venta: Venta) => {
    setVentaPago(venta);
    setMontoPago(String(venta.saldo_pendiente));
    setMedioPagoId('');
    setRefPagoPos('');
    setRefPgTransf('');
    setBancoEmisor('');
    setErrorPago('');
  };

  const handleRegistrarPago = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ventaPago || !medioPagoId || !montoPago) return;
    const monto = parseFloat(montoPago);
    if (isNaN(monto) || monto <= 0) {
      setErrorPago('Ingrese un monto válido mayor a cero.');
      return;
    }
    if (monto > ventaPago.saldo_pendiente) {
      setErrorPago(`El monto no puede superar el saldo pendiente (Gs. ${ventaPago.saldo_pendiente.toLocaleString('es-PY')}).`);
      return;
    }
    const medioSeleccionado = mediosPago.find(m => m.id_medio_pago === Number(medioPagoId));
    const esTransferencia = medioSeleccionado?.nombre.toLowerCase().includes('transfer');
    const esPOS = !esTransferencia && medioSeleccionado && (
      medioSeleccionado.nombre.toLowerCase().includes('tarjeta') ||
      medioSeleccionado.nombre.toLowerCase().includes('pos') ||
      medioSeleccionado.nombre.toLowerCase().includes('débit') ||
      medioSeleccionado.nombre.toLowerCase().includes('debit') ||
      medioSeleccionado.nombre.toLowerCase().includes('crédit') ||
      medioSeleccionado.nombre.toLowerCase().includes('credit')
    );
    if (esTransferencia && !refPgTransf.trim()) {
      setErrorPago('Ingrese el número de referencia de la transferencia.');
      return;
    }
    setProcesandoPago(true);
    setErrorPago('');
    try {
      await posService.registrarPago({
        id_venta: ventaPago.id_venta,
        id_medio_pago: Number(medioPagoId),
        monto,
        ...(esPOS && refPagoPos.trim() ? { ref_pago_pos: refPagoPos.trim() } : {}),
        ...(esTransferencia ? { ref_pg_transf: refPgTransf.trim(), ...(bancoEmisor.trim() ? { banco_emisor: bancoEmisor.trim() } : {}) } : {}),
      });
      setVentaPago(null);
      cargarVentas(paginaActual);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.response?.data?.non_field_errors?.[0] || 'Error al registrar el pago.';
      setErrorPago(String(msg));
    } finally {
      setProcesandoPago(false);
    }
  };

  const handleBuscar = (e: React.FormEvent) => {
    e.preventDefault();
    cargarVentas(1, true);
  };

  const handleLimpiarFiltros = () => {
    setBusqueda(''); setEstadoPago(''); setTipoVenta('');
    setFechaDesde(''); setFechaHasta('');
    setPaginaActual(1);
    // Cargar sin filtros
    setTimeout(() => cargarVentas(1, true), 0);
  };

  const totalPaginas = Math.ceil(totalRegistros / PAGE_SIZE);

  const formatearMoneda = (monto: number | string) =>
    `Gs. ${Number(monto).toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;

  const formatearFecha = (fecha: string) =>
    new Date(fecha).toLocaleDateString('es-PY', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

  const getEstadoPagoBadge = (estado: string) => {
    switch (estado) {
      case 'Pagado': return <Badge variant="success">{estado}</Badge>;
      case 'Pendiente': return <Badge variant="warning">{estado}</Badge>;
      case 'Parcial': return <Badge variant="info">{estado}</Badge>;
      default: return <Badge variant="default">{estado}</Badge>;
    }
  };

  const getTipoVentaBadge = (tipo: string) => {
    return tipo === 'Contado'
      ? <Badge variant="success">Contado</Badge>
      : <Badge variant="info">Crédito</Badge>;
  };

  // Totales rápidos de la página actual
  const totalPagina = ventas.reduce((s, v) => s + Number(v.monto_total), 0);

  return (
    <div className="space-y-4">
      {/* Barra de búsqueda y filtros */}
      <form onSubmit={handleBuscar} className="flex flex-wrap gap-3">
        <div className="flex flex-1 min-w-64">
          <Input
            type="text"
            placeholder="Buscar por factura, cliente, nombre..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            leftIcon={<Search className="h-4 w-4 text-gray-400" />}
          />
        </div>
        <Button type="submit" variant="primary" leftIcon={<Search className="h-4 w-4" />}>
          Buscar
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => setMostrarFiltros(f => !f)}
          leftIcon={<Filter className="h-4 w-4" />}
        >
          Filtros {(estadoPago || tipoVenta || fechaDesde || fechaHasta) ? '●' : ''}
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => cargarVentas(paginaActual)}
          leftIcon={<RefreshCw className="h-4 w-4" />}
        >
          Actualizar
        </Button>
      </form>

      {/* Panel de filtros avanzados */}
      {mostrarFiltros && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Estado de Pago</label>
              <select
                value={estadoPago}
                onChange={(e) => setEstadoPago(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              >
                <option value="">Todos</option>
                {ESTADOS_PAGO.map(e => <option key={e} value={e}>{e}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Tipo de Venta</label>
              <select
                value={tipoVenta}
                onChange={(e) => setTipoVenta(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              >
                <option value="">Todos</option>
                {TIPOS_VENTA.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Fecha Desde</label>
              <input
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Fecha Hasta</label>
              <input
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="mt-3 flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={handleLimpiarFiltros}>
              Limpiar
            </Button>
            <Button type="button" variant="primary" onClick={() => cargarVentas(1, true)}>
              Aplicar Filtros
            </Button>
          </div>
        </div>
      )}

      {/* Resumen rápido */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 flex items-center gap-3">
          <ShoppingBag className="h-7 w-7 text-amber-500 shrink-0" />
          <div>
            <p className="text-xs text-gray-500">Total registros</p>
            <p className="text-xl font-bold text-gray-800">{totalRegistros.toLocaleString('es-PY')}</p>
          </div>
        </div>
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 flex items-center gap-3">
          <DollarSign className="h-7 w-7 text-green-500 shrink-0" />
          <div>
            <p className="text-xs text-gray-500">Total en esta página</p>
            <p className="text-xl font-bold text-green-700">{formatearMoneda(totalPagina)}</p>
          </div>
        </div>
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 flex items-center gap-3">
          <TrendingUp className="h-7 w-7 text-blue-500 shrink-0" />
          <div>
            <p className="text-xs text-gray-500">Página</p>
            <p className="text-xl font-bold text-gray-800">{paginaActual} / {totalPaginas || 1}</p>
          </div>
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-hidden rounded-lg border border-gray-200">
        {cargando ? (
          <div className="flex items-center justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : ventas.length === 0 ? (
          <EmptyState
            icon={ShoppingBag}
            title="No hay ventas registradas"
            description={busqueda || estadoPago || tipoVenta || fechaDesde || fechaHasta
              ? "Intenta cambiar los filtros"
              : "Comienza a registrar ventas"}
            action={busqueda || estadoPago || tipoVenta || fechaDesde || fechaHasta ? {
              label: "Limpiar filtros",
              onClick: () => {
                setBusqueda('');
                setEstadoPago('');
                setTipoVenta('');
                setFechaDesde('');
                setFechaHasta('');
                cargarVentas(1, true);
              }
            } : undefined}
          />
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Factura / Fecha
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cliente
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tipo
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Estado Pago
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {ventas.map((venta) => (
                <tr
                  key={venta.id_venta}
                  className="hover:bg-amber-50/40 transition-colors"
                >
                  <td className="px-4 py-3">
                    <p className="font-mono text-sm font-semibold text-gray-800">
                      {venta.nro_factura_venta ? `#${venta.nro_factura_venta}` : `ID ${venta.id_venta}`}
                    </p>
                    <div className="mt-0.5 flex items-center gap-1 text-xs text-gray-400">
                      <Calendar className="h-3 w-3" />
                      <span>{formatearFecha(venta.fecha)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <p className="text-sm text-gray-800">
                      {venta.cliente_nombre || venta.hijo_nombre || '—'}
                    </p>
                    {venta.hijo_nombre && venta.cliente_nombre && (
                      <p className="text-xs text-gray-400">{venta.cliente_nombre}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <p className="font-semibold text-gray-900">{formatearMoneda(venta.monto_total)}</p>
                    {venta.saldo_pendiente > 0 && (
                      <p className="text-xs text-red-500">Pendiente: {formatearMoneda(venta.saldo_pendiente)}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {getTipoVentaBadge(venta.tipo_venta)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {getEstadoPagoBadge(venta.estado_pago)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-1">
                      <button
                        type="button"
                        onClick={() => setVentaDetalle(venta)}
                        className="rounded-lg p-1.5 text-gray-400 hover:bg-amber-100 hover:text-amber-700 transition-colors"
                        title="Ver detalle"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      {venta.saldo_pendiente > 0 && (
                        <button
                          type="button"
                          onClick={() => abrirModalPago(venta)}
                          className="rounded-lg p-1.5 text-red-400 hover:bg-green-100 hover:text-green-700 transition-colors"
                          title="Registrar pago"
                        >
                          <Banknote className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Paginación */}
      {totalPaginas > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 pt-3">
          <p className="text-sm text-gray-500">
            Mostrando {((paginaActual - 1) * PAGE_SIZE) + 1}–{Math.min(paginaActual * PAGE_SIZE, totalRegistros)} de {totalRegistros} registros
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPaginaActual(p => Math.max(1, p - 1))}
              disabled={paginaActual === 1 || cargando}
              className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            {Array.from({ length: Math.min(5, totalPaginas) }, (_, i) => {
              const offset = Math.max(0, Math.min(paginaActual - 3, totalPaginas - 5));
              const page = i + 1 + offset;
              return (
                <button
                  key={page}
                  type="button"
                  onClick={() => setPaginaActual(page)}
                  disabled={cargando}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                    page === paginaActual
                      ? 'bg-amber-500 text-white'
                      : 'border border-gray-300 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {page}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => setPaginaActual(p => Math.min(totalPaginas, p + 1))}
              disabled={paginaActual === totalPaginas || cargando}
              className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Modal de Detalle */}
      {ventaDetalle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setVentaDetalle(null)}>
          <div
            className="w-full max-w-lg rounded-xl bg-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-800">
                Detalle de Venta {ventaDetalle.nro_factura_venta ? `#${ventaDetalle.nro_factura_venta}` : `ID ${ventaDetalle.id_venta}`}
              </h3>
              <button
                type="button"
                onClick={() => setVentaDetalle(null)}
                className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3 p-6 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Fecha:</span>
                <span className="font-medium">{formatearFecha(ventaDetalle.fecha)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Cliente:</span>
                <span className="font-medium">{ventaDetalle.cliente_nombre || ventaDetalle.hijo_nombre || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Tipo de venta:</span>
                {getTipoVentaBadge(ventaDetalle.tipo_venta)}
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Estado de pago:</span>
                {getEstadoPagoBadge(ventaDetalle.estado_pago)}
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Estado:</span>
                <span className="font-medium">{ventaDetalle.estado}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Tipo pago:</span>
                <span className="font-medium">{ventaDetalle.tipo_venta}</span>
              </div>
              <div className="border-t border-gray-100 pt-3">
                <div className="flex justify-between text-base">
                  <span className="font-semibold text-gray-700">Total:</span>
                  <span className="font-bold text-amber-600">{formatearMoneda(ventaDetalle.monto_total)}</span>
                </div>
                {ventaDetalle.saldo_pendiente > 0 && (
                  <div className="flex justify-between text-sm mt-1">
                    <span className="text-red-500">Saldo pendiente:</span>
                    <span className="font-semibold text-red-600">{formatearMoneda(ventaDetalle.saldo_pendiente)}</span>
                  </div>
                )}
              </div>
              {((ventaDetalle.iva_10 ?? 0) > 0 || (ventaDetalle.iva_5 ?? 0) > 0 || (ventaDetalle.monto_exenta ?? 0) > 0) && (
                <div className="mt-3 rounded-lg bg-gray-50 border border-gray-200 p-3">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">Desglose Fiscal (IVA incluido)</p>
                  <div className="space-y-1">
                    {(ventaDetalle.monto_exenta ?? 0) > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Exenta:</span>
                        <span className="font-medium">{formatearMoneda(ventaDetalle.monto_exenta!)}</span>
                      </div>
                    )}
                    {(ventaDetalle.monto_gravada_10 ?? 0) > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Gravada 10%:</span>
                        <span className="font-medium">{formatearMoneda(ventaDetalle.monto_gravada_10!)}</span>
                      </div>
                    )}
                    {(ventaDetalle.iva_10 ?? 0) > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">IVA (10%):</span>
                        <span className="font-medium text-blue-700">{formatearMoneda(ventaDetalle.iva_10!)}</span>
                      </div>
                    )}
                    {(ventaDetalle.monto_gravada_5 ?? 0) > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Gravada 5%:</span>
                        <span className="font-medium">{formatearMoneda(ventaDetalle.monto_gravada_5!)}</span>
                      </div>
                    )}
                    {(ventaDetalle.iva_5 ?? 0) > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">IVA (5%):</span>
                        <span className="font-medium text-blue-700">{formatearMoneda(ventaDetalle.iva_5!)}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="border-t border-gray-200 px-6 py-3 text-right">
              <Button type="button" variant="secondary" onClick={() => setVentaDetalle(null)}>
                Cerrar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Registro de Pago */}
      {ventaPago && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setVentaPago(null)}>
          <div
            className="w-full max-w-md rounded-xl bg-white shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800">Registrar Pago</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Factura {ventaPago.nro_factura_venta ? `#${ventaPago.nro_factura_venta}` : `ID ${ventaPago.id_venta}`}
                  {' · '}Cliente: {ventaPago.cliente_nombre || ventaPago.hijo_nombre || '—'}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setVentaPago(null)}
                className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleRegistrarPago} className="space-y-4 p-6">
              <div className="rounded-lg bg-red-50 border border-red-200 p-3 flex justify-between text-sm">
                <span className="text-red-600 font-medium">Saldo pendiente:</span>
                <span className="font-bold text-red-700">{formatearMoneda(ventaPago.saldo_pendiente)}</span>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Monto a pagar *</label>
                <input
                  type="number"
                  min="1"
                  max={ventaPago.saldo_pendiente}
                  step="1"
                  value={montoPago}
                  onChange={(e) => setMontoPago(e.target.value)}
                  required
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                  placeholder={`Máx. ${ventaPago.saldo_pendiente.toLocaleString('es-PY')}`}
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Medio de pago *</label>
                <select
                  value={medioPagoId}
                  onChange={(e) => { setMedioPagoId(e.target.value); setRefPagoPos(''); setRefPgTransf(''); setBancoEmisor(''); }}
                  required
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                >
                  <option value="">Seleccionar...</option>
                  {mediosPago.map(m => (
                    <option key={m.id_medio_pago} value={m.id_medio_pago}>{m.nombre}</option>
                  ))}
                </select>
              </div>

              {/* Campos condicionales según medio de pago */}
              {(() => {
                const medio = mediosPago.find(m => m.id_medio_pago === Number(medioPagoId));
                if (!medio) return null;
                const nombre = medio.nombre.toLowerCase();
                const esTransferencia = nombre.includes('transfer');
                const esPOS = !esTransferencia && (nombre.includes('tarjeta') || nombre.includes('pos') || nombre.includes('debit') || nombre.includes('crédit') || nombre.includes('credit'));
                return (
                  <>
                    {esPOS && (
                      <div>
                        <label className="mb-1 block text-sm font-medium text-gray-700">Ref. POS / Comprobante</label>
                        <input
                          type="text"
                          value={refPagoPos}
                          onChange={(e) => setRefPagoPos(e.target.value)}
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                          placeholder="N° de referencia del terminal"
                          maxLength={100}
                        />
                      </div>
                    )}
                    {esTransferencia && (
                      <>
                        <div>
                          <label className="mb-1 block text-sm font-medium text-gray-700">N° Referencia transferencia *</label>
                          <input
                            type="text"
                            value={refPgTransf}
                            onChange={(e) => setRefPgTransf(e.target.value)}
                            required
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                            placeholder="Número de operación bancaria"
                            maxLength={100}
                          />
                        </div>
                        <div>
                          <label className="mb-1 block text-sm font-medium text-gray-700">Banco emisor</label>
                          <input
                            type="text"
                            value={bancoEmisor}
                            onChange={(e) => setBancoEmisor(e.target.value)}
                            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
                            placeholder="Ej: Banco Continental"
                            maxLength={100}
                          />
                        </div>
                      </>
                    )}
                  </>
                );
              })()}

              {errorPago && (
                <p className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-600">{errorPago}</p>
              )}

              <div className="flex gap-3 pt-2">
                <Button type="button" variant="secondary" onClick={() => setVentaPago(null)} className="flex-1">
                  Cancelar
                </Button>
                <Button type="submit" variant="primary" className="flex-1" disabled={procesandoPago}>
                  {procesandoPago ? <Spinner size="sm" /> : 'Registrar Pago'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistorialVentas;
