import { useCallback, useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { MessageCircle, CheckCircle2, XCircle, AlertCircle, RefreshCw, Send } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import { inputClass, labelClass } from './helpers'

interface WAHAEstado {
  configurado: boolean
  conectado: boolean
  session: string
  estado?: string
  nombre?: string | null
  error?: string
  mensaje?: string
}

export default function TabWhatsApp() {
  const [estado, setEstado] = useState<WAHAEstado | null>(null)
  const [loadingEstado, setLoadingEstado] = useState(false)
  const [telefono, setTelefono] = useState('')
  const [mensajePrueba, setMensajePrueba] = useState('Hola, este es un mensaje de prueba de Cantina Tita.')
  const [enviando, setEnviando] = useState(false)

  const cargarEstado = useCallback(async () => {
    setLoadingEstado(true)
    try {
      const { data } = await api.get<WAHAEstado>('/notificaciones/whatsapp-estado/')
      setEstado(data)
    } catch {
      toast.error('No se pudo consultar el estado de WhatsApp')
    } finally {
      setLoadingEstado(false)
    }
  }, [])

  // Carga de datos al montar: el setLoadingEstado(true) inicial es intencional.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { cargarEstado() }, [cargarEstado])

  const enviarPrueba = async () => {
    if (!telefono.trim()) {
      toast.error('Ingresá un número de teléfono')
      return
    }
    setEnviando(true)
    try {
      await api.post('/notificaciones/whatsapp-estado/', {
        telefono: telefono.trim(),
        mensaje: mensajePrueba.trim() || 'Mensaje de prueba — Cantina Tita',
      })
      toast.success('Mensaje enviado correctamente')
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: string } } }
      toast.error(e?.response?.data?.error ?? 'Error al enviar el mensaje')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-green-600" />
          Configuración de WhatsApp
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Cantina Tita envía notificaciones a padres vía WhatsApp usando{' '}
          <span className="font-medium text-slate-700">WAHA</span>{' '}
          (servicio autoalojado en el servidor).
        </p>
      </div>

      {/* Estado de conexión */}
      <div className="border border-slate-200 rounded-xl p-5 bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
            Estado de la sesión
          </h3>
          <button
            onClick={cargarEstado}
            disabled={loadingEstado}
            className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 transition-colors cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingEstado ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>

        {loadingEstado && !estado && (
          <div className="text-sm text-slate-400 py-2">Verificando conexión…</div>
        )}

        {estado && (
          <div className="space-y-3">
            {/* Configurado */}
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-600">WAHA configurado</span>
              <span className={`flex items-center gap-1.5 text-sm font-medium ${estado.configurado ? 'text-green-600' : 'text-slate-400'}`}>
                {estado.configurado
                  ? <><CheckCircle2 className="w-4 h-4" /> Sí</>
                  : <><XCircle className="w-4 h-4" /> No</>
                }
              </span>
            </div>

            {/* Conectado */}
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-600">Sesión activa</span>
              <span className={`flex items-center gap-1.5 text-sm font-medium ${estado.conectado ? 'text-green-600' : 'text-red-500'}`}>
                {estado.conectado
                  ? <><CheckCircle2 className="w-4 h-4" /> Conectado</>
                  : <><XCircle className="w-4 h-4" /> Desconectado</>
                }
              </span>
            </div>

            {/* Sesión */}
            <div className="flex items-center justify-between py-2 border-b border-slate-100">
              <span className="text-sm text-slate-600">Nombre de sesión</span>
              <span className="text-sm font-mono text-slate-800">{estado.session}</span>
            </div>

            {/* Estado WAHA */}
            {estado.estado && (
              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-sm text-slate-600">Estado WAHA</span>
                <span className={`text-xs font-mono px-2 py-0.5 rounded-md ${
                  estado.estado === 'WORKING'
                    ? 'bg-green-100 text-green-700'
                    : estado.estado === 'NOT_FOUND'
                    ? 'bg-slate-100 text-slate-500'
                    : 'bg-amber-100 text-amber-700'
                }`}>
                  {estado.estado}
                </span>
              </div>
            )}

            {/* Error */}
            {estado.error && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg mt-2">
                <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                <p className="text-sm text-red-700">{estado.error}</p>
              </div>
            )}

            {/* No configurado */}
            {!estado.configurado && estado.mensaje && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg mt-2">
                <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-amber-700 font-medium">WAHA no configurado</p>
                  <p className="text-xs text-amber-600 mt-0.5">{estado.mensaje}</p>
                  <p className="text-xs text-amber-600 mt-1">
                    Agregá <code className="bg-amber-100 px-1 rounded">EVOLUTION_API_URL=http://waha:3001</code> en el archivo <code className="bg-amber-100 px-1 rounded">.env.production</code>.
                  </p>
                </div>
              </div>
            )}

            {/* Conectado pero desconectado de WA */}
            {estado.configurado && !estado.conectado && !estado.error && (
              <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg mt-2">
                <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm text-amber-700 font-medium">Sesión no activa</p>
                  <p className="text-xs text-amber-600 mt-0.5">
                    WAHA está corriendo pero la sesión <strong>{estado.session}</strong> no está conectada a WhatsApp.
                    Abrí <a href="http://localhost:3001" target="_blank" rel="noreferrer" className="underline">http://localhost:3001</a> (panel de WAHA) y escaneá el código QR con el teléfono de la cantina.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Formulario de prueba */}
      {estado?.conectado && (
        <div className="border border-slate-200 rounded-xl p-5 bg-white">
          <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4">
            Enviar mensaje de prueba
          </h3>
          <div className="space-y-4">
            <div>
              <label className={labelClass}>
                Número de teléfono
              </label>
              <input
                type="tel"
                placeholder="595981234567 (sin +, sin espacios)"
                value={telefono}
                onChange={e => setTelefono(e.target.value)}
                className={inputClass}
              />
              <p className="text-xs text-slate-400 mt-1">
                Formato internacional sin +. Ejemplo: 595981234567
              </p>
            </div>
            <div>
              <label className={labelClass}>
                Mensaje
              </label>
              <textarea
                rows={3}
                value={mensajePrueba}
                onChange={e => setMensajePrueba(e.target.value)}
                className={inputClass}
              />
            </div>
            <Button
              onClick={enviarPrueba}
              loading={enviando}
              disabled={!telefono.trim() || enviando}
              className="flex items-center gap-2"
            >
              <Send className="w-4 h-4" />
              Enviar mensaje de prueba
            </Button>
          </div>
        </div>
      )}

      {/* Información sobre notificaciones */}
      <div className="border border-slate-200 rounded-xl p-5 bg-white">
        <h3 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-3">
          Tipos de notificación por WhatsApp
        </h3>
        <p className="text-sm text-slate-500 mb-4">
          Se envían automáticamente a todo padre con teléfono cargado en su ficha, mientras
          las notificaciones estén activas a nivel sistema. Todavía no hay una opción para que
          un padre individual se dé de baja.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {[
            { label: 'Recarga de saldo',          desc: 'Al acreditar saldo en la tarjeta' },
            { label: 'Consumo en caja',           desc: 'Cada vez que el alumno compra' },
            { label: 'Saldo bajo',                desc: 'Cuando el saldo llega al mínimo' },
            { label: 'Consumo de almuerzo',       desc: 'Al registrar el almuerzo del día' },
            { label: 'Cuenta mensual generada',   desc: 'Al generar la cuota del mes' },
            { label: 'Pago de cuenta recibido',   desc: 'Al acreditar el pago mensual' },
          ].map(({ label, desc }) => (
            <div key={label} className="flex items-start gap-2.5 p-3 bg-slate-50 rounded-lg">
              <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium text-slate-700">{label}</p>
                <p className="text-xs text-slate-400">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
