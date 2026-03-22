import React, { useState } from 'react';
import {
  DollarSign, CreditCard, Banknote, CheckCircle, Building2,
  Copy, ArrowRight, ArrowLeft, FileText, Loader2, Info,
} from 'lucide-react';
import { Input, Button, Spinner } from '../../../components/common';
import { recargasService } from '../../../services/recargas.service';
import type { Hijo, Tarjeta } from '../../../types';
import toast from 'react-hot-toast';

type MetodoPago = 'efectivo' | 'tarjeta_pos' | 'transferencia';
type PasoTransferencia = 'monto' | 'referencia' | 'comprobante';

interface DatosReferencia {
  codigo_referencia: string;
  monto_transferir: number;
  datos_bancarios: {
    banco?: string;
    titular?: string;
    cuenta?: string;
    ruc?: string;
    [key: string]: any;
  };
  instrucciones: string;
}

interface FormularioRecargaProps {
  hijo: Hijo;
  tarjeta: Tarjeta;
  onRecargaExitosa: () => void;
}

const FormularioRecarga: React.FC<FormularioRecargaProps> = ({
  hijo,
  tarjeta,
  onRecargaExitosa,
}) => {
  const [monto, setMonto] = useState('');
  const [metodoPago, setMetodoPago] = useState<MetodoPago>('efectivo');
  const [referencia, setReferencia] = useState('');
  const [procesando, setProcesando] = useState(false);

  // Estado para flujo de transferencia bancaria
  const [pasoTransferencia, setPasoTransferencia] = useState<PasoTransferencia>('monto');
  const [datosReferencia, setDatosReferencia] = useState<DatosReferencia | null>(null);
  const [numeroComprobante, setNumeroComprobante] = useState('');
  const [generandoReferencia, setGenerandoReferencia] = useState(false);

  const montosRapidos = [10000, 20000, 50000, 100000];

  const validarMonto = (): number | null => {
    const montoNumerico = parseFloat(monto);
    if (!monto || montoNumerico <= 0) { toast.error('Ingresa un monto válido'); return null; }
    if (montoNumerico < 1000) { toast.error('El monto mínimo es Gs. 1.000'); return null; }
    if (montoNumerico > 1000000) { toast.error('El monto máximo es Gs. 1.000.000'); return null; }
    return montoNumerico;
  };

  const handleSubmitCaja = async (e: React.FormEvent) => {
    e.preventDefault();
    const montoNumerico = validarMonto();
    if (!montoNumerico) return;
    setProcesando(true);
    try {
      await recargasService.procesarRecargaCaja({
        hijo_id: hijo.id_hijo,
        monto: montoNumerico,
        metodo_pago: metodoPago as 'efectivo' | 'tarjeta_pos',
        referencia: referencia || undefined,
      });
      toast.success(
        <div>
          <p className="font-semibold">¡Recarga procesada exitosamente!</p>
          <p className="text-sm">Monto: Gs. {montoNumerico.toLocaleString('es-PY')}</p>
          <p className="text-sm">Método: {metodoPago === 'efectivo' ? 'Efectivo' : 'Tarjeta POS'}</p>
        </div>,
        { duration: 5000 }
      );
      setMonto(''); setReferencia('');
      onRecargaExitosa();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Error al procesar la recarga. Intenta nuevamente.');
    } finally {
      setProcesando(false);
    }
  };

  const handleGenerarReferencia = async () => {
    const montoNumerico = validarMonto();
    if (!montoNumerico) return;
    setGenerandoReferencia(true);
    try {
      const datos = await recargasService.generarReferenciaTransferencia({
        hijo_id: hijo.id_hijo,
        monto: montoNumerico,
      });
      setDatosReferencia(datos);
      setPasoTransferencia('referencia');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Error al generar la referencia de transferencia.');
    } finally {
      setGenerandoReferencia(false);
    }
  };

  const handleConfirmarTransferencia = async () => {
    if (!numeroComprobante.trim()) {
      toast.error('Ingresa el número de comprobante de la transferencia');
      return;
    }
    if (!datosReferencia) return;
    setProcesando(true);
    try {
      await recargasService.validarTransferencia({
        codigo_referencia: datosReferencia.codigo_referencia,
        numero_comprobante: numeroComprobante,
        hijo_id: hijo.id_hijo,
        monto: datosReferencia.monto_transferir,
      });
      toast.success(
        <div>
          <p className="font-semibold">¡Transferencia validada exitosamente!</p>
          <p className="text-sm">La recarga será acreditada una vez confirmada.</p>
        </div>,
        { duration: 6000 }
      );
      // Reset todo
      setMonto(''); setNumeroComprobante('');
      setDatosReferencia(null); setPasoTransferencia('monto');
      onRecargaExitosa();
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Error al validar la transferencia.');
    } finally {
      setProcesando(false);
    }
  };

  const handleMetodoPago = (metodo: MetodoPago) => {
    setMetodoPago(metodo);
    // Resetear flujo de transferencia al cambiar método
    if (metodo !== 'transferencia') {
      setPasoTransferencia('monto');
      setDatosReferencia(null);
      setNumeroComprobante('');
    }
  };

  const formatearMoneda = (valor: string | number): string => {
    const numero = typeof valor === 'string' ? parseFloat(valor) : valor;
    if (isNaN(numero)) return 'Gs. 0';
    return `Gs. ${numero.toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;
  };

  const calcularNuevoSaldo = (): number => (Number(tarjeta.saldo_actual) + (parseFloat(monto) || 0));

  const copiarAlPortapapeles = (texto: string, etiqueta: string) => {
    navigator.clipboard.writeText(texto).then(() => toast.success(`${etiqueta} copiado`));
  };

  // ── UI: Paso 2 de transferencia ─────────────────────────────────────────────
  if (metodoPago === 'transferencia' && pasoTransferencia === 'referencia' && datosReferencia) {
    return (
      <div className="space-y-5">
        {/* Indicador de pasos */}
        <div className="flex items-center gap-2 text-sm">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-white text-xs font-bold">✓</span>
          <span className="text-green-600 font-medium">Monto</span>
          <div className="h-px flex-1 bg-amber-400" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-white text-xs font-bold">2</span>
          <span className="text-amber-700 font-medium">Transferir</span>
          <div className="h-px flex-1 bg-gray-200" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-200 text-gray-500 text-xs font-bold">3</span>
          <span className="text-gray-400">Confirmar</span>
        </div>

        {/* Código de referencia */}
        <div className="rounded-lg bg-amber-50 border-2 border-amber-300 p-4">
          <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Código de Referencia</p>
          <div className="flex items-center gap-2">
            <span className="flex-1 font-mono text-2xl font-bold text-amber-800 tracking-widest">
              {datosReferencia.codigo_referencia}
            </span>
            <button
              type="button"
              onClick={() => copiarAlPortapapeles(datosReferencia.codigo_referencia, 'Código')}
              className="rounded-lg bg-amber-200 p-2 text-amber-700 hover:bg-amber-300 transition-colors"
              title="Copiar código"
            >
              <Copy className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1 text-xs text-amber-600">Incluí este código en el concepto de tu transferencia</p>
        </div>

        {/* Datos bancarios */}
        <div className="rounded-lg border border-gray-200 p-4 space-y-2">
          <div className="flex items-center gap-2 mb-3">
            <Building2 className="h-5 w-5 text-gray-500" />
            <h4 className="font-semibold text-gray-800">Datos Bancarios</h4>
          </div>
          {datosReferencia.datos_bancarios.banco && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Banco:</span>
              <span className="font-medium text-gray-900">{datosReferencia.datos_bancarios.banco}</span>
            </div>
          )}
          {datosReferencia.datos_bancarios.titular && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Titular:</span>
              <span className="font-medium text-gray-900">{datosReferencia.datos_bancarios.titular}</span>
            </div>
          )}
          {datosReferencia.datos_bancarios.cuenta && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">N° de Cuenta:</span>
              <div className="flex items-center gap-1">
                <span className="font-mono font-medium text-gray-900">{datosReferencia.datos_bancarios.cuenta}</span>
                <button
                  type="button"
                  onClick={() => copiarAlPortapapeles(datosReferencia.datos_bancarios.cuenta!, 'Cuenta')}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <Copy className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
          {datosReferencia.datos_bancarios.ruc && (
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">RUC:</span>
              <span className="font-medium text-gray-900">{datosReferencia.datos_bancarios.ruc}</span>
            </div>
          )}
          <div className="flex justify-between text-sm border-t border-gray-100 pt-2 mt-2">
            <span className="text-gray-500">Monto exacto:</span>
            <span className="font-bold text-green-600">{formatearMoneda(datosReferencia.monto_transferir)}</span>
          </div>
        </div>

        {/* Instrucciones */}
        {datosReferencia.instrucciones && (
          <div className="flex gap-2 rounded-lg bg-blue-50 border border-blue-200 p-3 text-sm text-blue-700">
            <Info className="h-4 w-4 mt-0.5 shrink-0" />
            <p>{datosReferencia.instrucciones}</p>
          </div>
        )}

        {/* Botones de navegación */}
        <div className="flex gap-3 border-t border-gray-200 pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setPasoTransferencia('monto')}
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Volver
          </Button>
          <Button
            type="button"
            variant="primary"
            fullWidth
            onClick={() => setPasoTransferencia('comprobante')}
            leftIcon={<ArrowRight className="h-4 w-4" />}
          >
            Ya transferí — Ingresar Comprobante
          </Button>
        </div>
      </div>
    );
  }

  // ── UI: Paso 3 de transferencia ─────────────────────────────────────────────
  if (metodoPago === 'transferencia' && pasoTransferencia === 'comprobante') {
    return (
      <div className="space-y-5">
        {/* Indicador de pasos */}
        <div className="flex items-center gap-2 text-sm">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-white text-xs font-bold">✓</span>
          <span className="text-green-600 font-medium">Monto</span>
          <div className="h-px flex-1 bg-green-400" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-white text-xs font-bold">✓</span>
          <span className="text-green-600 font-medium">Transferir</span>
          <div className="h-px flex-1 bg-amber-400" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-white text-xs font-bold">3</span>
          <span className="text-amber-700 font-medium">Confirmar</span>
        </div>

        {/* Resumen */}
        <div className="rounded-lg bg-green-50 border border-green-200 p-4 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Código de referencia:</span>
            <span className="font-mono font-bold text-gray-900">{datosReferencia?.codigo_referencia}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Monto transferido:</span>
            <span className="font-bold text-green-700">{formatearMoneda(datosReferencia?.monto_transferir || 0)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Tarjeta a acreditar:</span>
            <span className="font-mono text-gray-900">{tarjeta.nro_tarjeta}</span>
          </div>
        </div>

        {/* Número de comprobante */}
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            Número de Comprobante *
          </label>
          <Input
            type="text"
            placeholder="Ej: 1234567890 o REF-ABC123"
            value={numeroComprobante}
            onChange={(e) => setNumeroComprobante(e.target.value)}
            leftIcon={<FileText className="h-5 w-5 text-gray-400" />}
            maxLength={50}
          />
          <p className="mt-1 text-xs text-gray-500">
            Número de confirmación que aparece en tu resumen de transferencia
          </p>
        </div>

        {/* Botones */}
        <div className="flex gap-3 border-t border-gray-200 pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setPasoTransferencia('referencia')}
            leftIcon={<ArrowLeft className="h-4 w-4" />}
          >
            Volver
          </Button>
          <Button
            type="button"
            variant="primary"
            fullWidth
            disabled={procesando || !numeroComprobante.trim()}
            onClick={handleConfirmarTransferencia}
            leftIcon={procesando ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle className="h-4 w-4" />}
          >
            {procesando ? 'Validando...' : 'Confirmar Transferencia'}
          </Button>
        </div>
      </div>
    );
  }

  // ── UI: Formulario principal (Paso 1 / efectivo / POS) ──────────────────────
  const esTransferencia = metodoPago === 'transferencia';

  return (
    <form onSubmit={esTransferencia ? (e) => e.preventDefault() : handleSubmitCaja} className="space-y-6">
      {/* Saldo Actual */}
      <div className="rounded-lg bg-gradient-to-r from-amber-50 to-yellow-50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Saldo Actual</p>
            <p className="text-2xl font-bold text-amber-600">
              {formatearMoneda(tarjeta.saldo_actual.toString())}
            </p>
          </div>
          {monto && parseFloat(monto) > 0 && !esTransferencia && (
            <div className="text-right">
              <p className="text-sm text-gray-600">Nuevo Saldo</p>
              <p className="text-2xl font-bold text-green-600">
                {formatearMoneda(calcularNuevoSaldo().toString())}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Indicador de pasos (solo transferencia) */}
      {esTransferencia && (
        <div className="flex items-center gap-2 text-sm">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-white text-xs font-bold">1</span>
          <span className="text-amber-700 font-medium">Monto</span>
          <div className="h-px flex-1 bg-gray-200" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-200 text-gray-400 text-xs font-bold">2</span>
          <span className="text-gray-400">Transferir</span>
          <div className="h-px flex-1 bg-gray-200" />
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gray-200 text-gray-400 text-xs font-bold">3</span>
          <span className="text-gray-400">Confirmar</span>
        </div>
      )}

      {/* Monto de Recarga */}
      <div>
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Monto a Recargar *
        </label>
        <Input
          type="number"
          placeholder="Ej: 50000"
          value={monto}
          onChange={(e) => setMonto(e.target.value)}
          leftIcon={<DollarSign className="h-5 w-5 text-gray-400" />}
          required
          min="1000"
          max="1000000"
          step="1000"
        />
        <p className="mt-1 text-xs text-gray-500">Mínimo: Gs. 1.000 | Máximo: Gs. 1.000.000</p>

        {/* Montos Rápidos */}
        <div className="mt-3 space-y-2">
          <p className="text-xs font-medium text-gray-600">Montos Rápidos:</p>
          <div className="grid grid-cols-4 gap-2">
            {montosRapidos.map((montoRapido) => (
              <button
                key={montoRapido}
                type="button"
                onClick={() => setMonto(montoRapido.toString())}
                className={`rounded-lg border-2 px-3 py-2 text-sm font-medium transition-colors ${
                  monto === montoRapido.toString()
                    ? 'border-amber-500 bg-amber-50 text-amber-700'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-amber-300 hover:bg-amber-50'
                }`}
              >
                {montoRapido.toLocaleString('es-PY')} Gs.
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Método de Pago */}
      <div>
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Método de Pago *
        </label>
        <div className="grid grid-cols-3 gap-3">
          <button
            type="button"
            onClick={() => handleMetodoPago('efectivo')}
            className={`flex items-center justify-center gap-2 rounded-lg border-2 p-4 transition-colors ${
              metodoPago === 'efectivo'
                ? 'border-green-500 bg-green-50 text-green-700'
                : 'border-gray-200 bg-white text-gray-700 hover:border-green-300'
            }`}
          >
            <Banknote className="h-5 w-5" />
            <span className="font-medium text-sm">Efectivo</span>
          </button>

          <button
            type="button"
            onClick={() => handleMetodoPago('tarjeta_pos')}
            className={`flex items-center justify-center gap-2 rounded-lg border-2 p-4 transition-colors ${
              metodoPago === 'tarjeta_pos'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300'
            }`}
          >
            <CreditCard className="h-5 w-5" />
            <span className="font-medium text-sm">Tarjeta POS</span>
          </button>

          <button
            type="button"
            onClick={() => handleMetodoPago('transferencia')}
            className={`flex items-center justify-center gap-2 rounded-lg border-2 p-4 transition-colors ${
              metodoPago === 'transferencia'
                ? 'border-purple-500 bg-purple-50 text-purple-700'
                : 'border-gray-200 bg-white text-gray-700 hover:border-purple-300'
            }`}
          >
            <Building2 className="h-5 w-5" />
            <span className="font-medium text-sm">Transferencia</span>
          </button>
        </div>
      </div>

      {/* Referencia/Comprobante solo para efectivo/pos */}
      {!esTransferencia && (
        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            Referencia / Comprobante (Opcional)
          </label>
          <Input
            type="text"
            placeholder="Ej: CAJA-001, COMP-12345"
            value={referencia}
            onChange={(e) => setReferencia(e.target.value)}
            maxLength={100}
          />
          <p className="mt-1 text-xs text-gray-500">Número de comprobante o referencia interna</p>
        </div>
      )}

      {/* Nota informativa para transferencia */}
      {esTransferencia && (
        <div className="flex gap-2 rounded-lg bg-purple-50 border border-purple-200 p-3 text-sm text-purple-700">
          <Info className="h-4 w-4 mt-0.5 shrink-0" />
          <p>Se generará un código de referencia único para esta transferencia. Deberás incluirlo en el concepto al transferir.</p>
        </div>
      )}

      {/* Botón de acción */}
      <div className="flex gap-3 border-t border-gray-200 pt-4">
        {esTransferencia ? (
          <Button
            type="button"
            variant="primary"
            fullWidth
            disabled={generandoReferencia || !monto || parseFloat(monto) <= 0}
            onClick={handleGenerarReferencia}
            leftIcon={generandoReferencia ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowRight className="h-5 w-5" />}
          >
            {generandoReferencia ? 'Generando...' : 'Generar Código de Referencia'}
          </Button>
        ) : (
          <Button
            type="submit"
            variant="primary"
            fullWidth
            disabled={procesando || !monto || parseFloat(monto) <= 0}
            leftIcon={procesando ? <Spinner size="sm" /> : <CheckCircle className="h-5 w-5" />}
          >
            {procesando ? 'Procesando...' : 'Procesar Recarga'}
          </Button>
        )}
      </div>

      {/* Resumen (solo efectivo/pos) */}
      {!esTransferencia && monto && parseFloat(monto) > 0 && (
        <div className="rounded-lg border-2 border-dashed border-amber-300 bg-amber-50/30 p-4">
          <h4 className="mb-2 font-semibold text-gray-800">Resumen de la Operación</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Hijo:</span>
              <span className="font-medium text-gray-900">{hijo.nombre} {hijo.apellido}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Tarjeta:</span>
              <span className="font-mono font-medium text-gray-900">{tarjeta.nro_tarjeta}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Monto a recargar:</span>
              <span className="font-bold text-amber-600">{formatearMoneda(monto)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Método de pago:</span>
              <span className="font-medium text-gray-900">
                {metodoPago === 'efectivo' ? 'Efectivo' : 'Tarjeta POS'}
              </span>
            </div>
            <div className="mt-2 flex justify-between border-t border-amber-200 pt-2">
              <span className="font-semibold text-gray-700">Nuevo Saldo:</span>
              <span className="text-lg font-bold text-green-600">
                {formatearMoneda(calcularNuevoSaldo().toString())}
              </span>
            </div>
          </div>
        </div>
      )}
    </form>
  );
};

export default FormularioRecarga;
