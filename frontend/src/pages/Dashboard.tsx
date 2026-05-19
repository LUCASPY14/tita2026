import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShoppingCart, Users, Package, AlertTriangle, Banknote,
  TrendingUp, CreditCard, Truck, ArrowRight,
} from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import Badge from '../components/ui/Badge'
import Spinner from '../components/ui/Spinner'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Resumen {
  ventasHoy: number
  montoHoy: number
  clientes: number
  productos: number
  stockBajo: number
  cajasAbiertas: number
}

interface VentaTipo {
  tipo: string
  cantidad: number
  monto: number
}

interface ChartData {
  por_tipo: VentaTipo[]
  monto_total: number
  cantidad_total: number
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getWeekRange() {
  const hoy = new Date()
  const desde = new Date(hoy)
  desde.setDate(hoy.getDate() - 6)
  const fmt = (d: Date) => d.toISOString().slice(0, 10)
  return { desde: fmt(desde), hasta: fmt(hoy) }
}

function formatGs(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}k`
  return String(n)
}

const TIPO_LABEL: Record<string, string> = { CONTADO: 'Contado', CREDITO: 'Crédito', TARJETA: 'Tarjeta' }
const PIE_COLORS = ['#22c55e', '#3b82f6', '#f59e0b', '#8b5cf6']

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [resumen, setResumen] = useState<Resumen | null>(null)
  const [chart, setChart] = useState<ChartData | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const { user } = useAuthStore()

  useEffect(() => {
    const { desde, hasta } = getWeekRange()
    Promise.all([
      api.get('/contabilidad/dashboard/'),
      api.get('/contabilidad/reportes/', { params: { fecha_desde: desde, fecha_hasta: hasta } }),
    ])
      .then(([dashRes, repRes]) => {
        setResumen(dashRes.data)
        const v = repRes.data?.ventas
        setChart({
          por_tipo: v?.por_tipo ?? [],
          monto_total: v?.monto_total ?? 0,
          cantidad_total: v?.cantidad ?? 0,
        })
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const hora = new Date().getHours()
  const saludo = hora < 12 ? 'Buenos días' : hora < 19 ? 'Buenas tardes' : 'Buenas noches'

  if (loading) return <Spinner className="mt-24" />

  const r = resumen ?? { ventasHoy: 0, montoHoy: 0, clientes: 0, productos: 0, stockBajo: 0, cajasAbiertas: 0 }

  const stats = [
    {
      label: 'Ventas Hoy', value: r.ventasHoy, sub: `${r.montoHoy.toLocaleString('es-PY')} Gs.`,
      icon: ShoppingCart, color: 'text-blue-600', bg: 'bg-blue-50',
    },
    {
      label: 'Clientes Activos', value: r.clientes, sub: 'registrados',
      icon: Users, color: 'text-green-600', bg: 'bg-green-50',
    },
    {
      label: 'Productos', value: r.productos, sub: 'en catálogo',
      icon: Package, color: 'text-orange-600', bg: 'bg-orange-50',
    },
    {
      label: 'Alertas Stock', value: r.stockBajo, sub: 'activas',
      icon: AlertTriangle,
      color: r.stockBajo > 0 ? 'text-red-600' : 'text-slate-400',
      bg: r.stockBajo > 0 ? 'bg-red-50' : 'bg-slate-50',
    },
    {
      label: 'Cajas Abiertas', value: r.cajasAbiertas, sub: 'en operación',
      icon: Banknote, color: 'text-purple-600', bg: 'bg-purple-50',
    },
  ]

  const accesos = [
    { path: '/ventas', label: 'Nueva Venta', icon: ShoppingCart, color: 'bg-blue-600', desc: 'Registrar venta en POS' },
    { path: '/tarjetas', label: 'Recargar Tarjeta', icon: CreditCard, color: 'bg-emerald-600', desc: 'Carga de saldo' },
    { path: '/caja', label: 'Gestionar Caja', icon: Banknote, color: 'bg-purple-600', desc: 'Abrir / cerrar caja' },
    { path: '/compras', label: 'Nueva Compra', icon: Truck, color: 'bg-orange-600', desc: 'Registrar ingreso de stock' },
  ]

  const pieData = (chart?.por_tipo ?? []).map(t => ({
    name: TIPO_LABEL[t.tipo] ?? t.tipo,
    value: Number(t.monto) || 0,
    cantidad: t.cantidad,
  }))

  const barData = (chart?.por_tipo ?? []).map(t => ({
    tipo: TIPO_LABEL[t.tipo] ?? t.tipo,
    Ventas: t.cantidad,
    'Monto (k)': Math.round((Number(t.monto) || 0) / 1000),
  }))

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">
          {saludo}, {user?.nombre ?? 'Usuario'}
        </h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Resumen del día — {new Date().toLocaleDateString('es-PY', {
            weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
          })}
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {stats.map(({ label, value, sub, icon: Icon, color, bg }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-4">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide truncate">{label}</p>
                <p className={`text-3xl font-bold mt-1 tabular-nums ${color}`}>{value}</p>
                <p className="text-xs text-slate-400 mt-0.5 truncate">{sub}</p>
              </div>
              <div className={`w-9 h-9 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
                <Icon className={`w-4.5 h-4.5 ${color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Accesos rápidos */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Accesos Rápidos</h2>
          </div>
          <div className="p-5 grid grid-cols-2 gap-3">
            {accesos.map(({ path, label, icon: Icon, color, desc }) => (
              <button
                key={path}
                onClick={() => navigate(path)}
                className="flex items-center gap-3 p-4 rounded-xl border border-slate-100 hover:border-slate-200 hover:bg-slate-50/80 transition-all group text-left"
              >
                <div className={`w-10 h-10 ${color} rounded-xl flex items-center justify-center shrink-0`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800 group-hover:text-slate-900">{label}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition-colors shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Estado del sistema */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Estado del Sistema</h2>
          </div>
          <div className="px-6 py-4 space-y-3">
            {[
              { label: 'API', badge: 'Conectado', color: 'green' as const },
              { label: 'Base de datos', badge: 'PostgreSQL', color: 'blue' as const },
              { label: 'Versión', badge: '1.0.0', color: 'default' as const },
              { label: 'Entorno', badge: 'Producción', color: 'purple' as const },
            ].map(({ label, badge, color }) => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                <span className="text-sm text-slate-600">{label}</span>
                <Badge color={color}>{badge}</Badge>
              </div>
            ))}
          </div>
          <div className="px-6 pb-5">
            <div className="flex items-center gap-2 mt-2 p-3 bg-green-50 rounded-xl">
              <TrendingUp className="w-4 h-4 text-green-600 shrink-0" />
              <p className="text-xs text-green-700 font-medium">
                {r.cajasAbiertas > 0
                  ? `${r.cajasAbiertas} caja${r.cajasAbiertas !== 1 ? 's' : ''} en operación`
                  : 'Sin cajas abiertas hoy'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Gráficos de la semana ─────────────────────────────────────────────── */}
      {chart && chart.por_tipo.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Distribución por tipo */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-800">Ventas por tipo — últimos 7 días</h2>
              <span className="text-xs text-slate-400 tabular-nums">
                {chart.cantidad_total} ventas · Gs. {chart.monto_total.toLocaleString('es-PY')}
              </span>
            </div>
            <div className="p-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(v: number) => [`Gs. ${v.toLocaleString('es-PY')}`, 'Monto']}
                  />
                  <Legend
                    formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Comparativa por tipo */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="text-sm font-semibold text-slate-800">Comparativa de ventas</h2>
            </div>
            <div className="p-4 h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="tipo" tick={{ fontSize: 12, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                    formatter={(v: number, name: string) =>
                      name === 'Monto (k)' ? [`${formatGs(v * 1000)} Gs.`, 'Monto'] : [v, name]
                    }
                  />
                  <Legend formatter={(v) => <span className="text-xs text-slate-600">{v}</span>} />
                  <Bar dataKey="Ventas" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Monto (k)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Stock crítico alert */}
      {r.stockBajo > 0 && (
        <div
          className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-2xl px-5 py-3 cursor-pointer hover:bg-red-100 transition-colors group"
          onClick={() => navigate('/productos')}
        >
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-sm text-red-800 flex-1">
            <span className="font-semibold">{r.stockBajo} alerta{r.stockBajo !== 1 ? 's' : ''} de stock</span>
            {' '}activa{r.stockBajo !== 1 ? 's' : ''}. Revisá el módulo de Productos.
          </p>
          <ArrowRight className="w-4 h-4 text-red-400 group-hover:text-red-600 transition-colors" />
        </div>
      )}
    </div>
  )
}
