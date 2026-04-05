import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Printer, XCircle, Search, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';
import facturacionService, { DocumentoEmitido } from '../../services/facturacion.service';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const fmtGs = (s: string | number) =>
  new Intl.NumberFormat('es-PY', { minimumFractionDigits: 0 }).format(Number(s));

const fmtFecha = (s: string) => {
  try {
    return new Date(s).toLocaleDateString('es-PY', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  } catch {
    return s;
  }
};

// ─── HistorialFacturas ────────────────────────────────────────────────────────

const HistorialFacturas: React.FC = () => {
  const [documentos, setDocumentos] = useState<DocumentoEmitido[]>([]);
  const [total, setTotal]           = useState(0);
  const [pagina, setPagina]         = useState(1);
  const [cargando, setCargando]     = useState(false);
  const [anulando, setAnulando]     = useState<number | null>(null);

  // Filtros
  const [fechaDesde, setFechaDesde]       = useState('');
  const [fechaHasta, setFechaHasta]       = useState('');
  const [condicion, setCondicion]         = useState<'' | 'CONTADO' | 'CREDITO'>('');
  const [busqueda, setBusqueda]           = useState('');

  const PAGE_SIZE = 20;

  const cargar = useCallback(async (pag = 1) => {
    try {
      setCargando(true);
      const params: Record<string, string | number> = { page: pag };
      if (fechaDesde) params.fecha_desde = fechaDesde;
      if (fechaHasta) params.fecha_hasta = fechaHasta;
      if (condicion) params.condicion_venta = condicion;
      const data = await facturacionService.getHistorial(params as any);
      setDocumentos(data.results ?? (data as any));
      setTotal(data.count ?? (data as any).length ?? 0);
      setPagina(pag);
    } catch {
      toast.error('Error al cargar historial de facturas');
    } finally {
      setCargando(false);
    }
  }, [fechaDesde, fechaHasta, condicion]);

  useEffect(() => { cargar(1); }, [cargar]);

  const handleImprimir = async (doc: DocumentoEmitido) => {
    try {
      const texto = await facturacionService.fetchTextoImpresion(doc.id_documento);
      const wins = window.open('', '_blank', 'width=700,height=600');
      if (!wins) { toast.error('Permití ventanas emergentes para imprimir.'); return; }
      wins.document.write(`<html><body><pre style="font-family:monospace;font-size:13px">${texto}</pre></body></html>`);
      wins.document.close();
      wins.focus();
      wins.print();
    } catch {
      toast.error('Error al obtener texto de impresión');
    }
  };

  const handleAnular = async (doc: DocumentoEmitido) => {
    if (!window.confirm(`¿Anular factura ${doc.nro_preimpreso_interno}? Esta acción no se puede deshacer.`)) return;
    try {
      setAnulando(doc.id_documento);
      await facturacionService.anular(doc.id_documento);
      toast.success(`Factura ${doc.nro_preimpreso_interno} anulada`);
      cargar(pagina);
    } catch {
      toast.error('Error al anular la factura');
    } finally {
      setAnulando(null);
    }
  };

  // Filtro local por búsqueda (cliente / nro)
  const filtradas = documentos.filter((d) => {
    if (!busqueda) return true;
    const q = busqueda.toLowerCase();
    return (
      (d.cliente_nombre ?? '').toLowerCase().includes(q) ||
      (d.nro_preimpreso_interno ?? '').includes(q) ||
      (d.cliente_ruc ?? '').includes(q)
    );
  });

  const totalPaginas = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Encabezado */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="h-7 w-7 text-amber-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Historial de Facturas</h1>
            <p className="text-sm text-gray-500">Facturas timbradas emitidas</p>
          </div>
        </div>
        <button
          onClick={() => cargar(pagina)}
          disabled={cargando}
          className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Filtros */}
      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Desde</label>
          <input
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Hasta</label>
          <input
            type="date"
            value={fechaHasta}
            onChange={(e) => setFechaHasta(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Condición</label>
          <select
            value={condicion}
            onChange={(e) => setCondicion(e.target.value as any)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">Todas</option>
            <option value="CONTADO">Contado</option>
            <option value="CREDITO">Crédito</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Buscar</label>
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Cliente, RUC o Nro…"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              className="w-full rounded-lg border border-gray-300 py-2 pl-8 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
          </div>
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        {cargando ? (
          <div className="flex items-center justify-center py-16">
            <RefreshCw className="h-8 w-8 animate-spin text-amber-500" />
          </div>
        ) : filtradas.length === 0 ? (
          <div className="py-16 text-center text-gray-500">
            <FileText className="mx-auto mb-3 h-12 w-12 text-gray-300" />
            <p>No hay facturas que coincidan con los filtros.</p>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-xs font-semibold uppercase tracking-wide text-gray-500">
              <tr>
                <th className="px-4 py-3 text-left">Nro. Factura</th>
                <th className="px-4 py-3 text-left">Fecha</th>
                <th className="px-4 py-3 text-left">Cliente</th>
                <th className="px-4 py-3 text-left">RUC/CI</th>
                <th className="px-4 py-3 text-right">Monto</th>
                <th className="px-4 py-3 text-center">Condición</th>
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filtradas.map((doc) => (
                <tr key={doc.id_documento} className="hover:bg-amber-50/40 transition-colors">
                  <td className="px-4 py-3 font-mono font-medium text-gray-900">
                    {doc.nro_preimpreso_interno}
                  </td>
                  <td className="px-4 py-3 text-gray-600">{fmtFecha(doc.fecha_emision)}</td>
                  <td className="px-4 py-3 text-gray-800">{doc.cliente_nombre ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{doc.cliente_ruc ?? '—'}</td>
                  <td className="px-4 py-3 text-right font-medium text-gray-900">
                    Gs. {fmtGs(doc.monto_total)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        doc.condicion_venta === 'CREDITO'
                          ? 'bg-orange-100 text-orange-700'
                          : 'bg-green-100 text-green-700'
                      }`}
                    >
                      {doc.condicion_venta_display ?? doc.condicion_venta}
                      {doc.condicion_venta === 'CREDITO' && doc.plazo_dias
                        ? ` ${doc.plazo_dias}d`
                        : ''}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        onClick={() => handleImprimir(doc)}
                        title="Imprimir"
                        className="rounded-lg p-1.5 text-gray-500 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                      >
                        <Printer className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleAnular(doc)}
                        disabled={anulando === doc.id_documento}
                        title="Anular"
                        className="rounded-lg p-1.5 text-gray-500 hover:bg-red-50 hover:text-red-600 transition-colors disabled:opacity-40"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Paginación */}
      {totalPaginas > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <span>
            {total} factura{total !== 1 ? 's' : ''} en total
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => cargar(pagina - 1)}
              disabled={pagina <= 1 || cargando}
              className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" /> Anterior
            </button>
            <span className="px-2 font-medium">
              {pagina} / {totalPaginas}
            </span>
            <button
              onClick={() => cargar(pagina + 1)}
              disabled={pagina >= totalPaginas || cargando}
              className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
            >
              Siguiente <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistorialFacturas;
