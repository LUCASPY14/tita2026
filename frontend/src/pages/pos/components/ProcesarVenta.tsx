import React, { useState, useEffect } from 'react';
import { X, CreditCard, Wallet, DollarSign, AlertTriangle, CheckCircle, Banknote, Calculator, Plus, Trash2 } from 'lucide-react';
import { Button, Card } from '../../../components/common';
import { BusquedaHijo } from '../../recargas/components';
import { posService } from '../../../services/pos.service';
import type { Producto, Hijo, Tarjeta, MedioPago, VentaData, Venta, TarjetaEscaneada } from '../../../types';
import ReciboVenta from './ReciboVenta';
import ReciboCobro from '../../almuerzos/components/ReciboCobro';
import type { ReciboData } from '../../almuerzos/components/ReciboCobro';
import { almuerzosService } from '../../../services/almuerzos.service';
import toast from 'react-hot-toast';

interface ItemCarrito {
  producto: Producto;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

interface ProcesarVentaProps {
  items: ItemCarrito[];
  total: number;
  tarjetaEscaneada?: TarjetaEscaneada;
  onCerrar: () => void;
  onVentaExitosa: () => void;
}

type MetodoPago = 'efectivo' | 'tarjeta_hijo' | 'pos' | 'transferencia' | 'mixto';

interface PagoMixtoItem {
  metodo: Exclude<MetodoPago, 'mixto'>;
  monto: number;
  ref?: string;
  bancoEmisor?: string;
}

const ProcesarVenta: React.FC<ProcesarVentaProps> = ({
  items,
  total,
  tarjetaEscaneada,
  onCerrar,
  onVentaExitosa,
}) => {
  const [metodoPago, setMetodoPago] = useState<MetodoPago>(tarjetaEscaneada ? 'tarjeta_hijo' : 'efectivo');
  const [refPagoPos, setRefPagoPos] = useState('');
  const [refPgTransf, setRefPgTransf] = useState('');
  const [bancoEmisor, setBancoEmisor] = useState('');
  const [procesando, setProcesando] = useState(false);
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([]);
  const [hijoSeleccionado, setHijoSeleccionado] = useState<Hijo | null>(null);
  const [tarjetaSeleccionada, setTarjetaSeleccionada] = useState<Tarjeta | null>(null);
  const [montoRecibido, setMontoRecibido] = useState<string>(''); // Para efectivo
  const [pagosMixtos, setPagosMixtos] = useState<PagoMixtoItem[]>([]);
  const [nuevoMetodoMixto, setNuevoMetodoMixto] = useState<Exclude<MetodoPago, 'mixto'>>('efectivo');
  const [nuevoMontoMixto, setNuevoMontoMixto] = useState<string>('');
  const [ventaRealizada, setVentaRealizada] = useState<Venta | null>(null);
  const [mostrarRecibo, setMostrarRecibo] = useState(false);
  const [reciboCobroData, setReciboCobroData] = useState<ReciboData | null>(null);

  useEffect(() => {
    cargarMediosPago();
    if (tarjetaEscaneada) {
      // Pre-cargar datos del hijo ya escaneado
      setHijoSeleccionado({
        id_hijo: tarjetaEscaneada.hijo.id,
        nombre: tarjetaEscaneada.hijo.nombre,
        apellido: tarjetaEscaneada.hijo.apellido,
        estado: true,
        id_cliente_responsable: 0,
      } as Hijo);
      setTarjetaSeleccionada({
        nro_tarjeta: tarjetaEscaneada.numero,
        saldo_actual: tarjetaEscaneada.saldo.actual,
        estado: tarjetaEscaneada.estado as Tarjeta['estado'],
        fecha_creacion: '',
        permite_saldo_negativo: false,
        limite_credito: 0,
        notificar_saldo_bajo: false,
        id_hijo: tarjetaEscaneada.hijo.id,
      });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
    const buscar = (term: string) => mediosPago.find(m => m.nombre?.toLowerCase().includes(term))?.id_medio_pago;
    if (metodoPago === 'pos') return buscar('pos');
    if (metodoPago === 'tarjeta_hijo') return buscar('tarjeta');
    if (metodoPago === 'transferencia') return buscar('transf') ?? buscar('transfer');
    return undefined;
  };

  const medioPagoPos = mediosPago.find(m => m.nombre?.toLowerCase().includes('pos')) ?? null;
  const posGeneraComision = metodoPago === 'pos' && (medioPagoPos?.genera_comision ?? false);
  const formatearPrecio = (precio?: number): string => {
    if (!precio) return 'Gs. 0';
    return `Gs. ${precio.toLocaleString('es-PY')}`;
  };

  const calcularVuelto = (): number => {
    if (metodoPago !== 'efectivo' || !montoRecibido) return 0;
    const recibido = Number(montoRecibido);
    return recibido > total ? recibido - total : 0;
  };

  const calcularTotalPagosMixtos = (): number => {
    return pagosMixtos.reduce((sum, p) => sum + p.monto, 0);
  };

  const calcularFaltanteMixto = (): number => {
    return total - calcularTotalPagosMixtos();
  };

  const agregarPagoMixto = () => {
    const monto = Number(nuevoMontoMixto);
    if (!monto || monto <= 0) {
      toast.error('Ingresá un monto válido');
      return;
    }
    const faltante = calcularFaltanteMixto();
    if (monto > faltante) {
      toast.error(`El monto supera el faltante (${formatearPrecio(faltante)})`);
      return;
    }
    if (nuevoMetodoMixto === 'pos' && !refPagoPos.trim()) {
      toast.error('Ingresá la referencia POS');
      return;
    }
    if (nuevoMetodoMixto === 'transferencia' && !refPgTransf.trim()) {
      toast.error('Ingresá la referencia de transferencia');
      return;
    }
    const nuevoPago: PagoMixtoItem = {
      metodo: nuevoMetodoMixto,
      monto,
      ref: nuevoMetodoMixto === 'pos' ? refPagoPos : nuevoMetodoMixto === 'transferencia' ? refPgTransf : undefined,
      bancoEmisor: nuevoMetodoMixto === 'transferencia' ? bancoEmisor : undefined,
    };
    setPagosMixtos([...pagosMixtos, nuevoPago]);
    setNuevoMontoMixto('');
    setRefPagoPos('');
    setRefPgTransf('');
    setBancoEmisor('');
  };

  const eliminarPagoMixto = (index: number) => {
    setPagosMixtos(pagosMixtos.filter((_, i) => i !== index));
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

      if (tarjetaSeleccionada.saldo_actual < total) {
        return `Saldo insuficiente. Disponible: ${formatearPrecio(tarjetaSeleccionada.saldo_actual)}`;
      }
    }

    if (metodoPago === 'pos' && !refPagoPos.trim()) {
      return 'Debes ingresar la referencia del terminal POS';
    }

    if (metodoPago === 'transferencia' && !refPgTransf.trim()) {
      return 'Debes ingresar el número de referencia de la transferencia';
    }

    if (metodoPago === 'mixto') {
      const totalMixto = calcularTotalPagosMixtos();
      if (pagosMixtos.length === 0) {
        return 'Agregá al menos un método de pago';
      }
      if (totalMixto < total) {
        return `Falta cubrir ${formatearPrecio(total - totalMixto)}`;
      }
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
        tipo_venta: 'Contado',
        detalles: items.map(item => ({
          id_producto: item.producto.id_producto,
          cantidad: item.cantidad,
          precio_unitario: item.producto.precio || 0,
        })),
      };

      if (metodoPago === 'tarjeta_hijo' && hijoSeleccionado) {
        ventaData.id_hijo = hijoSeleccionado.id_hijo;
      }

      if (metodoPago === 'pos' || metodoPago === 'tarjeta_hijo' || metodoPago === 'transferencia') {
        ventaData.id_medio_pago = getMedioPagoId();
      }

      if (metodoPago === 'pos' && refPagoPos.trim()) {
        ventaData.ref_pago_pos = refPagoPos.trim();
      }
      if (metodoPago === 'transferencia') {
        if (refPgTransf.trim()) ventaData.ref_pg_transf = refPgTransf.trim();
        if (bancoEmisor.trim()) ventaData.banco_emisor = bancoEmisor.trim();
      }

      // Pago mixto: enviar array de pagos al backend
      if (metodoPago === 'mixto' && pagosMixtos.length > 0) {
        ventaData.pagos_data = pagosMixtos.map(pago => {
          // Buscar en nombre o descripcion (campo legacy vs campo real del modelo)
          const buscar = (term: string) => mediosPago.find(m => 
            m.nombre?.toLowerCase().includes(term) || 
            (m as any).descripcion?.toLowerCase().includes(term)
          )?.id_medio_pago;
          
          let id_medio_pago: number | undefined;
          
          if (pago.metodo === 'efectivo') {
            // Buscar medio de pago para efectivo: puede ser "Efectivo", "Caja", "Cash"
            id_medio_pago = buscar('efectivo') ?? buscar('caja') ?? buscar('cash');
            if (!id_medio_pago) {
              // Si no existe, buscar cualquier medio que no genere comisión
              const sinComision = mediosPago.find(m => !m.genera_comision);
              if (sinComision) {
                id_medio_pago = sinComision.id_medio_pago;
              }
            }
          } else if (pago.metodo === 'pos') {
            id_medio_pago = buscar('pos') ?? buscar('tarjeta');
          } else if (pago.metodo === 'tarjeta_hijo') {
            id_medio_pago = buscar('tarjeta') ?? buscar('crédito') ?? buscar('débito');
            // Si es el primer pago con tarjeta hijo, asignar el hijo
            if (hijoSeleccionado && !ventaData.id_hijo) {
              ventaData.id_hijo = hijoSeleccionado.id_hijo;
            }
          } else if (pago.metodo === 'transferencia') {
            id_medio_pago = buscar('transf') ?? buscar('bancaria');
          }

          // Validar que se encontró un medio de pago válido
          if (!id_medio_pago) {
            console.error(`No se encontró medio de pago para "${pago.metodo}". Medios disponibles:`, mediosPago);
            throw new Error(`No se encontró un medio de pago para: ${pago.metodo}. Verifica que exista en el sistema.`);
          }

          return {
            id_medio_pago,
            monto: pago.monto,
            ref_pago_pos: pago.metodo === 'pos' ? pago.ref : undefined,
            ref_pg_transf: pago.metodo === 'transferencia' ? pago.ref : undefined,
            banco_emisor: pago.metodo === 'transferencia' ? pago.bancoEmisor : undefined,
          };
        });
      }

      const ventaCreada = await posService.crearVenta(ventaData);
      
      toast.success('Venta procesada exitosamente');
      setVentaRealizada(ventaCreada);
      setMostrarRecibo(true);
      onVentaExitosa();
    } catch (error: any) {
      console.error('Error al procesar venta:', error);
      const mensaje = error.response?.data?.error 
        || error.response?.data?.detail 
        || error.response?.data?.message
        || error.message
        || 'Error al procesar la venta';
      toast.error(mensaje);
      
      // Mostrar errores de validación si existen
      if (error.response?.data?.productos_faltantes) {
        error.response.data.productos_faltantes.forEach((p: any) => {
          toast.error(`${p.producto}: Stock insuficiente (falta ${p.faltante})`);
        });
      }
    } finally {
      setProcesando(false);
    }
  };

  const handleImprimirReciboCobro = async () => {
    if (!ventaRealizada) return;
    let empresa: ReciboData['empresa'] = { razon_social: 'CANTINA TITA' };
    try { empresa = await almuerzosService.getDatosEmpresa(); } catch { /* usar nombre por defecto */ }
    const concepto = items.length === 1
      ? `${items[0].cantidad}× ${items[0].producto.descripcion}`
      : `Venta N° ${ventaRealizada.nro_factura_venta ?? ventaRealizada.id_venta} · ${items.length} productos`;
    const nombreCliente = hijoSeleccionado
      ? `${hijoSeleccionado.nombre} ${hijoSeleccionado.apellido}`
      : ventaRealizada.cliente_nombre || 'Consumidor final';
    const ref = [refPagoPos, refPgTransf, bancoEmisor].filter(Boolean).join(' · ');
    setReciboCobroData({
      tipo: 'recibo_cobro',
      empresa,
      recibo: {
        nro_interno: `RC-POS-${String(ventaRealizada.id_venta).padStart(6, '0')}`,
        fecha_emision: ventaRealizada.fecha.substring(0, 10),
        alumno: nombreCliente,
        concepto,
        cantidad_almuerzos: 0,
        monto_total: String(ventaRealizada.monto_total),
        monto_cobrado: String(total),
        saldo_pendiente: String(ventaRealizada.saldo_pendiente ?? 0),
        forma_pago: metodoPago,
        comprobante_ref: ref,
        estado: ventaRealizada.estado_pago,
        mes_nombre: '',
        anio: new Date(ventaRealizada.fecha).getFullYear(),
      },
    });
  };

  const calcularNuevoSaldo = (): number => {
    if (metodoPago === 'tarjeta_hijo' && tarjetaSeleccionada) {
      return tarjetaSeleccionada.saldo_actual - total;
    }
    return 0;
  };

  const saldoInsuficiente = metodoPago === 'tarjeta_hijo' && 
    tarjetaSeleccionada ? 
    tarjetaSeleccionada.saldo_actual < total :
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
              {tarjetaEscaneada ? (
                // Tarjeta ya escaneada en el POS — mostrar info, no pedir búsqueda
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
                    <CreditCard className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">
                      {tarjetaEscaneada.hijo.nombre} {tarjetaEscaneada.hijo.apellido}
                    </p>
                    <p className="text-sm text-gray-500 font-mono">{tarjetaEscaneada.numero}</p>
                    <p className="text-sm text-blue-600 font-medium">
                      Saldo: Gs. {Number(tarjetaEscaneada.saldo.disponible).toLocaleString('es-PY')}
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">Seleccionar Hijo</h3>
                  <BusquedaHijo
                    onHijoSeleccionado={(hijo, tarjeta) => {
                      setHijoSeleccionado(hijo);
                      setTarjetaSeleccionada(tarjeta);
                    }}
                  />
                </>
              )}
            </Card>
          )}

          {/* Método de Pago */}
          <Card>
            <h3 className="mb-4 text-lg font-semibold text-gray-900">
              Método de Pago
            </h3>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
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

              <button
                onClick={() => setMetodoPago('transferencia')}
                className={`flex items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                  metodoPago === 'transferencia'
                    ? 'border-amber-600 bg-amber-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Banknote className="h-6 w-6 text-purple-600" />
                <div className="text-left">
                  <p className="font-semibold text-gray-900">Transferencia</p>
                  <p className="text-xs text-gray-500">Bancaria / digital</p>
                </div>
              </button>

              <button
                onClick={() => setMetodoPago('mixto')}
                className={`flex items-center gap-3 rounded-lg border-2 p-4 transition-all ${
                  metodoPago === 'mixto'
                    ? 'border-amber-600 bg-amber-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <Calculator className="h-6 w-6 text-indigo-600" />
                <div className="text-left">
                  <p className="font-semibold text-gray-900">Mixto</p>
                  <p className="text-xs text-gray-500">Varios métodos</p>
                </div>
              </button>
            </div>

            {metodoPago === 'efectivo' && (
              <div className="mt-4 space-y-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Monto recibido
                  </label>
                  <input
                    type="number"
                    value={montoRecibido}
                    onChange={(e) => setMontoRecibido(e.target.value)}
                    placeholder={`Total: ${formatearPrecio(total)}`}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                  />
                </div>
                {calcularVuelto() > 0 && (
                  <div className="flex items-center justify-between rounded-lg border-2 border-green-200 bg-green-50 p-4">
                    <span className="text-sm font-medium text-gray-700">Vuelto:</span>
                    <span className="text-xl font-bold text-green-700">
                      {formatearPrecio(calcularVuelto())}
                    </span>
                  </div>
                )}
              </div>
            )}

            {metodoPago === 'pos' && (
              <div className="mt-4 space-y-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Referencia POS <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={refPagoPos}
                    onChange={(e) => setRefPagoPos(e.target.value)}
                    placeholder="N° de aprobación del terminal POS"
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                  />
                </div>
                {posGeneraComision && (
                  <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                    <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                    <p>Este medio de pago genera una <strong>comisión adicional</strong> que será calculada y registrada al confirmar la venta.</p>
                  </div>
                )}
              </div>
            )}

            {metodoPago === 'transferencia' && (
              <div className="mt-4 space-y-3">
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    N° de Referencia / Comprobante <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={refPgTransf}
                    onChange={(e) => setRefPgTransf(e.target.value)}
                    placeholder="Número de transferencia o comprobante bancario"
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-sm font-medium text-gray-700">
                    Banco emisor
                  </label>
                  <input
                    type="text"
                    value={bancoEmisor}
                    onChange={(e) => setBancoEmisor(e.target.value)}
                    placeholder="Ej: Banco Continental, Itaú, BCP..."
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                  />
                </div>
              </div>
            )}

            {metodoPago === 'mixto' && (
              <div className="mt-4 space-y-4">
                <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4">
                  <h4 className="mb-3 flex items-center gap-2 text-sm font-semibold text-indigo-900">
                    <Plus className="h-4 w-4" />
                    Agregar método de pago
                  </h4>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <select
                        value={nuevoMetodoMixto}
                        onChange={(e) => setNuevoMetodoMixto(e.target.value as Exclude<MetodoPago, 'mixto'>)}
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                      >
                        <option value="efectivo">Efectivo</option>
                        <option value="pos">POS</option>
                        <option value="transferencia">Transferencia</option>
                        <option value="tarjeta_hijo">Tarjeta Hijo</option>
                      </select>
                      <input
                        type="number"
                        value={nuevoMontoMixto}
                        onChange={(e) => setNuevoMontoMixto(e.target.value)}
                        placeholder="Monto"
                        className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                      />
                    </div>
                    {nuevoMetodoMixto === 'pos' && (
                      <input
                        type="text"
                        value={refPagoPos}
                        onChange={(e) => setRefPagoPos(e.target.value)}
                        placeholder="Referencia POS"
                        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                      />
                    )}
                    {nuevoMetodoMixto === 'transferencia' && (
                      <>
                        <input
                          type="text"
                          value={refPgTransf}
                          onChange={(e) => setRefPgTransf(e.target.value)}
                          placeholder="Referencia transferencia"
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        />
                        <input
                          type="text"
                          value={bancoEmisor}
                          onChange={(e) => setBancoEmisor(e.target.value)}
                          placeholder="Banco emisor"
                          className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                        />
                      </>
                    )}
                    <button
                      type="button"
                      onClick={agregarPagoMixto}
                      className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-indigo-700"
                    >
                      Agregar
                    </button>
                  </div>
                </div>

                {pagosMixtos.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-gray-700">Pagos agregados:</h4>
                    {pagosMixtos.map((pago, idx) => (
                      <div key={idx} className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-3">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {pago.metodo === 'efectivo' ? 'Efectivo' : pago.metodo === 'pos' ? 'POS' : pago.metodo === 'transferencia' ? 'Transferencia' : 'Tarjeta Hijo'}
                          </p>
                          {pago.ref && <p className="text-xs text-gray-500">Ref: {pago.ref}</p>}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">{formatearPrecio(pago.monto)}</span>
                          <button
                            type="button"
                            onClick={() => eliminarPagoMixto(idx)}
                            className="rounded p-1 text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                    <div className="flex items-center justify-between rounded-lg border-2 border-indigo-200 bg-indigo-50 p-3">
                      <span className="text-sm font-semibold text-indigo-900">Faltante:</span>
                      <span className={`text-lg font-bold ${calcularFaltanteMixto() === 0 ? 'text-green-700' : 'text-indigo-700'}`}>
                        {formatearPrecio(calcularFaltanteMixto())}
                      </span>
                    </div>
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
                <span>Total</span>
                <span className="text-amber-600">
                  {formatearPrecio(total)}
                </span>
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
          metodoPago={metodoPago}
          refPagoPos={refPagoPos || undefined}
          refPgTransf={refPgTransf || undefined}
          bancoEmisor={bancoEmisor || undefined}
          clienteNombre={hijoSeleccionado ? `${hijoSeleccionado.nombre} ${hijoSeleccionado.apellido}` : undefined}
          tarjetaNro={tarjetaSeleccionada?.nro_tarjeta}
          iva10={ventaRealizada.iva_10}
          iva5={ventaRealizada.iva_5}
          montoExenta={ventaRealizada.monto_exenta}
          montoGravada10={ventaRealizada.monto_gravada_10}
          montoGravada5={ventaRealizada.monto_gravada_5}
          onReciboCobro={handleImprimirReciboCobro}
          onCerrar={() => {
            setMostrarRecibo(false);
            onCerrar();
          }}
        />
      )}
      {reciboCobroData && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#fff', overflowY: 'auto' }}>
          <ReciboCobro
            data={reciboCobroData}
            onClose={() => setReciboCobroData(null)}
            autoImprimir={false}
          />
        </div>
      )}
    </div>
  );
};

export default ProcesarVenta;
