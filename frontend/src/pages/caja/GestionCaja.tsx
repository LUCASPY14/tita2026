import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import {
  DollarSign, LogIn, LogOut, Clock, AlertTriangle, CheckCircle,
  RefreshCw, TrendingUp, TrendingDown, Settings, Monitor, Plus,
  Pencil, ToggleLeft, ToggleRight, X,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuth } from '../../hooks/useAuth';

const CAJA_CONFIG_KEY = 'pos_caja_id';

interface Caja {
  id_caja: number;
  nombre_caja: string;
  ubicacion: string | null;
  estado: boolean;
}

interface Empleado {
  id_empleado: number;
  nombre: string;
  apellido: string;
}

interface TurnoActivo {
  id_cierre: number;
  caja_nombre: string;
  empleado_nombre: string;
  fecha_hora_apertura: string;
  monto_inicial: string;
  estado: string;
  total_ingresos: number;
  total_egresos: number;
  total_ventas: number;
  movimientos: Movimiento[];
}

interface Movimiento {
  id_movimiento: number;
  tipo_movimiento: string;
  monto: string;
  descripcion: string;
  fecha_movimiento: string;
  medio_pago_descripcion: string;
  venta_nro: string | null;
}

/** Lee el id_caja configurado para este terminal desde localStorage. */
function getCajaConfigurada(): number | null {
  const v = localStorage.getItem(CAJA_CONFIG_KEY);
  const n = v ? parseInt(v, 10) : NaN;
  return isNaN(n) ? null : n;
}

// â”€â”€ Subcomponente: pantalla de configuraciÃ³n inicial â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

