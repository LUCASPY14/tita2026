import React, { useState, useEffect } from 'react';
import {
  User,
  Phone,
  Mail,
  MapPin,
  CreditCard,
  DollarSign,
  TrendingUp,
  Edit,
  Calendar,
} from 'lucide-react';
import { Card, Button, Badge, Spinner } from '../../../components/common';
import { clientesService } from '../../../services/clientes.service';
import type { Cliente, CuentaCorriente } from '../../../types';

interface DetalleClienteProps {
  cliente: Cliente;
  onEditar: (cliente: Cliente) => void;
}

const DetalleCliente: React.FC<DetalleClienteProps> = ({ cliente, onEditar }) => {
  const [cuentaCorriente, setCuentaCorriente] = useState<CuentaCorriente | null>(null);
  const [cargandoCuenta, setCargandoCuenta] = useState(false);

  useEffect(() => {
    cargarCuentaCorriente();
  }, [cliente.id_cliente]);

  const cargarCuentaCorriente = async () => {
    setCargandoCuenta(true);
    try {
      const cuenta = await clientesService.getCuentaCorriente(cliente.id_cliente);
      setCuentaCorriente(cuenta);
    } catch (error) {
      console.error('Error al cargar cuenta corriente:', error);
    } finally {
      setCargandoCuenta(false);
    }
  };

  const formatearMoneda = (monto: number): string => {
    return `Gs. ${monto.toLocaleString('es-PY')}`;
  };

  const formatearFecha = (fecha: string): string => {
    return new Date(fecha).toLocaleDateString('es-PY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header con Datos Principales */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card className="md:col-span-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
                <User className="h-8 w-8 text-amber-600" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {cliente.nombres} {cliente.apellidos}
                </h2>
                {cliente.razon_social && (
                  <p className="text-sm text-gray-500">{cliente.razon_social}</p>
                )}
                <div className="mt-1 flex items-center gap-2">
                  <Badge variant={cliente.activo ? 'success' : 'danger'}>
                    {cliente.activo ? 'Activo' : 'Inactivo'}
                  </Badge>
                  <span className="text-sm text-gray-500">
                    RUC/CI: {cliente.ruc_ci}
                  </span>
                </div>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={() => onEditar(cliente)}
              leftIcon={<Edit className="h-4 w-4" />}
            >
              Editar
            </Button>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 border-t pt-6 md:grid-cols-2">
            {/* Información de Contacto */}
            {cliente.telefono && (
              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Teléfono</p>
                  <p className="font-medium text-gray-900">{cliente.telefono}</p>
                </div>
              </div>
            )}

            {cliente.email && (
              <div className="flex items-center gap-3">
                <Mail className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Email</p>
                  <p className="font-medium text-gray-900">{cliente.email}</p>
                </div>
              </div>
            )}

            {cliente.direccion && (
              <div className="flex items-center gap-3">
                <MapPin className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-xs text-gray-500">Dirección</p>
                  <p className="font-medium text-gray-900">
                    {cliente.direccion}
                    {cliente.ciudad && `, ${cliente.ciudad}`}
                  </p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-3">
              <Calendar className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Cliente desde</p>
                <p className="font-medium text-gray-900">
                  {formatearFecha(cliente.fecha_registro)}
                </p>
              </div>
            </div>
          </div>
        </Card>

        {/* Resumen de Crédito */}
        <Card>
          <div className="flex items-center gap-3">
            <CreditCard className="h-6 w-6 text-amber-600" />
            <h3 className="text-lg font-semibold text-gray-900">Límite de Crédito</h3>
          </div>
          <div className="mt-4 space-y-3">
            <div>
              <p className="text-sm text-gray-500">Límite Total</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatearMoneda(cliente.limite_credito || 0)}
              </p>
            </div>
            {cliente.credito_disponible !== undefined && (
              <>
                <div>
                  <p className="text-sm text-gray-500">Disponible</p>
                  <p className="text-xl font-semibold text-green-600">
                    {formatearMoneda(cliente.credito_disponible)}
                  </p>
                </div>
                {cliente.credito_utilizado !== undefined && (
                  <div>
                    <p className="text-sm text-gray-500">Utilizado</p>
                    <p className="text-xl font-semibold text-orange-600">
                      {formatearMoneda(cliente.credito_utilizado)}
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </Card>
      </div>

      {/* Cuenta Corriente Detallada */}
      <Card>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <DollarSign className="h-6 w-6 text-amber-600" />
            <h3 className="text-lg font-semibold text-gray-900">Cuenta Corriente</h3>
          </div>
          <Button
            variant="outline"
            onClick={cargarCuentaCorriente}
            disabled={cargandoCuenta}
          >
            {cargandoCuenta ? 'Actualizando...' : 'Actualizar'}
          </Button>
        </div>

        {cargandoCuenta ? (
          <div className="flex items-center justify-center py-8">
            <Spinner />
            <span className="ml-2 text-gray-600">Cargando cuenta corriente...</span>
          </div>
        ) : cuentaCorriente ? (
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-4">
            <div className="rounded-lg bg-red-50 p-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-red-600" />
                <p className="text-sm font-medium text-red-600">Debe</p>
              </div>
              <p className="mt-2 text-xl font-bold text-red-900">
                {formatearMoneda(cuentaCorriente.total_debe)}
              </p>
              <p className="mt-1 text-xs text-red-600">
                {cuentaCorriente.cantidad_facturas_pendientes} facturas pendientes
              </p>
            </div>

            <div className="rounded-lg bg-green-50 p-4">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600 rotate-180" />
                <p className="text-sm font-medium text-green-600">Haber</p>
              </div>
              <p className="mt-2 text-xl font-bold text-green-900">
                {formatearMoneda(cuentaCorriente.total_haber)}
              </p>
              <p className="mt-1 text-xs text-green-600">
                {cuentaCorriente.cantidad_notas_credito} notas de crédito
              </p>
            </div>

            <div className="rounded-lg bg-blue-50 p-4">
              <div className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-blue-600" />
                <p className="text-sm font-medium text-blue-600">Saldo Neto</p>
              </div>
              <p className="mt-2 text-xl font-bold text-blue-900">
                {formatearMoneda(cuentaCorriente.saldo_neto)}
              </p>
            </div>

            <div className="rounded-lg bg-amber-50 p-4">
              <div className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-amber-600" />
                <p className="text-sm font-medium text-amber-600">Uso de Crédito</p>
              </div>
              <p className="mt-2 text-xl font-bold text-amber-900">
                {cuentaCorriente.porcentaje_usado.toFixed(1)}%
              </p>
              <div className="mt-2 h-2 w-full rounded-full bg-amber-200">
                <div
                  className="h-2 rounded-full bg-amber-600"
                  style={{ width: `${Math.min(cuentaCorriente.porcentaje_usado, 100)}%` }}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="py-8 text-center">
            <p className="text-gray-500">No se pudo cargar la cuenta corriente</p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default DetalleCliente;
