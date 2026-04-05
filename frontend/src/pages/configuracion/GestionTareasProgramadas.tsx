import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { Clock, RefreshCw, ToggleLeft, ToggleRight, Pencil, X, Check, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

interface Crontab {
  id: number;
  minute: string;
  hour: string;
  day_of_week: string;
  day_of_month: string;
  month_of_year: string;
}

interface TareaProgramada {
  id: number;
  name: string;
  task: string;
  enabled: boolean;
  last_run_at: string | null;
  total_run_count: number;
  crontab: Crontab | null;
}

// Nombres amigables para las tareas
const NOMBRES: Record<string, { label: string; desc: string; color: string }> = {
  'expirar-recargas-pendientes': { label: 'Expirar recargas pendientes', desc: 'Cancela recargas antiguas sin confirmar', color: 'bg-orange-100 text-orange-700' },
  'alertas-saldo-bajo': { label: 'Alertas saldo bajo', desc: 'Notifica tarjetas con saldo insuficiente', color: 'bg-amber-100 text-amber-700' },
  'limpiar-notificaciones-antiguas': { label: 'Limpiar notificaciones', desc: 'Elimina notificaciones leídas antiguas', color: 'bg-gray-100 text-gray-600' },
  'alertar-stock-minimo': { label: 'Alertas stock mínimo', desc: 'Avisa cuando un producto baja del stock mínimo', color: 'bg-red-100 text-red-700' },
  'verificar-vencimientos-productos': { label: 'Verificar vencimientos', desc: 'Alerta sobre productos próximos a vencer', color: 'bg-yellow-100 text-yellow-700' },
  'resumen-diario-stock': { label: 'Resumen diario stock', desc: 'Genera informe de stock al cierre del día', color: 'bg-blue-100 text-blue-700' },
  'resumen-diario-ventas': { label: 'Resumen diario ventas', desc: 'Genera informe de ventas al cierre del día', color: 'bg-indigo-100 text-indigo-700' },
  'cierre-automatico-cajas': { label: 'Cierre automático cajas', desc: 'Cierra cajas abiertas al final de la jornada', color: 'bg-purple-100 text-purple-700' },
  'generar-cuentas-almuerzos-mensuales': { label: 'Generar cuentas almuerzos', desc: 'Crea las cuentas del mes para almuerzos', color: 'bg-green-100 text-green-700' },
  'alertar-cuentas-almuerzos-vencidas': { label: 'Alertar cuentas vencidas', desc: 'Notifica cuentas de almuerzos sin pagar', color: 'bg-rose-100 text-rose-700' },
  'calcular-kpis-diarios': { label: 'Calcular KPIs diarios', desc: 'Procesa y guarda KPIs del dashboard', color: 'bg-teal-100 text-teal-700' },
};

const describeCron = (c: Crontab | null): string => {
  if (!c) return 'Sin programación';
  const h = c.hour === '*' ? 'cada hora' : `${c.hour}h`;
  const m = c.minute === '0' ? '' : `:${c.minute}`;
  const dom = c.day_of_month !== '*' ? ` el día ${c.day_of_month}` : '';
  const dow = c.day_of_week !== '*' ? [' los', ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'][parseInt(c.day_of_week)] ?? c.day_of_week].join(' ') : '';
  return `${h}${m}${dom}${dow}`.trim();
};

const GestionTareasProgramadas: React.FC = () => {
  const [tareas, setTareas] = useState<TareaProgramada[]>([]);
  const [loading, setLoading] = useState(true);
  const [editandoId, setEditandoId] = useState<number | null>(null);
  const [cronEdit, setCronEdit] = useState<Partial<Crontab>>({});

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/tareas-programadas/');
      const data = res.data.results ?? res.data;
      setTareas(Array.isArray(data) ? data : []);
    } catch {
      toast.error('Error cargando tareas programadas');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const toggleEnabled = async (t: TareaProgramada) => {
    try {
      await api.patch(`/tareas-programadas/${t.id}/`, { enabled: !t.enabled });
      toast.success(t.enabled ? 'Tarea desactivada' : 'Tarea activada');
      cargar();
    } catch {
      toast.error('Error al cambiar estado');
    }
  };

  const abrirEdicionCron = (t: TareaProgramada) => {
    setEditandoId(t.id);
    setCronEdit({
      minute: t.crontab?.minute ?? '0',
      hour: t.crontab?.hour ?? '*',
      day_of_week: t.crontab?.day_of_week ?? '*',
      day_of_month: t.crontab?.day_of_month ?? '*',
      month_of_year: t.crontab?.month_of_year ?? '*',
    });
  };

  const guardarCron = async (id: number) => {
    try {
      await api.patch(`/tareas-programadas/${id}/`, cronEdit);
      toast.success('Horario actualizado');
      setEditandoId(null);
      cargar();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al guardar');
    }
  };

  if (loading) return <div className="flex items-center justify-center h-40"><RefreshCw className="animate-spin text-teal-500 w-6 h-6" /></div>;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Clock className="w-8 h-8 text-teal-600" />
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tareas Programadas</h1>
          <p className="text-sm text-gray-500">Activá, desactivá y cambiá el horario de las tareas automáticas del sistema</p>
        </div>
      </div>

      {/* Aviso */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-xl p-4">
        <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-blue-700">
          Los cambios de horario usan formato cron: <code className="bg-blue-100 px-1 rounded">*</code> = siempre,
          número = valor específico. Ejemplo: hora <code className="bg-blue-100 px-1 rounded">23</code> minuto <code className="bg-blue-100 px-1 rounded">0</code> = 23:00 diario.
        </p>
      </div>

      {/* Lista de tareas */}
      <div className="space-y-3">
        {tareas.map(t => {
          const info = NOMBRES[t.name] ?? { label: t.name, desc: t.task, color: 'bg-gray-100 text-gray-600' };
          const editando = editandoId === t.id;

          return (
            <div key={t.id} className="bg-white border rounded-xl shadow-sm overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4">
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${info.color}`}>
                    {info.label}
                  </span>
                  {!t.enabled && (
                    <span className="text-xs text-gray-400 italic">desactivada</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {!editando && (
                    <button onClick={() => abrirEdicionCron(t)} className="p-1.5 rounded hover:bg-teal-50 text-teal-600" title="Cambiar horario">
                      <Pencil className="w-4 h-4" />
                    </button>
                  )}
                  <button onClick={() => toggleEnabled(t)} className="p-1.5 rounded hover:bg-gray-100" title={t.enabled ? 'Desactivar' : 'Activar'}>
                    {t.enabled
                      ? <ToggleRight className="w-5 h-5 text-green-600" />
                      : <ToggleLeft className="w-5 h-5 text-gray-400" />}
                  </button>
                </div>
              </div>

              <div className="px-5 pb-3 flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">{info.desc}</p>
                  {!editando && (
                    <p className="text-xs text-teal-600 font-medium mt-0.5">
                      <Clock className="inline w-3 h-3 mr-1" />
                      {describeCron(t.crontab)}
                      {t.crontab && (
                        <span className="ml-2 text-gray-400 font-mono">
                          ({t.crontab.minute} {t.crontab.hour} {t.crontab.day_of_month} {t.crontab.month_of_year} {t.crontab.day_of_week})
                        </span>
                      )}
                    </p>
                  )}
                </div>
                <div className="text-right text-xs text-gray-400">
                  <p>{t.total_run_count} ejecuciones</p>
                  {t.last_run_at && <p>Última: {new Date(t.last_run_at).toLocaleString('es-PY', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</p>}
                </div>
              </div>

              {/* Editor de crontab inline */}
              {editando && (
                <div className="px-5 py-3 bg-teal-50 border-t border-teal-100">
                  <p className="text-xs font-medium text-teal-700 mb-2">Modificar horario (formato cron)</p>
                  <div className="flex items-end gap-3 flex-wrap">
                    {[
                      { key: 'minute', label: 'Minuto (0-59)' },
                      { key: 'hour', label: 'Hora (0-23)' },
                      { key: 'day_of_month', label: 'Día mes (1-31)' },
                      { key: 'month_of_year', label: 'Mes (1-12)' },
                      { key: 'day_of_week', label: 'Día semana (0=Dom)' },
                    ].map(({ key, label }) => (
                      <label key={key} className="block text-xs text-gray-600 w-32">
                        {label}
                        <input
                          value={(cronEdit as any)[key] ?? '*'}
                          onChange={e => setCronEdit(c => ({ ...c, [key]: e.target.value }))}
                          className="mt-1 w-full border rounded px-2 py-1 text-sm font-mono focus:ring-1 focus:ring-teal-400 focus:outline-none"
                        />
                      </label>
                    ))}
                    <div className="flex gap-2 pb-0.5">
                      <button onClick={() => guardarCron(t.id)} className="flex items-center gap-1 bg-teal-600 text-white text-xs px-3 py-1.5 rounded hover:bg-teal-700">
                        <Check className="w-3 h-3" /> Guardar
                      </button>
                      <button onClick={() => setEditandoId(null)} className="flex items-center gap-1 border text-xs px-3 py-1.5 rounded hover:bg-white">
                        <X className="w-3 h-3" /> Cancelar
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default GestionTareasProgramadas;
