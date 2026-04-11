import React, { useState, useEffect, useCallback } from 'react';
import { Globe, Plus, Pencil, Trash2, X, Check, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';
import { paisesService } from '../../services/clientes.service';
import type { Pais } from '../../types';

const GestionPaises: React.FC = () => {
  const [paises, setPaises] = useState<Pais[]>([]);
  const [loading, setLoading] = useState(true);
  const [nombre, setNombre] = useState('');
  const [editId, setEditId] = useState<number | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [eliminandoId, setEliminandoId] = useState<number | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      setPaises(await paisesService.getPaises());
    } catch {
      toast.error('Error cargando países');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const abrirNuevo = () => { setNombre(''); setEditId(null); setMostrarForm(true); };

  const abrirEditar = (p: Pais) => { setNombre(p.nombre); setEditId(p.id_pais); setMostrarForm(true); };

  const cancelar = () => { setMostrarForm(false); setNombre(''); setEditId(null); };

  const guardar = async () => {
    if (!nombre.trim()) { toast.error('Ingrese un nombre'); return; }
    try {
      if (editId !== null) {
        await paisesService.actualizar(editId, nombre.trim());
        toast.success('País actualizado');
      } else {
        await paisesService.crear(nombre.trim());
        toast.success('País creado');
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
      await paisesService.eliminar(id);
      toast.success('País eliminado');
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
          <Globe className="w-8 h-8 text-indigo-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Países</h1>
            <p className="text-sm text-gray-500">Catálogo de países para clientes y proveedores</p>
          </div>
        </div>
        {!mostrarForm && (
          <button
            onClick={abrirNuevo}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition-colors"
          >
            <Plus className="w-4 h-4" /> Nuevo país
          </button>
        )}
      </div>

      {/* Formulario inline */}
      {mostrarForm && (
        <div className="bg-white border border-indigo-200 rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-3">
            {editId ? 'Editar país' : 'Nuevo país'}
          </h3>
          <div className="flex gap-3 items-end">
            <label className="flex-1 block text-sm text-gray-600">
              Nombre *
              <input
                value={nombre}
                onChange={e => setNombre(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && guardar()}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-400 focus:outline-none"
                placeholder="ej: Paraguay"
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
            {paises.length === 0 ? (
              <tr>
                <td colSpan={3} className="text-center py-10 text-gray-400">
                  No hay países registrados
                </td>
              </tr>
            ) : (
              paises.map(p => (
                <tr key={p.id_pais} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400">{p.id_pais}</td>
                  <td className="px-4 py-3 font-medium text-gray-800">{p.nombre}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => abrirEditar(p)}
                        className="p-1.5 rounded hover:bg-indigo-100 text-indigo-600 transition-colors"
                        title="Editar"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEliminar(p.id_pais)}
                        className={`p-1.5 rounded transition-colors ${
                          eliminandoId === p.id_pais
                            ? 'bg-red-100 text-red-700'
                            : 'hover:bg-red-100 text-red-500'
                        }`}
                        title={eliminandoId === p.id_pais ? 'Clic de nuevo para confirmar' : 'Eliminar'}
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
      <p className="text-xs text-gray-400">{paises.length} registro(s)</p>
    </div>
  );
};

export default GestionPaises;
