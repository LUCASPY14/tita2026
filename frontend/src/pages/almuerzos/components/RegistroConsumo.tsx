import React, { useState, useEffect } from 'react';
import { Card, Button, Input, Spinner } from '../../../components/common';
import { Search, CheckCircle, AlertCircle, Clock, User, CreditCard, DollarSign } from 'lucide-react';
import { recargasService } from '../../../services/recargas.service';
import { almuerzosService } from '../../../services/almuerzos.service';
import toast from 'react-hot-toast';
import type { Hijo, Tarjeta, TipoAlmuerzo, SuscripcionAlmuerzo, RegistroConsumoAlmuerzo, Alergeno } from '../../../types';

interface RegistroConsumoProps {
  onRegistroExitoso: () => void;
  actualizarClave: number;
}

const RegistroConsumo: React.FC<RegistroConsumoProps> = ({ onRegistroExitoso, actualizarClave }) => {
  const [busqueda, setBusqueda] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [hijoSeleccionado, setHijoSeleccionado] = useState<Hijo | null>(null);
  const [tarjetaSeleccionada, setTarjetaSeleccionada] = useState<Tarjeta | null>(null);
  const [tiposAlmuerzo, setTiposAlmuerzo] = useState<TipoAlmuerzo[]>([]);
  const [suscripcionActiva, setSuscripcionActiva] = useState<SuscripcionAlmuerzo | null>(null);
  const [tipoSeleccionado, setTipoSeleccionado] = useState<number>(0);
  const [registrando, setRegistrando] = useState(false);
  const [registrosHoy, setRegistrosHoy] = useState<RegistroConsumoAlmuerzo[]>([]);
  const [cargandoRegistros, setCargandoRegistros] = useState(false);
  const [alergenos, setAlergenos] = useState<Alergeno[]>([]);

  useEffect(() => {
    cargarTiposAlmuerzo();
    cargarRegistrosDelDia();
  }, [actualizarClave]);

  useEffect(() => {
    if (hijoSeleccionado) {
      verificarSuscripcionActiva();
      cargarAlergenos();
    } else {
      setAlergenos([]);
    }
  }, [hijoSeleccionado]);

  const cargarTiposAlmuerzo = async () => {
    try {
      const response = await almuerzosService.getTipos({ activo: true });
      setTiposAlmuerzo(response.results || response);
    } catch (error) {
      console.error('Error al cargar tipos de almuerzo:', error);
    }
  };

  const cargarRegistrosDelDia = async () => {
    try {
      setCargandoRegistros(true);
      const hoy = new Date().toISOString().split('T')[0];
      const response = await almuerzosService.getRegistrosDelDia(hoy);
      setRegistrosHoy(response.results || response);
    } catch (error) {
      console.error('Error al cargar registros del día:', error);
    } finally {
      setCargandoRegistros(false);
    }
  };

  const verificarSuscripcionActiva = async () => {
    if (!hijoSeleccionado) return;
    
    try {
      const response = await almuerzosService.getSuscripcionesPorHijo(hijoSeleccionado.id_hijo);
      const suscripciones = response.results || response;
      const activa = suscripciones.find((s: SuscripcionAlmuerzo) => s.estado === 'Activa');
      setSuscripcionActiva(activa || null);
    } catch (error) {
      console.error('Error al verificar suscripción:', error);
      setSuscripcionActiva(null);
    }
  };

  const cargarAlergenos = async () => {
    try {
      const response = await almuerzosService.getAlergenos({ activo: true });
      setAlergenos(response.results || response);
    } catch (error) {
      console.error('Error al cargar alérgenos:', error);
    }
  };

  const handleBuscar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!busqueda.trim()) {
      toast.error('Ingresa un número de tarjeta o nombre');
      return;
    }

    setBuscando(true);
    try {
      // Buscar por número de tarjeta primero
      const responseTarjeta = await recargasService.buscarTarjetas({ search: busqueda });
      
      if (responseTarjeta.results && responseTarjeta.results.length > 0) {
        const tarjeta = responseTarjeta.results[0];
        
        if (tarjeta.estado !== 'Activa') {
          toast.error('La tarjeta está inactiva');
          return;
        }

        // Obtener datos completos del hijo
        const hijo = await recargasService.getHijoById(tarjeta.id_hijo);
        
        setHijoSeleccionado(hijo);
        setTarjetaSeleccionada(tarjeta);
        toast.success(`Hijo encontrado: ${hijo.nombre} ${hijo.apellido}`);
      } else {
        toast.error('No se encontró ninguna tarjeta con ese número');
      }
    } catch (error: any) {
      console.error('Error en búsqueda:', error);
      toast.error(error.response?.data?.error || 'Error al buscar');
    } finally {
      setBuscando(false);
    }
  };

  const handleRegistrar = async () => {
    if (!hijoSeleccionado || !tarjetaSeleccionada) {
      toast.error('Selecciona un hijo primero');
      return;
    }

    // Si no tiene suscripción activa, debe seleccionar un tipo de almuerzo
    if (!suscripcionActiva && tipoSeleccionado === 0) {
      toast.error('Selecciona un tipo de almuerzo');
      return;
    }

    setRegistrando(true);
    try {
      const data = {
        fecha_consumo: new Date().toISOString().split('T')[0],
        id_hijo: hijoSeleccionado.id_hijo,
        nro_tarjeta: tarjetaSeleccionada.nro_tarjeta,
        ...(suscripcionActiva && { id_suscripcion: suscripcionActiva.id_suscripcion }),
        ...(!suscripcionActiva && tipoSeleccionado > 0 && { id_tipo_almuerzo: tipoSeleccionado })
      };

      await almuerzosService.registrarConsumo(data);
      toast.success('Consumo registrado exitosamente');
      
      // Limpiar formulario
      setBusqueda('');
      setHijoSeleccionado(null);
      setTarjetaSeleccionada(null);
      setTipoSeleccionado(0);
      setSuscripcionActiva(null);
      
      // Notificar registro exitoso y recargar datos
      onRegistroExitoso();
      cargarRegistrosDelDia();
    } catch (error: any) {
      console.error('Error al registrar consumo:', error);
      
      if (error.response?.data?.error) {
        toast.error(error.response.data.error);
        
        // Mostrar información adicional si hay saldo insuficiente
        if (error.response.data.saldo_actual !== undefined) {
          const { saldo_actual, costo_almuerzo, faltante } = error.response.data;
          toast.error(
            `Saldo insuficiente. Saldo: Gs. ${formatearMoneda(saldo_actual)} | ` +
            `Costo: Gs. ${formatearMoneda(costo_almuerzo)} | ` +
            `Falta: Gs. ${formatearMoneda(faltante)}`,
            { duration: 5000 }
          );
        }
      } else {
        toast.error('Error al registrar el consumo');
      }
    } finally {
      setRegistrando(false);
    }
  };

  const handleLimpiar = () => {
    setBusqueda('');
    setHijoSeleccionado(null);
    setTarjetaSeleccionada(null);
    setTipoSeleccionado(0);
    setSuscripcionActiva(null);
    setAlergenos([]);
  };

  const formatearMoneda = (valor: number) => {
    return new Intl.NumberFormat('es-PY', {
      style: 'currency',
      currency: 'PYG',
      minimumFractionDigits: 0
    }).format(valor);
  };

  const formatearHora = (hora: string) => {
    return hora.substring(0, 5); // HH:MM
  };

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      {/* Columna izquierda: Búsqueda y Registro */}
      <div className="space-y-6 lg:col-span-2">
        {/* Card de Búsqueda */}
        <Card title="Buscar Hijo" subtitle="Ingresa el número de tarjeta">
          <form onSubmit={handleBuscar} className="space-y-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  type="text"
                  placeholder="Número de tarjeta..."
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  disabled={buscando}
                />
              </div>
              <Button type="submit" disabled={buscando || !busqueda.trim()}>
                {buscando ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    Buscando...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4" />
                    Buscar
                  </>
                )}
              </Button>
            </div>
          </form>
        </Card>

        {/* Card de Datos del Hijo y Registro */}
        {hijoSeleccionado && tarjetaSeleccionada ? (
          <Card title="Registrar Consumo de Almuerzo">
            <div className="space-y-6">
              {/* Información del Hijo */}
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-blue-100 p-2">
                      <User className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Hijo</p>
                      <p className="font-medium text-gray-900">
                        {hijoSeleccionado.nombre} {hijoSeleccionado.apellido}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-amber-100 p-2">
                      <CreditCard className="h-5 w-5 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Tarjeta</p>
                      <p className="font-medium text-gray-900">{tarjetaSeleccionada.nro_tarjeta}</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-green-100 p-2">
                      <DollarSign className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Saldo Disponible</p>
                      <p className="font-semibold text-green-600">
                        {formatearMoneda(tarjetaSeleccionada.saldo_actual)}
                      </p>
                    </div>
                  </div>

                  {suscripcionActiva && (
                    <div className="flex items-start gap-3">
                      <div className="rounded-full bg-purple-100 p-2">
                        <CheckCircle className="h-5 w-5 text-purple-600" />
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">Suscripción</p>
                        <p className="font-medium text-purple-600">{suscripcionActiva.plan_nombre}</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Alérgenos del Menú */}
              {alergenos.length > 0 && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                  <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-amber-800">
                    <AlertCircle className="h-4 w-4" />
                    Alérgenos presentes en el menú — verificar con el alumno
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {alergenos.map((a) => {
                      const colorClasses =
                        a.nivel_severidad === 'Alto'
                          ? 'bg-red-100 text-red-800 border-red-200'
                          : a.nivel_severidad === 'Medio'
                          ? 'bg-orange-100 text-orange-800 border-orange-200'
                          : 'bg-gray-100 text-gray-700 border-gray-200';
                      return (
                        <span
                          key={a.id_alergeno}
                          className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-medium ${colorClasses}`}
                        >
                          {a.icono && <span>{a.icono}</span>}
                          {a.nombre}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Selección de Tipo de Almuerzo (solo si no tiene suscripción) */}
              {!suscripcionActiva && (
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Tipo de Almuerzo *
                  </label>
                  <select
                    value={tipoSeleccionado}
                    onChange={(e) => setTipoSeleccionado(Number(e.target.value))}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-amber-500 focus:outline-none focus:ring-2 focus:ring-amber-200"
                  >
                    <option value={0}>Seleccione un tipo de almuerzo...</option>
                    {tiposAlmuerzo.map((tipo) => (
                      <option key={tipo.id_tipo_almuerzo} value={tipo.id_tipo_almuerzo}>
                        {tipo.nombre} - {formatearMoneda(tipo.precio_unitario)}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {/* Información sobre el cobro */}
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
                <div className="flex gap-2">
                  <AlertCircle className="h-5 w-5 flex-shrink-0 text-blue-600" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium">Importante:</p>
                    <ul className="mt-1 list-inside list-disc space-y-1">
                      <li>El primer registro del día descuenta saldo de la tarjeta</li>
                      <li>El segundo registro no genera cobro (solo operativo)</li>
                      <li>Máximo 2 registros por alumno por día</li>
                    </ul>
                  </div>
                </div>
              </div>

              {/* Botones de acción */}
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleLimpiar}
                  className="flex-1"
                >
                  Cancelar
                </Button>
                <Button
                  onClick={handleRegistrar}
                  disabled={registrando || (!suscripcionActiva && tipoSeleccionado === 0)}
                  className="flex-1"
                >
                  {registrando ? (
                    <>
                      <Spinner className="h-4 w-4" />
                      Registrando...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Registrar Consumo
                    </>
                  )}
                </Button>
              </div>
            </div>
          </Card>
        ) : (
          <Card>
            <div className="py-12 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-amber-100">
                <Search className="h-8 w-8 text-amber-600" />
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                Busca un hijo
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Ingresa el número de tarjeta para registrar un consumo de almuerzo
              </p>
            </div>
          </Card>
        )}
      </div>

      {/* Columna derecha: Registros de Hoy */}
      <div className="lg:col-span-1">
        <Card title="Registros de Hoy" subtitle={`${registrosHoy.length} consumos`}>
          {cargandoRegistros ? (
            <div className="flex items-center justify-center py-8">
              <Spinner className="h-8 w-8" />
            </div>
          ) : registrosHoy.length > 0 ? (
            <div className="space-y-3">
              {registrosHoy.slice(0, 10).map((registro) => (
                <div
                  key={registro.id_registro_consumo}
                  className="rounded-lg border border-gray-200 bg-white p-3 hover:border-amber-300 hover:shadow-sm"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        {registro.hijo_nombre || `Hijo #${registro.id_hijo}`}
                      </p>
                      <p className="text-sm text-gray-500">
                        {registro.tipo_almuerzo_nombre || 'Suscripción'}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-sm text-gray-600">
                        <Clock className="h-3 w-3" />
                        {formatearHora(registro.hora_registro)}
                      </div>
                      {registro.ya_cobrado && (
                        <p className="mt-1 text-xs font-semibold text-green-600">
                          {formatearMoneda(registro.costo_almuerzo || 0)}
                        </p>
                      )}
                      {!registro.ya_cobrado && (
                        <p className="mt-1 text-xs text-gray-500">Sin cobro</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-sm text-gray-500">
              <Clock className="mx-auto mb-2 h-8 w-8 text-gray-400" />
              <p>No hay registros hoy</p>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default RegistroConsumo;
