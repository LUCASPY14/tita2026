import React, { useState } from 'react';
import { DollarSign, CreditCard, Banknote, CheckCircle } from 'lucide-react';
import { Input, Button, Spinner } from '../../../components/common';
import { recargasService } from '../../../services/recargas.service';
import type { Hijo, Tarjeta } from '../../../types';
import toast from 'react-hot-toast';

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
  const [metodoPago, setMetodoPago] = useState<'efectivo' | 'tarjeta_pos'>('efectivo');
  const [referencia, setReferencia] = useState('');
  const [procesando, setProcesando] = useState(false);

  const montosRapidos = [10000, 20000, 50000, 100000];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const montoNumerico = parseFloat(monto);

    if (!monto || montoNumerico <= 0) {
      toast.error('Ingresa un monto válido');
      return;
    }

    if (montoNumerico < 1000) {
      toast.error('El monto mínimo es Gs. 1.000');
      return;
    }

    if (montoNumerico > 1000000) {
      toast.error('El monto máximo es Gs. 1.000.000');
      return;
    }

    setProcesando(true);

    try {
      await recargasService.procesarRecargaCaja({
        hijo_id: hijo.id_hijo,
        monto: montoNumerico,
        metodo_pago: metodoPago,
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

      // Limpiar formulario
      setMonto('');
      setReferencia('');
      
      // Notificar al padre
      onRecargaExitosa();

    } catch (error: any) {
      console.error('Error al procesar recarga:', error);
      toast.error(
        error.response?.data?.error || 'Error al procesar la recarga. Intenta nuevamente.'
      );
    } finally {
      setProcesando(false);
    }
  };

  const handleMontoRapido = (montoSeleccionado: number) => {
    setMonto(montoSeleccionado.toString());
  };

  const formatearMoneda = (valor: string): string => {
    const numero = parseFloat(valor);
    if (isNaN(numero)) return 'Gs. 0';
    return `Gs. ${numero.toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;
  };

  const calcularNuevoSaldo = (): number => {
    const montoNumerico = parseFloat(monto) || 0;
    return tarjeta.saldo_actual + montoNumerico;
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Saldo Actual */}
      <div className="rounded-lg bg-gradient-to-r from-amber-50 to-yellow-50 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">Saldo Actual</p>
            <p className="text-2xl font-bold text-amber-600">
              {formatearMoneda(tarjeta.saldo_actual.toString())}
            </p>
          </div>
          {monto && parseFloat(monto) > 0 && (
            <div className="text-right">
              <p className="text-sm text-gray-600">Nuevo Saldo</p>
              <p className="text-2xl font-bold text-green-600">
                {formatearMoneda(calcularNuevoSaldo().toString())}
              </p>
            </div>
          )}
        </div>
      </div>

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
                onClick={() => handleMontoRapido(montoRapido)}
                className={`rounded-lg border-2 px-3 py-2 text-sm font-medium transition-colors ${
                  monto === montoRapido.toString()
                    ? 'border-amber-500 bg-amber-50 text-amber-700'
                    : 'border-gray-200 bg-white text-gray-700 hover:border-amber-300 hover:bg-amber-50'
                }`}
              >
                {montoRapido >= 1000 ? `${montoRapido / 1000}k` : montoRapido}
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
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={() => setMetodoPago('efectivo')}
            className={`flex items-center justify-center gap-2 rounded-lg border-2 p-4 transition-colors ${
              metodoPago === 'efectivo'
                ? 'border-green-500 bg-green-50 text-green-700'
                : 'border-gray-200 bg-white text-gray-700 hover:border-green-300'
            }`}
          >
            <Banknote className="h-5 w-5" />
            <span className="font-medium">Efectivo</span>
          </button>

          <button
            type="button"
            onClick={() => setMetodoPago('tarjeta_pos')}
            className={`flex items-center justify-center gap-2 rounded-lg border-2 p-4 transition-colors ${
              metodoPago === 'tarjeta_pos'
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300'
            }`}
          >
            <CreditCard className="h-5 w-5" />
            <span className="font-medium">Tarjeta POS</span>
          </button>
        </div>
      </div>

      {/* Referencia/Comprobante (Opcional) */}
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
        <p className="mt-1 text-xs text-gray-500">
          Número de comprobante o referencia interna
        </p>
      </div>

      {/* Botones de Acción */}
      <div className="flex gap-3 border-t border-gray-200 pt-4">
        <Button
          type="submit"
          variant="primary"
          fullWidth
          disabled={procesando || !monto || parseFloat(monto) <= 0}
          leftIcon={procesando ? <Spinner size="sm" /> : <CheckCircle className="h-5 w-5" />}
        >
          {procesando ? 'Procesando...' : 'Procesar Recarga'}
        </Button>
      </div>

      {/* Resumen */}
      {monto && parseFloat(monto) > 0 && (
        <div className="rounded-lg border-2 border-dashed border-amber-300 bg-amber-50/30 p-4">
          <h4 className="mb-2 font-semibold text-gray-800">Resumen de la Operación</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Hijo:</span>
              <span className="font-medium text-gray-900">
                {hijo.nombre} {hijo.apellido}
              </span>
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
