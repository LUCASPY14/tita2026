import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { Mail, Pencil, ToggleLeft, ToggleRight, X, Check, RefreshCw, ChevronDown, ChevronUp, Eye } from 'lucide-react';
import toast from 'react-hot-toast';

interface PlantillaEmail {
  id_template: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
  asunto: string;
  cuerpo_html: string;
  cuerpo_texto: string | null;
  variables: string[];
  categoria: string;
  estado: boolean;
  created_at: string;
  updated_at: string;
}

type Tab = 'asunto' | 'html' | 'texto';

const CATEGORIAS = ['transaccional', 'alertas', 'marketing', 'sistema'];

const BadgeCategoria: React.FC<{ cat: string }> = ({ cat }) => {
  const colors: Record<string, string> = {
    transaccional: 'bg-blue-100 text-blue-700',
    alertas: 'bg-orange-100 text-orange-700',
    marketing: 'bg-purple-100 text-purple-700',
    sistema: 'bg-gray-100 text-gray-700',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${colors[cat] ?? 'bg-gray-100 text-gray-600'}`}>
      {cat}
    </span>
  );
};

const GestionPlantillasEmail: React.FC = () => {
  const [plantillas, setPlantillas] = useState<PlantillaEmail[]>([]);
  const [loading, setLoading] = useState(true);
  const [editando, setEditando] = useState<PlantillaEmail | null>(null);
  const [tab, setTab] = useState<Tab>('asunto');
  const [expandido, setExpandido] = useState<number | null>(null);
  const [vistaPrevia, setVistaPrevia] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/plantillas-email/');
      const data = res.data.results ?? res.data;
      setPlantillas(Array.isArray(data) ? data : []);
    } catch {
      toast.error('Error cargando plantillas');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const abrirEdicion = (p: PlantillaEmail) => {
    setEditando({ ...p });
    setTab('asunto');
  };

  const guardar = async () => {
    if (!editando) return;
    try {
      await api.patch(`/plantillas-email/${editando.id_template}/`, {
        nombre: editando.nombre,
        descripcion: editando.descripcion,
        asunto: editando.asunto,
        cuerpo_html: editando.cuerpo_html,
        cuerpo_texto: editando.cuerpo_texto,
        categoria: editando.categoria,
        estado: editando.estado,
      });
      toast.success('Plantilla guardada');
      setEditando(null);
      cargar();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al guardar');
    }
  };

  const toggleEstado = async (p: PlantillaEmail) => {
    try {
      await api.patch(`/plantillas-email/${p.id_template}/`, { estado: !p.estado });
      toast.success(p.estado ? 'Plantilla desactivada' : 'Plantilla activada');
      cargar();
    } catch {
      toast.error('Error al cambiar estado');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-blue-500 w-6 h-6" /></div>;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Mail className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Plantillas de Email</h1>
          <p className="text-sm text-gray-500">Editá el asunto y cuerpo de los emails transaccionales del sistema</p>
        </div>
      </div>

      {/* Editor de plantilla */}
      {editando && (
        <div className="bg-white border border-blue-200 rounded-xl shadow-sm">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="font-semibold text-gray-800">Editando: {editando.nombre}</h3>
            <div className="flex gap-2">
              <button
                onClick={() => setVistaPrevia(editando.cuerpo_html)}
                className="flex items-center gap-1 text-sm px-3 py-1.5 border rounded-lg hover:bg-blue-50 text-blue-600"
              >
                <Eye className="w-4 h-4" /> Vista previa
              </button>
              <button onClick={guardar} className="flex items-center gap-1 bg-blue-600 text-white text-sm px-3 py-1.5 rounded-lg hover:bg-blue-700">
                <Check className="w-4 h-4" /> Guardar
              </button>
              <button onClick={() => setEditando(null)} className="flex items-center gap-1 border text-sm px-3 py-1.5 rounded-lg hover:bg-gray-50">
                <X className="w-4 h-4" /> Cancelar
              </button>
            </div>
          </div>

          <div className="p-4 space-y-4">
            {/* Nombre y categoría */}
            <div className="grid grid-cols-2 gap-4">
              <label className="block text-sm text-gray-600">
                Nombre
                <input
                  value={editando.nombre}
                  onChange={e => setEditando(p => p ? { ...p, nombre: e.target.value } : p)}
                  className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none text-sm"
                />
              </label>
              <label className="block text-sm text-gray-600">
                Categoría
                <select
                  value={editando.categoria}
                  onChange={e => setEditando(p => p ? { ...p, categoria: e.target.value } : p)}
                  className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none text-sm"
                >
                  {CATEGORIAS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
            </div>

            {/* Tabs: asunto / html / texto */}
            <div className="border-b flex gap-1">
              {(['asunto', 'html', 'texto'] as Tab[]).map(t => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors capitalize ${tab === t ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-800'}`}
                >
                  {t === 'html' ? 'Cuerpo HTML' : t === 'texto' ? 'Cuerpo Texto' : 'Asunto'}
                </button>
              ))}
            </div>

            {tab === 'asunto' && (
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Asunto del email
                  <span className="ml-2 text-xs text-gray-400">Variables: {'{{'} variable {'}}' }</span>
                </label>
                <input
                  value={editando.asunto}
                  onChange={e => setEditando(p => p ? { ...p, asunto: e.target.value } : p)}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none text-sm"
                  placeholder="ej: Confirmación de recarga — {{nombre_cliente}}"
                />
                {editando.variables?.length > 0 && (
                  <p className="mt-2 text-xs text-gray-500">
                    Variables disponibles: {editando.variables.map(v => (
                      <code key={v} className="mx-0.5 bg-gray-100 px-1 py-0.5 rounded">{v}</code>
                    ))}
                  </p>
                )}
              </div>
            )}

            {tab === 'html' && (
              <div>
                <label className="block text-sm text-gray-600 mb-1">Cuerpo HTML</label>
                <textarea
                  value={editando.cuerpo_html}
                  onChange={e => setEditando(p => p ? { ...p, cuerpo_html: e.target.value } : p)}
                  rows={16}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none text-sm font-mono"
                  spellCheck={false}
                />
              </div>
            )}

            {tab === 'texto' && (
              <div>
                <label className="block text-sm text-gray-600 mb-1">Cuerpo en texto plano (para clientes sin HTML)</label>
                <textarea
                  value={editando.cuerpo_texto ?? ''}
                  onChange={e => setEditando(p => p ? { ...p, cuerpo_texto: e.target.value } : p)}
                  rows={12}
                  className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-400 focus:outline-none text-sm font-mono"
                  spellCheck={false}
                />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Vista previa HTML */}
      {vistaPrevia && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-white rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold">Vista previa HTML</h3>
              <button onClick={() => setVistaPrevia(null)} className="p-1.5 rounded hover:bg-gray-100">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-2">
              <iframe
                srcDoc={vistaPrevia}
                title="Vista previa"
                className="w-full h-full min-h-[500px] border-0 rounded"
                sandbox="allow-same-origin"
              />
            </div>
          </div>
        </div>
      )}

      {/* Lista de plantillas por categoría */}
      {CATEGORIAS.map(cat => {
        const grupo = plantillas.filter(p => p.categoria === cat);
        if (grupo.length === 0) return null;
        return (
          <div key={cat} className="bg-white rounded-xl border shadow-sm overflow-hidden">
            <div className="bg-gray-50 px-5 py-3 border-b flex items-center gap-2">
              <BadgeCategoria cat={cat} />
              <span className="text-sm text-gray-500">{grupo.length} plantilla{grupo.length !== 1 ? 's' : ''}</span>
            </div>
            {grupo.map(p => (
              <div key={p.id_template} className="border-t first:border-t-0">
                <div className="flex items-center justify-between px-5 py-3 hover:bg-gray-50">
                  <div>
                    <p className="font-medium text-gray-800">{p.nombre}</p>
                    <p className="text-xs text-gray-400 font-mono">{p.codigo}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${p.estado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                      {p.estado ? 'Activa' : 'Inactiva'}
                    </span>
                    <button onClick={() => abrirEdicion(p)} className="p-1.5 rounded hover:bg-blue-50 text-blue-600" title="Editar">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => toggleEstado(p)} className="p-1.5 rounded hover:bg-gray-100 text-gray-500" title={p.estado ? 'Desactivar' : 'Activar'}>
                      {p.estado ? <ToggleRight className="w-4 h-4 text-green-600" /> : <ToggleLeft className="w-4 h-4" />}
                    </button>
                    <button onClick={() => setExpandido(expandido === p.id_template ? null : p.id_template)} className="p-1.5 rounded hover:bg-gray-100 text-gray-400">
                      {expandido === p.id_template ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                {expandido === p.id_template && (
                  <div className="px-5 py-3 bg-gray-50 border-t text-sm text-gray-600 space-y-1">
                    <p><span className="font-medium">Asunto:</span> {p.asunto}</p>
                    {p.descripcion && <p className="text-gray-400">{p.descripcion}</p>}
                    {p.variables?.length > 0 && (
                      <p>
                        <span className="font-medium">Variables:</span>{' '}
                        {p.variables.map(v => (
                          <code key={v} className="mx-0.5 bg-white border px-1 py-0.5 rounded text-xs">{v}</code>
                        ))}
                      </p>
                    )}
                    <p className="text-xs text-gray-400">Actualizado: {new Date(p.updated_at).toLocaleString('es-PY')}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        );
      })}

      {plantillas.length === 0 && (
        <p className="text-center text-gray-400 py-12">No hay plantillas de email registradas.</p>
      )}
    </div>
  );
};

export default GestionPlantillasEmail;
