import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { Percent, Plus, Pencil, ToggleLeft, ToggleRight, X, Check, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

interface Impuesto {
  id_impuesto: number;
  nombre_impuesto: string;
  porcentaje: string;
  vigente_desde: string;
  vigente_hasta: string | null;
  estado: boolean;
}

const EMPTY: Omit<Impuesto, 'id_impuesto'> = {
  nombre_impuesto: '',
  porcentaje: '10.00',
  vigente_desde: new Date().toISOString().split('T')[0],
  vigente_hasta: null,
  estado: true,
};

const GestionImpuestos: React.FC = () => {
  const [impuestos, setImpuestos] = useState<Impuesto[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<Omit<Impuesto, 'id_impuesto'>>(EMPTY);
  const [editId, setEditId] = useState<number | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/impuestos/');
      const data = res.data.results ?? res.data;
      setImpuestos(Array.isArray(data) ? data : []);
    } catch {
      toast.error('Error cargando impuestos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const abrirNuevo = () => {
    setForm({ ...EMPTY, vigente_desde: new Date().toISOString().split('T')[0] });
    setEditId(null);
    setMostrarForm(true);
  };

  const abrirEditar = (imp: Impuesto) => {
    setForm({
      nombre_impuesto: imp.nombre_impuesto,
      porcentaje: imp.porcentaje,
      vigente_desde: imp.vigente_desde,
      vigente_hasta: imp.vigente_hasta ?? null,
      estado: imp.estado,
    });
    setEditId(imp.id_impuesto);
    setMostrarForm(true);
  };

  const guardar = async () => {
    if (!form.nombre_impuesto.trim()) { toast.error('Ingrese un nombre'); return; }
    const payload = { ...form, vigente_hasta: form.vigente_hasta || null };
    try {
      if (editId !== null) {
        await api.patch(`/impuestos/${editId}/`, payload);
        toast.success('Impuesto actualizado');
      } else {
        await api.post('/impuestos/', payload);
        toast.success('Impuesto creado');
      }
      setMostrarForm(false);
      cargar();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al guardar');
    }
  };

  const toggleEstado = async (imp: Impuesto) => {
    try {
      await api.patch(`/impuestos/${imp.id_impuesto}/`, { estado: !imp.estado });
      toast.success(imp.estado ? 'Impuesto desactivado' : 'Impuesto activado');
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
          <Percent className="w-8 h-8 text-amber-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Impuestos y Tasas</h1>
            <p className="text-sm text-gray-500">IVA, Exentas y otras tasas aplicadas a productos y servicios</p>
          </div>
        </div>
        <button
          onClick={abrirNuevo}
          className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg text-sm hover:bg-amber-700 transition-colors"
        >
          <Plus className="w-4 h-4" /> Nuevo impuesto
        </button>
      </div>

      {/* Formulario inline */}
      {mostrarForm && (
        <div className="bg-white border border-amber-200 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">{editId ? 'Editar impuesto' : 'Nuevo impuesto'}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <label className="block text-sm text-gray-600">
              Nombre *
              <input
                value={form.nombre_impuesto}
                onChange={e => setForm(f => ({ ...f, nombre_impuesto: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-400 focus:outline-none"
                placeholder="ej: IVA 10%"
                maxLength={50}
              />
            </label>
            <label className="block text-sm text-gray-600">
              Porcentaje (%)
              <input
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={form.porcentaje}
                onChange={e => setForm(f => ({ ...f, porcentaje: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-400 focus:outline-none"
              />
            </label>
            <label className="block text-sm text-gray-600">
              Vigente desde *
              <input
                type="date"
                value={form.vigente_desde}
                onChange={e => setForm(f => ({ ...f, vigente_desde: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-400 focus:outline-none"
              />
            </label>
            <label className="block text-sm text-gray-600">
              Vigente hasta (opcional)
              <input
                type="date"
                value={form.vigente_hasta ?? ''}
                onChange={e => setForm(f => ({ ...f, vigente_hasta: e.target.value || null }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-amber-400 focus:outline-none"
              />
            </label>
          </div>
          <div className="flex items-center gap-4 mt-4">
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={form.estado}
                onChange={e => setForm(f => ({ ...f, estado: e.target.checked }))}
                className="w-4 h-4 rounded text-amber-600"
              />
              Activo
            </label>
            <button onClick={guardar} className="flex items-center gap-1 bg-amber-600 text-white px-4 py-2 rounded-lg hover:bg-amber-700 text-sm">
              <Check className="w-4 h-4" /> Guardar
            </button>
            <button onClick={() => setMostrarForm(false)} className="flex items-center gap-1 border px-4 py-2 rounded-lg hover:bg-gray-50 text-sm">
              <X className="w-4 h-4" /> Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Tabla */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-gray-600 text-left">
              <th className="px-5 py-3">Nombre</th>
              <th className="px-5 py-3 text-center">Porcentaje</th>
              <th className="px-5 py-3 text-center">Vigente desde</th>
              <th className="px-5 py-3 text-center">Vigente hasta</th>
              <th className="px-5 py-3 text-center">Estado</th>
              <th className="px-5 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {impuestos.map(imp => (
              <tr key={imp.id_impuesto} className="border-t hover:bg-gray-50 transition-colors">
                <td className="px-5 py-3 font-medium text-gray-800">{imp.nombre_impuesto}</td>
                <td className="px-5 py-3 text-center">
                  <span className="font-mono font-semibold text-amber-700">{parseFloat(imp.porcentaje).toFixed(1)}%</span>
                </td>
                <td className="px-5 py-3 text-center text-gray-600">{imp.vigente_desde}</td>
                <td className="px-5 py-3 text-center text-gray-400">{imp.vigente_hasta ?? '—'}</td>
                <td className="px-5 py-3 text-center">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${imp.estado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {imp.estado ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="px-5 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => abrirEditar(imp)} className="p-1.5 rounded hover:bg-amber-50 text-amber-600" title="Editar">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => toggleEstado(imp)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500" title={imp.estado ? 'Desactivar' : 'Activar'}>
                      {imp.estado ? <ToggleRight className="w-4 h-4 text-green-600" /> : <ToggleLeft className="w-4 h-4" />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {impuestos.length === 0 && (
              <tr><td colSpan={6} className="px-5 py-10 text-center text-gray-400">No hay impuestos. Creá el primero.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default GestionImpuestos;
