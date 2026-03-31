import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText, ChevronDown, ChevronUp, Printer, RotateCcw,
  CheckCircle, AlertCircle, Loader2, RefreshCw, User,
} from 'lucide-react';
import toast from 'react-hot-toast';
import facturacionService, {
  ClienteConPendientes,
  ItemPendiente,
  DocumentoEmitido,
} from '../../services/facturacion.service';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmt = (n: number) =>
  new Intl.NumberFormat('es-PY', { minimumFractionDigits: 0 }).format(n);

// ─── Modal de emisión ─────────────────────────────────────────────────────────

interface ModalEmitirProps {
  cliente: ClienteConPendientes;
  onClose: () => void;
  onEmitido: (doc: DocumentoEmitido) => void;
}

const ModalEmitir: React.FC<ModalEmitirProps> = ({ cliente, onClose, onEmitido }) => {
  const todosLosItems: ItemPendiente[] = [
    ...cliente.ventas,
    ...cliente.almuerzos,
  ];
  const [seleccionados, setSeleccionados] = useState<Set<string>>(
    new Set(todosLosItems.map((i) => `${i.tipo}:${i.id}`))
  );
  const [nroPreimpreso, setNroPreimpreso] = useState('');
  const [loading, setLoading] = useState(false);

  const toggleItem = (key: string) => {
    setSeleccionados((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const totalSeleccionado = todosLosItems
    .filter((i) => seleccionados.has(`${i.tipo}:${i.id}`))
    .reduce((acc, i) => acc + i.monto, 0);

  const handleEmitir = async () => {
    const nro = parseInt(nroPreimpreso, 10);
    if (!nroPreimpreso || isNaN(nro) || nro <= 0) {
      toast.error('Ingresá el número del formulario preimpreso.');
      return;
    }
    if (seleccionados.size === 0) {
      toast.error('Seleccioná al menos un item.');
      return;
    }

    const ventas_ids = todosLosItems
      .filter((i) => i.tipo === 'venta' && seleccionados.has(`venta:${i.id}`))
      .map((i) => i.id);
    const almuerzos_ids = todosLosItems
      .filter((i) => i.tipo === 'almuerzo' && seleccionados.has(`almuerzo:${i.id}`))
      .map((i) => i.id);

    setLoading(true);
    try {
      const doc = await facturacionService.emitir({
        id_cliente: cliente.id_cliente,
        nro_preimpreso: nro,
        ventas_ids,
        almuerzos_ids,
      });
      toast.success(`Factura ${doc.nro_preimpreso_interno} emitida.`);
      onEmitido(doc);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Error al emitir la factura.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Emitir Factura</h2>
            <p className="text-sm text-gray-500 mt-0.5">
              {cliente.nombre_completo} · RUC/CI: {cliente.ruc_ci}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-2xl font-light"
          >
            ×
          </button>
        </div>

        {/* Items scrollables */}
        <div className="flex-1 overflow-y-auto p-6 space-y-2">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
            Seleccioná los items a incluir
          </p>
          {todosLosItems.length === 0 && (
            <p className="text-gray-400 text-sm">No hay items disponibles.</p>
          )}
          {todosLosItems.map((item) => {
            const key = `${item.tipo}:${item.id}`;
            const checked = seleccionados.has(key);
            return (
              <label
                key={key}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  checked ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleItem(key)}
                  className="w-4 h-4 accent-blue-600"
                />
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    item.tipo === 'venta'
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-emerald-100 text-emerald-700'
                  }`}
                >
                  {item.tipo === 'venta' ? 'POS' : 'Almuerzo'}
                </span>
                <span className="flex-1 text-sm text-gray-700">{item.descripcion}</span>
                <span className="text-sm font-semibold text-gray-900">
                  Gs {fmt(item.monto)}
                </span>
              </label>
            );
          })}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 rounded-b-2xl space-y-4">
          <div className="flex items-center justify-between text-lg font-bold text-gray-900">
            <span>Total a facturar:</span>
            <span>Gs {fmt(totalSeleccionado)}</span>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nro. del formulario preimpreso *
            </label>
            <input
              type="number"
              value={nroPreimpreso}
              onChange={(e) => setNroPreimpreso(e.target.value)}
              placeholder="Ej: 123"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-gray-900
                         focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none
                         text-xl font-mono tracking-widest"
            />
            <p className="text-xs text-gray-400 mt-1">
              Ingresá el número del formulario que vas a utilizar.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={loading}
              className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-gray-700
                         hover:bg-gray-100 transition-colors disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              onClick={handleEmitir}
              disabled={loading || seleccionados.size === 0}
              className="flex-1 px-4 py-2.5 bg-blue-600 text-white rounded-lg font-semibold
                         hover:bg-blue-700 transition-colors disabled:opacity-50
                         flex items-center justify-center gap-2"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <FileText className="w-4 h-4" />
              )}
              {loading ? 'Emitiendo…' : 'Emitir Factura'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── Tarjeta de cliente ───────────────────────────────────────────────────────

interface TarjetaClienteProps {
  cliente: ClienteConPendientes;
  onFacturar: (c: ClienteConPendientes) => void;
}

const TarjetaCliente: React.FC<TarjetaClienteProps> = ({ cliente, onFacturar }) => {
  const [expandido, setExpandido] = useState(false);
  const totalItems = cliente.ventas.length + cliente.almuerzos.length;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Fila principal */}
      <div className="flex items-center gap-4 p-4">
        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-blue-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 truncate">{cliente.nombre_completo}</p>
          <p className="text-xs text-gray-400">RUC/CI: {cliente.ruc_ci}</p>
        </div>
        <div className="text-right mr-2">
          <p className="font-bold text-gray-900">Gs {fmt(cliente.total_pendiente)}</p>
          <p className="text-xs text-gray-400">{totalItems} item{totalItems !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={() => onFacturar(cliente)}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg
                     hover:bg-blue-700 transition-colors flex items-center gap-1.5 flex-shrink-0"
        >
          <FileText className="w-4 h-4" />
          Facturar
        </button>
        <button
          onClick={() => setExpandido((p) => !p)}
          className="p-2 text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
        >
          {expandido ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Detalle expandible */}
      {expandido && (
        <div className="border-t border-gray-100 bg-gray-50 px-4 py-3 space-y-1">
          {[...cliente.ventas, ...cliente.almuerzos].map((item) => (
            <div
              key={`${item.tipo}:${item.id}`}
              className="flex items-center justify-between text-sm py-1"
            >
              <div className="flex items-center gap-2">
                <span
                  className={`text-xs px-1.5 py-0.5 rounded font-medium ${
                    item.tipo === 'venta'
                      ? 'bg-indigo-100 text-indigo-600'
                      : 'bg-emerald-100 text-emerald-600'
                  }`}
                >
                  {item.tipo === 'venta' ? 'POS' : 'Alm'}
                </span>
                <span className="text-gray-600">{item.descripcion}</span>
              </div>
              <span className="font-medium text-gray-800">Gs {fmt(item.monto)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ─── Modal de éxito + impresión ───────────────────────────────────────────────

interface ModalImprimirProps {
  doc: DocumentoEmitido;
  onClose: () => void;
}

const ModalImprimir: React.FC<ModalImprimirProps> = ({ doc, onClose }) => {
  const [printing, setPrinting] = useState(false);

  const handleImprimir = async () => {
    setPrinting(true);
    try {
      const texto = await facturacionService.fetchTextoImpresion(doc.id_documento);
      const blob = new Blob([texto], { type: 'text/plain; charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const win = window.open(url, '_blank', 'noopener,noreferrer');
      // Revocar el object URL después de que la ventana lo cargue
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      if (!win) toast.error('El navegador bloqueó la ventana emergente. Permitila e intentá de nuevo.');
    } catch {
      toast.error('Error al obtener el texto de impresión.');
    } finally {
      setPrinting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-1">Factura emitida</h2>
        <p className="text-gray-500 mb-1">{doc.nro_preimpreso_interno}</p>
        <p className="text-sm text-gray-400 mb-6">
          {doc.cliente_nombre} · Gs {fmt(parseFloat(doc.monto_total))}
        </p>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-gray-700
                       hover:bg-gray-50 transition-colors"
          >
            Cerrar
          </button>
          <button
            onClick={handleImprimir}
            disabled={printing}
            className="flex-1 px-4 py-2.5 bg-gray-900 text-white rounded-lg font-semibold
                       hover:bg-gray-800 transition-colors flex items-center justify-center gap-2
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {printing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Printer className="w-4 h-4" />}
            {printing ? 'Generando...' : 'Imprimir'}
          </button>
        </div>
      </div>
    </div>
  );
};

// ─── Página principal ────────────────────────────────────────────────────────

const ColaFacturacion: React.FC = () => {
  const [cola, setCola] = useState<ClienteConPendientes[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clienteModal, setClienteModal] = useState<ClienteConPendientes | null>(null);
  const [docEmitido, setDocEmitido] = useState<DocumentoEmitido | null>(null);

  const cargarCola = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await facturacionService.getCola();
      setCola(data);
    } catch {
      setError('No se pudo cargar la cola de facturación.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    cargarCola();
  }, [cargarCola]);

  const handleEmitido = (doc: DocumentoEmitido) => {
    setClienteModal(null);
    setDocEmitido(doc);
    // Remover cliente de la cola (o recargar)
    cargarCola();
  };

  const totalPendiente = cola.reduce((acc, c) => acc + c.total_pendiente, 0);

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" />
            Cola de Facturación
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Ventas y almuerzos pagados pendientes de factura física
          </p>
        </div>
        <button
          onClick={cargarCola}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg
                     text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Resumen */}
      {!loading && !error && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
            <p className="text-sm text-blue-600 font-medium">Clientes pendientes</p>
            <p className="text-3xl font-bold text-blue-700 mt-1">{cola.length}</p>
          </div>
          <div className="bg-amber-50 rounded-xl p-4 border border-amber-100">
            <p className="text-sm text-amber-600 font-medium">Total a facturar</p>
            <p className="text-3xl font-bold text-amber-700 mt-1">Gs {fmt(totalPendiente)}</p>
          </div>
        </div>
      )}

      {/* Estado de carga */}
      {loading && (
        <div className="flex items-center justify-center py-16 text-gray-400">
          <Loader2 className="w-8 h-8 animate-spin mr-3" />
          Cargando cola…
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 rounded-xl border border-red-200 text-red-700">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
          <button onClick={cargarCola} className="ml-auto flex items-center gap-1 underline text-sm">
            <RotateCcw className="w-3 h-3" /> Reintentar
          </button>
        </div>
      )}

      {/* Lista vacía */}
      {!loading && !error && cola.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-400" />
          <p className="text-lg font-medium text-gray-600">Todo al día</p>
          <p className="text-sm">No hay ventas ni almuerzos pendientes de facturación.</p>
        </div>
      )}

      {/* Cola */}
      {!loading && !error && cola.length > 0 && (
        <div className="space-y-3">
          {cola.map((cliente) => (
            <TarjetaCliente
              key={cliente.id_cliente}
              cliente={cliente}
              onFacturar={setClienteModal}
            />
          ))}
        </div>
      )}

      {/* Modal emisión */}
      {clienteModal && (
        <ModalEmitir
          cliente={clienteModal}
          onClose={() => setClienteModal(null)}
          onEmitido={handleEmitido}
        />
      )}

      {/* Modal impresión */}
      {docEmitido && (
        <ModalImprimir
          doc={docEmitido}
          onClose={() => setDocEmitido(null)}
        />
      )}
    </div>
  );
};

export default ColaFacturacion;
