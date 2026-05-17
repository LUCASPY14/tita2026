import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import { useAuthStore } from '../../store/authStore'
import Spinner from '../../components/ui/Spinner'
import Button from '../../components/ui/Button'

interface Hijo {
  id: number
  nombre_completo: string
  grado: string
}

interface TarjetaInfo {
  nro_tarjeta: string
  saldo_actual: string
}

interface CuentaAlmuerzo {
  id: number
  mes: number
  anio: number
  cantidad_almuerzos: number
  monto_total: string
  monto_pagado: string
  estado: string
}

export default function PortalDashboard() {
  const { user, logout } = useAuthStore()
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [tarjetas, setTarjetas] = useState<Record<number, TarjetaInfo>>({})
  const [cuentas, setCuentas] = useState<Record<number, CuentaAlmuerzo[]>>({})
  const [loading, setLoading] = useState(true)
  const [hijoExpandido, setHijoExpandido] = useState<number | null>(null)
  const [montoRecarga, setMontoRecarga] = useState<Record<number, number>>({})
  const [recargando, setRecargando] = useState(false)

  const meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

  const cargarDatos = async () => {
    if (!user?.cliente_id) return
    setLoading(true)
    try {
      const { data } = await api.get('/clientes/hijos/', {
        params: { cliente_responsable: user.cliente_id }
      })
      const lista: Hijo[] = data.results || []
      setHijos(lista)

      const tData: Record<number, TarjetaInfo> = {}
      const cData: Record<number, CuentaAlmuerzo[]> = {}
      
      for (const h of lista) {
        try {
          const { data: tResp } = await api.get('/core/tarjetas/', {
            params: { search: h.nombre_completo }
          })
          const encontrada = (tResp.results || []).find(
            (t: { hijo_nombre: string }) => t.hijo_nombre === h.nombre_completo
          )
          if (encontrada) tData[h.id] = encontrada
        } catch {}

        try {
          const { data: cResp } = await api.get('/almuerzos/cuentas-mensuales/', {
            params: { hijo: h.id, ordering: '-anio,-mes' }
          })
          cData[h.id] = cResp.results || []
        } catch {}
      }
      setTarjetas(tData)
      setCuentas(cData)
    } catch {} finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargarDatos() }, [user])

  const handleRecarga = async (hijoId: number, nroTarjeta: string) => {
    const monto = montoRecarga[hijoId]
    if (!monto || monto < 1000) {
      toast.error('Ingrese un monto válido (mínimo Gs. 1.000)')
      return
    }
    setRecargando(true)
    try {
      await api.post('/core/cargas-saldo/', {
        tarjeta: nroTarjeta,
        monto_cargado: monto,
        metodo_pago: 'EFECTIVO',
      })
      toast.success('Recarga exitosa')
      setMontoRecarga((prev) => ({ ...prev, [hijoId]: 0 }))
      cargarDatos()
    } catch {
      toast.error('Error al recargar')
    } finally {
      setRecargando(false)
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Bienvenido, {user?.nombre}</h2>
          <p className="text-gray-500">Portal de Padres</p>
        </div>
        <button onClick={logout} className="text-sm text-red-500 hover:underline">
          Cerrar sesión
        </button>
      </div>

      <div className="grid gap-6">
        {hijos.map((hijo) => (
          <div key={hijo.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Cabecera */}
            <div className="p-6">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-bold text-gray-800">{hijo.nombre_completo}</h3>
                  <p className="text-sm text-gray-500">{hijo.grado || 'Sin grado'}</p>
                </div>
                {tarjetas[hijo.id] && (
                  <div className="text-right">
                    <p className="text-xs text-gray-400">Saldo tarjeta</p>
                    <p className="text-2xl font-bold text-green-700">
                      Gs. {parseInt(tarjetas[hijo.id].saldo_actual).toLocaleString('es-PY')}
                    </p>
                    <p className="text-xs text-gray-400">{tarjetas[hijo.id].nro_tarjeta}</p>
                  </div>
                )}
              </div>

              {/* Cuenta almuerzo */}
              {cuentas[hijo.id]?.length > 0 && (
                <div className="mt-4 bg-orange-50 rounded-lg p-3">
                  <p className="text-sm font-bold text-orange-800">
                    🍽️ Cuenta Almuerzo - {meses[cuentas[hijo.id][0].mes]} {cuentas[hijo.id][0].anio}
                  </p>
                  <div className="flex justify-between mt-1 text-sm">
                    <span>Total: Gs. {parseInt(cuentas[hijo.id][0].monto_total).toLocaleString('es-PY')}</span>
                    <span>Pagado: Gs. {parseInt(cuentas[hijo.id][0].monto_pagado).toLocaleString('es-PY')}</span>
                    <span className="font-bold text-red-600">
                      Pendiente: Gs. {(parseInt(cuentas[hijo.id][0].monto_total) - parseInt(cuentas[hijo.id][0].monto_pagado)).toLocaleString('es-PY')}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Acciones */}
            <div className="bg-gray-50 px-6 py-3 flex gap-2 border-t">
              {tarjetas[hijo.id] && (
                <div className="flex gap-1 flex-1">
                  <input
                    type="number"
                    placeholder="Monto Gs."
                    className="border rounded px-2 py-1 w-28 text-sm"
                    value={montoRecarga[hijo.id] || ''}
                    onChange={(e) => setMontoRecarga((prev) => ({ ...prev, [hijo.id]: parseInt(e.target.value) || 0 }))}
                  />
                  <Button
                    size="sm"
                    variant="primary"
                    loading={recargando}
                    onClick={() => handleRecarga(hijo.id, tarjetas[hijo.id].nro_tarjeta)}
                  >
                    Recargar
                  </Button>
                </div>
              )}
              <Button
                size="sm"
                variant="secondary"
                onClick={() => setHijoExpandido(hijoExpandido === hijo.id ? null : hijo.id)}
              >
                {hijoExpandido === hijo.id ? 'Ocultar' : 'Ver consumos'}
              </Button>
            </div>

            {/* Consumos expandidos */}
            {hijoExpandido === hijo.id && cuentas[hijo.id] && (
              <div className="px-6 pb-4">
                <table className="w-full text-sm mt-2">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="py-2">Mes</th>
                      <th className="py-2">Almuerzos</th>
                      <th className="py-2">Total</th>
                      <th className="py-2">Pagado</th>
                      <th className="py-2">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cuentas[hijo.id].map((c) => (
                      <tr key={c.id} className="border-b border-gray-100">
                        <td className="py-2">{meses[c.mes]} {c.anio}</td>
                        <td className="py-2">{c.cantidad_almuerzos}</td>
                        <td className="py-2">Gs. {parseInt(c.monto_total).toLocaleString('es-PY')}</td>
                        <td className="py-2">Gs. {parseInt(c.monto_pagado).toLocaleString('es-PY')}</td>
                        <td className="py-2">
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            c.estado === 'PAGADO' ? 'bg-green-100 text-green-800' :
                            c.estado === 'PARCIAL' ? 'bg-blue-100 text-blue-800' :
                            'bg-orange-100 text-orange-800'
                          }`}>
                            {c.estado}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}
        {hijos.length === 0 && (
          <p className="text-center text-gray-400 py-8">
            No se encontraron hijos asociados a tu cuenta.
          </p>
        )}
      </div>
    </div>
  )
}