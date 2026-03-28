/**
 * FacturaImpresa - Factura fisica timbrada (documento tributario formal).
 * Formato optimizado para impresora termica 80mm.
 * Requiere timbrado vigente configurado en el sistema.
 */
import React, { useEffect } from 'react';

interface IvaData {
  base_imponible_10: string;
  iva_10: string;
  base_imponible_5: string;
  iva_5: string;
  monto_exento: string;
  total: string;
}

interface FacturaData {
  tipo: string;
  es_nueva: boolean;
  empresa: {
    ruc?: string;
    razon_social?: string;
    direccion?: string;
    ciudad?: string;
    telefono?: string;
    email?: string;
  };
  factura: {
    nro_comprobante: string;
    nro_timbrado: number;
    timbrado_desde: string;
    timbrado_hasta: string;
    fecha_emision: string;
    alumno: string;
    concepto: string;
    cantidad_almuerzos: number;
    precio_unitario_promedio: string;
    iva: IvaData;
    estado_sifen: string;
    cdc: string | null;
    mes_nombre: string;
    anio: number;
    id_cuenta: number;
  };
}

interface Props {
  data: FacturaData;
  onClose?: () => void;
}

const formatGs = (val: string | number) =>
  `Gs. ${Math.round(Number(val)).toLocaleString('es-PY')}`;

const fmtDate = (iso: string) => {
  const [y, m, d] = iso.split('-');
  return `${d}/${m}/${y}`;
};

