import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePortalAuth } from '../../contexts/PortalAuthContext';
import { portalAuthService, DashboardData } from '../../services/portalAuth.service';
import toast from 'react-hot-toast';

const formatGs = (val: string | number) =>
  `Gs. ${Number(val).toLocaleString('es-PY')}`;

const formatFecha = (iso: string) =>
  new Date(iso).toLocaleString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });

const DashboardPortal: React.FC = () => {
  const { user, logout } = usePortalAuth();
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [hijoExpandido, setHijoExpandido] = useState<number | null>(null);

  useEffect(() => {
    portalAuthService
      .getDashboard()
      .then(setData)
      .catch(() => toast.error('Error cargando datos'))
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/portal/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-orange-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-orange-400 border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🍽️</span>
            <div>
              <h1 className="font-bold text-gray-900">Portal de Clientes</h1>
              <p className="text-xs text-gray-500">Cantina Tita</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-700 hidden sm:block">
              {user?.nombre_completo}
            </span>
            <button
              onClick={handleLogout}
              className="text-sm text-gray-500 hover:text-red-600 transition-colors"
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
        {/* Resumen del cliente */}
        {data && (
          <div className="bg-white rounded-xl shadow-sm p-5">
            <h2 className="font-semibold text-gray-900 mb-4">Resumen de cuenta</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-center">
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">Hijos registrados</p>
                <p className="text-2xl font-bold text-blue-700">{data.hijos.length}</p>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">Crédito disponible</p>
                <p className="text-lg font-bold text-green-700">
                  {formatGs(data.cliente.credito_disponible)}
                </p>
              </div>
              <div className="bg-orange-50 rounded-lg p-3 col-span-2 sm:col-span-1">
                <p className="text-xs text-gray-500">Límite de crédito</p>
                <p className="text-lg font-bold text-orange-700">
                  {formatGs(data.cliente.limite_credito)}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Cuenta Corriente - Información de Deuda */}
        {data && data.cuenta_corriente && (
          <div className="bg-white rounded-xl shadow-sm p-5">
            <h2 className="font-semibold text-gray-900 mb-4">Estado de Cuenta</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div className={`rounded-lg p-4 ${
                Number(data.cuenta_corriente.total_deuda) > 0 
                  ? 'bg-red-50 border-2 border-red-200' 
                  : 'bg-green-50 border-2 border-green-200'
              }`}>
                <p className="text-xs text-gray-600 mb-1">Saldo Pendiente</p>
                <p className={`text-2xl font-bold ${
                  Number(data.cuenta_corriente.total_deuda) > 0 
                    ? 'text-red-700' 
                    : 'text-green-700'
                }`}>
                  {formatGs(data.cuenta_corriente.total_deuda)}
                </p>
                {Number(data.cuenta_corriente.total_deuda) > 0 && (
                  <p className="text-xs text-red-600 mt-1">⚠ Requiere atención</p>
                )}
              </div>
              <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
                <p className="text-xs text-gray-600 mb-1">Facturas Pendientes</p>
                <p className="text-2xl font-bold text-blue-700">
                  {data.cuenta_corriente.cantidad_facturas_pendientes}
                </p>
                {data.cuenta_corriente.cantidad_facturas_pendientes > 0 && (
                  <p className="text-xs text-blue-600 mt-1">
                    {data.cuenta_corriente.cantidad_facturas_pendientes === 1 
                      ? 'factura' 
                      : 'facturas'} por pagar
                  </p>
                )}
              </div>
            </div>

            {/* Facturas Recientes */}
            {data.cuenta_corriente.facturas_recientes.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Facturas Pendientes Recientes
                </h3>
                <div className="divide-y border rounded-lg">
                  {data.cuenta_corriente.facturas_recientes.map((factura) => (
                    <div 
                      key={factura.id_venta}
                      className="flex items-center justify-between px-4 py-3 hover:bg-gray-50"
                    >
                      <div>
                        <p className="font-semibold text-gray-900">
                          {factura.nro_factura_venta}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(factura.fecha).toLocaleDateString('es-PY')}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">
                          Total: {formatGs(factura.total_venta)}
                        </p>
                        <p className="text-sm font-bold text-red-600">
                          Pendiente: {formatGs(factura.saldo_pendiente)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
                {data.cuenta_corriente.cantidad_facturas_pendientes > data.cuenta_corriente.facturas_recientes.length && (
                  <p className="text-xs text-gray-500 text-center mt-2">
                    Mostrando las {data.cuenta_corriente.facturas_recientes.length} más recientes de {data.cuenta_corriente.cantidad_facturas_pendientes} facturas pendientes
                  </p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Hijos y tarjetas */}
        <h2 className="font-semibold text-gray-900 text-lg">Estudiantes y saldos</h2>

        {!data || data.hijos.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-8 text-center text-gray-500">
            No hay estudiantes registrados para esta cuenta.
          </div>
        ) : (
          data.hijos.map((hijo) => (
            <div key={hijo.id_hijo} className="bg-white rounded-xl shadow-sm overflow-hidden">
              {/* Header del hijo */}
              <div className="flex items-center justify-between px-5 py-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center font-bold text-orange-600">
                    {hijo.nombre[0]}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{hijo.nombre_completo}</p>
                    <p className="text-xs text-gray-500">{hijo.grado || 'Sin grado'}</p>
                  </div>
                </div>
                <div className="text-right">
                  {hijo.tarjeta ? (
                    <>
                      <p className="text-xs text-gray-500">Saldo</p>
                      <p
                        className={`font-bold text-lg ${
                          hijo.tarjeta.esta_en_alerta ? 'text-red-600' : 'text-green-600'
                        }`}
                      >
                        {formatGs(hijo.tarjeta.saldo_actual)}
                      </p>
                      {hijo.tarjeta.esta_en_alerta && (
                        <p className="text-xs text-red-500">⚠ Saldo bajo</p>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-gray-400">Sin tarjeta</p>
                  )}
                </div>
              </div>

              {/* Movimientos */}
              {hijo.tarjeta && hijo.tarjeta.ultimos_consumos.length > 0 && (
                <>
                  <button
                    onClick={() =>
                      setHijoExpandido(hijoExpandido === hijo.id_hijo ? null : hijo.id_hijo)
                    }
                    className="w-full text-left px-5 py-2 bg-gray-50 text-xs text-blue-600 hover:bg-gray-100 transition-colors border-t"
                  >
                    {hijoExpandido === hijo.id_hijo
                      ? '▲ Ocultar movimientos'
                      : `▼ Ver últimos ${hijo.tarjeta.ultimos_consumos.length} movimientos`}
                  </button>

                  {hijoExpandido === hijo.id_hijo && (
                    <div className="divide-y">
                      {hijo.tarjeta.ultimos_consumos.map((c) => {
                        const esConsumo = Number(c.monto_consumido) > 0;
                        return (
                          <div
                            key={c.id_consumo}
                            className="flex items-center justify-between px-5 py-3 text-sm"
                          >
                            <div>
                              <p className="text-gray-700">{c.detalle || 'Consumo'}</p>
                              <p className="text-xs text-gray-400">{formatFecha(c.fecha_consumo)}</p>
                            </div>
                            <div className="text-right">
                              <p
                                className={`font-semibold ${
                                  esConsumo ? 'text-red-600' : 'text-green-600'
                                }`}
                              >
                                {esConsumo ? '−' : '+'}{formatGs(Math.abs(Number(c.monto_consumido)))}
                              </p>
                              <p className="text-xs text-gray-400">
                                Saldo: {formatGs(c.saldo_posterior)}
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
          ))
        )}
      </main>
    </div>
  );
};

export default DashboardPortal;
