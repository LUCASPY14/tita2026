import React, { useEffect } from 'react';
import type { Hijo, Tarjeta, RegistroConsumoAlmuerzo, SuscripcionAlmuerzo } from '../../../types';

interface TicketAlmuerzoProps {
  registro: RegistroConsumoAlmuerzo;
  hijo: Hijo;
  tarjeta: Tarjeta;
  suscripcionActiva: SuscripcionAlmuerzo | null;
  tipoAlmuerzoNombre: string;
  onClose: () => void;
}

const TicketAlmuerzo: React.FC<TicketAlmuerzoProps> = ({
  registro,
  hijo,
  tarjeta,
  suscripcionActiva,
  tipoAlmuerzoNombre,
  onClose,
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      window.print();
      // Close after print dialog is dismissed
      window.onafterprint = () => {
        window.onafterprint = null;
        onClose();
      };
      // Fallback: close after 3 seconds if onafterprint doesn't fire
      const fallback = setTimeout(onClose, 3000);
      return () => clearTimeout(fallback);
    }, 150);
    return () => clearTimeout(timer);
  }, [onClose]);

  const formatearHora = (hora: string) => hora.substring(0, 5);
  const formatearFecha = (fecha: string) => {
    const [anio, mes, dia] = fecha.split('-');
    return `${dia}/${mes}/${anio}`;
  };
  const formatearMoneda = (valor: number) =>
    new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(valor);

  const esSegundoServicio = !registro.ya_cobrado;
  const planNombre = suscripcionActiva?.plan_nombre || tipoAlmuerzoNombre;

  return (
    <>
      {/* Print styles injected into head */}
      <style>{`
        @media print {
          body > *:not(#ticket-almuerzo-root) { display: none !important; }
          #ticket-almuerzo-root { display: block !important; }
          .ticket-overlay { display: none !important; }
          .ticket-card {
            box-shadow: none !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
          }
        }
      `}</style>

      {/* Screen overlay */}
      <div className="ticket-overlay fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div
          id="ticket-almuerzo-root"
          className="ticket-card mx-auto w-72 rounded-lg bg-white p-5 text-center shadow-2xl"
          style={{ fontFamily: 'monospace' }}
        >
          {/* Header */}
          <div className="border-b border-dashed border-gray-400 pb-3">
            <p className="text-lg font-bold tracking-widest text-gray-900">CANTINA TITA</p>
            <p className="text-xs text-gray-500">Ticket de Almuerzo</p>
          </div>

          {/* Date / Time */}
          <div className="border-b border-dashed border-gray-400 py-3 text-xs text-gray-700">
            <p>
              <span className="font-semibold">Fecha:</span>{' '}
              {formatearFecha(registro.fecha_consumo)}
            </p>
            <p>
              <span className="font-semibold">Hora:</span>{' '}
              {formatearHora(registro.hora_registro)}
            </p>
          </div>

          {/* Student info */}
          <div className="border-b border-dashed border-gray-400 py-3 text-left text-xs text-gray-700">
            <p className="mb-1 text-sm font-bold text-gray-900">
              {hijo.nombre} {hijo.apellido}
            </p>
            {hijo.grado && (
              <p>
                <span className="font-semibold">Curso:</span> {hijo.grado}
              </p>
            )}
            <p>
              <span className="font-semibold">Tarjeta:</span> {tarjeta.nro_tarjeta}
            </p>
          </div>

          {/* Service info */}
          <div className="border-b border-dashed border-gray-400 py-3 text-xs text-gray-700">
            <p className="mb-1 font-semibold text-gray-800">{planNombre}</p>
            <p
              className={`text-sm font-bold ${esSegundoServicio ? 'text-orange-600' : 'text-green-700'}`}
            >
              {esSegundoServicio ? '2do Servicio' : '1er Servicio'}
            </p>
          </div>

          {/* Cost */}
          <div className="border-b border-dashed border-gray-400 py-3 text-xs">
            {esSegundoServicio ? (
              <p className="text-sm font-bold text-orange-600">SIN COSTO</p>
            ) : suscripcionActiva ? (
              <p className="text-sm font-bold text-purple-700">PLAN MENSUAL</p>
            ) : (
              <p className="text-sm font-bold text-gray-900">
                {formatearMoneda(registro.costo_almuerzo || 0)}
              </p>
            )}
          </div>

          {/* Footer */}
          <div className="pt-3 text-xs text-gray-400">
            <p>#{registro.id_registro_consumo}</p>
            <p>Buen provecho!</p>
          </div>
        </div>

        {/* Screen-only close button */}
        <div className="ticket-overlay absolute bottom-8 flex gap-4">
          <button
            onClick={() => { window.print(); }}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-blue-700"
          >
            Reimprimir
          </button>
          <button
            onClick={onClose}
            className="rounded-lg bg-gray-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-gray-700"
          >
            Cerrar
          </button>
        </div>
      </div>
    </>
  );
};

export default TicketAlmuerzo;
