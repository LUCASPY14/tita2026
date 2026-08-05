import { useState, useMemo, useEffect } from 'react'
import toast from 'react-hot-toast'
import { UtensilsCrossed, TrendingUp, Download, FileText } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import api from '../../services/api'
import { exportarAlmuerzosPDF } from '../../utils/pdf'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import { formatGs, descargaBlob, ESTADO_ALM_COLOR } from './reportesUtils'
import {
  FilterBar, EmptyState,
  type AlmuerzosData, type AlmuerzoFila,
} from './shared'

interface GradoOption { id: number; nombre: string; activo: boolean }

export default function TabAlmuerzos() {
  const hoy = new Date()
  const [anioAlm, setAnioAlm] = useState(hoy.getFullYear())
  const [mesAlm, setMesAlm] = useState(hoy.getMonth() + 1)
  const [gradoAlm, setGradoAlm] = useState('')
  const [tarjetaAlm, setTarjetaAlm] = useState('')
  const [almuerzosData, setAlmuerzosData] = useState<AlmuerzosData | null>(null)
  const [loadingAlm, setLoadingAlm] = useState(false)
  const [grados, setGrados] = useState<GradoOption[]>([])

  // El filtro sale de los grados reales (clientes_grado), no de texto libre —
  // así coincide siempre con lo que el backend filtra (grado__nombre__icontains).
  useEffect(() => {
    api.get<{ results?: GradoOption[] } | GradoOption[]>('/clientes/grados/', { params: { page_size: 100 } })
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : (data.results ?? [])
        setGrados(list.filter(g => g.activo))
      })
      .catch(() => { /* el filtro simplemente queda vacío si falla */ })
  }, [])

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  function almParams(extra?: Record<string, unknown>) {
    return {
      anio: anioAlm, mes: mesAlm,
      ...(gradoAlm ? { grado: gradoAlm } : {}),
      ...(tarjetaAlm ? { tarjeta: tarjetaAlm } : {}),
      ...extra,
    }
  }

  async function cargarAlmuerzos() {
    setLoadingAlm(true)
    try {
      const { data: res } = await api.get('/almuerzos/reportes/', { params: almParams() })
      setAlmuerzosData(res)
    } catch { toast.error('Error al cargar reporte de almuerzos') }
    finally { setLoadingAlm(false) }
  }

  async function exportarAlmuerzosCSV() {
    try {
      const res = await api.get('/almuerzos/reportes/', {
        params: almParams({ formato: 'csv' }),
        responseType: 'blob',
      })
      descargaBlob(res.data, `almuerzos_${anioAlm}_${String(mesAlm).padStart(2, '0')}.csv`)
      toast.success('CSV descargado')
    } catch { toast.error('Error al exportar') }
  }

  function handleAlmuerzosPDF() {
    if (!almuerzosData) return
    try {
      exportarAlmuerzosPDF(almuerzosData.filas, almuerzosData.totales, anioAlm, mesAlm || undefined, gradoAlm || undefined)
      toast.success('PDF descargado')
    } catch { toast.error('Error al generar PDF') }
  }

  const filasAlmVisibles = useMemo(() => {
    const filas = almuerzosData?.filas ?? []
    const g = gradoAlm.trim().toLowerCase()
    const t = tarjetaAlm.trim().toLowerCase()
    if (!g && !t) return filas
    return filas.filter(r =>
      (!g || r.grado.toLowerCase().includes(g) || r.hijo.toLowerCase().includes(g)) &&
      (!t || r.nro_tarjeta.toLowerCase().includes(t))
    )
  }, [almuerzosData, gradoAlm, tarjetaAlm])

  const colsAlmuerzos: Column<AlmuerzoFila>[] = [
    {
      title: 'Alumno', key: 'hijo',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.hijo}</p>
          <p className="text-sm text-slate-400">{r.grado || '—'}</p>
        </div>
      ),
    },
    {
      title: 'Tarjeta', key: 'nro_tarjeta',
      render: (_, r) => <span className="font-mono text-sm text-slate-600">{r.nro_tarjeta || '—'}</span>,
    },
    {
      title: 'Almuerzos', key: 'cantidad_almuerzos',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{r.cantidad_almuerzos}</span>,
    },
    {
      title: 'Total', key: 'monto_total',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'Pagado', key: 'monto_pagado',
      render: (_, r) => <span className="tabular-nums text-sm text-emerald-700 font-semibold">{formatGs(r.monto_pagado)}</span>,
    },
    {
      title: 'Pendiente', key: 'monto_pendiente',
      render: (_, r) => (
        <span className={`tabular-nums text-sm font-bold ${r.monto_pendiente > 0 ? 'text-red-600' : 'text-slate-400'}`}>
          {formatGs(r.monto_pendiente)}
        </span>
      ),
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_ALM_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
  ]

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Año</label>
          <input
            type="number" min={2020} max={2099} value={anioAlm}
            onChange={e => setAnioAlm(Number(e.target.value))}
            className={`${inputDateClass} w-24`}
          />
        </div>
        <div>
          <label className={labelClass}>Mes</label>
          <select value={mesAlm} onChange={e => setMesAlm(Number(e.target.value))} className={`${inputDateClass} w-auto`}>
            {['Enero','Febrero','Marzo','Abril','Mayo','Junio',
              'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'].map((m, i) => (
              <option key={i + 1} value={i + 1}>{m}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Grado</label>
          <select value={gradoAlm} onChange={e => setGradoAlm(e.target.value)} className={`${inputDateClass} w-40`}>
            <option value="">Todos</option>
            {grados.map(g => (
              <option key={g.id} value={g.nombre}>{g.nombre}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Tarjeta</label>
          <input
            placeholder="Nro. de tarjeta..."
            value={tarjetaAlm}
            onChange={e => setTarjetaAlm(e.target.value)}
            className={`${inputDateClass} w-36`}
          />
        </div>
        <Button variant="primary" onClick={cargarAlmuerzos} disabled={loadingAlm}>
          <TrendingUp className="w-4 h-4" />{loadingAlm ? 'Cargando...' : 'Buscar'}
        </Button>
        {almuerzosData && (
          <>
            <Button variant="secondary" onClick={exportarAlmuerzosCSV}>
              <Download className="w-4 h-4" />CSV
            </Button>
            <Button variant="secondary" onClick={handleAlmuerzosPDF}>
              <FileText className="w-4 h-4" />PDF
            </Button>
          </>
        )}
      </FilterBar>

      {almuerzosData && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { label: 'Alumnos', value: almuerzosData.totales.alumnos },
              { label: 'Almuerzos', value: almuerzosData.totales.cantidad_almuerzos },
              { label: 'Total', value: formatGs(almuerzosData.totales.monto_total) },
              { label: 'Pagado', value: formatGs(almuerzosData.totales.monto_pagado) },
              { label: 'Pendiente', value: formatGs(almuerzosData.totales.monto_pendiente) },
              { label: 'Con deuda', value: almuerzosData.totales.con_deuda },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-3 py-3 text-center">
                <p className="text-sm font-semibold text-slate-400 uppercase tracking-wide">{label}</p>
                <p className="text-sm font-bold text-slate-800 mt-0.5 tabular-nums">{value}</p>
              </div>
            ))}
          </div>

          {almuerzosData.totales.monto_total > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">Distribución de cobros</h2>
                </div>
                <div className="p-4 h-56">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Pagado', value: almuerzosData.totales.monto_pagado },
                          { name: 'Pendiente', value: almuerzosData.totales.monto_pendiente },
                        ]}
                        cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                        paddingAngle={3} dataKey="value"
                      >
                        <Cell fill="#22c55e" />
                        <Cell fill="#f59e0b" />
                      </Pie>
                      <Tooltip formatter={(v) => [`Gs. ${(Number(v) || 0).toLocaleString('es-PY')}`, '']} />
                      <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h2 className="text-sm font-semibold text-slate-800">Alumnos por estado</h2>
                </div>
                <div className="p-4 h-56">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: 'Al día', value: almuerzosData.totales.alumnos - almuerzosData.totales.con_deuda },
                          { name: 'Con deuda', value: almuerzosData.totales.con_deuda },
                        ]}
                        cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                        paddingAngle={3} dataKey="value"
                        label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                        labelLine={false}
                      >
                        <Cell fill="#22c55e" />
                        <Cell fill="#ef4444" />
                      </Pie>
                      <Tooltip formatter={(v) => [Number(v), 'Alumnos']} />
                      <Legend formatter={v => <span className="text-sm text-slate-600">{v}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsAlmuerzos} dataSource={filasAlmVisibles} rowKey="hijo_id"
                loading={loadingAlm} pageSize={filasAlmVisibles.length || 1} />
            </div>
          </div>
        </>
      )}
      {!almuerzosData && !loadingAlm && <EmptyState icon={<UtensilsCrossed className="w-full h-full" />} text='Seleccioná año y mes, luego hacé clic en "Buscar"' />}
    </>
  )
}
