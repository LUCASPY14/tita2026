import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { CreditCard, Plus, Pencil, ToggleLeft, ToggleRight, X, Check, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

interface MedioPago {
  id_medio_pago: number;
  descripcion: string;
  genera_comision: boolean;
  requiere_validacion: boolean;
  estado: boolean;
}

const EMPTY: Omit<MedioPago, 'id_medio_pago'> = {
  descripcion: '',
  genera_comision: false,
  requiere_validacion: false,
  estado: true,
};

const GestionMediosPago: React.FC = () => {
  const [medios, setMedios] = useState<MedioPago[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<Omit<MedioPago, 'id_medio_pago'>>(EMPTY);
  const [editId, setEditId] = useState<number | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/medios-pago/');
      const data = res.data.results ?? res.data;
      setMedios(Array.isArray(data) ? data : []);
    } catch {
      toast.error('Error cargando medios de pago');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const abrirNuevo = () => {
    setForm(EMPTY);
    setEditId(null);
    setMostrarForm(true);
  };

  const abrirEditar = (m: MedioPago) => {
    setForm({ descripcion: m.descripcion, genera_comision: m.genera_comision, requiere_validacion: m.requiere_validacion, estado: m.estado });
    setEditId(m.id_medio_pago);
    setMostrarForm(true);
  };

  const guardar = async () => {
    if (!form.descripcion.trim()) { toast.error('Ingrese una descripción'); return; }
    try {
      if (editId !== null) {
        await api.patch(`/medios-pago/${editId}/`, form);
        toast.success('Medio de pago actualizado');
      } else {
        await api.post('/medios-pago/', form);
        toast.success('Medio de pago creado');
      }
      setMostrarForm(false);
      cargar();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al guardar');
    }
  };

  const toggleEstado = async (m: MedioPago) => {
    try {
      await api.patch(`/medios-pago/${m.id_medio_pago}/`, { estado: !m.estado });
      toast.success(m.estado ? 'Desactivado' : 'Activado');
      cargar();
    } catch {
      toast.error('Error al cambiar estado');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-indigo-500 w-6 h-6" /></div>;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CreditCard className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Medios de Pago</h1>
            <p className="text-sm text-gray-500">Configurá los métodos de pago aceptados en ventas y recargas</p>
          </div>
        </div>
        <button
          onClick={abrirNuevo}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-4 h-4" /> Nuevo medio
        </button>
      </div>

      {/* Formulario inline */}
      {mostrarForm && (
        <div className="bg-white border border-indigo-200 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">{editId ? 'Editar medio de pago' : 'Nuevo medio de pago'}</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="block text-sm text-gray-600 md:col-span-1">
              Descripción *
              <input
                value={form.descripcion}
                onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                placeholder="ej: Efectivo"
                maxLength={50}
              />
            </label>
            <div className="flex flex-col gap-3 justify-center">
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.genera_comision}
                  onChange={e => setForm(f => ({ ...f, genera_comision: e.target.checked }))}
                  className="w-4 h-4 rounded text-indigo-600"
                />
                Genera comisión
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.requiere_validacion}
                  onChange={e => setForm(f => ({ ...f, requiere_validacion: e.target.checked }))}
                  className="w-4 h-4 rounded text-indigo-600"
                />
                Requiere validación
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.estado}
                  onChange={e => setForm(f => ({ ...f, estado: e.target.checked }))}
                  className="w-4 h-4 rounded text-indigo-600"
                />
                Activo
              </label>
            </div>
            <div className="flex items-end gap-2">
              <button onClick={guardar} className="flex items-center gap-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm">
                <Check className="w-4 h-4" /> Guardar
              </button>
              <button onClick={() => setMostrarForm(false)} className="flex items-center gap-1 border px-4 py-2 rounded-lg hover:bg-gray-50 text-sm">
                <X className="w-4 h-4" /> Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabla */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-gray-600 text-left">
              <th className="px-5 py-3">Descripción</th>
              <th className="px-5 py-3 text-center">Comisión</th>
              <th className="px-5 py-3 text-center">Validación</th>
              <th className="px-5 py-3 text-center">Estado</th>
              <th className="px-5 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {medios.map(m => (
              <tr key={m.id_medio_pago} className="border-t hover:bg-gray-50 transition-colors">
                <td className="px-5 py-3 font-medium text-gray-800">{m.descripcion}</td>
                <td className="px-5 py-3 text-center">
                  {m.genera_comision
                    ? <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Sí</span>
                    : <span className="text-xs text-gray-400">No</span>}
                </td>
                <td className="px-5 py-3 text-center">
                  {m.requiere_validacion
                    ? <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">Sí</span>
                    : <span className="text-xs text-gray-400">No</span>}
                </td>
                <td className="px-5 py-3 text-center">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${m.estado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {m.estado ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="px-5 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => abrirEditar(m)} className="p-1.5 rounded hover:bg-indigo-50 text-indigo-600" title="Editar">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => toggleEstado(m)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500" title={m.estado ? 'Desactivar' : 'Activar'}>
                      {m.estado ? <ToggleRight className="w-4 h-4 text-green-600" /> : <ToggleLeft className="w-4 h-4" />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {medios.length === 0 && (
              <tr><td colSpan={5} className="px-5 py-10 text-center text-gray-400">No hay medios de pago. Creá el primero.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default GestionMediosPago;
