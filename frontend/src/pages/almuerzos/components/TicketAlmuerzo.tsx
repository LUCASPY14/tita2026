import React, { useEffect, useCallback } from 'react';
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

  const buildTicketHTML = useCallback(() => {
    const colorServicio = esSegundoServicio ? '#ea580c' : '#15803d';
    const costoHTML = esSegundoServicio
      ? `<p style="font-size:14px;font-weight:bold;color:#ea580c;">SIN COSTO</p>`
      : suscripcionActiva
      ? `<p style="font-size:14px;font-weight:bold;color:#7c3aed;">PLAN MENSUAL</p>`
      : `<p style="font-size:14px;font-weight:bold;color:#111;">${formatearMoneda(registro.costo_almuerzo || 0)}</p>`;

    return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Ticket Almuerzo</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: monospace; width: 280px; padding: 10px; }
    .hr { border: none; border-top: 1px dashed #888; margin: 8px 0; }
    .center { text-align: center; }
    .left   { text-align: left; }
    .bold   { font-weight: bold; }
    .sm     { font-size: 11px; color: #555; }
    .xs     { font-size: 10px; color: #aaa; }
    .title  { font-size: 16px; font-weight: bold; letter-spacing: 2px; }
    .name   { font-size: 14px; font-weight: bold; color: #111; margin-bottom: 3px; }
    .row    { font-size: 12px; color: #444; margin-bottom: 2px; }
    .servicio { font-size: 14px; font-weight: bold; color: ${colorServicio}; }
    @media print {
      @page { margin: 0; size: 80mm auto; }
      body  { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="center" style="padding-bottom:8px;">
    <p class="title">CANTINA TITA</p>
    <p class="sm">Ticket de Almuerzo</p>
  </div>
  <hr class="hr" />
  <div class="left" style="margin-bottom:4px;">
    <p class="row"><span class="bold">Fecha:</span> ${formatearFecha(registro.fecha_consumo)}</p>
    <p class="row"><span class="bold">Hora:</span>  ${formatearHora(registro.hora_registro)}</p>
  </div>
  <hr class="hr" />
  <div class="left" style="margin-bottom:4px;">
    <p class="name">${hijo.nombre} ${hijo.apellido}</p>
    ${hijo.grado ? `<p class="row"><span class="bold">Curso:</span> ${hijo.grado}</p>` : ''}
    <p class="row"><span class="bold">Tarjeta:</span> ${tarjeta.nro_tarjeta}</p>
  </div>
  <hr class="hr" />
  <div class="center" style="margin-bottom:4px;">
    <p class="row bold">${planNombre}</p>
    <p class="servicio">${esSegundoServicio ? '2do Servicio' : '1er Servicio'}</p>
  </div>
  <hr class="hr" />
  <div class="center" style="margin-bottom:4px;">
    ${costoHTML}
  </div>
  <hr class="hr" />
  <div class="center xs">
    <p>#${registro.id_registro_consumo}</p>
    <p>Buen provecho!</p>
  </div>
</body>
</html>`;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [registro, hijo, tarjeta, suscripcionActiva, planNombre, esSegundoServicio]);

  const imprimir = useCallback(() => {
    const pw = window.open('', '_blank', 'width=380,height=550,toolbar=0,menubar=0,location=0,scrollbars=0');
    if (!pw) return;
    pw.document.write(buildTicketHTML());
    pw.document.close();
    pw.focus();
    // Small delay so the browser renders the HTML before showing the print dialog
    setTimeout(() => {
      pw.print();
      // onafterprint fires when the print dialog is dismissed (whether printed or cancelled)
      pw.onafterprint = () => {
        pw.close();
        onClose(); // auto-clear the form for the next student
      };
    }, 300);
  }, [buildTicketHTML, onClose]);

  // Auto-print on mount
  useEffect(() => {
    const t = setTimeout(imprimir, 100);
    return () => clearTimeout(t);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Screen overlay (visual confirmation for the operator) ──────────────────
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        className="mx-auto w-72 rounded-lg bg-white p-5 text-center shadow-2xl"
        style={{ fontFamily: 'monospace' }}
      >
        {/* Header */}
        <div className="border-b border-dashed border-gray-400 pb-3">
          <p className="text-lg font-bold tracking-widest text-gray-900">CANTINA TITA</p>
          <p className="text-xs text-gray-500">Ticket de Almuerzo</p>
        </div>

        {/* Date / Time */}
        <div className="border-b border-dashed border-gray-400 py-3 text-xs text-gray-700">
          <p><span className="font-semibold">Fecha:</span> {formatearFecha(registro.fecha_consumo)}</p>
          <p><span className="font-semibold">Hora:</span>  {formatearHora(registro.hora_registro)}</p>
        </div>

        {/* Student info */}
        <div className="border-b border-dashed border-gray-400 py-3 text-left text-xs text-gray-700">
          <p className="mb-1 text-sm font-bold text-gray-900">
            {hijo.nombre} {hijo.apellido}
          </p>
          {hijo.grado && <p><span className="font-semibold">Curso:</span> {hijo.grado}</p>}
          <p><span className="font-semibold">Tarjeta:</span> {tarjeta.nro_tarjeta}</p>
        </div>

        {/* Service info */}
        <div className="border-b border-dashed border-gray-400 py-3 text-xs text-gray-700">
          <p className="mb-1 font-semibold text-gray-800">{planNombre}</p>
          <p className={`text-sm font-bold ${esSegundoServicio ? 'text-orange-600' : 'text-green-700'}`}>
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

      {/* Action buttons */}
      <div className="absolute bottom-8 flex gap-4">
        <button
          onClick={imprimir}
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
  );
};

export default TicketAlmuerzo;
