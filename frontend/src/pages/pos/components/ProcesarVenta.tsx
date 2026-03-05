import React, { useState, useEffect } from 'react';
import { X, CreditCard, Wallet, DollarSign, AlertTriangle, CheckCircle, Tag, Loader2 } from 'lucide-react';
import { Button, Card } from '../../../components/common';
import { BusquedaHijo } from '../../recargas/components';
import { posService } from '../../../services/pos.service';
import type { Producto, Hijo, Tarjeta, MedioPago, VentaData, Venta } from '../../../types';
import ReciboVenta from './ReciboVenta';
import toast from 'react-hot-toast';

interface ItemCarrito {
  producto: Producto;
  cantidad: number;
  subtotal: number;
}

interface ProcesarVentaProps {
  items: ItemCarrito[];
  total: number;
  onCerrar: () => void;
  onVentaExitosa: () => void;
}

type MetodoPago = 'efectivo' | 'tarjeta_hijo' | 'pos';

const ProcesarVenta: React.FC<ProcesarVentaProps> = ({
  items,
  total,
  onCerrar,
  onVentaExitosa,
}) => {
  const [metodoPago, setMetodoPago] = useState<MetodoPago>('efectivo');
  const [numeroComprobante, setNumeroComprobante] = useState('');
  const [procesando, setProcesando] = useState(false);
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([]);
  const [hijoSeleccionado, setHijoSeleccionado] = useState<Hijo | null>(null);
  const [tarjetaSeleccionada, setTarjetaSeleccionada] = useState<Tarjeta | null>(null);
  const [codigoPromo, setCodigoPromo] = useState('');
  const [validandoPromo, setValidandoPromo] = useState(false);
  const [promoValidada, setPromoValidada] = useState<{
    descuento_calculado: number;
    tipo_descuento: string;
    descripcion: string;
  } | null>(null);
  const [ventaRealizada, setVentaRealizada] = useState<Venta | null>(null);
  const [mostrarRecibo, setMostrarRecibo] = useState(false);

  useEffect(() => {
    cargarMediosPago();
  }, []);

  const cargarMediosPago = async () => {
    try {
      const response = await posService.getMediosPago();
      setMediosPago(response || []);
    } catch (error) {
      console.error('Error al cargar medios de pago:', error);
    }
  };

  const getMedioPagoId = (): number | undefined => {
    if (metodoPago === 'pos' || metodoPago === 'tarjeta_hijo') {
      const medio = mediosPago.find(m => 
        m.nombre.toLowerCase().includes(metodoPago === 'pos' ? 'pos' : 'tarjeta')
      );
      return medio?.id_medio_pago;
    }
    return undefined;
  };

  const medioPagoPos = mediosPago.find(m => m.nombre.toLowerCase().includes('pos')) ?? null;
  const posGeneraComision = metodoPago === 'pos' && (medioPagoPos?.genera_comision ?? false);
  const totalConDescuento = promoValidada ? total - promoValidada.descuento_calculado : total;

  const handleValidarPromo = async () => {
    if (!codigoPromo.trim()) return;
    setValidandoPromo(true);
    try {
      const result = await posService.validarCodigoPromo({
        codigo_promocion: codigoPromo.trim(),
        monto_total: total,
        productos: items.map(i => ({ id_producto: i.producto.id_producto, cantidad: i.cantidad })),
      });
      if (result.valido) {
        setPromoValidada({
          descuento_calculado: result.descuento_calculado,
          tipo_descuento: result.tipo_descuento,
          descripcion: result.descripcion,
        });
        toast.success(`Promoción aplicada: ${result.descripcion}`);
      } else {
        toast.error(result.mensaje || 'Código de promoción inválido');
      }
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error al validar la promoción');
    } finally {
      setValidandoPromo(false);
    }
  };

  const formatearPrecio = (precio?: number): string => {
    if (!precio) return 'Gs. 0';
    return `Gs. ${precio.toLocaleString('es-PY')}`;
  };

  const validarVenta = (): string | null => {
    if (items.length === 0) {
      return 'El carrito está vacío';
    }

    if (metodoPago === 'tarjeta_hijo') {
      if (!hijoSeleccionado || !tarjetaSeleccionada) {
        return 'Debes seleccionar un hijo con tarjeta para pagar con saldo';
      }

      if (tarjetaSeleccionada.estado !== 'Activa') {
        return 'La tarjeta seleccionada no está activa';
      }

      if (tarjetaSeleccionada.saldo_actual < totalConDescuento) {
        return `Saldo insuficiente. Disponible: ${formatearPrecio(tarjetaSeleccionada.saldo_actual)}`;
      }
    }

    if (metodoPago === 'pos' && !numeroComprobante.trim()) {
      return 'Debes ingresar el número de comprobante para pago con POS';
    }

    return null;
  };

  const handleProcesar = async () => {
    const error = validarVenta();
    if (error) {
      toast.error(error);
      return;
    }

    setProcesando(true);
    try {
      const ventaData: VentaData = {
        tipo_venta: metodoPago === 'tarjeta_hijo' && tarjetaSeleccionada ? 'Credito' : 'Contado',
        detalles: items.map(item => ({
          id_producto: item.producto.id_producto,
          cantidad: item.cantidad,
          precio_unitario: item.producto.precio || 0,
        })),
      };

      if (metodoPago === 'tarjeta_hijo' && hijoSeleccionado) {
        ventaData.id_hijo = hijoSeleccionado.id_hijo;
      }

      if (metodoPago === 'pos' || metodoPago === 'tarjeta_hijo') {
        ventaData.id_medio_pago = getMedioPagoId();
      }

      if (metodoPago === 'pos' && numeroComprobante.trim()) {
        ventaData.numero_comprobante = numeroComprobante.trim();
      }

      if (promoValidada && codigoPromo.trim()) {
        ventaData.codigo_promocion = codigoPromo.trim();
        ventaData.aplicar_promociones = true;
      }

      const ventaCreada = await posService.crearVenta(ventaData);
      
      toast.success('Venta procesada exitosamente');
      setVentaRealizada(ventaCreada);
      setMostrarRecibo(true);
      onVentaExitosa();
    } catch (error: any) {
      console.error('Error al procesar venta:', error);
      toast.error(error.response?.data?.detail || 'Error al procesar la venta');
    } finally {
      setProcesando(false);
    }
  };

  const calcularNuevoSaldo = (): number => {
    if (metodoPago === 'tarjeta_hijo' && tarjetaSeleccionada) {
      return tarjetaSeleccionada.saldo_actual - totalConDescuento;
    }
    return 0;
  };

  const saldoInsuficiente = metodoPago === 'tarjeta_hijo' && 
    tarjetaSeleccionada ? 
    tarjetaSeleccionada.saldo_actual < totalConDescuento :
    false;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="relative h-full w-full overflow-y-auto bg-white md:h-auto md:max-h-[90vh] md:w-full md:max-w-4xl md:rounded-lg">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b bg-white px-6 py-4">
          <div className="flex items-center gap-3">
            <DollarSign className="h-6 w-6 text-amber-600" />
            <h2 className="text-2xl font-bold text-gray-900">Procesar Venta</h2>
          </div>
          <button
            onClick={onCerrar}
            className="rounded-lg p-2 hover:bg-gray-100"
            disabled={procesando}
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-6 p-6">
          {/* Selección Cliente/Hijo */}
          {metodoPago === 'tarjeta_hijo' && (
            <Card>
              <h3 className="mb-4 text-lg font-semibold text-gray-900">
                Seleccionar Hijo
              </h3>
              <BusquedaHijo
                onHijoSeleccionado={(hijo, tarjeta) => {
                  setHijoSeleccionado(hijo);
                  setTarjetaSeleccionada(tarjeta);
                }}
              />
            </Card>
          )}

          {/* Método de Pago */}
          <Card>
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Método de Pago
            </h3>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <button
                onClick={() => setMetodoPago('efectivo')}
                className={`flex items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                  metodoPago === 'efectivo'
                    ? 'border-amber-600 bg-amber-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Wallet className="h-6 w-6 text-amber-600" />
                <div className="text-left">
                  <p className="font-semibold text-gray-900">Efectivo</p>
                  <p className="text-xs text-gray-500">Pago en caja</p>
                </div>
              </button>

              <button
                onClick={() => setMetodoPago('tarjeta_hijo')}
                className={`flex items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                  metodoPago === 'tarjeta_hijo'
                    ? 'border-amber-600 bg-amber-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <CreditCard className="h-6 w-6 text-blue-600" />
                <div className="text-left">
                  <p className="font-semibold text-gray-900">Tarjeta Hijo</p>
                  <p className="text-xs text-gray-500">Saldo estudiante</p>
                </div>
              </button>

              <button
                onClick={() => setMetodoPago('pos')}
                className={`flex items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                  metodoPago === 'pos'
                    ? 'border-amber-600 bg-amber-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <DollarSign className="h-6 w-6 text-green-600" />
                <div className="text-left">
                  <p className="font-semibold text-gray-900">POS</p>
                  <p className="text-xs text-gray-500">Tarjeta débito/crédito</p>
                </div>
              </button>
            </div>

            {metodoPago === 'pos' && (
              <div className="mt-4">
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Número de Comprobante
                </label>
                <input
                  type="text"
                  value={numeroComprobante}
                  onChange={(e) => setNumeroComprobante(e.target.value)}
                  placeholder="Ej: 123456"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                />
                {posGeneraComision && (
                  <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                    <p>Este medio de pago genera una <strong>comisión adicional</strong> que será calculada y registrada al confirmar la venta.</p>
                  </div>
                )}
              </div>
            )}
          </Card>

          {/* Resumen de Venta */}
          <Card>
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Resumen de Venta
            </h3>

            {/* Items */}
            <div className="mb-4 space-y-2">
              {items.map((item) => (
                <div
                  key={item.producto.id_producto}
                  className="flex items-center justify-between text-sm"
                >
                  <span className="text-gray-600">
                    {item.cantidad}x {item.producto.descripcion}
                  </span>
                  <span className="font-medium text-gray-900">
                    {formatearPrecio(item.subtotal)}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t pt-4">
              <div className="flex items-center justify-between text-lg font-bold">
                <span>{promoValidada ? 'Subtotal' : 'Total'}</span>
                <span className={promoValidada ? 'text-gray-500 line-through' : 'text-amber-600'}>
                  {formatearPrecio(total)}
                </span>
              </div>

              {promoValidada && (
                <div className="mt-1 flex items-center justify-between text-sm text-green-700">
                  <span className="flex items-center gap-1">
                    <Tag className="h-3.5 w-3.5" />
                    Descuento ({promoValidada.descripcion})
                  </span>
                  <span className="font-medium">- {formatearPrecio(promoValidada.descuento_calculado)}</span>
                </div>
              )}

              {promoValidada && (
                <div className="mt-2 flex items-center justify-between text-lg font-bold text-green-700">
                  <span>Total final</span>
                  <span>{formatearPrecio(totalConDescuento)}</span>
                </div>
              )}

              {/* Código de Promoción */}
              <div className="mt-4 rounded-lg border border-gray-200 p-3">
                <p className="mb-2 flex items-center gap-1 text-sm font-medium text-gray-700">
                  <Tag className="h-4 w-4" />
                  Código de Promoción
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={codigoPromo}
                    onChange={(e) => {
                      setCodigoPromo(e.target.value);
                      if (promoValidada) setPromoValidada(null);
                    }}
                    placeholder="Ingresá el código"
                    className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                    disabled={validandoPromo}
                  />
                  <button
                    type="button"
                    onClick={handleValidarPromo}
                    disabled={!codigoPromo.trim() || validandoPromo}
                    className="flex items-center gap-1 rounded-lg bg-amber-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-amber-700 disabled:opacity-50"
                  >
                    {validandoPromo ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Aplicar'}
                  </button>
                </div>
                {promoValidada && (
                  <p className="mt-1.5 flex items-center gap-1 text-xs text-green-700">
                    <CheckCircle className="h-3.5 w-3.5" />
                    Promoción aplicada correctamente
                  </p>
                )}
              </div>

              {metodoPago === 'tarjeta_hijo' && tarjetaSeleccionada && (
                <div className="mt-4 rounded-lg bg-blue-50 p-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Saldo actual</span>
                    <span className="font-medium">
                      {formatearPrecio(tarjetaSeleccionada.saldo_actual)}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-sm font-bold">
                    <span className={saldoInsuficiente ? 'text-red-600' : 'text-green-600'}>
                      Nuevo saldo
                    </span>
                    <span className={saldoInsuficiente ? 'text-red-600' : 'text-green-600'}>
                      {formatearPrecio(calcularNuevoSaldo())}
                    </span>
                  </div>
                </div>
              )}

              {saldoInsuficiente && (
                <div className="mt-4 flex items-start gap-2 rounded-lg bg-red-50 p-4 text-sm text-red-700">
                  <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">Saldo insuficiente</p>
                    <p className="mt-1">
                      El saldo actual no es suficiente para completar esta compra.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 border-t bg-white px-6 py-4">
          <div className="flex gap-3">
            <Button
              variant="outline"
              fullWidth
              onClick={onCerrar}
              disabled={procesando}
            >
              Cancelar
            </Button>
            <Button
              variant="primary"
              fullWidth
              onClick={handleProcesar}
              disabled={procesando || saldoInsuficiente}
              leftIcon={procesando ? undefined : <CheckCircle className="h-5 w-5" />}
            >
              {procesando ? 'Procesando...' : 'Confirmar Venta'}
            </Button>
          </div>
        </div>
      </div>

      {/* Recibo post-venta */}
      {mostrarRecibo && ventaRealizada && (
        <ReciboVenta
          nroFactura={ventaRealizada.nro_factura_venta}
          fecha={ventaRealizada.fecha}
          items={items.map(i => ({
            descripcion: i.producto.descripcion,
            cantidad: i.cantidad,
            precio_unitario: i.precio_unitario,
            subtotal: i.subtotal,
          }))}
          total={total}
          descuento={promoValidada?.descuento_calculado}
          metodoPago={metodoPago}
          comprobante={numeroComprobante || undefined}
          clienteNombre={hijoSeleccionado ? `${hijoSeleccionado.nombre} ${hijoSeleccionado.apellido}` : undefined}
          tarjetaNro={tarjetaSeleccionada?.nro_tarjeta}
          onCerrar={() => {
            setMostrarRecibo(false);
            onCerrar();
          }}
        />
      )}
    </div>
  );
};

export default ProcesarVenta;
