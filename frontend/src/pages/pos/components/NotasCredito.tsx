import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw, ChevronLeft, ChevronRight, RotateCcw,
  XCircle, FileX, Search, AlertTriangle,
} from 'lucide-react';
import { Button, Spinner, Badge, EmptyState } from '../../../components/common';
import { posService } from '../../../services/pos.service';
import type { Venta } from '../../../types';
import type { NotaCredito, DevolucionData } from '../../../services/pos.service';
import toast from 'react-hot-toast';

const PAGE_SIZE = 15;

// ── Modal de crear devolución ────────────────────────────────────────────────
interface ModalDevolucionProps {
  venta: Venta;
  onCerrar: () => void;
  onCreada: () => void;
}

const ModalDevolucion: React.FC<ModalDevolucionProps> = ({ venta, onCerrar, onCreada }) => {
  const [motivo, setMotivo] = useState('');
  const [tipo, setTipo] = useState<'total' | 'parcial'>('total');
  const [enviando, setEnviando] = useState(false);

  const handleCrear = async () => {
    if (!motivo.trim()) {
      toast.error('Debés ingresar un motivo para la devolución');
      return;
    }
    setEnviando(true);
    try {
      const data: DevolucionData = {
        id_venta: venta.id_venta,
        productos: [], // Backend acepta lista vacía para devolución total
        motivo: motivo.trim(),
        tipo_devolucion: tipo,
      };
      const resultado = await posService.crearDevolucion(data);
      toast.success(`Nota de crédito #${resultado.nota_credito.nro_nota_credito} creada. Monto: Gs. ${Number(resultado.monto_devuelto).toLocaleString('es-PY')}`);
      onCreada();
      onCerrar();
    } catch (err: any) {
      const msg = err?.response?.data?.error ?? err?.response?.data?.detail ?? 'Error al crear la devolución';
      toast.error(msg);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onCerrar}
    >
      <div
        className="w-full max-w-md rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-gray-200 px-6 py-4">
          <RotateCcw className="h-5 w-5 text-amber-500" />
          <h3 className="text-lg font-semibold text-gray-800">Nueva Devolución</h3>
        </div>

        <div className="space-y-4 p-6">
          {/* Venta info */}
          <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 text-sm">
            <p className="font-medium text-gray-700">
              Venta {venta.nro_factura_venta ? `#${venta.nro_factura_venta}` : `ID ${venta.id_venta}`}
            </p>
            <p className="text-gray-500 mt-0.5">
              Cliente: {venta.cliente_nombre ?? venta.hijo_nombre ?? '—'} ·{' '}
              Total: <span className="font-semibold text-amber-600">
                Gs. {Number(venta.monto_total).toLocaleString('es-PY')}
              </span>
            </p>
          </div>

          {/* Tipo */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Tipo de devolución</label>
            <div className="flex gap-3">
              {(['total', 'parcial'] as const).map((t) => (
                <label key={t} className="flex cursor-pointer items-center gap-2">
                  <input
                    type="radio"
                    name="tipo"
                    value={t}
                    checked={tipo === t}
                    onChange={() => setTipo(t)}
                    className="h-4 w-4 text-amber-600 focus:ring-amber-500"
                  />
                  <span className="text-sm capitalize text-gray-700">{t}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Motivo */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Motivo <span className="text-red-500">*</span>
            </label>
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Ej: Producto defectuoso, error de cobro..."
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none resize-none"
            />
          </div>

          {/* Advertencia */}
          <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700">
              Esta acción creará una nota de crédito. El monto será reintegrado al cliente según la política de devoluciones.
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
          <Button type="button" variant="secondary" onClick={onCerrar} disabled={enviando}>
            Cancelar
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={handleCrear}
            disabled={enviando || !motivo.trim()}
            leftIcon={enviando ? <Spinner size="sm" /> : <RotateCcw className="h-4 w-4" />}
          >
            {enviando ? 'Procesando...' : 'Crear Devolución'}
          </Button>
        </div>
      </div>
    </div>
  );
};

// ── Modal de anular nota de crédito ─────────────────────────────────────────
interface ModalAnularProps {
  nota: NotaCredito;
  onCerrar: () => void;
  onAnulada: () => void;
}

const ModalAnular: React.FC<ModalAnularProps> = ({ nota, onCerrar, onAnulada }) => {
  const [motivo, setMotivo] = useState('');
  const [enviando, setEnviando] = useState(false);

  const handleAnular = async () => {
    if (!motivo.trim()) {
      toast.error('Debés ingresar un motivo de anulación');
      return;
    }
    setEnviando(true);
    try {
      await posService.anularNotaCredito(nota.id_nota, motivo.trim());
      toast.success(`Nota de crédito #${nota.nro_nota_credito} anulada`);
      onAnulada();
      onCerrar();
    } catch (err: any) {
      const msg = err?.response?.data?.error ?? 'Error al anular la nota';
      toast.error(msg);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onCerrar}
    >
      <div
        className="w-full max-w-sm rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 border-b border-gray-200 px-6 py-4">
          <XCircle className="h-5 w-5 text-red-500" />
          <h3 className="text-lg font-semibold text-gray-800">Anular Nota de Crédito</h3>
        </div>
        <div className="space-y-4 p-6">
          <p className="text-sm text-gray-600">
            ¿Anular nota de crédito <span className="font-semibold">#{nota.nro_nota_credito}</span>{' '}
            por <span className="font-semibold text-amber-600">
              Gs. {Number(nota.monto_total).toLocaleString('es-PY')}
            </span>?
          </p>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Motivo de anulación <span className="text-red-500">*</span>
            </label>
            <textarea
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Ej: Error en registro..."
              rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none resize-none"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 border-t border-gray-200 px-6 py-3">
          <Button type="button" variant="secondary" onClick={onCerrar} disabled={enviando}>
            Cancelar
          </Button>
          <Button
            type="button"
            className="bg-red-600 hover:bg-red-700 text-white"
            onClick={handleAnular}
            disabled={enviando || !motivo.trim()}
          >
            {enviando ? 'Anulando...' : 'Anular'}
          </Button>
        </div>
      </div>
    </div>
  );
};

// ── Componente principal ─────────────────────────────────────────────────────
const NotasCredito: React.FC = () => {
  const [notas, setNotas] = useState<NotaCredito[]>([]);
  const [ventas, setVentas] = useState<Venta[]>([]);
  const [cargandoNotas, setCargandoNotas] = useState(true);
  const [cargandoVentas, setCargandoVentas] = useState(true);
  const [totalNotas, setTotalNotas] = useState(0);
  const [paginaNotas, setPaginaNotas] = useState(1);
  const [estadoFiltro, setEstadoFiltro] = useState('');
  const [tabActiva, setTabActiva] = useState<'notas' | 'nueva'>('notas');
  const [ventaParaDevolver, setVentaParaDevolver] = useState<Venta | null>(null);
  const [notaParaAnular, setNotaParaAnular] = useState<NotaCredito | null>(null);
  const [busquedaVenta, setBusquedaVenta] = useState('');

  const cargarNotas = useCallback(async (p = 1) => {
    setCargandoNotas(true);
    try {
      const params: any = { page: p, page_size: PAGE_SIZE, ordering: '-fecha_emision' };
      if (estadoFiltro) params.estado = estadoFiltro;
      const data = await posService.getNotasCredito(params);
      setNotas(data.results ?? []);
      setTotalNotas(data.count ?? 0);
    } catch (err) {
      console.error(err);
    } finally {
      setCargandoNotas(false);
    }
  }, [estadoFiltro]);

  const cargarVentas = useCallback(async () => {
    setCargandoVentas(true);
    try {
      const params: any = { page: 1, page_size: 50, ordering: '-fecha', estado: 'Activo' };
      if (busquedaVenta.trim()) params.search = busquedaVenta.trim();
      const data = await posService.getVentas(params);
      setVentas(data.results ?? []);
    } catch (err) {
      console.error(err);
    } finally {
      setCargandoVentas(false);
    }
  }, [busquedaVenta]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { cargarNotas(paginaNotas); }, [paginaNotas, estadoFiltro]);
  useEffect(() => {
    if (tabActiva === 'nueva') cargarVentas();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tabActiva, busquedaVenta]);

  const totalPaginasNotas = Math.ceil(totalNotas / PAGE_SIZE);

  const formatGS = (val: string | number) =>
    `Gs. ${Number(val).toLocaleString('es-PY', { minimumFractionDigits: 0 })}`;

  const formatFecha = (f: string) =>
    new Date(f).toLocaleString('es-PY', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });

  const getEstadoBadge = (estado: string) => {
    switch (estado.toLowerCase()) {
      case 'activa': return <Badge variant="success">Activa</Badge>;
      case 'anulada': return <Badge variant="default">Anulada</Badge>;
      case 'usada': return <Badge variant="info">Usada</Badge>;
      default: return <Badge variant="warning">{estado}</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Sub-tabs */}
      <div className="flex gap-1 rounded-xl bg-gray-100 p-1 max-w-sm">
        <button
          type="button"
          onClick={() => setTabActiva('notas')}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
            tabActiva === 'notas' ? 'bg-white text-amber-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Notas de Crédito
        </button>
        <button
          type="button"
          onClick={() => setTabActiva('nueva')}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
            tabActiva === 'nueva' ? 'bg-white text-amber-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Nueva Devolución
        </button>
      </div>

      {/* Vista: Lista de notas de crédito */}
      {tabActiva === 'notas' && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-3 items-center">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Estado</label>
              <select
                value={estadoFiltro}
                onChange={(e) => { setEstadoFiltro(e.target.value); setPaginaNotas(1); }}
                className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              >
                <option value="">Todos</option>
                <option value="Activa">Activas</option>
                <option value="Anulada">Anuladas</option>
                <option value="Usada">Usadas</option>
              </select>
            </div>
            <Button
              type="button"
              variant="secondary"
              className="mt-5"
              onClick={() => cargarNotas(paginaNotas)}
              leftIcon={<RefreshCw className="h-4 w-4" />}
            >
              Actualizar
            </Button>
          </div>

          <div className="overflow-hidden rounded-lg border border-gray-200">
            {cargandoNotas ? (
              <div className="flex items-center justify-center py-16"><Spinner size="lg" /></div>
            ) : notas.length === 0 ? (
              <EmptyState
                icon={FileX}
                title="Sin notas de crédito"
                description={estadoFiltro
                  ? "No hay notas con este estado"
                  : "No hay notas de crédito registradas"}
                action={estadoFiltro ? {
                  label: "Limpiar filtro",
                  onClick: () => setEstadoFiltro('')
                } : undefined}
              />
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">N° Nota</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Motivo</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Monto</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {notas.map((nota) => (
                    <tr key={nota.id_nota} className="hover:bg-amber-50/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className="font-mono text-sm font-semibold text-gray-800">#{nota.nro_nota_credito}</span>
                        {nota.id_venta_origen && (
                          <p className="text-xs text-gray-400">Venta #{nota.id_venta_origen}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">{formatFecha(nota.fecha_emision)}</td>
                      <td className="px-4 py-3">
                        <p className="text-sm text-gray-700 line-clamp-2 max-w-xs">{nota.motivo}</p>
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-amber-600 text-sm">
                        {formatGS(nota.monto_total)}
                      </td>
                      <td className="px-4 py-3 text-center">{getEstadoBadge(nota.estado)}</td>
                      <td className="px-4 py-3 text-center">
                        {nota.estado.toLowerCase() === 'activa' && (
                          <button
                            type="button"
                            onClick={() => setNotaParaAnular(nota)}
                            className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors"
                            title="Anular nota de crédito"
                          >
                            <XCircle className="h-4 w-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {totalPaginasNotas > 1 && (
            <div className="flex items-center justify-between border-t border-gray-200 pt-3">
              <p className="text-sm text-gray-500">
                {totalNotas} notas en total
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setPaginaNotas(p => p - 1)}
                  disabled={paginaNotas === 1}
                  className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-600">{paginaNotas} / {totalPaginasNotas}</span>
                <button
                  type="button"
                  onClick={() => setPaginaNotas(p => p + 1)}
                  disabled={paginaNotas === totalPaginasNotas}
                  className="rounded-lg border border-gray-300 p-1.5 text-gray-500 hover:bg-gray-50 disabled:opacity-40 transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Vista: Nueva devolución - seleccionar venta */}
      {tabActiva === 'nueva' && (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            Seleccioná una venta para procesar la devolución:
          </p>
          <form
            onSubmit={(e) => { e.preventDefault(); cargarVentas(); }}
            className="flex gap-3"
          >
            <div className="flex-1">
              <input
                type="text"
                placeholder="Buscar por factura, cliente, nombre..."
                value={busquedaVenta}
                onChange={(e) => setBusquedaVenta(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
              />
            </div>
            <Button type="submit" variant="primary" leftIcon={<Search className="h-4 w-4" />}>
              Buscar
            </Button>
          </form>

          <div className="overflow-hidden rounded-lg border border-gray-200">
            {cargandoVentas ? (
              <div className="flex items-center justify-center py-12"><Spinner size="lg" /></div>
            ) : ventas.length === 0 ? (
              <EmptyState
                icon={Search}
                title="Sin ventas disponibles"
                description={busquedaVenta
                  ? "No se encontraron resultados"
                  : "No hay ventas activas para devolver"}
                action={busquedaVenta ? {
                  label: "Limpiar búsqueda",
                  onClick: () => setBusquedaVenta('')
                } : undefined}
                size="sm"
              />
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Factura</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                    <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {ventas.map((venta) => (
                    <tr key={venta.id_venta} className="hover:bg-amber-50/30 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-mono text-sm font-semibold text-gray-800">
                          {venta.nro_factura_venta ? `#${venta.nro_factura_venta}` : `ID ${venta.id_venta}`}
                        </p>
                        <p className="text-xs text-gray-400">
                          {new Date(venta.fecha).toLocaleDateString('es-PY')}
                        </p>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {venta.cliente_nombre ?? venta.hijo_nombre ?? '—'}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-gray-900 text-sm">
                        {formatGS(venta.monto_total)}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="text-xs text-gray-600">{venta.estado_pago}</span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <button
                          type="button"
                          onClick={() => setVentaParaDevolver(venta)}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-50 px-3 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100 transition-colors"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Devolución
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Modales */}
      {ventaParaDevolver && (
        <ModalDevolucion
          venta={ventaParaDevolver}
          onCerrar={() => setVentaParaDevolver(null)}
          onCreada={() => { cargarNotas(1); setTabActiva('notas'); }}
        />
      )}

      {notaParaAnular && (
        <ModalAnular
          nota={notaParaAnular}
          onCerrar={() => setNotaParaAnular(null)}
          onAnulada={() => cargarNotas(paginaNotas)}
        />
      )}
    </div>
  );
};

export default NotasCredito;
