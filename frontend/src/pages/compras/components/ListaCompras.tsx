import React, { useState, useEffect } from 'react';
import { Search, ShoppingCart, Edit, Eye, Trash2, CheckCircle, Clock, DollarSign, Package, AlertCircle } from 'lucide-react';
import { comprasService } from '../../../services/compras.service';
import { Compra, Proveedor } from '../../../types';
import { Card, Spinner, EmptyState, Skeleton } from '../../../components/common';
import toast from 'react-hot-toast';

interface EstadisticasCompras {
  total_compras: number;
  compras_pendientes: number;
  monto_total: number;
  saldo_pendiente: number;
}

interface ListaComprasProps {
  onEditar: (compra: Compra) => void;
  onVerDetalle: (compra: Compra) => void;
}

const ListaCompras: React.FC<ListaComprasProps> = ({ onEditar, onVerDetalle }) => {
  const [compras, setCompras] = useState<Compra[]>([]);
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState<'Pendiente' | 'Parcial' | 'Pagado' | undefined>();
  const [filtroProveedor, setFiltroProveedor] = useState<number | undefined>();
  const [paginaActual, setPaginaActual] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [estadisticas, setEstadisticas] = useState<EstadisticasCompras | null>(null);

  useEffect(() => {
    cargarProveedores();
    comprasService.getEstadisticasCompras().then(setEstadisticas).catch(() => {});
  }, []);

  useEffect(() => {
    cargarCompras();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busqueda, filtroEstado, filtroProveedor, paginaActual]);

  const cargarProveedores = async () => {
    try {
      const response = await comprasService.getProveedores({ estado: true });
      setProveedores(response.results);
    } catch (error) {
      console.error('Error al cargar proveedores:', error);
    }
  };

  const cargarCompras = async () => {
    setCargando(true);
    try {
      const params: any = {
        page: paginaActual,
        page_size: 10,
      };

      if (busqueda) params.search = busqueda;
      if (filtroEstado) params.estado_pago = filtroEstado;
      if (filtroProveedor) params.id_proveedor = filtroProveedor;

      const response = await comprasService.getCompras(params);
      setCompras(response.results);
      setTotalPaginas(Math.ceil(response.count / 10));
    } catch (error) {
      toast.error('Error al cargar compras');
      console.error('Error:', error);
    } finally {
      setCargando(false);
    }
  };

  const handleConfirmar = async (compra: Compra) => {
    if (!window.confirm(`¿Está seguro de confirmar la compra #${compra.id_compra}?`)) {
      return;
    }

    try {
      await comprasService.confirmarCompra(compra.id_compra);
      toast.success('Compra confirmada exitosamente');
      cargarCompras();
    } catch (error) {
      toast.error('Error al confirmar compra');
      console.error('Error:', error);
    }
  };

  const handleEliminar = async (compra: Compra) => {
    if (!window.confirm(`¿Está seguro de eliminar la compra #${compra.id_compra}?`)) {
      return;
    }

    try {
      await comprasService.eliminarCompra(compra.id_compra);
      toast.success('Compra eliminada exitosamente');
      cargarCompras();
    } catch (error) {
      toast.error('Error al eliminar compra');
      console.error('Error:', error);
    }
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0,
    }).format(valor);
  };

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-PY', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  const getEstadoBadge = (estado: string) => {
    const badges = {
      Pendiente: 'bg-yellow-100 text-yellow-800',
      Parcial: 'bg-blue-100 text-blue-800',
      Pagado: 'bg-green-100 text-green-800',
    };
    return badges[estado as keyof typeof badges] || 'bg-gray-100 text-gray-800';
  };

  if (cargando && compras.length === 0) {
    return (
      <Card>
        <div className="flex items-center justify-center py-12">
          <Spinner size="lg" />
        </div>
      </Card>
    );
  }

  const formatearMonedaStr = (valor: number) =>
    new Intl.NumberFormat('es-PY', { style: 'currency', currency: 'PYG', minimumFractionDigits: 0 }).format(valor);

  return (
    <div className="space-y-6">
      {/* Cards de estadísticas */}
      {estadisticas && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <Package className="h-7 w-7 text-amber-500 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Total compras</p>
              <p className="text-xl font-bold text-gray-800">{estadisticas.total_compras}</p>
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <AlertCircle className="h-7 w-7 text-yellow-500 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Pendientes</p>
              <p className="text-xl font-bold text-yellow-700">{estadisticas.compras_pendientes}</p>
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <DollarSign className="h-7 w-7 text-green-500 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Monto total</p>
              <p className="text-lg font-bold text-green-700">{formatearMonedaStr(estadisticas.monto_total)}</p>
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <Clock className="h-7 w-7 text-red-400 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Saldo pendiente</p>
              <p className="text-lg font-bold text-red-600">{formatearMonedaStr(estadisticas.saldo_pendiente)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <Card>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          {/* Búsqueda */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por número de factura o proveedor..."
                value={busqueda}
                onChange={(e) => {
                  setBusqueda(e.target.value);
                  setPaginaActual(1);
                }}
                className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>
          </div>

          {/* Filtro Proveedor */}
          <div>
            <select
              value={filtroProveedor || ''}
              onChange={(e) => {
                setFiltroProveedor(e.target.value ? Number(e.target.value) : undefined);
                setPaginaActual(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              <option value="">Todos los proveedores</option>
              {proveedores.map((proveedor) => (
                <option key={proveedor.id_proveedor} value={proveedor.id_proveedor}>
                  {proveedor.razon_social}
                </option>
              ))}
            </select>
          </div>

          {/* Filtro Estado */}
          <div>
            <select
              value={filtroEstado || ''}
              onChange={(e) => {
                setFiltroEstado(e.target.value as any);
                setPaginaActual(1);
              }}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
            >
              <option value="">Todos los estados</option>
              <option value="Pendiente">Pendiente</option>
              <option value="Parcial">Parcial</option>
              <option value="Pagado">Pagado</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Tabla de Compras */}
      <Card>
        {cargando ? (
          <Skeleton rows={8} cols={6} />
        ) : compras.length === 0 ? (
          <EmptyState
            icon={ShoppingCart}
            title="No hay compras"
            description={busqueda || filtroEstado || filtroProveedor
              ? "No se encontraron compras con los filtros seleccionados"
              : "Comienza registrando tu primera compra"}
            action={busqueda || filtroEstado || filtroProveedor ? {
              label: "Limpiar filtros",
              onClick: () => {
                setBusqueda('');
                setFiltroEstado(undefined);
                setFiltroProveedor(undefined);
              }
            } : undefined}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Fecha
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Factura
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Proveedor
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Monto Total
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      Saldo Pendiente
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                      Estado
                    </th>
                    <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {compras.map((compra) => (
                    <tr key={compra.id_compra} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <Clock className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-900">
                            {formatearFecha(compra.fecha)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {compra.nro_factura || 'Sin número'}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm text-gray-900">
                          {compra.proveedor_nombre || 'N/A'}
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <DollarSign className="h-4 w-4 text-green-600" />
                          <span className="text-sm font-semibold text-gray-900">
                            {formatearMoneda(compra.monto_total)}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-4">
                        <div className="text-sm font-medium text-gray-900">
                          {formatearMoneda(compra.saldo_pendiente)}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span
                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getEstadoBadge(
                            compra.estado_pago
                          )}`}
                        >
                          {compra.estado_pago}
                        </span>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => onVerDetalle(compra)}
                            className="rounded p-1 text-blue-600 hover:bg-blue-50"
                            title="Ver detalle"
                          >
                            <Eye className="h-5 w-5" />
                          </button>
                          {compra.estado_pago === 'Pendiente' && (
                            <>
                              <button
                                onClick={() => onEditar(compra)}
                                className="rounded p-1 text-amber-600 hover:bg-amber-50"
                                title="Editar"
                              >
                                <Edit className="h-5 w-5" />
                              </button>
                              <button
                                onClick={() => handleConfirmar(compra)}
                                className="rounded p-1 text-green-600 hover:bg-green-50"
                                title="Confirmar compra"
                              >
                                <CheckCircle className="h-5 w-5" />
                              </button>
                              <button
                                onClick={() => handleEliminar(compra)}
                                className="rounded p-1 text-red-600 hover:bg-red-50"
                                title="Eliminar"
                              >
                                <Trash2 className="h-5 w-5" />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Paginación */}
            {totalPaginas > 1 && (
              <div className="mt-4 flex items-center justify-between border-t border-gray-200 px-4 py-3">
                <div className="text-sm text-gray-700">
                  Página {paginaActual} de {totalPaginas}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPaginaActual((prev) => Math.max(1, prev - 1))}
                    disabled={paginaActual === 1}
                    className="rounded-lg border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPaginaActual((prev) => Math.min(totalPaginas, prev + 1))}
                    disabled={paginaActual === totalPaginas}
                    className="rounded-lg border border-gray-300 px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
};

export default ListaCompras;
