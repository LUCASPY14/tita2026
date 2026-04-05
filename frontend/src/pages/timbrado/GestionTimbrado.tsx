import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { FileText, Plus, CheckCircle, AlertTriangle, RefreshCw, Hash, Calendar } from 'lucide-react';
import toast from 'react-hot-toast';

interface PuntoExpedicion {
  id_punto: number;
  codigo_establecimiento: string;
  codigo_punto_expedicion: string;
  descripcion_ubicacion: string | null;
  estado: boolean;
}

interface Timbrado {
  nro_timbrado: number;
  tipo_documento: string;
  fecha_inicio: string;
  fecha_fin: string;
  nro_inicial: number;
  nro_final: number;
  estado: boolean;
  id_punto: number;
  punto_detalle: PuntoExpedicion | null;
  nro_disponibles: number;
}

interface DocumentoTributario {
  id_documento: number;
  nro_secuencial: number;
  nro_preimpreso_interno: string | null;
  tipo_documento: string;
  monto_total: string;
  fecha_emision: string;
  cliente_nombre: string | null;
}

interface NuevoTimbrado {
  nro_timbrado: string;
  tipo_documento: string;
  fecha_inicio: string;
  fecha_fin: string;
  nro_inicial: string;
  nro_final: string;
  id_punto: string;
}


const EMPTY_TIMBRADO: NuevoTimbrado = {
  nro_timbrado: '',
  tipo_documento: 'FACTURA',
  fecha_inicio: '',
  fecha_fin: '',
  nro_inicial: '1',
  nro_final: '999',
  id_punto: '',
};