interface ConfigPanelProps {
  cajas: Caja[];
  onConfirmar: (idCaja: number) => void;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({ cajas, onConfirmar }) => {
  const [seleccionado, setSeleccionado] = useState('');
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="bg-white border-2 border-blue-200 rounded-2xl p-8 max-w-md w-full shadow-lg">
        <div className="flex items-center gap-3 mb-5">
          <Monitor className="w-8 h-8 text-blue-600" />
          <div>
            <h2 className="text-xl font-bold text-gray-900">Configurar este terminal</h2>
            <p className="text-sm text-gray-500">Â¿QuÃ© caja registradora es este punto de venta?</p>
          </div>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Esta configuraciÃ³n se guarda en este navegador y no necesita repetirse cada vez.
        </p>
        <label className="block text-sm font-medium text-gray-700 mb-1">Caja asignada a este terminal</label>
        <select
          value={seleccionado}
          onChange={e => setSeleccionado(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 mb-4 focus:ring-2 focus:ring-blue-500 focus:outline-none"
        >
          <option value="">Seleccionar caja...</option>
          {cajas.filter(c => c.estado).map(c => (
            <option key={c.id_caja} value={c.id_caja}>
              {c.nombre_caja}{c.ubicacion ? ` â€” ${c.ubicacion}` : ''}
            </option>
          ))}
        </select>
        <button
          disabled={!seleccionado}
          onClick={() => onConfirmar(parseInt(seleccionado, 10))}
          className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:opacity-40 font-medium"
        >
          Confirmar y continuar
        </button>
      </div>
    </div>
  );
};

// ── Panel de administración de cajas (solo admin) ────────────────────────────

interface AdminCajasProps {
  cajas: Caja[];
  onRefresh: () => void;
}

const AdminCajas: React.FC<AdminCajasProps> = ({ cajas, onRefresh }) => {
  const [mostrarForm, setMostrarForm] = useState(false);
  const [editando, setEditando] = useState<Caja | null>(null);
  const [nombre, setNombre] = useState('');
  const [ubicacion, setUbicacion] = useState('');
  const [saving, setSaving] = useState(false);

  const abrirNueva = () => {
    setEditando(null);
    setNombre('');
    setUbicacion('');
    setMostrarForm(true);
  };

  const abrirEditar = (caja: Caja) => {
    setEditando(caja);
    setNombre(caja.nombre_caja);
    setUbicacion(caja.ubicacion ?? '');
    setMostrarForm(true);
  };

  const cancelar = () => { setMostrarForm(false); setEditando(null); };

  const guardar = async () => {
    if (!nombre.trim()) { toast.error('El nombre es obligatorio.'); return; }
    setSaving(true);
    try {
      if (editando) {
        await api.patch(`/cajas/${editando.id_caja}/`, { nombre_caja: nombre.trim(), ubicacion: ubicacion.trim() || null });
        toast.success('Caja actualizada.');
      } else {
        await api.post('/cajas/', { nombre_caja: nombre.trim(), ubicacion: ubicacion.trim() || null, estado: true });
        toast.success('Caja creada.');
      }
      setMostrarForm(false);
      setEditando(null);
      onRefresh();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al guardar.');
    } finally {
      setSaving(false);
    }
  };

  const toggleEstado = async (caja: Caja) => {
    try {
      await api.patch(`/cajas/${caja.id_caja}/`, { estado: !caja.estado });
      toast.success(caja.estado ? 'Caja desactivada.' : 'Caja activada.');
      onRefresh();
    } catch {
      toast.error('Error al cambiar estado.');
    }
  };

  return (
    <div className="bg-white border rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Administrar Cajas</h2>
        <button
          onClick={abrirNueva}
          className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          <Plus className="w-4 h-4" /> Nueva caja
        </button>
      </div>

      {mostrarForm && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
          <p className="font-medium text-blue-900 text-sm">
            {editando ? `Editar: ${editando.nombre_caja}` : 'Nueva caja'}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nombre *</label>
              <input
                type="text"
                value={nombre}
                onChange={e => setNombre(e.target.value)}
                placeholder="Ej: Caja Principal"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Ubicación</label>
              <input
                type="text"
                value={ubicacion}
                onChange={e => setUbicacion(e.target.value)}
                placeholder="Ej: Salón principal"
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={guardar}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
            <button
              onClick={cancelar}
              className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50 flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" /> Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="pb-2 pr-4">Nombre</th>
              <th className="pb-2 pr-4">Ubicación</th>
              <th className="pb-2 pr-4">Estado</th>
              <th className="pb-2 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cajas.length === 0 && (
              <tr><td colSpan={4} className="py-6 text-center text-gray-400">No hay cajas registradas. Creá una con "Nueva caja".</td></tr>
            )}
            {cajas.map(caja => (
              <tr key={caja.id_caja} className="border-b last:border-0 hover:bg-gray-50">
                <td className="py-2.5 pr-4 font-medium text-gray-800">{caja.nombre_caja}</td>
                <td className="py-2.5 pr-4 text-gray-500">{caja.ubicacion ?? '—'}</td>
                <td className="py-2.5 pr-4">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                    ${caja.estado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {caja.estado ? 'Activa' : 'Inactiva'}
                  </span>
                </td>
                <td className="py-2.5 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => abrirEditar(caja)}
                      title="Editar"
                      className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => toggleEstado(caja)}
                      title={caja.estado ? 'Desactivar' : 'Activar'}
                      className={`p-1.5 rounded-lg transition-colors
                        ${caja.estado
                          ? 'text-green-600 hover:text-red-600 hover:bg-red-50'
                          : 'text-gray-400 hover:text-green-600 hover:bg-green-50'}`}
                    >
                      {caja.estado ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ── Componente principal ──────────────────────────────────────────────────────

const GestionCaja: React.FC = () => {
  const [cajas, setCajas] = useState<Caja[]>([]);
  const [empleados, setEmpleados] = useState<Empleado[]>([]);
  const [turnoActivo, setTurnoActivo] = useState<TurnoActivo | null>(null);
  const [loading, setLoading] = useState(true);
  const [vista, setVista] = useState<'principal' | 'abrir' | 'cerrar'>('principal');

  // Caja de ESTE terminal (persistida en localStorage)
  const [cajaId, setCajaId] = useState<number | null>(getCajaConfigurada);
  const [mostrarConfig, setMostrarConfig] = useState(false);

  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Form apertura
  const [empleadoSeleccionado, setEmpleadoSeleccionado] = useState('');
  const [montoInicial, setMontoInicial] = useState('');

  // Form cierre
  const [montoContado, setMontoContado] = useState('');

  const cajaActual = cajas.find(c => c.id_caja === cajaId) ?? null;

  const cargarDatos = useCallback(async (idCaja?: number) => {
    const targetId = idCaja ?? cajaId;
    setLoading(true);
    try {
      const [cajasRes, empleadosRes] = await Promise.all([
        api.get('/cajas/'),
        api.get('/empleados/'),
      ]);
      setCajas(cajasRes.data.results ?? cajasRes.data);
      setEmpleados(empleadosRes.data.results ?? empleadosRes.data);

      if (targetId) {
        try {
          const turnoRes = await api.get(`/cierres-caja/turno-activo/?id_caja=${targetId}`);
          setTurnoActivo(turnoRes.data);
        } catch {
          setTurnoActivo(null);
        }
      }
    } catch {
      toast.error('Error cargando datos de caja');
    } finally {
      setLoading(false);
    }
  }, [cajaId]);

  useEffect(() => { cargarDatos(); }, [cargarDatos]);

  const confirmarCaja = (id: number) => {
    localStorage.setItem(CAJA_CONFIG_KEY, String(id));
    setCajaId(id);
    setMostrarConfig(false);
    cargarDatos(id);
  };

  const abrirCaja = async () => {
    if (!cajaId || !empleadoSeleccionado || !montoInicial) {
      toast.error('Complete todos los campos');
      return;
    }
    try {
      await api.post('/cierres-caja/abrir/', {
        id_caja: cajaId,
        id_empleado: parseInt(empleadoSeleccionado),
        monto_inicial: parseFloat(montoInicial),
      });
      toast.success('Caja abierta correctamente');
      setVista('principal');
      setMontoInicial('');
      setEmpleadoSeleccionado('');
      cargarDatos();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al abrir caja');
    }
  };

  const cerrarCaja = async () => {
    if (!turnoActivo || !montoContado) {
      toast.error('Ingrese el monto contado fÃ­sicamente');
      return;
    }
    try {
      await api.post(`/cierres-caja/${turnoActivo.id_cierre}/cerrar/`, {
        monto_contado_fisico: parseFloat(montoContado),
      });
      toast.success('Caja cerrada correctamente');
      setVista('principal');
      setMontoContado('');
      cargarDatos();
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Error al cerrar caja');
    }
  };

  const formatGs = (val: string | number) =>
    `Gs. ${Number(val).toLocaleString('es-PY')}`;

  const formatFecha = (iso: string) =>
    new Date(iso).toLocaleString('es-PY', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="animate-spin text-blue-500 w-8 h-8" />
      </div>
    );
  }

  // Primera vez: terminal sin caja asignada
  if (!cajaId || mostrarConfig) {
    return (
      <div className="p-6 space-y-6">
        <ConfigPanel cajas={cajas} onConfirmar={confirmarCaja} />
        {isAdmin && (
          <AdminCajas cajas={cajas} onRefresh={cargarDatos} />
        )}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <DollarSign className="w-8 h-8 text-green-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">GestiÃ³n de Caja</h1>
            <p className="text-sm text-gray-500 flex items-center gap-1">
              <Monitor className="w-3 h-3" />
              Terminal asignado a: <strong className="ml-1">{cajaActual?.nombre_caja ?? `Caja ${cajaId}`}</strong>
              {cajaActual?.ubicacion && <span className="text-gray-400"> â€” {cajaActual.ubicacion}</span>}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMostrarConfig(true)}
            title="Cambiar caja de este terminal"
            className="flex items-center gap-1 px-3 py-2 text-gray-500 border rounded-lg hover:bg-gray-50 text-sm"
          >
            <Settings className="w-4 h-4" /> Cambiar caja
          </button>
          <button
            onClick={() => cargarDatos()}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 border rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" /> Actualizar
          </button>
        </div>
      </div>

      {/* Estado turno activo */}
      {turnoActivo ? (
        <div className="bg-green-50 border border-green-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="font-semibold text-green-800">Turno activo: {turnoActivo.caja_nombre}</span>
              <span className="text-sm text-green-600">â€” {turnoActivo.empleado_nombre}</span>
            </div>
            <span className="text-sm text-green-700 flex items-center gap-1">
              <Clock className="w-4 h-4" /> Abierto: {formatFecha(turnoActivo.fecha_hora_apertura)}
            </span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-gray-500">Fondo inicial</p>
              <p className="font-bold text-gray-800">{formatGs(turnoActivo.monto_inicial)}</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-green-600 flex items-center justify-center gap-1">
                <TrendingUp className="w-3 h-3" /> Ingresos
              </p>
              <p className="font-bold text-green-700">{formatGs(turnoActivo.total_ingresos)}</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-blue-600 flex items-center justify-center gap-1">
                <DollarSign className="w-3 h-3" /> Ventas
              </p>
              <p className="font-bold text-blue-700">{formatGs(turnoActivo.total_ventas)}</p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-xs text-red-600 flex items-center justify-center gap-1">
                <TrendingDown className="w-3 h-3" /> Egresos
              </p>
              <p className="font-bold text-red-700">{formatGs(turnoActivo.total_egresos)}</p>
            </div>
          </div>

          {vista === 'cerrar' ? (
            <div className="bg-white rounded-lg p-4 space-y-3">
              <p className="font-medium text-gray-700">Cierre de turno</p>
              <label className="block text-sm text-gray-600">
                Monto contado fÃ­sicamente (Gs.)
                <input
                  type="number"
                  value={montoContado}
                  onChange={e => setMontoContado(e.target.value)}
                  className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="0"
                />
              </label>
              <div className="flex gap-2">
                <button
                  onClick={cerrarCaja}
                  className="flex-1 bg-red-600 text-white py-2 rounded-lg hover:bg-red-700 font-medium"
                >
                  <LogOut className="w-4 h-4 inline mr-1" /> Confirmar cierre
                </button>
                <button
                  onClick={() => setVista('principal')}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setVista('cerrar')}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
            >
              <LogOut className="w-4 h-4" /> Cerrar turno
            </button>
          )}

          {/* Movimientos del turno */}
          {turnoActivo.movimientos?.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Ãšltimos movimientos</p>
              <div className="max-h-64 overflow-y-auto space-y-1">
                {turnoActivo.movimientos.slice(-10).reverse().map(mov => (
                  <div key={mov.id_movimiento} className="flex justify-between text-sm bg-white px-3 py-2 rounded-lg">
                    <span className="text-gray-600">{mov.descripcion} â€” {mov.medio_pago_descripcion}</span>
                    <span className={`font-medium ${mov.tipo_movimiento === 'Egreso' ? 'text-red-600' : 'text-green-600'}`}>
                      {mov.tipo_movimiento === 'Egreso' ? 'âˆ’' : '+'}{formatGs(mov.monto)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600" />
            <span className="font-semibold text-yellow-800">No hay turno activo en {cajaActual?.nombre_caja ?? `Caja ${cajaId}`}</span>
          </div>

          {vista === 'abrir' ? (
            <div className="bg-white rounded-lg p-4 space-y-3">
              <p className="font-medium text-gray-700">Apertura de turno â€” {cajaActual?.nombre_caja}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="block text-sm text-gray-600">
                  Cajero
                  <select
                    value={empleadoSeleccionado}
                    onChange={e => setEmpleadoSeleccionado(e.target.value)}
                    className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  >
                    <option value="">Seleccionar cajero...</option>
                    {empleados.map(e => (
                      <option key={e.id_empleado} value={e.id_empleado}>{e.nombre} {e.apellido}</option>
                    ))}
                  </select>
                </label>
                <label className="block text-sm text-gray-600">
                  Fondo inicial (Gs.)
                  <input
                    type="number"
                    value={montoInicial}
                    onChange={e => setMontoInicial(e.target.value)}
                    className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                    placeholder="0"
                  />
                </label>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={abrirCaja}
                  className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 font-medium"
                >
                  <LogIn className="w-4 h-4 inline mr-1" /> Abrir caja
                </button>
                <button
                  onClick={() => setVista('principal')}
                  className="px-4 py-2 border rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setVista('abrir')}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              <LogIn className="w-4 h-4" /> Abrir turno
            </button>
          )}
        </div>
      )}

      {/* Panel según rol */}
      {isAdmin ? (
        <AdminCajas cajas={cajas} onRefresh={cargarDatos} />
      ) : (
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-3">Cajas registradas</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {cajas.map(caja => (
              <div key={caja.id_caja} className="bg-white border rounded-xl p-4 shadow-sm">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-gray-800">{caja.nombre_caja}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${caja.estado ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                    {caja.estado ? 'Activa' : 'Inactiva'}
                  </span>
                </div>
                {caja.ubicacion && <p className="text-sm text-gray-500">{caja.ubicacion}</p>}
              </div>
            ))}
            {cajas.length === 0 && (
              <p className="text-gray-400 col-span-3 text-center py-8">No hay cajas configuradas.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default GestionCaja;
