import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ShoppingCart, Users, Package, AlertTriangle, Banknote,
  TrendingUp, CreditCard, Truck, ArrowRight,
  Zap, ChefHat, BarChart2, Wallet, UtensilsCrossed, Warehouse,
} from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
} from 'recharts'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import { useDashboardKPI } from '../hooks/useDashboardKPI'
import Badge from '../components/ui/Badge'
import Spinner from '../components/ui/Spinner'

// ─── Interfaces ───────────────────────────────────────────────────────────────

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

interface TendenciaPoint {
  fecha: string
  cantidad: number
  monto: number
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
  const [chart, setChart] = useState<ChartData | null>(null)
  const [tendencia, setTendencia] = useState<TendenciaPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [hiddenPie, setHiddenPie] = useState<Set<string>>(new Set())
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { kpi: resumen, connected: wsConnected } = useDashboardKPI()

  const showCharts = user?.rol !== 'COCINA'

  useEffect(() => {
    const { desde, hasta } = getWeekRange()
    const reqs: Promise<{ data: unknown }>[] = []
    if (showCharts) {
      reqs.push(
        api.get('/contabilidad/reportes/', { params: { fecha_desde: desde, fecha_hasta: hasta } }),
        api.get('/contabilidad/dashboard/tendencia/', { params: { dias: 14 } }),
      )
    }
    if (reqs.length === 0) { setLoading(false); return }
    Promise.all(reqs)
      .then(([repRes, tendRes]) => {
        if (showCharts && repRes) {
          const v = (repRes.data as { ventas?: { por_tipo?: VentaTipo[]; monto_total?: number; cantidad?: number } })?.ventas
          setChart({ por_tipo: v?.por_tipo ?? [], monto_total: v?.monto_total ?? 0, cantidad_total: v?.cantidad ?? 0 })
          setTendencia(((tendRes?.data as { data?: TendenciaPoint[] })?.data) ?? [])
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [showCharts])

  const hora = new Date().getHours()
  const saludo = hora < 12 ? 'Buenos días' : hora < 19 ? 'Buenas tardes' : 'Buenas noches'

  const r = useMemo(
    () => resumen ?? { ventasHoy: 0, montoHoy: 0, clientes: 0, productos: 0, stockBajo: 0, cajasAbiertas: 0 },
    [resumen]
  )

  const ALL_STATS = useMemo(() => [
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
      link: '/inventario',
    },
    {
      label: 'Cajas Abiertas', value: r.cajasAbiertas, sub: 'en operación',
      icon: Banknote, color: 'text-purple-600', bg: 'bg-purple-50',
    },
  ], [r])

  const STATS_POR_ROL: Record<string, string[]> = {
    ADMIN:      ['Ventas Hoy', 'Clientes Activos', 'Productos', 'Alertas Stock', 'Cajas Abiertas'],
    CAJERO:     ['Ventas Hoy', 'Alertas Stock', 'Cajas Abiertas'],
    SUPERVISOR: ['Ventas Hoy', 'Clientes Activos', 'Productos', 'Alertas Stock', 'Cajas Abiertas'],
    COBRADOR:   ['Ventas Hoy', 'Clientes Activos', 'Alertas Stock', 'Cajas Abiertas'],
    COCINA:     ['Ventas Hoy', 'Cajas Abiertas'],
  }

  const stats = useMemo(() => {
    const allowed = STATS_POR_ROL[user?.rol ?? '']
    return allowed ? ALL_STATS.filter(s => allowed.includes(s.label)) : ALL_STATS
  }, [ALL_STATS, user?.rol])

  const pieData = useMemo(
    () => (chart?.por_tipo ?? []).map(t => ({
      name: TIPO_LABEL[t.tipo] ?? t.tipo,
      value: Number(t.monto) || 0,
      cantidad: t.cantidad,
    })),
    [chart]
  )

  const pieDataFiltered = useMemo(
    () => pieData.filter(d => !hiddenPie.has(d.name)),
    [pieData, hiddenPie]
  )

  const barData = useMemo(
    () => (chart?.por_tipo ?? []).map(t => ({
      tipo: TIPO_LABEL[t.tipo] ?? t.tipo,
      Ventas: t.cantidad,
      'Monto (k)': Math.round((Number(t.monto) || 0) / 1000),
    })),
    [chart]
  )

  const tendenciaData = useMemo(
    () => tendencia.map(d => ({
      dia: new Date(d.fecha + 'T00:00:00').toLocaleDateString('es-PY', { day: '2-digit', month: '2-digit' }),
      Ventas: d.cantidad,
      'Monto (k)': Math.round(d.monto / 1000),
    })),
    [tendencia]
  )

  const togglePieSeries = useCallback((name: string) => {
    setHiddenPie(prev => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }, [])

  const renderPieLegend = ({ payload = [] }: { payload?: ReadonlyArray<{ value: unknown; color?: string }> }) => (
    <div className="flex flex-wrap justify-center gap-1.5 mt-2 px-2">
      {payload.map((entry, i) => {
        const name = String(entry.value)
        const hidden = hiddenPie.has(name)
        return (
          <button
            key={i}
            onClick={() => togglePieSeries(name)}
            className={`flex items-center gap-1.5 text-sm px-2.5 py-1 rounded-full border transition-all cursor-pointer select-none ${
              hidden
                ? 'border-slate-200 text-slate-400 bg-slate-50 line-through'
                : 'border-slate-200 text-slate-600 bg-white hover:bg-slate-50'
            }`}
          >
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: hidden ? '#cbd5e1' : (entry.color ?? PIE_COLORS[i % PIE_COLORS.length]) }}
            />
            {name}
          </button>
        )
      })}
    </div>
  )

  if (loading) return <Spinner className="mt-24" />

  const rol = user?.rol ?? ''
  const accesos = [
    { path: '/modo-recreo',  label: 'Modo Recreo',      icon: Zap,            color: 'bg-green-600',   desc: 'POS — venta en recreo',        roles: ['ADMIN', 'CAJERO'] },
    { path: '/carga-saldo',  label: 'Recargar Tarjeta', icon: Wallet,         color: 'bg-emerald-600', desc: 'Carga de saldo RFID',           roles: ['ADMIN', 'CAJERO'] },
    { path: '/caja',         label: 'Gestionar Caja',   icon: Banknote,       color: 'bg-purple-600',  desc: 'Abrir / cerrar caja',           roles: ['ADMIN', 'CAJERO'] },
    { path: '/almuerzos',    label: 'Almuerzos',        icon: UtensilsCrossed, color: 'bg-amber-600',  desc: 'Gestión de almuerzos',          roles: ['ADMIN', 'CAJERO', 'SUPERVISOR', 'COCINA'] },
    { path: '/comedor',      label: 'Comedor',          icon: ChefHat,        color: 'bg-teal-600',    desc: 'Registro de servicio comedor',  roles: ['ADMIN', 'COCINA'] },
    { path: '/menu-diario',  label: 'Menú Diario',      icon: ChefHat,        color: 'bg-orange-600',  desc: 'Configurar menú del día',       roles: ['ADMIN', 'SUPERVISOR', 'COCINA'] },
    { path: '/clientes',     label: 'Clientes',         icon: Users,          color: 'bg-cyan-600',    desc: 'Ver y gestionar clientes',      roles: ['ADMIN', 'CAJERO', 'SUPERVISOR', 'COBRADOR'] },
    { path: '/tarjetas',     label: 'Tarjetas',         icon: CreditCard,     color: 'bg-sky-600',     desc: 'Gestión de tarjetas RFID',     roles: ['ADMIN', 'CAJERO', 'SUPERVISOR', 'COBRADOR'] },
    { path: '/inventario',   label: 'Inventario',       icon: Warehouse,      color: 'bg-slate-600',   desc: 'Stock y alertas',               roles: ['ADMIN', 'SUPERVISOR'] },
    { path: '/reportes',     label: 'Reportes',         icon: BarChart2,      color: 'bg-rose-600',    desc: 'Ver reportes del período',      roles: ['ADMIN', 'SUPERVISOR', 'COBRADOR'] },
    { path: '/compras',      label: 'Compras',          icon: Truck,          color: 'bg-indigo-600',  desc: 'Registrar ingreso de stock',    roles: ['ADMIN', 'CAJERO', 'SUPERVISOR'] },
    { path: '/facturacion',  label: 'Facturación',      icon: CreditCard,     color: 'bg-blue-600',    desc: 'Emitir facturas',               roles: ['ADMIN', 'CAJERO', 'COBRADOR'] },
  ].filter(a => a.roles.includes(rol))

  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-slate-900">
            {saludo}, {user?.nombre ?? 'Usuario'}
          </h1>
          <p className="text-lg text-slate-500 mt-0.5">
            Resumen del día — {new Date().toLocaleDateString('es-PY', {
              weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
            })}
          </p>
        </div>
        <div className={`flex items-center gap-1.5 mt-1 text-xs font-medium px-2.5 py-1 rounded-full border ${
          wsConnected
            ? 'text-green-700 bg-green-50 border-green-200'
            : 'text-slate-400 bg-slate-50 border-slate-200'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-slate-300'}`} />
          {wsConnected ? 'En vivo' : 'Sin conexión'}
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {stats.map(({ label, value, sub, icon: Icon, color, bg, link }) => {
          const inner = (
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide truncate">{label}</p>
                <p className={`text-5xl font-bold mt-1.5 tabular-nums ${color}`}>{value}</p>
                <p className="text-base text-slate-400 mt-1 truncate">{sub}</p>
              </div>
              <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center shrink-0`}>
                <Icon className={`w-6 h-6 ${color}`} />
              </div>
            </div>
          )
          return link ? (
            <button
              key={label}
              type="button"
              onClick={() => navigate(link)}
              title={`Ver ${label}`}
              className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-5 text-left cursor-pointer hover:shadow-md hover:border-slate-200 transition-all"
            >
              {inner}
            </button>
          ) : (
            <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-5">
              {inner}
            </div>
          )
        })}
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Accesos rápidos */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-800">Accesos Rápidos</h2>
          </div>
          <div className="p-5 grid grid-cols-2 gap-3">
            {accesos.map(({ path, label, icon: Icon, color, desc }) => (
              <button
                key={path}
                onClick={() => navigate(path)}
                className="flex items-center gap-3 p-4 rounded-xl border border-slate-100 hover:border-slate-200 hover:bg-slate-50/80 transition-all group text-left"
              >
                <div className={`w-12 h-12 ${color} rounded-xl flex items-center justify-center shrink-0`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-base font-semibold text-slate-800 group-hover:text-slate-900">{label}</p>
                  <p className="text-sm text-slate-400 mt-0.5">{desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition-colors shrink-0" />
              </button>
            ))}
          </div>
        </div>

        {/* Estado del sistema */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-800">Estado del Sistema</h2>
          </div>
          <div className="px-6 py-4 space-y-3">
            {[
              { label: 'API', badge: 'Conectado', color: 'green' as const },
              { label: 'Base de datos', badge: 'PostgreSQL', color: 'blue' as const },
              { label: 'Versión', badge: '1.0.0', color: 'default' as const },
              { label: 'Entorno', badge: 'Producción', color: 'purple' as const },
            ].map(({ label, badge, color }) => (
              <div key={label} className="flex items-center justify-between py-1.5 border-b border-slate-50 last:border-0">
                <span className="text-base text-slate-600">{label}</span>
                <Badge color={color}>{badge}</Badge>
              </div>
            ))}
          </div>
          <div className="px-6 pb-5">
            <div className="flex items-center gap-2 mt-2 p-3 bg-green-50 rounded-xl">
              <TrendingUp className="w-4 h-4 text-green-600 shrink-0" />
              <p className="text-base text-green-700 font-medium">
                {r.cajasAbiertas > 0
                  ? `${r.cajasAbiertas} caja${r.cajasAbiertas !== 1 ? 's' : ''} en operación`
                  : 'Sin cajas abiertas hoy'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Tendencia de ventas ───────────────────────────────────────────────── */}
      {showCharts && tendenciaData.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800">Tendencia de ventas — últimos 14 días</h2>
            <span className="text-sm text-slate-400 tabular-nums">
              {tendencia.reduce((s, d) => s + d.cantidad, 0)} ventas
            </span>
          </div>
          <div className="p-4 h-64">
            <ResponsiveContainer width="100%" height="100%" minWidth={0}>
              <AreaChart data={tendenciaData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="dia" tick={{ fontSize: 11, fill: '#94a3b8' }} interval={1} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                  formatter={(v, name) =>
                    name === 'Monto (k)' ? [`${formatGs((Number(v) || 0) * 1000)} Gs.`, 'Monto'] : [Number(v), String(name)]
                  }
                />
                <Legend formatter={(v) => <span className="text-sm text-slate-600">{v}</span>} />
                <Area type="monotone" dataKey="Ventas" stroke="#22c55e" fill="#22c55e20" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="Monto (k)" stroke="#3b82f6" fill="#3b82f620" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* ── Gráficos de la semana ─────────────────────────────────────────────── */}
      {showCharts && chart && chart.por_tipo.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Distribución por tipo */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-800">Ventas por tipo — últimos 7 días</h2>
              <span className="text-sm text-slate-400 tabular-nums">
                {chart.cantidad_total} ventas · Gs. {chart.monto_total.toLocaleString('es-PY')}
              </span>
            </div>
            <div className="p-4 h-64">
              <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <PieChart>
                  <Pie
                    data={pieDataFiltered}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {pieDataFiltered.map((entry, i) => {
                      const origIdx = pieData.findIndex(d => d.name === entry.name)
                      return (
                        <Cell key={i} fill={PIE_COLORS[(origIdx >= 0 ? origIdx : i) % PIE_COLORS.length]} />
                      )
                    })}
                  </Pie>
                  <Tooltip
                    formatter={(v) => [`Gs. ${(Number(v) || 0).toLocaleString('es-PY')}`, 'Monto']}
                  />
                  <Legend content={renderPieLegend} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Comparativa por tipo */}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="text-lg font-semibold text-slate-800">Comparativa de ventas</h2>
            </div>
            <div className="p-4 h-64">
              <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                <BarChart data={barData} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="tipo" tick={{ fontSize: 12, fill: '#64748b' }} />
                  <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} />
                  <Tooltip
                    contentStyle={{ borderRadius: 12, border: '1px solid #e2e8f0', fontSize: 12 }}
                    formatter={(v, name) =>
                      name === 'Monto (k)' ? [`${formatGs((Number(v) || 0) * 1000)} Gs.`, 'Monto'] : [Number(v), String(name)]
                    }
                  />
                  <Legend formatter={(v) => <span className="text-sm text-slate-600">{v}</span>} />
                  <Bar dataKey="Ventas" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Monto (k)" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Stock crítico alert */}
      {r.stockBajo > 0 && ['ADMIN', 'SUPERVISOR', 'CAJERO'].includes(rol) && (
        <div
          className="flex items-center gap-3 bg-red-50 border border-red-200 rounded-2xl px-5 py-3 cursor-pointer hover:bg-red-100 transition-colors group"
          onClick={() => navigate('/productos')}
        >
          <AlertTriangle className="w-5 h-5 text-red-500 shrink-0" />
          <p className="text-base text-red-800 flex-1">
            <span className="font-semibold">{r.stockBajo} alerta{r.stockBajo !== 1 ? 's' : ''} de stock</span>
            {' '}activa{r.stockBajo !== 1 ? 's' : ''}. Revisá el módulo de Productos.
          </p>
          <ArrowRight className="w-4 h-4 text-red-400 group-hover:text-red-600 transition-colors" />
        </div>
      )}
    </div>
  )
}
