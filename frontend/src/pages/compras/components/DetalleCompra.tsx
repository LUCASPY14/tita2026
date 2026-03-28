import React, { useState, useEffect } from 'react';
import { ArrowLeft, Edit, ShoppingCart, DollarSign, Package, FileText, TrendingUp } from 'lucide-react';
import { comprasService } from '../../../services/compras.service';
import { Compra, CuentaCorrienteProveedor } from '../../../types';
import { Card, Spinner } from '../../../components/common';

interface DetalleCompraProps {
  compra: Compra;
  onEditar: (compra: Compra) => void;
  onVolver: () => void;
}

const DetalleCompra: React.FC<DetalleCompraProps> = ({ compra, onEditar, onVolver }) => {
  const [cuentaCorriente, setCuentaCorriente] = useState<CuentaCorrienteProveedor | null>(null);
  const [cargandoCuenta, setCargandoCuenta] = useState(false);

  useEffect(() => {
    if (compra.id_proveedor) {
      cargarCuentaCorriente();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [compra.id_proveedor]);

  const cargarCuentaCorriente = async () => {
    setCargandoCuenta(true);
    try {
      const cuenta = await comprasService.getCuentaCorrienteProveedor(compra.id_proveedor);
      setCuentaCorriente(cuenta);
    } catch (error) {
      console.error('Error al cargar cuenta corriente:', error);
    } finally {
      setCargandoCuenta(false);
    }
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(valor);
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-PY', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getEstadoBadge = (estado: string) => {
    const badges = {
      Pendiente: 'bg-yellow-100 text-yellow-800',
      Parcial: 'bg-blue-100 text-blue-800',
      Pagado: 'bg-green-100 text-green-800',
    };
    return badges[estado as keyof typeof badges] || 'bg-gray-100 text-gray-800';
  };

  const calcularPorcentajePagado = () => {
    if (!compra.monto_total || compra.monto_total === 0) return 0;
    const pagado = compra.monto_total - compra.saldo_pendiente;
    return (pagado / compra.monto_total) * 100;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onVolver}
            className="rounded-lg border border-gray-300 p-2 hover:bg-gray-50"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Detalle de la Compra</h2>
            <p className="mt-1 text-sm text-gray-600">
              Información completa y estado de pago
            </p>
          </div>
        </div>
        {compra.estado_pago === 'Pendiente' && (
          <button
            onClick={() => onEditar(compra)}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            <Edit className="h-4 w-4" />
            Editar
          </button>
        )}
      </div>

      {/* Grid Principal */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Columna Izquierda - Información de la Compra */}
        <div className="space-y-6 lg:col-span-2">
          {/* Card Info Principal */}
          <Card title="Información de la Compra">
            <div className="space-y-4">
              <div className="flex items-start gap-4 border-b border-gray-200 pb-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
                  <ShoppingCart className="h-8 w-8 text-amber-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900">
                    Compra #{compra.id_compra}
                  </h3>
                  <p className="mt-1 text-sm text-gray-600">
                    {compra.proveedor_nombre || 'Proveedor no especificado'}
                  </p>
                  <div className="mt-2">
                    <span
                      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${getEstadoBadge(
                        compra.estado_pago
                      )}`}
                    >
                      {compra.estado_pago}
                    </span>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Fecha de Compra</p>
                  <p className="mt-1 text-sm text-gray-900">{formatearFecha(compra.fecha)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Número de Factura</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {compra.nro_factura || 'No asignado'}
                  </p>
                </div>
              </div>

              {compra.observaciones && (
                <div className="rounded-lg bg-gray-50 p-3">
                  <p className="text-sm font-medium text-gray-700">Observaciones:</p>
                  <p className="mt-1 text-sm text-gray-600">{compra.observaciones}</p>
                </div>
              )}

              {/* Barra de progreso de pago */}
              <div>
                <div className="mb-2 flex justify-between text-sm">
                  <span className="font-medium text-gray-700">Progreso de Pago</span>
                  <span className="text-gray-600">{calcularPorcentajePagado().toFixed(1)}%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-full bg-green-600 transition-all"
                    style={{ width: `${calcularPorcentajePagado()}%` }}
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Card Detalles de Productos */}
          <Card title="Productos">
            {compra.detalles && compra.detalles.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 bg-gray-50">
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                        Producto
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                        Cantidad
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                        Costo Unit.
                      </th>
                      <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                        Subtotal
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {compra.detalles.map((detalle) => (
                      <tr key={detalle.id_detalle}>
                        <td className="px-4 py-4">
                          <div className="flex items-center gap-2">
                            <Package className="h-4 w-4 text-gray-400" />
                            <span className="text-sm font-medium text-gray-900">
                              {detalle.producto_nombre || `Producto #${detalle.id_producto}`}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-right text-sm text-gray-900">
                          {detalle.cantidad}
                        </td>
                        <td className="px-4 py-4 text-right text-sm text-gray-900">
                          {formatearMoneda(detalle.costo_unitario)}
                        </td>
                        <td className="px-4 py-4 text-right text-sm font-semibold text-gray-900">
                          {formatearMoneda(detalle.subtotal)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t-2 border-gray-300 bg-gray-50">
                      <td colSpan={3} className="px-4 py-3 text-right text-sm font-bold text-gray-900">
                        TOTAL:
                      </td>
                      <td className="px-4 py-3 text-right text-lg font-bold text-amber-600">
                        {formatearMoneda(compra.monto_total)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center">
                <Package className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-4 text-sm font-medium text-gray-900">
                  No hay productos
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  Esta compra no tiene productos registrados
                </p>
              </div>
            )}
          </Card>
        </div>

        {/* Columna Derecha - Resumen Financiero */}
        <div className="space-y-6">
          {/* Card Monto Total */}
          <Card>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-amber-100 p-3">
                  <DollarSign className="h-6 w-6 text-amber-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Monto Total</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatearMoneda(compra.monto_total)}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Card Saldo Pendiente */}
          <Card>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-red-100 p-3">
                  <FileText className="h-6 w-6 text-red-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-600">Saldo Pendiente</p>
                  <p className="text-2xl font-bold text-red-600">
                    {formatearMoneda(compra.saldo_pendiente)}
                  </p>
                </div>
              </div>
              <div className="border-t border-gray-200 pt-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Monto Pagado:</span>
                  <span className="font-medium text-green-600">
                    {formatearMoneda(compra.monto_total - compra.saldo_pendiente)}
                  </span>
                </div>
              </div>
            </div>
          </Card>

          {/* Card Cuenta Corriente Proveedor */}
          {cargandoCuenta ? (
            <Card>
              <div className="flex items-center justify-center py-8">
                <Spinner size="md" />
              </div>
            </Card>
          ) : cuentaCorriente ? (
            <Card title="Cuenta Corriente del Proveedor">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-blue-100 p-3">
                    <TrendingUp className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-600">Saldo Total</p>
                    <p className="text-xl font-bold text-blue-600">
                      {formatearMoneda(cuentaCorriente.saldo_pendiente)}
                    </p>
                  </div>
                </div>
                <div className="space-y-2 border-t border-gray-200 pt-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Compras:</span>
                    <span className="font-medium text-gray-900">
                      {formatearMoneda(cuentaCorriente.total_compras)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Pagado:</span>
                    <span className="font-medium text-green-600">
                      {formatearMoneda(cuentaCorriente.total_pagado)}
                    </span>
                  </div>
                  <div className="flex justify-between border-t border-gray-200 pt-2">
                    <span className="text-gray-600">Compras Pendientes:</span>
                    <span className="font-medium text-gray-900">
                      {cuentaCorriente.compras_pendientes}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default DetalleCompra;
