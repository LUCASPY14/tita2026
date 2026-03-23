/**
 * ReciboCobro — Comprobante interno de pago.
 * Formato optimizado para impresora térmica 80mm.
 * NO es un documento tributario (no lleva timbrado ni IVA).
 */
import React, { useEffect } from 'react';

export interface ReciboData {
  tipo: string;
  empresa: {
    ruc?: string;
    razon_social?: string;
    direccion?: string;
    ciudad?: string;
    telefono?: string;
    email?: string;
  };
  recibo: {
    nro_interno: string;
    fecha_emision: string;
    alumno: string;
    concepto: string;
    cantidad_almuerzos: number;
    monto_total: string;
    monto_cobrado: string;
    saldo_pendiente: string;
    forma_pago: string;
    comprobante_ref: string;
    estado: string;
    mes_nombre: string;
    anio: number;
  };
}

interface Props {
  data: ReciboData;
  onClose?: () => void;
  autoImprimir?: boolean;
}

const FORMAS_PAGO: Record<string, string> = {
  efectivo: 'Efectivo',
  transferencia: 'Transferencia',
  online: 'Pago online',
  debito_automatico: 'Debito automatico',
  tarjeta_hijo: 'Tarjeta estudiante',
  pos: 'POS (tarjeta)',
};

const formatGs = (val: string | number) =>
  `Gs. ${Math.round(Number(val)).toLocaleString('es-PY')}`;

/** Convierte un entero a texto en español para Guaraníes. */
const numALetras = (n: number): string => {
  // Guaraníes no tienen decimales — redondear antes de convertir
  n = Math.round(n);
  const unidades = ['', 'UN', 'DOS', 'TRES', 'CUATRO', 'CINCO', 'SEIS', 'SIETE', 'OCHO', 'NUEVE',
    'DIEZ', 'ONCE', 'DOCE', 'TRECE', 'CATORCE', 'QUINCE', 'DIECISEIS', 'DIECISIETE', 'DIECIOCHO', 'DIECINUEVE'];
  const decenas = ['', '', 'VEINTE', 'TREINTA', 'CUARENTA', 'CINCUENTA', 'SESENTA', 'SETENTA', 'OCHENTA', 'NOVENTA'];
  const centenas = ['', 'CIEN', 'DOSCIENTOS', 'TRESCIENTOS', 'CUATROCIENTOS', 'QUINIENTOS',
    'SEISCIENTOS', 'SETECIENTOS', 'OCHOCIENTOS', 'NOVECIENTOS'];
  if (n === 0) return 'CERO';
  if (n < 0) return 'MENOS ' + numALetras(-n);
  if (n < 20) return unidades[n];
  if (n < 100) return decenas[Math.floor(n / 10)] + (n % 10 ? ' Y ' + unidades[n % 10] : '');
  if (n < 1000) {
    const c = Math.floor(n / 100);
    const resto = n % 100;
    return (c === 1 && resto > 0 ? 'CIENTO' : centenas[c]) + (resto ? ' ' + numALetras(resto) : '');
  }
  if (n < 1000000) {
    const miles = Math.floor(n / 1000);
    const resto = n % 1000;
    return (miles === 1 ? 'MIL' : numALetras(miles) + ' MIL') + (resto ? ' ' + numALetras(resto) : '');
  }
  if (n < 1000000000) {
    const mill = Math.floor(n / 1000000);
    const resto = n % 1000000;
    return (mill === 1 ? 'UN MILLON' : numALetras(mill) + ' MILLONES') + (resto ? ' ' + numALetras(resto) : '');
  }
  return n.toLocaleString('es-PY');
};

const SEP = '--------------------------------';