const GestionTimbrado: React.FC = () => {
  const [timbrados, setTimbrados] = useState<Timbrado[]>([]);
  const [puntos, setPuntos] = useState<PuntoExpedicion[]>([]);
  const [documentos, setDocumentos] = useState<DocumentoTributario[]>([]);
  const [loading, setLoading] = useState(true);
  const [mostrarFormTimbrado, setMostrarFormTimbrado] = useState(false);
  const [mostrarFormPunto, setMostrarFormPunto] = useState(false);
  const [form, setForm] = useState<NuevoTimbrado>(EMPTY_TIMBRADO);
  const [formPunto, setFormPunto] = useState({ codigo_establecimiento: '001', codigo_punto_expedicion: '001', descripcion_ubicacion: '' });

  const cargarDatos = useCallback(async () => {
    setLoading(true);
    try {
      const [timbresRes, puntosRes, docsRes] = await Promise.all([
        api.get('/timbrados/'),
        api.get('/puntos-expedicion/'),
        api.get('/documentos-tributarios/?limit=20'),
      ]);
      setTimbrados(timbresRes.data.results ?? timbresRes.data);
      setPuntos(puntosRes.data.results ?? puntosRes.data);
      setDocumentos(docsRes.data.results ?? docsRes.data);
    } catch {
      toast.error('Error cargando datos de timbrado');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { cargarDatos(); }, [cargarDatos]);

  const crearTimbrado = async () => {
    if (!form.nro_timbrado || !form.fecha_inicio || !form.fecha_fin || !form.id_punto) {
      toast.error('Complete todos los campos obligatorios');
      return;
    }
    try {
      await api.post('/timbrados/', {
        ...form,
        nro_timbrado: parseInt(form.nro_timbrado),
        nro_inicial: parseInt(form.nro_inicial),
        nro_final: parseInt(form.nro_final),
        id_punto: parseInt(form.id_punto),
        estado: true,
      });
      toast.success('Timbrado registrado correctamente');
      setMostrarFormTimbrado(false);
      setForm(EMPTY_TIMBRADO);
      cargarDatos();
    } catch (err: any) {
      const detail = err.response?.data;
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail) ?? 'Error al registrar timbrado');
    }
  };

  const crearPunto = async () => {
    if (!formPunto.codigo_establecimiento || !formPunto.codigo_punto_expedicion) {
      toast.error('Ingrese los códigos del punto de expedición');
      return;
    }
    try {
      await api.post('/puntos-expedicion/', { ...formPunto, estado: true });
      toast.success('Punto de expedición creado');
      setMostrarFormPunto(false);
      setFormPunto({ codigo_establecimiento: '001', codigo_punto_expedicion: '001', descripcion_ubicacion: '' });
      cargarDatos();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al crear punto de expedición');
    }
  };

  const hoy = new Date().toISOString().split('T')[0];
  const timbradoVigente = timbrados.find(
    t => t.estado && t.fecha_inicio <= hoy && t.fecha_fin >= hoy
  );

  // Días hasta el vencimiento del timbrado vigente
  const diasParaVencer = timbradoVigente
    ? Math.ceil((new Date(timbradoVigente.fecha_fin).getTime() - new Date(hoy).getTime()) / 86400000)
    : null;

  const porcentajeUsado = (t: Timbrado) => {
    const total = t.nro_final - t.nro_inicial + 1;
    const usados = total - t.nro_disponibles;
    return total > 0 ? Math.round((usados / total) * 100) : 0;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-blue-500 w-8 h-8" />
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
            <h1 className="text-2xl font-bold text-gray-900">Timbrado y Facturación</h1>
            <p className="text-sm text-gray-500">Gestión de timbrados SET, puntos de expedición y documentos</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMostrarFormPunto(true)}
            className="flex items-center gap-1 px-3 py-2 border rounded-lg text-sm hover:bg-gray-50"
          >
            <Plus className="w-4 h-4" /> Punto expedición
          </button>
          <button
            onClick={() => setMostrarFormTimbrado(true)}
            className="flex items-center gap-1 px-3 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4" /> Nuevo timbrado
          </button>
        </div>
      </div>

      {/* Alerta vencimiento próximo */}
      {timbradoVigente && diasParaVencer !== null && diasParaVencer <= 30 && (
        <div className={`border rounded-xl p-4 flex items-center gap-3 ${diasParaVencer <= 5 ? 'bg-red-50 border-red-300' : 'bg-orange-50 border-orange-300'}`}>
          <AlertTriangle className={`w-6 h-6 flex-shrink-0 ${diasParaVencer <= 5 ? 'text-red-600' : 'text-orange-500'}`} />
          <div>
            <p className={`font-semibold ${diasParaVencer <= 5 ? 'text-red-800' : 'text-orange-800'}`}>
              {diasParaVencer <= 0
                ? 'Timbrado vencido hoy — registrá el nuevo timbrado SET urgente'
                : diasParaVencer === 1
                  ? 'El timbrado vence mañana — registrá el nuevo timbrado SET'
                  : `El timbrado vence en ${diasParaVencer} días (${timbradoVigente.fecha_fin})`}
            </p>
            <p className={`text-sm ${diasParaVencer <= 5 ? 'text-red-700' : 'text-orange-700'}`}>
              Solicitá el nuevo timbrado ante la SET y regístralo con el botón "Nuevo timbrado".
            </p>
          </div>
        </div>
      )}

      {/* Timbrado vigente banner */}
      {timbradoVigente ? (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-6 h-6 text-green-600" />
            <div>
              <p className="font-semibold text-green-800">Timbrado vigente activo</p>
              <p className="text-sm text-green-700">
                N° {timbradoVigente.nro_timbrado} — válido hasta {timbradoVigente.fecha_fin}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-green-700">{timbradoVigente.nro_disponibles} facturas disponibles</p>
            <div className="w-32 bg-green-200 rounded-full h-2 mt-1">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: `${100 - porcentajeUsado(timbradoVigente)}%` }}
              />
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <AlertTriangle className="w-6 h-6 text-red-600" />
          <div>
            <p className="font-semibold text-red-800">Sin timbrado vigente</p>
            <p className="text-sm text-red-700">
              No hay timbrado físico activo. Las ventas no generarán facturas hasta que configure uno.
            </p>
          </div>
        </div>
      )}

      {/* Formulario nuevo timbrado */}
      {mostrarFormTimbrado && (
        <div className="bg-white border rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">Registrar nuevo timbrado</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: 'N° Timbrado (SET)', key: 'nro_timbrado', type: 'number' },
              { label: 'Fecha inicio', key: 'fecha_inicio', type: 'date' },
              { label: 'Fecha fin', key: 'fecha_fin', type: 'date' },
              { label: 'N° inicial', key: 'nro_inicial', type: 'number' },
              { label: 'N° final', key: 'nro_final', type: 'number' },
            ].map(({ label, key, type }) => (
              <label key={key} className="block text-sm text-gray-600">
                {label}
                <input
                  type={type}
                  value={form[key as keyof NuevoTimbrado] as string}
                  onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                  className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </label>
            ))}
            <label className="block text-sm text-gray-600">
              Punto de expedición
              <select
                value={form.id_punto}
                onChange={e => setForm(f => ({ ...f, id_punto: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="">Seleccionar...</option>
                {puntos.map(p => (
                  <option key={p.id_punto} value={p.id_punto}>
                    {p.codigo_establecimiento}-{p.codigo_punto_expedicion}{p.descripcion_ubicacion ? ` (${p.descripcion_ubicacion})` : ''}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm text-gray-600">
              Tipo de documento
              <select
                value={form.tipo_documento}
                onChange={e => setForm(f => ({ ...f, tipo_documento: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                <option value="FACTURA">Factura</option>
                <option value="NOTA_CREDITO">Nota de crédito</option>
                <option value="AUTOFACTURA">Autofactura</option>
              </select>
            </label>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={crearTimbrado} className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
              Guardar timbrado
            </button>
            <button onClick={() => { setMostrarFormTimbrado(false); setForm(EMPTY_TIMBRADO); }}
              className="px-4 py-2 border rounded-lg hover:bg-gray-50">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Formulario nuevo punto de expedición */}
      {mostrarFormPunto && (
        <div className="bg-white border rounded-xl p-5 shadow-sm">
          <h3 className="font-semibold text-gray-800 mb-4">Nuevo punto de expedición</h3>
          <div className="grid grid-cols-3 gap-4">
            <label className="block text-sm text-gray-600">
              Cód. establecimiento
              <input
                value={formPunto.codigo_establecimiento}
                onChange={e => setFormPunto(f => ({ ...f, codigo_establecimiento: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                maxLength={3}
              />
            </label>
            <label className="block text-sm text-gray-600">
              Cód. punto expedición
              <input
                value={formPunto.codigo_punto_expedicion}
                onChange={e => setFormPunto(f => ({ ...f, codigo_punto_expedicion: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                maxLength={3}
              />
            </label>
            <label className="block text-sm text-gray-600">
              Ubicación (opcional)
              <input
                value={formPunto.descripcion_ubicacion}
                onChange={e => setFormPunto(f => ({ ...f, descripcion_ubicacion: e.target.value }))}
                className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </label>
          </div>
          <div className="flex gap-2 mt-4">
            <button onClick={crearPunto} className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
              Guardar punto
            </button>
            <button onClick={() => setMostrarFormPunto(false)} className="px-4 py-2 border rounded-lg hover:bg-gray-50">
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Lista de timbrados */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <Hash className="w-5 h-5" /> Timbrados registrados
        </h2>
        <div className="space-y-3">
          {timbrados.map(t => {
            const usado = porcentajeUsado(t);
            const vigente = t.estado && t.fecha_inicio <= hoy && t.fecha_fin >= hoy;
            return (
              <div key={t.nro_timbrado} className={`bg-white border rounded-xl p-4 shadow-sm ${vigente ? 'border-green-300' : ''}`}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-bold text-gray-800 mr-3">N° {t.nro_timbrado}</span>
                    <span className="text-sm text-gray-500">{t.tipo_documento}</span>
                    {vigente && <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Vigente</span>}
                    {!t.estado && <span className="ml-2 text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Inactivo</span>}
                  </div>
                  <span className="text-sm text-gray-500 flex items-center gap-1">
                    <Calendar className="w-4 h-4" /> {t.fecha_inicio} → {t.fecha_fin}
                  </span>
                </div>
                <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                  <span>Rango: {t.nro_inicial} – {t.nro_final}</span>
                  <span className="text-green-600">{t.nro_disponibles} disponibles</span>
                  <span className="text-gray-400">{t.nro_final - t.nro_inicial + 1 - t.nro_disponibles} usados</span>
                </div>
                <div className="mt-1 w-full bg-gray-100 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${usado > 90 ? 'bg-red-500' : usado > 70 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${usado}%` }}
                  />
                </div>
              </div>
            );
          })}
          {timbrados.length === 0 && (
            <p className="text-gray-400 text-center py-8">No hay timbrados registrados.</p>
          )}
        </div>
      </div>

      {/* Últimos documentos emitidos */}
      <div>
        <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5" /> Últimas facturas emitidas
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-gray-600">
                <th className="px-4 py-2 text-left">N° Comprobante</th>
                <th className="px-4 py-2 text-left">Tipo</th>
                <th className="px-4 py-2 text-left">Cliente</th>
                <th className="px-4 py-2 text-left">Monto</th>
                <th className="px-4 py-2 text-left">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {documentos.map(doc => (
                <tr key={doc.id_documento} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-2 font-mono">{doc.nro_preimpreso_interno ?? String(doc.nro_secuencial).padStart(7, '0')}</td>
                  <td className="px-4 py-2">{doc.tipo_documento}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{doc.cliente_nombre ?? '–'}</td>
                  <td className="px-4 py-2">Gs. {Number(doc.monto_total).toLocaleString('es-PY')}</td>
                  <td className="px-4 py-2">{new Date(doc.fecha_emision).toLocaleString('es-PY', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
                </tr>
              ))}
              {documentos.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Sin documentos emitidos</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default GestionTimbrado;
