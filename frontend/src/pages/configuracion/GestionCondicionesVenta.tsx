import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Plus, Pencil, Trash2, X, Check, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { condicionesVentaService } from '../../services/ventas.service';
import type { CondicionVenta } from '../../types';

const GestionCondicionesVenta: React.FC = () => {
  const [condiciones, setCondiciones] = useState<CondicionVenta[]>([]);
  const [loading, setLoading] = useState(true);
  const [nombre, setNombre] = useState('');
  const [editId, setEditId] = useState<number | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [eliminandoId, setEliminandoId] = useState<number | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      setCondiciones(await condicionesVentaService.getCondicionesVenta());
    } catch {
      toast.error('Error cargando condiciones de venta');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const abrirNuevo = () => { setNombre(''); setEditId(null); setMostrarForm(true); };

  const abrirEditar = (c: CondicionVenta) => { setNombre(c.nombre); setEditId(c.id_condicion_venta); setMostrarForm(true); };

  const cancelar = () => { setMostrarForm(false); setNombre(''); setEditId(null); };

  const guardar = async () => {
    if (!nombre.trim()) { toast.error('Ingrese un nombre'); return; }
    try {
      if (editId !== null) {
        await condicionesVentaService.actualizar(editId, nombre.trim());
        toast.success('Condición de venta actualizada');
      } else {
        await condicionesVentaService.crear(nombre.trim());
        toast.success('Condición de venta creada');
      }
      cancelar();
      cargar();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al guardar');
    }
  };

  const handleEliminar = async (id: number) => {
    if (eliminandoId !== id) { setEliminandoId(id); return; }
    try {
      await condicionesVentaService.eliminar(id);
      toast.success('Condición de venta eliminada');
      setEliminandoId(null);
      cargar();
    } catch {
      toast.error('No se puede eliminar. Puede tener registros relacionados.');
      setEliminandoId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <RefreshCw className="animate-spin text-indigo-500 w-6 h-6" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Condiciones de Venta</h1>
            <p className="text-sm text-gray-500">Catálogo de condiciones: contado, crédito 30 días, etc.</p>
          </div>
        </div>
        {!mostrarForm && (
          <button
            onClick={abrirNuevo}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" /> Nueva condición
          </button>
        )}
      </div>

      {/* Formulario inline */}
      {mostrarForm && (
        <div className="bg-white border border-indigo-200 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-3">
            {editId ? 'Editar condición de venta' : 'Nueva condición de venta'}
          </h3>
          <div className="flex gap-3 items-end">
            <label className="flex-1 block text-sm text-gray-600">
              Nombre *
              <input
                value={nombre}
                onChange={e => setNombre(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && guardar()}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                placeholder="ej: Contado"
                maxLength={100}
                autoFocus
              />
            </label>
            <button
              onClick={guardar}
              className="flex items-center gap-1 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition-colors"
            >
              <Check className="w-4 h-4" /> Guardar
            </button>
            <button
              onClick={cancelar}
              className="flex items-center gap-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300 transition-colors"
            >
              <X className="w-4 h-4" /> Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Tabla */}
      <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 text-left text-gray-600 font-medium border-b">
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">Nombre</th>
              <th className="px-4 py-3 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {condiciones.length === 0 ? (
              <tr>
                <td colSpan={3} className="text-center py-10 text-gray-400">
                  No hay condiciones de venta registradas
                </td>
              </tr>
            ) : (
              condiciones.map(c => (
                <tr key={c.id_condicion_venta} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400">{c.id_condicion_venta}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{c.nombre}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => abrirEditar(c)}
                        className="p-1.5 rounded hover:bg-indigo-100 text-indigo-600 transition-colors"
                        title="Editar"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEliminar(c.id_condicion_venta)}
                        className={`p-1.5 rounded transition-colors ${
                          eliminandoId === c.id_condicion_venta
                            ? 'bg-red-100 text-red-700'
                            : 'hover:bg-red-100 text-red-500'
                        }`}
                        title={eliminandoId === c.id_condicion_venta ? 'Clic de nuevo para confirmar' : 'Eliminar'}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-400">{condiciones.length} registro(s)</p>
    </div>
  );
};

export default GestionCondicionesVenta;
