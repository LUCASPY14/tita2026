import { useEffect, useState } from 'react'
import api from '../services/api'
import Spinner from '../components/ui/Spinner'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'

interface Resumen {
  ventasHoy: number
  clientes: number
  productos: number
  stockBajo: number
  cajasAbiertas: number
}

const statCards = (r: Resumen) => [
  { title: 'Ventas Hoy', value: r.ventasHoy, suffix: 'ventas', icon: '💰', color: 'bg-blue-50 text-blue-800' },
  { title: 'Clientes', value: r.clientes, suffix: 'registrados', icon: '👥', color: 'bg-green-50 text-green-800' },
  { title: 'Productos', value: r.productos, suffix: 'en catálogo', icon: '📦', color: 'bg-orange-50 text-orange-800' },
  { title: 'Stock Bajo', value: r.stockBajo, suffix: 'productos', icon: '⚠', color: r.stockBajo > 0 ? 'bg-red-50 text-red-800' : 'bg-green-50 text-green-800' },
  { title: 'Cajas Abiertas', value: r.cajasAbiertas, suffix: 'cajas', icon: '🏧', color: 'bg-purple-50 text-purple-800' },
]

export default function Dashboard() {
  const [resumen, setResumen] = useState<Resumen>({ ventasHoy: 0, clientes: 0, productos: 0, stockBajo: 0, cajasAbiertas: 0 })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const hoy = new Date().toISOString().split('T')[0]
    Promise.all([
      api.get('/ventas/ventas/', { params: { fecha: hoy } }),
      api.get('/clientes/clientes/'),
      api.get('/productos/productos/'),
      api.get('/inventario/stock/'),
      api.get('/contabilidad/cierres-caja/', { params: { estado: 'ABIERTO' } }),
    ])
      .then(([v, c, p, s, ca]) => {
        setResumen({
          ventasHoy: v.data.count || 0,
          clientes: c.data.count || 0,
          productos: p.data.count || 0,
          stockBajo: (s.data.results || []).filter((x: { requiere_reposicion: boolean }) => x.requiere_reposicion).length,
          cajasAbiertas: ca.data.count || 0,
        })
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner className="mt-20" />

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Panel de Control</h2>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 mb-8">
        {statCards(resumen).map((card) => (
          <div key={card.title} className={`rounded-lg p-4 ${card.color}`}>
            <div className="flex justify-between items-start">
              <div>
                <p className="text-xs opacity-75 font-medium">{card.title}</p>
                <p className="text-3xl font-bold mt-1">{card.value}</p>
                <p className="text-xs opacity-75 mt-0.5">{card.suffix}</p>
              </div>
              <span className="text-3xl opacity-40">{card.icon}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Accesos Rapidos">
          <div className="grid grid-cols-2 gap-3">
            {[
              { href: '/ventas', color: 'blue', icon: '💰', label: 'Nueva Venta' },
              { href: '/tarjetas', color: 'green', icon: '💳', label: 'Recargar Tarjeta' },
              { href: '/caja', color: 'purple', icon: '🏧', label: 'Abrir Caja' },
              { href: '/compras', color: 'orange', icon: '🚚', label: 'Nueva Compra' },
            ].map((item) => (
              <a
                key={item.href}
                href={item.href}
                className={`p-4 bg-${item.color}-50 rounded-lg hover:bg-${item.color}-100 text-center transition-colors`}
              >
                <div className="text-2xl mb-1">{item.icon}</div>
                <p className="font-medium text-sm text-gray-800">{item.label}</p>
              </a>
            ))}
          </div>
        </Card>

        <Card title="Estado del Sistema">
          <div className="space-y-3">
            {[
              { label: 'Conexion API', badge: 'Conectado' as const, color: 'green' as const },
              { label: 'Base de datos', badge: 'PostgreSQL' as const, color: 'blue' as const },
              { label: 'Version', badge: '1.0.0' as const, color: 'default' as const },
            ].map((row) => (
              <div key={row.label} className="flex justify-between items-center py-1 border-b border-gray-100 last:border-0">
                <span className="text-sm text-gray-700">{row.label}</span>
                <Badge color={row.color}>{row.badge}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