const FacturaImpresa: React.FC<Props> = ({ data, onClose }) => {
  const { empresa, factura } = data;

  useEffect(() => {
    const t = setTimeout(() => window.print(), 600);
    return () => clearTimeout(t);
  }, []);

  const precioUnit = Number(factura.precio_unitario_promedio);
  const total = Number(factura.iva.total);

  return (
    <>
      <style>{`
        @page { size: 80mm auto; margin: 0; }
        @media print {
          html, body { margin: 0 !important; padding: 0 !important; background: #fff; }
          .ft-no-print { display: none !important; }
          .ft-ticket { box-shadow: none !important; }
        }
        .ft-ticket {
          font-family: 'Courier New', Courier, monospace;
          font-size: 11px;
          width: 72mm;
          max-width: 72mm;
          margin: 0 auto;
          padding: 4mm 2mm;
          background: #fff;
          color: #000;
          line-height: 1.5;
        }
        .ft-center { text-align: center; }
        .ft-bold { font-weight: bold; }
        .ft-big { font-size: 15px; font-weight: bold; letter-spacing: 1px; }
        .ft-sep { border: none; border-top: 1px dashed #000; margin: 5px 0; }
        .ft-sep-s { border: none; border-top: 2px solid #000; margin: 5px 0; }
        .ft-row { display: flex; justify-content: space-between; margin: 2px 0; }
        .ft-sec { font-size: 9px; color: #555; margin-top: 4px; }
        .ft-item-sub { display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; }
        .ft-iva-t { font-size: 9px; text-align: center; font-weight: bold; margin: 4px 0 2px; }
        .ft-iva-r { display: flex; justify-content: space-between; font-size: 10px; margin: 1px 0; }
        .ft-total { display: flex; justify-content: space-between; font-size: 14px; font-weight: bold; margin: 4px 0; }
        .ft-firma-row { display: flex; justify-content: space-between; margin-top: 10mm; gap: 4mm; }
        .ft-firma { flex: 1; text-align: center; font-size: 9px; border-top: 1px solid #000; padding-top: 2px; }
        .ft-foot { text-align: center; font-size: 8px; color: #555; margin-top: 6px; }
        .ft-cdc { font-size: 8px; word-break: break-all; text-align: center; color: #555; margin-top: 4px; }
        .ft-screen {
          min-height: 100vh; background: #e5e7eb;
          display: flex; flex-direction: column; align-items: center; padding: 16px;
        }
        .ft-actions { display: flex; gap: 8px; margin-bottom: 12px; }
        .ft-btn { padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 14px; border: 1px solid #999; background: #fff; }
        .ft-btn-ok { background: #d1fae5; color: #065f46; border-color: #6ee7b7; }
        .ft-btn-p { background: #d97706; color: white; border-color: #b45309; font-weight: bold; }
        .ft-shadow { box-shadow: 0 4px 16px rgba(0,0,0,.15); border-radius: 4px; }
      `}</style>

      <div className="ft-screen ft-no-print">
        <div className="ft-actions">
          {data.es_nueva && <span className="ft-btn ft-btn-ok">Factura generada</span>}
          <button className="ft-btn" onClick={onClose}>Cerrar</button>
          <button className="ft-btn ft-btn-p" onClick={() => window.print()}>Imprimir</button>
        </div>
      </div>

      <div className="ft-ticket ft-shadow">

        <div className="ft-center">
          <div className="ft-big">{(empresa.razon_social || 'CANTINA TITA').toUpperCase()}</div>
          {empresa.ruc && <div>RUC: {empresa.ruc}</div>}
          {empresa.direccion && <div>{empresa.direccion}</div>}
          {empresa.ciudad && <div>{empresa.ciudad}</div>}
          {empresa.telefono && <div>Tel: {empresa.telefono}</div>}
        </div>

        <hr className="ft-sep-s" />

        <div className="ft-center ft-bold" style={{ fontSize: 14, letterSpacing: 2 }}>FACTURA</div>
        <div className="ft-center" style={{ fontSize: 9 }}>Documento Tributario - Contado - PYG</div>

        <hr className="ft-sep" />

        <div className="ft-center ft-bold" style={{ fontSize: 10 }}>Timbrado N. {factura.nro_timbrado}</div>
        <div className="ft-center" style={{ fontSize: 9 }}>
          Vig: {fmtDate(factura.timbrado_desde)} al {fmtDate(factura.timbrado_hasta)}
        </div>

        <hr className="ft-sep" />

        <div className="ft-row">
          <span className="ft-bold">{factura.nro_comprobante}</span>
          <span>{factura.fecha_emision}</span>
        </div>

        <hr className="ft-sep" />

        <div className="ft-sec">CLIENTE</div>
        <div className="ft-bold">{factura.alumno}</div>
        <div className="ft-row"><span>RUC/CI:</span><span>SIN RUC</span></div>

        <hr className="ft-sep" />

        <div className="ft-sec">DETALLE</div>
        <div style={{ fontSize: 10 }}>{factura.concepto}</div>
        <div className="ft-row" style={{ fontSize: 10 }}>
          <span>{factura.cantidad_almuerzos} u. x {formatGs(precioUnit)}</span>
        </div>
        <div className="ft-item-sub">
          <span>SUBTOTAL</span>
          <span>{formatGs(total)}</span>
        </div>

        <hr className="ft-sep-s" />

        <div className="ft-iva-t">LIQUIDACION DE IVA (incluido)</div>
        <div className="ft-iva-r">
          <span>Exento:</span><span>{formatGs(factura.iva.monto_exento)}</span>
        </div>
        {Number(factura.iva.base_imponible_5) > 0 && (
          <>
            <div className="ft-iva-r"><span>Base 5%:</span><span>{formatGs(factura.iva.base_imponible_5)}</span></div>
            <div className="ft-iva-r"><span>IVA 5%:</span><span>{formatGs(factura.iva.iva_5)}</span></div>
          </>
        )}
        {Number(factura.iva.base_imponible_10) > 0 && (
          <>
            <div className="ft-iva-r"><span>Base 10%:</span><span>{formatGs(factura.iva.base_imponible_10)}</span></div>
            <div className="ft-iva-r"><span>IVA 10%:</span><span>{formatGs(factura.iva.iva_10)}</span></div>
          </>
        )}

        <hr className="ft-sep" />

        <div className="ft-total">
          <span>TOTAL</span>
          <span>{formatGs(total)}</span>
        </div>

        <hr className="ft-sep-s" />

        <div className="ft-firma-row">
          <div className="ft-firma">Firma vendedor</div>
          <div className="ft-firma">Firma comprador</div>
        </div>

        {factura.cdc && <div className="ft-cdc">CDC: {factura.cdc}</div>}
        {factura.estado_sifen === 'pendiente_envio' && (
          <div className="ft-center" style={{ fontSize: 8, color: '#b45309', marginTop: 4 }}>
            Envio SIFEN pendiente
          </div>
        )}

        <div className="ft-foot">
          --------------------------------<br />
          Ley N. 6657/20 - SET Paraguay<br />
          ================================<br />
          Sistema Cantina Tita<br />
          {new Date().toLocaleString('es-PY')}
        </div>
      </div>
    </>
  );
};

export default FacturaImpresa;
