import React, { useRef } from 'react';
import { X, Printer, CheckCircle } from 'lucide-react';

interface ItemRecibo {
  descripcion: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

interface ReciboVentaProps {
  nroFactura?: number;
  fecha: string;
  items: ItemRecibo[];
  total: number;
  descuento?: number;
  metodoPago: string;
  comprobante?: string;
  clienteNombre?: string;
  tarjetaNro?: string;
  onCerrar: () => void;
}

const METODO_LABELS: Record<string, string> = {
  efectivo: 'Efectivo',
  tarjeta_hijo: 'Tarjeta Estudiante',
  pos: 'POS (Tarjeta débito/crédito)',
};

const ReciboVenta: React.FC<ReciboVentaProps> = ({
  nroFactura,
  fecha,
  items,
  total,
  descuento,
  metodoPago,
  comprobante,
  clienteNombre,
  tarjetaNro,
  onCerrar,
}) => {
  const reciboRef = useRef<HTMLDivElement>(null);

  const formatearPrecio = (valor: number) =>
    `Gs. ${valor.toLocaleString('es-PY')}`;

  const formatearFecha = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString('es-PY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleImprimir = () => {
    const contenido = reciboRef.current?.innerHTML;
    if (!contenido) return;
    const ventana = window.open('', '_blank', 'width=400,height=600');
    if (!ventana) return;
    ventana.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8"/>
          <title>Recibo #${nroFactura ?? '—'}</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Courier New', monospace; font-size: 12px; color: #000; padding: 16px; width: 300px; }
            .centro { text-align: center; }
            .negrita { font-weight: bold; }
            .grande { font-size: 16px; }
            .separador { border-top: 1px dashed #000; margin: 8px 0; }
            .fila { display: flex; justify-content: space-between; margin: 3px 0; }
            .total-fila { display: flex; justify-content: space-between; font-weight: bold; font-size: 14px; margin-top: 4px; }
            .pie { margin-top: 16px; text-align: center; font-size: 10px; color: #555; }
          </style>
        </head>
        <body onload="window.print(); window.close();">
          ${contenido}
        </body>
      </html>
    `);
    ventana.document.close();
  };

  const totalFinal = descuento ? total - descuento : total;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
      <div className="relative w-full max-w-sm rounded-xl bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <h2 className="text-lg font-bold text-gray-900">Venta Exitosa</h2>
          </div>
          <button onClick={onCerrar} className="rounded-lg p-1.5 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Recibo */}
        <div className="max-h-[60vh] overflow-y-auto px-5 py-4">
          <div ref={reciboRef}>
            {/* Cabecera recibo */}
            <div className="centro negrita grande">CANTINA TITA</div>
            <div className="centro" style={{ fontSize: '10px', marginTop: '2px' }}>
              Sistema de Gestión de Cantina Escolar
            </div>
            <div className="separador" />

            <div className="fila">
              <span>Fecha:</span>
              <span>{formatearFecha(fecha)}</span>
            </div>
            {nroFactura && (
              <div className="fila negrita">
                <span>Factura N°:</span>
                <span>{nroFactura}</span>
              </div>
            )}
            {clienteNombre && (
              <div className="fila">
                <span>Cliente:</span>
                <span>{clienteNombre}</span>
              </div>
            )}
            {tarjetaNro && (
              <div className="fila">
                <span>Tarjeta:</span>
                <span>{tarjetaNro}</span>
              </div>
            )}

            <div className="separador" />

            {/* Items */}
            <div className="negrita" style={{ marginBottom: '4px', fontSize: '11px' }}>
              DETALLE
            </div>
            {items.map((item, i) => (
              <div key={i} style={{ marginBottom: '4px' }}>
                <div style={{ fontSize: '11px' }}>{item.descripcion}</div>
                <div className="fila" style={{ fontSize: '11px', color: '#444' }}>
                  <span>
                    {item.cantidad} × {formatearPrecio(item.precio_unitario)}
                  </span>
                  <span>{formatearPrecio(item.subtotal)}</span>
                </div>
              </div>
            ))}

            <div className="separador" />

            {descuento && descuento > 0 && (
              <div className="fila" style={{ color: '#16a34a' }}>
                <span>Descuento (promo):</span>
                <span>- {formatearPrecio(descuento)}</span>
              </div>
            )}

            <div className="total-fila">
              <span>TOTAL:</span>
              <span>{formatearPrecio(totalFinal)}</span>
            </div>

            <div className="separador" />

            <div className="fila">
              <span>Método de pago:</span>
              <span>{METODO_LABELS[metodoPago] ?? metodoPago}</span>
            </div>
            {comprobante && (
              <div className="fila">
                <span>Comprobante:</span>
                <span>{comprobante}</span>
              </div>
            )}

            <div className="pie">
              ¡Gracias por su compra! • Conserve su comprobante
            </div>
          </div>
        </div>

        {/* Acciones */}
        <div className="flex gap-3 border-t px-5 py-4">
          <button
            onClick={onCerrar}
            className="flex-1 rounded-lg border border-gray-300 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50"
          >
            Cerrar
          </button>
          <button
            onClick={handleImprimir}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-amber-600 py-2 text-sm font-semibold text-white transition hover:bg-amber-700"
          >
            <Printer className="h-4 w-4" />
            Imprimir
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReciboVenta;
