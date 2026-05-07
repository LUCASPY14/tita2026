import React, { useState, useEffect } from 'react';
import { Search, Edit, Eye, ToggleLeft, ToggleRight, Trash2, Users, UserCheck, UserX, CreditCard } from 'lucide-react';
import { Input, Button, Badge, ConfirmDialog, Skeleton, EmptyState } from '../../../components/common';
import { clientesService } from '../../../services/clientes.service';
import type { Cliente } from '../../../types';
import { useDebounce } from '../../../hooks/useDebounce';
import toast from 'react-hot-toast';

interface EstadisticasClientes {
  total: number;
  activos: number;
  inactivos: number;
  con_credito: number;
  sin_credito: number;
}

interface ListaClientesProps {
  onEditar: (cliente: Cliente) => void;
  onVerDetalle: (cliente: Cliente) => void;
}

const ListaClientes: React.FC<ListaClientesProps> = ({ onEditar, onVerDetalle }) => {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroActivo, setFiltroActivo] = useState<boolean | undefined>(undefined);
  const [paginaActual, setPaginaActual] = useState(1);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [clienteAEliminar, setClienteAEliminar] = useState<Cliente | null>(null);
  const [estadisticas, setEstadisticas] = useState<EstadisticasClientes | null>(null);

  const busquedaDebounced = useDebounce(busqueda);

  useEffect(() => {
    clientesService.getEstadisticas().then(setEstadisticas).catch(() => {});
  }, []);

  useEffect(() => {
    cargarClientes();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [busquedaDebounced, filtroActivo, paginaActual]);

  const cargarClientes = async () => {
    setCargando(true);
    try {
      const params: any = {
        page: paginaActual,
        page_size: 10,
      };

      if (busquedaDebounced) {
        params.search = busquedaDebounced;
      }

      if (filtroActivo !== undefined) {
        params.estado = filtroActivo;
      }

      const response = await clientesService.getClientes(params);
      setClientes(response.results || []);
      setTotalPaginas(Math.ceil(response.count / 10));
    } catch (error) {
      console.error('Error al cargar clientes:', error);
      toast.error('Error al cargar la lista de clientes');
    } finally {
      setCargando(false);
    }
  };

  const handleToggleEstado = async (cliente: Cliente) => {
    try {
      await clientesService.toggleEstadoCliente(cliente.id_cliente, !cliente.estado);
      toast.success(`Cliente ${!cliente.estado ? 'activado' : 'desactivado'} exitosamente`);
      cargarClientes();
    } catch (error) {
      toast.error('Error al cambiar el estado del cliente');
    }
  };

  const handleEliminar = (cliente: Cliente) => {
    setClienteAEliminar(cliente);
  };

  const confirmarEliminar = async () => {
    if (!clienteAEliminar) return;
    try {
      await clientesService.eliminarCliente(clienteAEliminar.id_cliente);
      toast.success('Cliente eliminado exitosamente');
      setClienteAEliminar(null);
      cargarClientes();
    } catch (error) {
      toast.error('Error al eliminar el cliente');
    }
  };

  const formatearMoneda = (monto?: number): string => {
    if (!monto) return 'Gs. 0';
    return `Gs. ${monto.toLocaleString('es-PY')}`;
  };

  return (
    <div className="space-y-4">
      {/* Cards de estadísticas */}
      {estadisticas && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <Users className="h-7 w-7 text-amber-500 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Total</p>
              <p className="text-xl font-bold text-gray-800">{estadisticas.total}</p>
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <UserCheck className="h-7 w-7 text-green-500 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Activos</p>
              <p className="text-xl font-bold text-green-700">{estadisticas.activos}</p>
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <CreditCard className="h-7 w-7 text-blue-500 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Con crédito</p>
              <p className="text-xl font-bold text-blue-700">{estadisticas.con_credito}</p>
            </div>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 flex items-center gap-3">
            <UserX className="h-7 w-7 text-gray-400 shrink-0" />
            <div>
              <p className="text-xs text-gray-500">Inactivos</p>
              <p className="text-xl font-bold text-gray-600">{estadisticas.inactivos}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="md:col-span-2">
          <Input
            type="text"
            placeholder="Buscar por nombre, RUC/CI o email..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            leftIcon={<Search className="h-5 w-5 text-gray-400" />}
          />
        </div>

        <div className="flex gap-2">
          <Button
            variant={filtroActivo === true ? 'primary' : 'outline'}
            onClick={() => setFiltroActivo(filtroActivo === true ? undefined : true)}
            className="flex-1"
          >
            Activos
          </Button>
          <Button
            variant={filtroActivo === false ? 'primary' : 'outline'}
            onClick={() => setFiltroActivo(filtroActivo === false ? undefined : false)}
            className="flex-1"
          >
            Inactivos
          </Button>
        </div>
      </div>

      {/* Tabla */}
      {cargando ? (
        <Skeleton rows={6} cols={5} />
      ) : clientes.length === 0 ? (
        <EmptyState
          icon={Search}
          title="No se encontraron clientes"
          description={busquedaDebounced || filtroActivo !== undefined
            ? "Intenta ajustar los filtros de búsqueda"
            : "Comienza agregando tu primer cliente"}
          action={busquedaDebounced || filtroActivo !== undefined ? {
            label: "Limpiar filtros",
            onClick: () => {
              setBusqueda('');
              setFiltroActivo(undefined);
            }
          } : undefined}
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Cliente
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    RUC/CI
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Contacto
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Crédito
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {clientes.map((cliente) => (
                  <tr key={cliente.id_cliente} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <div>
                          <div className="font-medium text-gray-900">
                            {cliente.nombres} {cliente.apellidos}
                          </div>
                          {cliente.razon_social && (
                            <div className="text-sm text-gray-500">{cliente.razon_social}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {cliente.ruc_ci}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{cliente.telefono || '-'}</div>
                      <div className="text-sm text-gray-500">{cliente.email || '-'}</div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm text-gray-900">
                        Límite: {formatearMoneda(cliente.limite_credito)}
                      </div>
                      {cliente.credito_disponible !== undefined && (
                        <div className="text-sm text-gray-500">
                          Disponible: {formatearMoneda(cliente.credito_disponible)}
                        </div>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <Badge variant={cliente.estado ? 'success' : 'danger'}>
                        {cliente.estado ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm font-medium">
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => onVerDetalle(cliente)}
                          className="text-blue-600 hover:text-blue-700"
                          title="Ver detalle"
                        >
                          <Eye className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => onEditar(cliente)}
                          className="text-amber-600 hover:text-amber-700"
                          title="Editar"
                        >
                          <Edit className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleToggleEstado(cliente)}
                          className={`${cliente.estado ? 'text-gray-600' : 'text-green-600'} hover:opacity-70`}
                          title={cliente.estado ? 'Desactivar' : 'Activar'}
                        >
                          {cliente.estado ? (
                            <ToggleRight className="h-5 w-5" />
                          ) : (
                            <ToggleLeft className="h-5 w-5" />
                          )}
                        </button>
                        <button
                          onClick={() => handleEliminar(cliente)}
                          className="text-red-600 hover:text-red-700"
                          title="Eliminar"
                        >
                          <Trash2 className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginación */}
          {totalPaginas > 1 && (
            <div className="flex items-center justify-between border-t pt-4">
              <div className="text-sm text-gray-700">
                Página {paginaActual} de {totalPaginas}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPaginaActual(prev => Math.max(1, prev - 1))}
                  disabled={paginaActual === 1}
                >
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setPaginaActual(prev => Math.min(totalPaginas, prev + 1))}
                  disabled={paginaActual === totalPaginas}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      <ConfirmDialog
        isOpen={!!clienteAEliminar}
        onClose={() => setClienteAEliminar(null)}
        onConfirm={confirmarEliminar}
        title="Eliminar cliente"
        message={clienteAEliminar ? `¿Estás seguro de eliminar al cliente ${clienteAEliminar.nombres} ${clienteAEliminar.apellidos}? Esta acción no se puede deshacer.` : ''}
        confirmText="Eliminar"
      />
    </div>
  );
};

export default ListaClientes;
