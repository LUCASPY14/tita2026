import React, { useState, useEffect } from 'react';
import { ShieldAlert, Plus, Pencil, Trash2, AlertTriangle, X, Save } from 'lucide-react';
import { Modal, Button, Spinner } from '../../../components/common';
import { restriccionesService, type RestriccionHijoDetalle, type RestriccionHijoData } from '../../../services/clientes.service';
import type { Hijo } from '../../../types';

interface RestriccionesHijoModalProps {
  hijo: Hijo;
  onClose: () => void;
}

const SEVERIDADES = ['Baja', 'Media', 'Alta', 'Crítica'] as const;

const severidadStyle: Record<string, string> = {
  crítica: 'bg-red-100 text-red-800 border border-red-300',
  critica: 'bg-red-100 text-red-800 border border-red-300',
  alta: 'bg-orange-100 text-orange-800 border border-orange-200',
  media: 'bg-yellow-50 text-yellow-800 border border-yellow-200',
  baja: 'bg-blue-50 text-blue-700 border border-blue-200',
};

const severidadBadge: Record<string, string> = {
  crítica: 'bg-red-200 text-red-900',
  critica: 'bg-red-200 text-red-900',
  alta: 'bg-orange-200 text-orange-900',
  media: 'bg-yellow-200 text-yellow-900',
  baja: 'bg-blue-100 text-blue-800',
};

const FORM_EMPTY: RestriccionHijoData = {
  id_hijo: 0,
  tipo_restriccion: '',
  descripcion: '',
  observaciones: '',
  severidad: 'Media',
  requiere_autorizacion: false,
  estado: true,
};

