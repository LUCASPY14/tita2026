import React, { useState, useEffect, useCallback } from 'react';
import { Plus, Search, Edit, Trash2, Building2, Phone, Mail, MapPin, CheckCircle, XCircle, X, Save } from 'lucide-react';
import { Card, Button, Badge, Spinner } from '../../components/common';
import { comprasService, ProveedorData, ProveedorParams } from '../../services/compras.service';
import type { Proveedor } from '../../types';
import toast from 'react-hot-toast';

// ── Modal de formulario ────────────────────────────────────────────────────────

interface ModalProps {
  proveedor?: Proveedor | null;
  onClose: () => void;
  onSave: () => void;
}

const ProveedorModal: React.FC<ModalProps> = ({ proveedor, onClose, onSave }) => {
  const isEditing = !!proveedor;
  const [formData, setFormData] = useState<ProveedorData>({
    ruc: proveedor?.ruc ?? '',
    razon_social: proveedor?.razon_social ?? '',
    telefono: proveedor?.telefono ?? '',
    email: proveedor?.email ?? '',
    direccion: proveedor?.direccion ?? '',
    ciudad: proveedor?.ciudad ?? '',
    estado: proveedor?.estado ?? true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
    if (errors[name]) setErrors(prev => { const n = { ...prev }; delete n[name]; return n; });
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.ruc.trim()) newErrors.ruc = 'El RUC es requerido';
    if (!formData.razon_social.trim()) newErrors.razon_social = 'La razón social es requerida';
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    try {
      if (isEditing) {
        await comprasService.actualizarProveedor(proveedor!.id_proveedor, formData);
        toast.success('Proveedor actualizado');
      } else {
        await comprasService.crearProveedor(formData);
        toast.success('Proveedor creado');
      }
      onSave();
    } catch (error: any) {
      if (error.response?.data) {
        const apiErrors: Record<string, string> = {};
        Object.entries(error.response.data).forEach(([k, v]) => {
          apiErrors[k] = Array.isArray(v) ? (v as string[])[0] : String(v);
        });
        setErrors(apiErrors);
      } else {
        toast.error('Error al guardar el proveedor');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100">
              <Building2 className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {isEditing ? 'Editar Proveedor' : 'Nuevo Proveedor'}
              </h3>
              <p className="text-sm text-gray-500">
                {isEditing ? proveedor!.razon_social : 'Completá los datos del proveedor'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-5">
          {errors.general && (
            <div className="rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-700">
              {errors.general}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            {/* RUC */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                RUC <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="ruc"
                value={formData.ruc}
                onChange={handleChange}
                disabled={isEditing}
                maxLength={20}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 ${
                  isEditing ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : ''
                } ${errors.ruc ? 'border-red-500' : 'border-gray-300'}`}
                placeholder="12345678-9"
              />
              {errors.ruc && <p className="mt-1 text-xs text-red-600">{errors.ruc}</p>}
            </div>

            {/* Ciudad */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Ciudad</label>
              <input
                type="text"
                name="ciudad"
                value={formData.ciudad ?? ''}
                onChange={handleChange}
                maxLength={100}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="Asunción"
              />
            </div>
          </div>

          {/* Razón Social */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Razón Social <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="razon_social"
              value={formData.razon_social}
              onChange={handleChange}
              maxLength={255}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 ${
                errors.razon_social ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Distribuidora S.A."
            />
            {errors.razon_social && <p className="mt-1 text-xs text-red-600">{errors.razon_social}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Teléfono */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Teléfono</label>
              <input
                type="text"
                name="telefono"
                value={formData.telefono ?? ''}
                onChange={handleChange}
                maxLength={20}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="0981-123456"
              />
            </div>

            {/* Email */}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                name="email"
                value={formData.email ?? ''}
                onChange={handleChange}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 ${
                  errors.email ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="proveedor@email.com"
              />
              {errors.email && <p className="mt-1 text-xs text-red-600">{errors.email}</p>}
            </div>
          </div>

          {/* Dirección */}
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Dirección</label>
            <input
              type="text"
              name="direccion"
              value={formData.direccion ?? ''}
              onChange={handleChange}
              maxLength={255}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
              placeholder="Av. Mcal. López 123"
            />
          </div>

          {/* Estado */}
          <div className="flex items-center gap-3 rounded-lg bg-gray-50 p-3">
            <input
              type="checkbox"
              id="estado"
              name="estado"
              checked={formData.estado}
              onChange={handleChange}
              className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
            />
            <label htmlFor="estado" className="text-sm font-medium text-gray-700">
              Proveedor activo
            </label>
          </div>

          <div className="flex gap-3 border-t pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving} className="flex-1">
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={saving}
              leftIcon={saving ? <Spinner size="sm" /> : <Save className="h-4 w-4" />}
              className="flex-1"
            >
              {saving ? 'Guardando...' : isEditing ? 'Guardar Cambios' : 'Crear Proveedor'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ── Página principal ───────────────────────────────────────────────────────────

const Proveedores: React.FC = () => {
  const [proveedores, setProveedores] = useState<Proveedor[]>([]);
  const [loading, setLoading] = useState(true);
  const [busqueda, setBusqueda] = useState('');
  const [filtroEstado, setFiltroEstado] = useState<'todos' | 'activos' | 'inactivos'>('activos');
  const [modalOpen, setModalOpen] = useState(false);
  const [proveedorSeleccionado, setProveedorSeleccionado] = useState<Proveedor | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  const cargarProveedores = useCallback(async () => {
    setLoading(true);
    try {
      const params: ProveedorParams = { page_size: 100, ordering: 'razon_social' };
      if (busqueda.trim()) params.search = busqueda.trim();
      if (filtroEstado === 'activos') params.estado = true;
      if (filtroEstado === 'inactivos') params.estado = false;

      const response = await comprasService.getProveedores(params);
      const lista = response.results ?? (response as unknown as Proveedor[]);
      setProveedores(lista);
      setTotalCount(response.count ?? lista.length);
    } catch {
      toast.error('Error al cargar proveedores');
    } finally {
      setLoading(false);
    }
  }, [busqueda, filtroEstado]);

  useEffect(() => {
    const timer = setTimeout(cargarProveedores, busqueda ? 400 : 0);
    return () => clearTimeout(timer);
  }, [cargarProveedores, busqueda]);

  const handleNuevo = () => {
    setProveedorSeleccionado(null);
    setModalOpen(true);
  };

  const handleEditar = (p: Proveedor) => {
    setProveedorSeleccionado(p);
    setModalOpen(true);
  };

  const handleToggleEstado = async (p: Proveedor) => {
    try {
      await comprasService.toggleEstadoProveedor(p.id_proveedor, !p.estado);
      toast.success(`Proveedor ${p.estado ? 'desactivado' : 'activado'}`);
      cargarProveedores();
    } catch {
      toast.error('Error al cambiar el estado');
    }
  };

  const handleEliminar = async (p: Proveedor) => {
    if (!window.confirm(`¿Eliminar a ${p.razon_social}? Esta acción no se puede deshacer.`)) return;
    try {
      await comprasService.eliminarProveedor(p.id_proveedor);
      toast.success('Proveedor eliminado');
      cargarProveedores();
    } catch (error: any) {
      const msg = error.response?.data?.detail || 'No se puede eliminar: tiene compras asociadas.';
      toast.error(msg);
    }
  };

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Proveedores</h1>
          <p className="mt-1 text-sm text-gray-600">
            Administrá la información de tus proveedores
          </p>
        </div>
        <Button onClick={handleNuevo} leftIcon={<Plus className="h-4 w-4" />}>
          Nuevo Proveedor
        </Button>
      </div>

      {/* Filtros */}
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
              placeholder="Buscar por razón social, RUC o email..."
              className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>
          <div className="flex gap-2">
            {(['todos', 'activos', 'inactivos'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFiltroEstado(f)}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  filtroEstado === f
                    ? 'bg-amber-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Lista */}
      <Card>
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : proveedores.length === 0 ? (
          <div className="py-16 text-center">
            <Building2 className="mx-auto h-12 w-12 text-gray-300" />
            <p className="mt-4 text-gray-500">No hay proveedores registrados</p>
            <Button onClick={handleNuevo} leftIcon={<Plus className="h-4 w-4" />} className="mt-4">
              Agregar Primer Proveedor
            </Button>
          </div>
        ) : (
          <>
            <p className="mb-4 text-sm text-gray-500">
              {totalCount} proveedor{totalCount !== 1 ? 'es' : ''} encontrado{totalCount !== 1 ? 's' : ''}
            </p>
            <div className="divide-y divide-gray-100">
              {proveedores.map(p => (
                <div
                  key={p.id_proveedor}
                  className="flex items-center justify-between gap-4 py-4 first:pt-0 last:pb-0"
                >
                  {/* Info */}
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-amber-50 border border-amber-200">
                      <Building2 className="h-5 w-5 text-amber-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-gray-900 truncate">{p.razon_social}</span>
                        <Badge variant={p.estado ? 'success' : 'danger'}>
                          {p.estado ? 'Activo' : 'Inactivo'}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-500">RUC: {p.ruc}</p>
                      <div className="mt-1 flex flex-wrap gap-3 text-xs text-gray-500">
                        {p.telefono && (
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" /> {p.telefono}
                          </span>
                        )}
                        {p.email && (
                          <span className="flex items-center gap-1">
                            <Mail className="h-3 w-3" /> {p.email}
                          </span>
                        )}
                        {p.ciudad && (
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3 w-3" /> {p.ciudad}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Acciones */}
                  <div className="flex flex-shrink-0 items-center gap-2">
                    <button
                      onClick={() => handleEditar(p)}
                      className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      <Edit className="h-3.5 w-3.5" />
                      Editar
                    </button>
                    <button
                      onClick={() => handleToggleEstado(p)}
                      className={`flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                        p.estado
                          ? 'border-orange-200 text-orange-700 hover:bg-orange-50'
                          : 'border-green-200 text-green-700 hover:bg-green-50'
                      }`}
                    >
                      {p.estado ? (
                        <><XCircle className="h-3.5 w-3.5" /> Desactivar</>
                      ) : (
                        <><CheckCircle className="h-3.5 w-3.5" /> Activar</>
                      )}
                    </button>
                    <button
                      onClick={() => handleEliminar(p)}
                      className="flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </Card>

      {/* Modal */}
      {modalOpen && (
        <ProveedorModal
          proveedor={proveedorSeleccionado}
          onClose={() => { setModalOpen(false); setProveedorSeleccionado(null); }}
          onSave={() => { setModalOpen(false); setProveedorSeleccionado(null); cargarProveedores(); }}
        />
      )}
    </div>
  );
};

export default Proveedores;