const ReciboCobro: React.FC<Props> = ({ data, onClose, autoImprimir = true }) => {
  const { empresa, recibo } = data;

  useEffect(() => {
    if (!autoImprimir) return;
    const t = setTimeout(() => window.print(), 600);
    return () => clearTimeout(t);
  }, [autoImprimir]);

  const montoCobrado = Number(recibo.monto_cobrado);
  const saldo = Number(recibo.saldo_pendiente);
  const fecha = new Date(recibo.fecha_emision + 'T00:00:00').toLocaleDateString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  });

  return (
    <>
      <style>{`
        @page {
          size: 80mm auto;
          margin: 0;
        }
        @media print {
          html, body { margin: 0 !important; padding: 0 !important; background: #fff; }
          .rc-no-print { display: none !important; }
          .rc-ticket { box-shadow: none !important; border: none !important; }
        }
        .rc-ticket {
          font-family: 'Courier New', Courier, monospace;
          font-size: 11px;
          width: 72mm;
          max-width: 72mm;
          margin: 0 auto;
          padding: 4mm 2mm;
          background: #fff;
          color: #000;
          line-height: 1.45;
        }
        .rc-center { text-align: center; }
        .rc-bold { font-weight: bold; }
        .rc-big { font-size: 15px; font-weight: bold; letter-spacing: 1px; }
        .rc-sep { border: none; border-top: 1px dashed #000; margin: 4px 0; }
        .rc-sep-solid { border: none; border-top: 1px solid #000; margin: 4px 0; }
        .rc-row { display: flex; justify-content: space-between; margin: 2px 0; }
        .rc-label { color: #333; white-space: nowrap; margin-right: 4px; flex-shrink: 0; }
        .rc-val { text-align: right; word-break: break-word; }
        .rc-monto { font-size: 18px; font-weight: bold; text-align: center; margin: 6px 0 2px; }
        .rc-letras { font-size: 9px; text-align: center; font-style: italic; word-break: break-word; }
        .rc-estado { display: inline-block; border: 1px solid #000; padding: 1px 6px; font-weight: bold; font-size: 10px; }
        .rc-saldo-ok { text-align: center; font-size: 10px; }
        .rc-saldo-pend { text-align: center; font-size: 10px; }
        .rc-firma-row { display: flex; justify-content: space-between; margin-top: 12mm; gap: 4mm; }
        .rc-firma { flex: 1; text-align: center; font-size: 9px; border-top: 1px solid #000; padding-top: 2px; }
        .rc-foot { text-align: center; font-size: 8px; color: #555; margin-top: 6px; }

        /* Vista previa en pantalla */
        .rc-screen-wrap {
          min-height: 100vh;
          background: #e5e7eb;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 16px;
        }
        .rc-actions {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
        }
        .rc-btn {
          padding: 8px 20px;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
          border: 1px solid #999;
          background: #fff;
        }
        .rc-btn-print {
          background: #d97706;
          color: white;
          border-color: #b45309;
          font-weight: bold;
        }
        .rc-shadow {
          box-shadow: 0 4px 16px rgba(0,0,0,0.15);
          border-radius: 4px;
        }
      `}</style>

      <div className="rc-screen-wrap rc-no-print">
        <div className="rc-actions">
          <button className="rc-btn" onClick={onClose}>✕ Cerrar</button>
          <button className="rc-btn rc-btn-print" onClick={() => window.print()}>🖨 Imprimir</button>
        </div>
      </div>

      {/* Ticket — visible tanto en pantalla como al imprimir */}
      <div className="rc-ticket rc-shadow">

        {/* ── Cabecera empresa ── */}
        <div className="rc-center">
          <div className="rc-big">{(empresa.razon_social || 'CANTINA TITA').toUpperCase()}</div>
          {empresa.ruc && <div>RUC: {empresa.ruc}</div>}
          {empresa.direccion && <div>{empresa.direccion}</div>}
          {empresa.ciudad && <div>{empresa.ciudad}</div>}
          {empresa.telefono && <div>Tel: {empresa.telefono}</div>}
        </div>

        <hr className="rc-sep-solid" />

        <div className="rc-center rc-bold" style={{ fontSize: 13, letterSpacing: 1 }}>
          RECIBO DE COBRO
        </div>
        <div className="rc-center" style={{ fontSize: 9 }}>Comprobante interno - No es doc. tributario</div>

        <hr className="rc-sep" />

        {/* ── Nro y fecha ── */}
        <div className="rc-row">
          <span className="rc-bold">N° {recibo.nro_interno}</span>
          <span>{fecha}</span>
        </div>

        <hr className="rc-sep" />

        {/* ── Datos ── */}
        <div style={{ marginBottom: 2 }}>
          <div style={{ fontSize: 9, color: '#555' }}>ALUMNO</div>
          <div className="rc-bold">{recibo.alumno}</div>
        </div>
        <div style={{ marginBottom: 2 }}>
          <div style={{ fontSize: 9, color: '#555' }}>CONCEPTO</div>
          <div>{recibo.concepto}</div>
        </div>
        {recibo.cantidad_almuerzos > 0 && (
          <div className="rc-row">
            <span className="rc-label">Almuerzos:</span>
            <span className="rc-val">{recibo.cantidad_almuerzos}</span>
          </div>
        )}
        <div className="rc-row">
          <span className="rc-label">Total facturado:</span>
          <span className="rc-val rc-bold">{formatGs(recibo.monto_total)}</span>
        </div>
        <div className="rc-row">
          <span className="rc-label">Forma de pago:</span>
          <span className="rc-val">{FORMAS_PAGO[recibo.forma_pago] || recibo.forma_pago || '—'}</span>
        </div>
        {recibo.comprobante_ref && (
          <div className="rc-row">
            <span className="rc-label">Ref:</span>
            <span className="rc-val" style={{ fontSize: 9 }}>{recibo.comprobante_ref}</span>
          </div>
        )}
        <div className="rc-row">
          <span className="rc-label">Estado:</span>
          <span className="rc-val"><span className="rc-estado">{recibo.estado.toUpperCase()}</span></span>
        </div>

        <hr className="rc-sep-solid" />

        {/* ── Monto cobrado ── */}
        <div className="rc-center" style={{ fontSize: 9 }}>MONTO COBRADO</div>
        <div className="rc-monto">{formatGs(montoCobrado)}</div>
        <div className="rc-letras">({numALetras(montoCobrado)} GUARANIES)</div>

        <hr className="rc-sep" />

        {saldo > 0 ? (
          <div className="rc-saldo-pend">
            ⚠ Saldo pendiente: {formatGs(saldo)}
          </div>
        ) : (
          <div className="rc-saldo-ok">✔ CUENTA SALDADA</div>
        )}

        {/* ── Firmas ── */}
        <div className="rc-firma-row">
          <div className="rc-firma">Firma autorizada</div>
          <div className="rc-firma">Firma receptor</div>
        </div>

        <div className="rc-foot">
          {SEP}<br />
          Sistema Cantina Tita<br />
          {new Date().toLocaleString('es-PY')}
        </div>
      </div>
    </>
  );
};

export default ReciboCobro;