const RestriccionesHijoModal: React.FC<RestriccionesHijoModalProps> = ({ hijo, onClose }) => {
  const [restricciones, setRestricciones] = useState<RestriccionHijoDetalle[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [showForm, setShowForm] = useState(false);
  const [editando, setEditando] = useState<RestriccionHijoDetalle | null>(null);
  const [form, setForm] = useState<RestriccionHijoData>({ ...FORM_EMPTY, id_hijo: hijo.id_hijo });

  const cargar = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await restriccionesService.getByHijo(hijo.id_hijo);
      setRestricciones(data);
    } catch {
      setError('Error al cargar las restricciones');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargar();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hijo.id_hijo]);

  const abrirNuevo = () => {
    setEditando(null);
    setForm({ ...FORM_EMPTY, id_hijo: hijo.id_hijo });
    setShowForm(true);
  };

  const abrirEditar = (r: RestriccionHijoDetalle) => {
    setEditando(r);
    setForm({
      id_hijo: hijo.id_hijo,
      tipo_restriccion: r.tipo_restriccion,
      descripcion: r.descripcion || '',
      observaciones: r.observaciones || '',
      severidad: r.severidad,
      requiere_autorizacion: r.requiere_autorizacion,
      estado: r.estado,
    });
    setShowForm(true);
  };

  const cancelarForm = () => {
    setShowForm(false);
    setEditando(null);
    setForm({ ...FORM_EMPTY, id_hijo: hijo.id_hijo });
  };

  const guardar = async () => {
    if (!form.tipo_restriccion.trim()) return;
    setSaving(true);
    setError(null);
    try {
      if (editando) {
        await restriccionesService.actualizar(editando.id_restriccion, form);
      } else {
        await restriccionesService.crear(form);
      }
      await cargar();
      cancelarForm();
    } catch {
      setError('Error al guardar la restricción');
    } finally {
      setSaving(false);
    }
  };

  const eliminar = async (id: number) => {
    setDeleting(id);
    setError(null);
    try {
      await restriccionesService.eliminar(id);
      setRestricciones(prev => prev.filter(r => r.id_restriccion !== id));
    } catch {
      setError('Error al eliminar la restricción');
    } finally {
      setDeleting(null);
    }
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      size="lg"
      title={`Restricciones de compra`}
      subtitle={`${hijo.nombre} ${hijo.apellido}`}
    >
      <div className="space-y-4">
        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Lista */}
        {loading ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : restricciones.length === 0 && !showForm ? (
          <div className="text-center py-8 text-gray-500">
            <ShieldAlert className="h-10 w-10 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">Sin restricciones registradas</p>
          </div>
        ) : (
          <div className="space-y-2">
            {restricciones.map(r => {
              const sev = r.severidad.toLowerCase();
              return (
                <div
                  key={r.id_restriccion}
                  className={`flex items-start gap-3 px-4 py-3 rounded-lg ${severidadStyle[sev] ?? 'bg-gray-50 border border-gray-200'}`}
                >
                  <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold">{r.tipo_restriccion}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${severidadBadge[sev] ?? 'bg-gray-200 text-gray-800'}`}>
                        {r.severidad}
                      </span>
                      {r.requiere_autorizacion && (
                        <span className="text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-800 font-medium">
                          Req. autorización
                        </span>
                      )}
                    </div>
                    {r.descripcion && (
                      <p className="text-sm mt-0.5 opacity-90">{r.descripcion}</p>
                    )}
                    {r.observaciones && (
                      <p className="text-xs mt-0.5 opacity-70">{r.observaciones}</p>
                    )}
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button
                      onClick={() => abrirEditar(r)}
                      className="p-1.5 rounded hover:bg-white/60 transition-colors"
                      title="Editar"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => eliminar(r.id_restriccion)}
                      disabled={deleting === r.id_restriccion}
                      className="p-1.5 rounded hover:bg-white/60 transition-colors disabled:opacity-50"
                      title="Eliminar"
                    >
                      {deleting === r.id_restriccion
                        ? <Spinner className="h-3.5 w-3.5" />
                        : <Trash2 className="h-3.5 w-3.5" />}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Formulario de agregar/editar */}
        {showForm ? (
          <div className="border border-gray-200 rounded-lg p-4 space-y-3 bg-gray-50">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-sm font-semibold text-gray-700">
                {editando ? 'Editar restricción' : 'Nueva restricción'}
              </h4>
              <button onClick={cancelarForm} className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* tipo_restriccion */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Restricción <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={form.tipo_restriccion}
                onChange={e => setForm(f => ({ ...f, tipo_restriccion: e.target.value }))}
                placeholder="Ej: Coca Cola, Frituras, Mariscos…"
                className="w-full text-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400"
              />
            </div>

            {/* descripcion + severidad */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Detalle</label>
                <input
                  type="text"
                  value={form.descripcion}
                  onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
                  placeholder="Información adicional"
                  className="w-full text-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Severidad</label>
                <select
                  value={form.severidad}
                  onChange={e => setForm(f => ({ ...f, severidad: e.target.value }))}
                  className="w-full text-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400 bg-white"
                >
                  {SEVERIDADES.map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* observaciones */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Observaciones</label>
              <textarea
                value={form.observaciones}
                onChange={e => setForm(f => ({ ...f, observaciones: e.target.value }))}
                placeholder="Notas médicas u otras observaciones"
                rows={2}
                className="w-full text-sm px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-400 resize-none"
              />
            </div>

            {/* requiere_autorizacion */}
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={form.requiere_autorizacion}
                onChange={e => setForm(f => ({ ...f, requiere_autorizacion: e.target.checked }))}
                className="rounded border-gray-300 text-orange-500 focus:ring-orange-400"
              />
              Requiere autorización para excepciones
            </label>

            <div className="flex gap-2 pt-1">
              <Button
                size="sm"
                onClick={guardar}
                disabled={saving || !form.tipo_restriccion.trim()}
                leftIcon={saving ? <Spinner className="h-3 w-3" /> : <Save className="h-3 w-3" />}
                className="bg-orange-500 hover:bg-orange-600 text-white"
              >
                {saving ? 'Guardando…' : 'Guardar'}
              </Button>
              <Button size="sm" variant="outline" onClick={cancelarForm}>
                Cancelar
              </Button>
            </div>
          </div>
        ) : (
          <Button
            size="sm"
            variant="outline"
            onClick={abrirNuevo}
            leftIcon={<Plus className="h-4 w-4" />}
            className="border-orange-400 text-orange-600 hover:bg-orange-50"
          >
            Agregar restricción
          </Button>
        )}
      </div>
    </Modal>
  );
};

export default RestriccionesHijoModal;
