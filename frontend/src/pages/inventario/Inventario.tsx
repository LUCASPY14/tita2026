import React, { useState, useEffect, useCallback } from 'react';
import { Package, TrendingDown, RefreshCw, Search, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { Spinner } from '../../components/common';
import { inventarioService, type StockItem, type MovimientoStock } from '../../services/inventario.service';
import toast from 'react-hot-toast';

type Vista = 'stock' | 'movimientos';

const MOTIVO_LABELS: Record<string, string> = {
  compra: 'Compra a proveedor',
  venta: 'Venta a cliente',
  ajuste_aumento: 'Ajuste (aumento)',
  ajuste_merma: 'Ajuste (merma)',
  devolucion_cliente: 'Devolución cliente',
  devolucion_proveedor: 'Devolución proveedor',
  correccion_manual: 'Corrección manual',
  transferencia: 'Transferencia',
  producto_vencido: 'Baja por vencimiento',
  producto_danado: 'Baja por daño',
  inventario_inicial: 'Inventario inicial',
};

const Inventario: React.FC = () => {
  const [vista, setVista] = useState<Vista>('stock');
  const [stock, setStock] = useState<StockItem[]>([]);
  const [movimientos, setMovimientos] = useState<MovimientoStock[]>([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroTipo, setFiltroTipo] = useState<'' | 'Ingreso' | 'Egreso'>('');

  const cargarStock = useCallback(async () => {
    setCargando(true);
    try {
      const params: any = { page_size: 100 };
      if (busqueda) params.search = busqueda;
      const resp = await inventarioService.getStock(params);
      setStock(resp.results || []);
    } catch {
      toast.error('Error al cargar el stock');
    } finally {
      setCargando(false);
    }
  }, [busqueda]);

  const cargarMovimientos = useCallback(async () => {
    setCargando(true);
    try {
      const params: any = { page_size: 50 };
      if (filtroTipo) params.tipo_movimiento = filtroTipo;
      const resp = await inventarioService.getMovimientos(params);
      setMovimientos(resp.results || []);
    } catch {
      toast.error('Error al cargar movimientos');
    } finally {
      setCargando(false);
    }
  }, [filtroTipo]);

  useEffect(() => {
    if (vista === 'stock') cargarStock();
    else cargarMovimientos();
  }, [vista, cargarStock, cargarMovimientos]);

  const formatearFecha = (iso: string) =>
    new Date(iso).toLocaleString('es-PY', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });

  const stockBajo = stock.filter(s => s.cantidad <= 0 || s.cantidad < 5);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inventario</h1>
          <p className="mt-1 text-gray-600">Stock actual y movimientos de productos</p>
        </div>
        <button
          onClick={() => vista === 'stock' ? cargarStock() : cargarMovimientos()}
          disabled={cargando}
          className="flex items-center gap-2 rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${cargando ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Alerta de stock bajo */}
      {vista === 'stock' && stockBajo.length > 0 && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
          <TrendingDown className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-600" />
          <div className="text-sm text-red-800">
            <span className="font-semibold">{stockBajo.length} producto{stockBajo.length !== 1 ? 's' : ''} con stock crítico:</span>{' '}
            {stockBajo.map(s => s.producto_nombre).join(', ')}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-gray-100 p-1">
        <button
          onClick={() => setVista('stock')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            vista === 'stock' ? 'bg-white text-amber-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <Package className="h-4 w-4" />
          Stock Actual
        </button>
        <button
          onClick={() => setVista('movimientos')}
          className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all ${
            vista === 'movimientos' ? 'bg-white text-amber-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <ArrowUpCircle className="h-4 w-4" />
          Movimientos
        </button>
      </div>

      {/* Vista Stock */}
      {vista === 'stock' && (
        <div className="space-y-4">
          {/* Búsqueda */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              placeholder="Buscar producto..."
              className="w-full rounded-lg border border-gray-300 py-2 pl-9 pr-4 text-sm focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
            />
          </div>

          {cargando ? (
            <div className="flex justify-center py-16"><Spinner className="h-8 w-8" /></div>
          ) : stock.length === 0 ? (
            <div className="rounded-xl border border-gray-200 py-16 text-center">
              <Package className="mx-auto mb-3 h-12 w-12 text-gray-300" />
              <p className="text-gray-500">No se encontraron registros de stock</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Producto</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Categoría</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500">Cantidad</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">Última actualización</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wide text-gray-500">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {stock.map(item => {
                    const sinStock = item.cantidad <= 0;
                    const bajstock = !sinStock && item.cantidad < 5;
                    return (
                      <tr key={item.id_stock} className={sinStock ? 'bg-red-50' : bajstock ? 'bg-amber-50' : ''}>
                        <td className="px-4 py-3 font-medium text-gray-900">{item.producto_nombre}</td>
                        <td className="px-4 py-3 text-sm text-gray-500">{item.producto_categoria || '—'}</td>
                        <td className="px-4 py-3 text-center">
                          <span className={`text-lg font-bold ${sinStock ? 'text-red-600' : bajstock ? 'text-amber-600' : 'text-gray-900'}`}>
                            {item.cantidad}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">{formatearFecha(item.fecha_ultima_actualizacion)}</td>
                        <td className="px-4 py-3 text-center">
                          {sinStock ? (
                            <span className="inline-flex rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-semibold text-red-700">Sin stock</span>
                          ) : bajstock ? (
                            <span className="inline-flex rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700">Stock bajo</span>
                          ) : (
                            <span className="inline-flex rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700">OK</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Vista Movimientos */}
      {vista === 'movimientos' && (
        <div className="space-y-4">
          {/* Filtro tipo */}
          <select
            value={filtroTipo}
            onChange={e => setFiltroTipo(e.target.value as any)}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-amber-500 focus:outline-none"
          >
            <option value="">Todos los movimientos</option>
            <option value="Ingreso">Solo Ingresos</option>
            <option value="Egreso">Solo Egresos</option>
          </select>

          {cargando ? (
            <div className="flex justify-center py-16"><Spinner className="h-8 w-8" /></div>
          ) : movimientos.length === 0 ? (
            <div className="rounded-xl border border-gray-200 py-16 text-center">
              <Package className="mx-auto mb-3 h-12 w-12 text-gray-300" />
              <p className="text-gray-500">No hay movimientos registrados</p>
            </div>
          ) : (
            <div className="space-y-2">
              {movimientos.map(mov => (
                <div key={mov.id_movimiento_stock} className="flex items-center gap-4 rounded-xl border border-gray-200 bg-white px-4 py-3">
                  <div className={`rounded-full p-2 ${mov.tipo_movimiento === 'Ingreso' ? 'bg-green-100' : 'bg-red-100'}`}>
                    {mov.tipo_movimiento === 'Ingreso'
                      ? <ArrowUpCircle className="h-5 w-5 text-green-600" />
                      : <ArrowDownCircle className="h-5 w-5 text-red-600" />
                    }
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{mov.producto_nombre}</p>
                    <p className="text-xs text-gray-500">{MOTIVO_LABELS[mov.motivo] ?? mov.motivo}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-lg font-bold ${mov.tipo_movimiento === 'Ingreso' ? 'text-green-600' : 'text-red-600'}`}>
                      {mov.tipo_movimiento === 'Ingreso' ? '+' : '-'}{mov.cantidad}
                    </p>
                    <p className="text-xs text-gray-500">Stock: {mov.stock_resultante}</p>
                  </div>
                  <div className="text-right text-xs text-gray-400 hidden sm:block">
                    {formatearFecha(mov.fecha_hora)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Inventario;
