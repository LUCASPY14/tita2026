import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  UtensilsCrossed, Plus, Search, Edit2, X,
  CheckCircle, Calendar, BookOpen, Users, BarChart2,
} from 'lucide-react'
import api from '../services/api'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import Modal from '../components/ui/Modal'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Error inesperado'
  if (typeof data === 'string') return data
  if (typeof data === 'object') {
    const d = data as Record<string, unknown>
    if (d.detail) return String(d.detail)
    const first = Object.values(d)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(data)
  }
  return 'Error inesperado'
}

function formatGs(n: number | string | null | undefined): string {
  return (Number(n) || 0).toLocaleString('es-PY') + ' Gs.'
}

function todayISO() {
  return new Date().toISOString().split('T')[0]
}

function formatFecha(iso: string | null | undefined): string {
  if (!iso) return '—'
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

const MESES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Hijo {
  id: number
  nombre: string
  apellido: string
  grado: string
  nombre_completo?: string
}

interface TarjetaBusqueda {
  nro_tarjeta: string
  hijo_nombre: string
  saldo_actual: string | number
  estado: string
}

interface TipoAlmuerzo {
  id: number
  nombre: string
  descripcion: string
  precio_unitario: string | number
  incluye_plato_principal: boolean
  incluye_postre: boolean
  incluye_bebida: boolean
  activo: boolean
}

interface PlanAlmuerzo {
  id: number
  nombre: string
  tipo: string
  precio_mensual: string | number
  cantidad_almuerzos_mes: number | null
  dias_semana_incluidos: number[]
  activo: boolean
}

interface Suscripcion {
  id: number
  hijo: number
  hijo_nombre: string
  plan: number
  plan_nombre: string
  estado: string
  fecha_inicio: string
  fecha_fin: string | null
}

interface MenuDiario {
  id: number
  fecha: string
  tipo_almuerzo: number
  tipo_almuerzo_nombre: string
  descripcion: string
  activo: boolean
}

interface RegistroConsumo {
  id: number
  hijo_nombre: string
  fecha_consumo: string
  tipo_almuerzo_nombre: string
  costo_almuerzo: string | number
  estado: string
  ya_cobrado: boolean
}

interface CuentaMensual {
  id: number
  hijo: number
  hijo_nombre: string
  anio: number
  mes: number
  cantidad_almuerzos: number
  monto_total: string | number
  monto_pagado: string | number
  saldo_pendiente: string | number
  estado: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const ESTADO_REGISTRO_COLOR: Record<string, BadgeColor> = {
  REGISTRADO: 'green',
  RECHAZADO: 'red',
  ANULADO: 'default',
}

const ESTADO_CUENTA_COLOR: Record<string, BadgeColor> = {
  PENDIENTE: 'orange',
  PAGADO: 'green',
  PARCIAL: 'blue',
  ANULADO: 'default',
}

const ESTADO_SUSCRIPCION_COLOR: Record<string, BadgeColor> = {
  ACTIVA: 'green',
  INACTIVA: 'default',
  SUSPENDIDA: 'orange',
}

type TabKey = 'consumos' | 'cuentas' | 'tipos' | 'planes' | 'suscripciones' | 'menu'

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Almuerzos() {
  const [tab, setTab] = useState<TabKey>('consumos')

  // ── Catalogs ─────────────────────────────────────────────────────
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [tiposAlmuerzo, setTiposAlmuerzo] = useState<TipoAlmuerzo[]>([])
  const [planes, setPlanes] = useState<PlanAlmuerzo[]>([])

  // ── Consumos ─────────────────────────────────────────────────────
  const [registros, setRegistros] = useState<RegistroConsumo[]>([])
  const [loadingRegistros, setLoadingRegistros] = useState(false)
  const [searchRegistros, setSearchRegistros] = useState('')
  const [pageRegistros, setPageRegistros] = useState(1)
  const [totalRegistros, setTotalRegistros] = useState(0)
  const searchTimerReg = useRef<ReturnType<typeof setTimeout>>(undefined)

  // ── Consumo modal ─────────────────────────────────────────────────
  const [consumoOpen, setConsumoOpen] = useState(false)
  const [tarjetaSearch, setTarjetaSearch] = useState('')
  const [tarjeta, setTarjeta] = useState<TarjetaBusqueda | null>(null)
  const [tarjetaBuscando, setTarjetaBuscando] = useState(false)
  const [hijoId, setHijoId] = useState<number | ''>('')
  const [tipoAlmuerzoId, setTipoAlmuerzoId] = useState<number | ''>('')
  const [fechaConsumo, setFechaConsumo] = useState(todayISO())
  const [registrando, setRegistrando] = useState(false)

  // ── Cuentas ───────────────────────────────────────────────────────
  const [cuentas, setCuentas] = useState<CuentaMensual[]>([])
  const [loadingCuentas, setLoadingCuentas] = useState(false)

  // ── Tipos de almuerzo ─────────────────────────────────────────────
  const [loadingTipos, setLoadingTipos] = useState(false)
  const [tipoModalOpen, setTipoModalOpen] = useState(false)
  const [editingTipo, setEditingTipo] = useState<TipoAlmuerzo | null>(null)
  const [tipoForm, setTipoForm] = useState({
    nombre: '', descripcion: '', precio_unitario: '',
    incluye_plato_principal: true, incluye_postre: false, incluye_bebida: false, activo: true,
  })
  const [savingTipo, setSavingTipo] = useState(false)

  // ── Planes ────────────────────────────────────────────────────────
  const [loadingPlanes, setLoadingPlanes] = useState(false)
  const [planModalOpen, setPlanModalOpen] = useState(false)
  const [editingPlan, setEditingPlan] = useState<PlanAlmuerzo | null>(null)
  const [planForm, setPlanForm] = useState({
    nombre: '', tipo: 'CANTIDAD', precio_mensual: '',
    cantidad_almuerzos_mes: '', dias_semana_incluidos: [] as number[], activo: true,
  })
  const [savingPlan, setSavingPlan] = useState(false)

  // ── Suscripciones ─────────────────────────────────────────────────
  const [suscripciones, setSuscripciones] = useState<Suscripcion[]>([])
  const [loadingSusc, setLoadingSusc] = useState(false)
  const [suscModalOpen, setSuscModalOpen] = useState(false)
  const [suscForm, setSuscForm] = useState({ hijo: '', plan: '', fecha_inicio: todayISO() })
  const [savingSusc, setSavingSusc] = useState(false)

  // ── Menú ──────────────────────────────────────────────────────────
  const [menu, setMenu] = useState<MenuDiario[]>([])
  const [loadingMenu, setLoadingMenu] = useState(false)
  const [menuModalOpen, setMenuModalOpen] = useState(false)
  const [menuForm, setMenuForm] = useState({ fecha: todayISO(), tipo_almuerzo: '', descripcion: '' })
  const [savingMenu, setSavingMenu] = useState(false)

  // ── Load catalogs ─────────────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      api.get('/clientes/hijos/', { params: { page_size: 500 } }),
      api.get('/almuerzos/tipos-almuerzo/', { params: { page_size: 100 } }),
      api.get('/almuerzos/planes-almuerzo/', { params: { page_size: 100 } }),
    ]).then(([hRes, tRes, pRes]) => {
      setHijos(hRes.data.results ?? [])
      setTiposAlmuerzo(tRes.data.results ?? [])
      setPlanes(pRes.data.results ?? [])
    }).catch(() => {})
  }, [])

  // ── Load consumos ─────────────────────────────────────────────────
  const loadRegistros = useCallback(async (q: string, p: number) => {
    setLoadingRegistros(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering: '-fecha_consumo' }
      if (q) params.search = q
      const { data } = await api.get('/almuerzos/registros-consumo/', { params })
      setRegistros(data.results ?? [])
      setTotalRegistros(data.count ?? 0)
    } catch {
      toast.error('Error al cargar consumos')
    } finally {
      setLoadingRegistros(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(searchTimerReg.current)
    searchTimerReg.current = setTimeout(() => {
      setPageRegistros(1)
      loadRegistros(searchRegistros, 1)
    }, 350)
    return () => clearTimeout(searchTimerReg.current)
  }, [searchRegistros, loadRegistros])

  useEffect(() => {
    loadRegistros(searchRegistros, pageRegistros)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageRegistros])

  // ── Load cuentas ──────────────────────────────────────────────────
  const loadCuentas = useCallback(async () => {
    setLoadingCuentas(true)
    try {
      const { data } = await api.get('/almuerzos/cuentas-mensuales/', { params: { ordering: '-anio,-mes', page_size: 200 } })
      setCuentas(data.results ?? [])
    } catch {
      toast.error('Error al cargar cuentas')
    } finally {
      setLoadingCuentas(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'cuentas') loadCuentas()
  }, [tab, loadCuentas])

  // ── Load tipos ────────────────────────────────────────────────────
  const loadTipos = useCallback(async () => {
    setLoadingTipos(true)
    try {
      const { data } = await api.get('/almuerzos/tipos-almuerzo/', { params: { page_size: 100 } })
      setTiposAlmuerzo(data.results ?? [])
    } catch {
      toast.error('Error al cargar tipos')
    } finally {
      setLoadingTipos(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'tipos') loadTipos()
  }, [tab, loadTipos])

  // ── Load planes ───────────────────────────────────────────────────
  const loadPlanes = useCallback(async () => {
    setLoadingPlanes(true)
    try {
      const { data } = await api.get('/almuerzos/planes-almuerzo/', { params: { page_size: 100 } })
      setPlanes(data.results ?? [])
    } catch {
      toast.error('Error al cargar planes')
    } finally {
      setLoadingPlanes(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'planes') loadPlanes()
  }, [tab, loadPlanes])

  // ── Load suscripciones ────────────────────────────────────────────
  const loadSuscripciones = useCallback(async () => {
    setLoadingSusc(true)
    try {
      const { data } = await api.get('/almuerzos/suscripciones/', { params: { page_size: 200 } })
      setSuscripciones(data.results ?? [])
    } catch {
      toast.error('Error al cargar suscripciones')
    } finally {
      setLoadingSusc(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'suscripciones') loadSuscripciones()
  }, [tab, loadSuscripciones])

  // ── Load menu ─────────────────────────────────────────────────────
  const loadMenu = useCallback(async () => {
    setLoadingMenu(true)
    try {
      const { data } = await api.get('/almuerzos/menu/', { params: { page_size: 60, ordering: '-fecha' } })
      setMenu(data.results ?? [])
    } catch {
      toast.error('Error al cargar menú')
    } finally {
      setLoadingMenu(false)
    }
  }, [])

  useEffect(() => {
    if (tab === 'menu') loadMenu()
  }, [tab, loadMenu])

  // ── Tarjeta search ────────────────────────────────────────────────
  const buscarTarjeta = useCallback(async () => {
    if (!tarjetaSearch.trim()) { toast.error('Ingresá un número de tarjeta'); return }
    setTarjetaBuscando(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: tarjetaSearch } })
      const found = (data.results ?? []).find((t: TarjetaBusqueda) => t.nro_tarjeta === tarjetaSearch)
      if (!found) { toast.error('Tarjeta no encontrada'); return }
      if (found.estado !== 'ACTIVA') { toast.error(`Tarjeta ${found.estado}`); return }
      setTarjeta(found)
      const h = hijos.find(x => `${x.nombre} ${x.apellido}` === found.hijo_nombre || x.nombre_completo === found.hijo_nombre)
      if (h) setHijoId(h.id)
      toast.success(found.hijo_nombre)
    } catch {
      toast.error('Error al buscar tarjeta')
    } finally {
      setTarjetaBuscando(false)
    }
  }, [tarjetaSearch, hijos])

  const handleRegistrarConsumo = useCallback(async () => {
    if (!hijoId) { toast.error('Seleccioná un estudiante'); return }
    if (!tarjeta) { toast.error('Buscá la tarjeta del estudiante'); return }
    setRegistrando(true)
    try {
      const payload: Record<string, unknown> = {
        hijo: hijoId,
        fecha_consumo: fechaConsumo,
        nro_tarjeta: tarjeta.nro_tarjeta,
      }
      if (tipoAlmuerzoId) payload.tipo_almuerzo = tipoAlmuerzoId
      await api.post('/almuerzos/registros-consumo/', payload)
      toast.success('Consumo registrado')
      setConsumoOpen(false)
      setTarjeta(null)
      setTarjetaSearch('')
      setHijoId('')
      setTipoAlmuerzoId('')
      setFechaConsumo(todayISO())
      setPageRegistros(1)
      loadRegistros('', 1)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setRegistrando(false)
    }
  }, [hijoId, tarjeta, fechaConsumo, tipoAlmuerzoId, loadRegistros])

  // ── Tipos CRUD ────────────────────────────────────────────────────
  const openTipoModal = useCallback((t?: TipoAlmuerzo) => {
    if (t) {
      setEditingTipo(t)
      setTipoForm({
        nombre: t.nombre, descripcion: t.descripcion,
        precio_unitario: String(Number(t.precio_unitario) || ''),
        incluye_plato_principal: t.incluye_plato_principal,
        incluye_postre: t.incluye_postre,
        incluye_bebida: t.incluye_bebida,
        activo: t.activo,
      })
    } else {
      setEditingTipo(null)
      setTipoForm({ nombre: '', descripcion: '', precio_unitario: '', incluye_plato_principal: true, incluye_postre: false, incluye_bebida: false, activo: true })
    }
    setTipoModalOpen(true)
  }, [])

  const handleSaveTipo = useCallback(async () => {
    if (!tipoForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingTipo(true)
    try {
      const payload = { ...tipoForm, precio_unitario: Number(tipoForm.precio_unitario) || 0 }
      if (editingTipo) {
        await api.put(`/almuerzos/tipos-almuerzo/${editingTipo.id}/`, payload)
        toast.success('Tipo actualizado')
      } else {
        await api.post('/almuerzos/tipos-almuerzo/', payload)
        toast.success('Tipo creado')
      }
      setTipoModalOpen(false)
      loadTipos()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingTipo(false)
    }
  }, [tipoForm, editingTipo, loadTipos])

  // ── Planes CRUD ───────────────────────────────────────────────────
  const openPlanModal = useCallback((p?: PlanAlmuerzo) => {
    if (p) {
      setEditingPlan(p)
      setPlanForm({
        nombre: p.nombre, tipo: p.tipo,
        precio_mensual: String(Number(p.precio_mensual) || ''),
        cantidad_almuerzos_mes: String(p.cantidad_almuerzos_mes ?? ''),
        dias_semana_incluidos: p.dias_semana_incluidos ?? [],
        activo: p.activo,
      })
    } else {
      setEditingPlan(null)
      setPlanForm({ nombre: '', tipo: 'CANTIDAD', precio_mensual: '', cantidad_almuerzos_mes: '', dias_semana_incluidos: [], activo: true })
    }
    setPlanModalOpen(true)
  }, [])

  const handleSavePlan = useCallback(async () => {
    if (!planForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingPlan(true)
    try {
      const payload = {
        ...planForm,
        precio_mensual: Number(planForm.precio_mensual) || 0,
        cantidad_almuerzos_mes: planForm.tipo === 'CANTIDAD' ? (Number(planForm.cantidad_almuerzos_mes) || null) : null,
      }
      if (editingPlan) {
        await api.put(`/almuerzos/planes-almuerzo/${editingPlan.id}/`, payload)
        toast.success('Plan actualizado')
      } else {
        await api.post('/almuerzos/planes-almuerzo/', payload)
        toast.success('Plan creado')
      }
      setPlanModalOpen(false)
      loadPlanes()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingPlan(false)
    }
  }, [planForm, editingPlan, loadPlanes])

  // ── Suscripciones ──────────────────────────────────────────────────
  const handleSaveSusc = useCallback(async () => {
    if (!suscForm.hijo || !suscForm.plan) { toast.error('Completá todos los campos'); return }
    setSavingSusc(true)
    try {
      await api.post('/almuerzos/suscripciones/', {
        hijo: Number(suscForm.hijo),
        plan: Number(suscForm.plan),
        fecha_inicio: suscForm.fecha_inicio,
      })
      toast.success('Suscripción creada')
      setSuscModalOpen(false)
      setSuscForm({ hijo: '', plan: '', fecha_inicio: todayISO() })
      loadSuscripciones()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingSusc(false)
    }
  }, [suscForm, loadSuscripciones])

  const cancelarSusc = useCallback(async (id: number) => {
    try {
      await api.patch(`/almuerzos/suscripciones/${id}/`, { estado: 'INACTIVA' })
      toast.success('Suscripción cancelada')
      loadSuscripciones()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadSuscripciones])

  // ── Menú ───────────────────────────────────────────────────────────
  const handleSaveMenu = useCallback(async () => {
    if (!menuForm.fecha || !menuForm.tipo_almuerzo) { toast.error('Completá los campos'); return }
    setSavingMenu(true)
    try {
      await api.post('/almuerzos/menu/', {
        fecha: menuForm.fecha,
        tipo_almuerzo: Number(menuForm.tipo_almuerzo),
        descripcion: menuForm.descripcion,
      })
      toast.success('Menú registrado')
      setMenuModalOpen(false)
      setMenuForm({ fecha: todayISO(), tipo_almuerzo: '', descripcion: '' })
      loadMenu()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingMenu(false)
    }
  }, [menuForm, loadMenu])

  // ── Summary stats ──────────────────────────────────────────────────
  const mesActual = new Date().getMonth() + 1
  const anioActual = new Date().getFullYear()
  const hoy = todayISO()

  const stats = useMemo(() => ({
    consumosHoy: registros.filter(r => r.fecha_consumo === hoy).length,
    cuentasPendientes: cuentas.filter(c => c.estado !== 'PAGADO' && c.estado !== 'ANULADO').length,
    facturadoMes: cuentas.filter(c => c.mes === mesActual && c.anio === anioActual).reduce((s, c) => s + (Number(c.monto_total) || 0), 0),
  }), [registros, cuentas, hoy, mesActual, anioActual])

  // ── Columns ──────────────────────────────────────────────────────

  const colsRegistros: Column<RegistroConsumo>[] = [
    {
      title: 'Estudiante',
      key: 'hijo',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.hijo_nombre}</span>,
    },
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-600">{formatFecha(r.fecha_consumo)}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <span className="text-sm text-slate-600">{r.tipo_almuerzo_nombre || '—'}</span>,
    },
    {
      title: 'Costo',
      key: 'costo',
      render: (_, r) => (
        <span className="tabular-nums text-sm text-emerald-700 font-medium">{formatGs(r.costo_almuerzo)}</span>
      ),
    },
    {
      title: 'Cobrado',
      key: 'cobrado',
      render: (_, r) => <Badge color={r.ya_cobrado ? 'blue' : 'default'}>{r.ya_cobrado ? 'Sí' : 'No'}</Badge>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_REGISTRO_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
  ]

  const colsCuentas: Column<CuentaMensual>[] = [
    {
      title: 'Estudiante',
      key: 'hijo',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.hijo_nombre}</span>,
    },
    {
      title: 'Período',
      key: 'periodo',
      render: (_, r) => <span className="text-sm text-slate-600">{MESES[r.mes]} {r.anio}</span>,
    },
    {
      title: 'Almuerzos',
      key: 'cant',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{r.cantidad_almuerzos}</span>,
    },
    {
      title: 'Total',
      key: 'total',
      render: (_, r) => <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_total)}</span>,
    },
    {
      title: 'Pagado',
      key: 'pagado',
      render: (_, r) => <span className="tabular-nums text-emerald-700">{formatGs(r.monto_pagado)}</span>,
    },
    {
      title: 'Saldo',
      key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_pendiente) || (Number(r.monto_total) - Number(r.monto_pagado))
        return <span className={`tabular-nums font-semibold text-sm ${n > 0 ? 'text-red-600' : 'text-slate-400'}`}>{formatGs(n)}</span>
      },
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_CUENTA_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
  ]

  const colsTipos: Column<TipoAlmuerzo>[] = [
    {
      title: 'Nombre',
      key: 'nombre',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span>,
    },
    {
      title: 'Precio',
      key: 'precio',
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.precio_unitario)}</span>,
    },
    {
      title: 'Incluye',
      key: 'incluye',
      render: (_, r) => (
        <div className="flex gap-1 flex-wrap">
          {r.incluye_plato_principal && <Badge color="blue">Plato</Badge>}
          {r.incluye_postre && <Badge color="purple">Postre</Badge>}
          {r.incluye_bebida && <Badge color="green">Bebida</Badge>}
        </div>
      ),
    },
    {
      title: 'Estado',
      key: 'activo',
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 80,
      render: (_, r) => (
        <Button size="sm" variant="secondary" onClick={() => openTipoModal(r)}>
          <Edit2 className="w-3.5 h-3.5" />
        </Button>
      ),
    },
  ]

  const colsPlanes: Column<PlanAlmuerzo>[] = [
    {
      title: 'Nombre',
      key: 'nombre',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <Badge color={r.tipo === 'SIN_LIMITE' ? 'green' : 'blue'}>{r.tipo}</Badge>,
    },
    {
      title: 'Precio Mensual',
      key: 'precio',
      render: (_, r) => <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.precio_mensual)}</span>,
    },
    {
      title: 'Almuerzos/mes',
      key: 'cant',
      render: (_, r) => (
        <span className="text-sm text-slate-600">{r.cantidad_almuerzos_mes ?? 'Sin límite'}</span>
      ),
    },
    {
      title: 'Días',
      key: 'dias',
      render: (_, r) => (
        <div className="flex gap-1 flex-wrap">
          {(r.dias_semana_incluidos ?? []).map(d => (
            <span key={d} className="text-xs bg-slate-100 text-slate-600 rounded px-1.5 py-0.5">{DIAS[d - 1] ?? d}</span>
          ))}
        </div>
      ),
    },
    {
      title: 'Estado',
      key: 'activo',
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 80,
      render: (_, r) => (
        <Button size="sm" variant="secondary" onClick={() => openPlanModal(r)}>
          <Edit2 className="w-3.5 h-3.5" />
        </Button>
      ),
    },
  ]

  const colsSusc: Column<Suscripcion>[] = [
    {
      title: 'Estudiante',
      key: 'hijo',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.hijo_nombre}</span>,
    },
    {
      title: 'Plan',
      key: 'plan',
      render: (_, r) => <span className="text-sm text-slate-700">{r.plan_nombre}</span>,
    },
    {
      title: 'Inicio',
      key: 'inicio',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha_inicio)}</span>,
    },
    {
      title: 'Fin',
      key: 'fin',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha_fin)}</span>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={ESTADO_SUSCRIPCION_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: '',
      key: 'acc',
      width: 100,
      render: (_, r) => r.estado === 'ACTIVA' ? (
        <Button size="sm" variant="danger" onClick={() => cancelarSusc(r.id)}>
          <X className="w-3.5 h-3.5" />
          Cancelar
        </Button>
      ) : null,
    },
  ]

  const colsMenu: Column<MenuDiario>[] = [
    {
      title: 'Fecha',
      key: 'fecha',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Tipo',
      key: 'tipo',
      render: (_, r) => <span className="text-sm text-slate-700">{r.tipo_almuerzo_nombre}</span>,
    },
    {
      title: 'Descripción',
      key: 'desc',
      render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span>,
    },
    {
      title: 'Estado',
      key: 'activo',
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
  ]

  // ── Styles ────────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const toggleSwitch = (checked: boolean, onChange: (v: boolean) => void, label: string) => (
    <label className="flex items-center gap-3 cursor-pointer">
      <div className="relative shrink-0">
        <input type="checkbox" className="sr-only peer" checked={checked} onChange={e => onChange(e.target.checked)} />
        <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
        <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
      </div>
      <span className="text-sm text-slate-700">{label}</span>
    </label>
  )

  const TABS: { key: TabKey; label: string; icon: typeof UtensilsCrossed }[] = [
    { key: 'consumos', label: 'Consumos', icon: UtensilsCrossed },
    { key: 'cuentas', label: 'Cuentas Mensuales', icon: BarChart2 },
    { key: 'tipos', label: 'Tipos', icon: BookOpen },
    { key: 'planes', label: 'Planes', icon: CheckCircle },
    { key: 'suscripciones', label: 'Suscripciones', icon: Users },
    { key: 'menu', label: 'Menú', icon: Calendar },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Almuerzos</h1>
          <p className="text-sm text-slate-500 mt-0.5">Gestión de consumos, menú y suscripciones</p>
        </div>
        {tab === 'consumos' && (
          <Button variant="primary" onClick={() => setConsumoOpen(true)}>
            <Plus className="w-4 h-4" />
            Registrar Consumo
          </Button>
        )}
        {tab === 'tipos' && (
          <Button variant="primary" onClick={() => openTipoModal()}>
            <Plus className="w-4 h-4" />
            Nuevo Tipo
          </Button>
        )}
        {tab === 'planes' && (
          <Button variant="primary" onClick={() => openPlanModal()}>
            <Plus className="w-4 h-4" />
            Nuevo Plan
          </Button>
        )}
        {tab === 'suscripciones' && (
          <Button variant="primary" onClick={() => { setSuscForm({ hijo: '', plan: '', fecha_inicio: todayISO() }); setSuscModalOpen(true) }}>
            <Plus className="w-4 h-4" />
            Nueva Suscripción
          </Button>
        )}
        {tab === 'menu' && (
          <Button variant="primary" onClick={() => setMenuModalOpen(true)}>
            <Plus className="w-4 h-4" />
            Agregar al Menú
          </Button>
        )}
      </div>

      {/* Summary cards (only on consumos/cuentas) */}
      {(tab === 'consumos' || tab === 'cuentas') && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { label: 'Consumos Hoy', value: String(stats.consumosHoy), color: 'text-blue-700', bg: 'bg-blue-50', icon: UtensilsCrossed, iconColor: 'text-blue-600' },
            { label: 'Cuentas Pendientes', value: String(stats.cuentasPendientes), color: 'text-orange-700', bg: 'bg-orange-50', icon: BarChart2, iconColor: 'text-orange-600' },
            { label: 'Facturado este Mes', value: formatGs(stats.facturadoMes), color: 'text-emerald-700', bg: 'bg-emerald-50', icon: CheckCircle, iconColor: 'text-emerald-600' },
          ].map(({ label, value, color, bg, icon: Icon, iconColor }) => (
            <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex items-start gap-4">
              <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center shrink-0`}>
                <Icon className={`w-5 h-5 ${iconColor}`} />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
                <p className={`text-xl font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex flex-wrap gap-0">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key
                  ? 'border-green-600 text-green-700'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Consumos tab ─────────────────────────────────────────── */}
      {tab === 'consumos' && (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
            <div className="relative max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <input
                placeholder="Buscar estudiante..."
                value={searchRegistros}
                onChange={e => setSearchRegistros(e.target.value)}
                className={`${inputClass} pl-9`}
              />
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table columns={colsRegistros} dataSource={registros} rowKey="id" loading={loadingRegistros}
                pageSize={15} page={pageRegistros} onPageChange={setPageRegistros} total={totalRegistros} />
            </div>
          </div>
        </>
      )}

      {/* ── Cuentas tab ──────────────────────────────────────────── */}
      {tab === 'cuentas' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Cuentas Mensuales de Almuerzos</h2>
          </div>
          <div className="p-1">
            <Table columns={colsCuentas} dataSource={cuentas} rowKey="id" loading={loadingCuentas} pageSize={15} />
          </div>
        </div>
      )}

      {/* ── Tipos tab ─────────────────────────────────────────────── */}
      {tab === 'tipos' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Tipos de Almuerzo</h2>
          </div>
          <div className="p-1">
            <Table columns={colsTipos} dataSource={tiposAlmuerzo} rowKey="id" loading={loadingTipos} pageSize={20} />
          </div>
        </div>
      )}

      {/* ── Planes tab ────────────────────────────────────────────── */}
      {tab === 'planes' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Planes de Almuerzo</h2>
          </div>
          <div className="p-1">
            <Table columns={colsPlanes} dataSource={planes} rowKey="id" loading={loadingPlanes} pageSize={20} />
          </div>
        </div>
      )}

      {/* ── Suscripciones tab ─────────────────────────────────────── */}
      {tab === 'suscripciones' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Suscripciones de Estudiantes</h2>
          </div>
          <div className="p-1">
            <Table columns={colsSusc} dataSource={suscripciones} rowKey="id" loading={loadingSusc} pageSize={15} />
          </div>
        </div>
      )}

      {/* ── Menú tab ──────────────────────────────────────────────── */}
      {tab === 'menu' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Menú Diario</h2>
          </div>
          <div className="p-1">
            <Table columns={colsMenu} dataSource={menu} rowKey="id" loading={loadingMenu} pageSize={15} />
          </div>
        </div>
      )}

      {/* ── Registrar consumo modal ───────────────────────────────── */}
      <Modal
        open={consumoOpen}
        title="Registrar Consumo de Almuerzo"
        onOk={handleRegistrarConsumo}
        onCancel={() => { setConsumoOpen(false); setTarjeta(null); setTarjetaSearch('') }}
        okText="Registrar"
        confirmLoading={registrando}
        width={480}
      >
        <div className="space-y-4">
          <div className="bg-slate-50 rounded-xl p-4">
            <label className={labelClass}>Tarjeta del Estudiante</label>
            <div className="flex gap-2">
              <input
                placeholder="Nro. tarjeta"
                value={tarjetaSearch}
                onChange={e => setTarjetaSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && buscarTarjeta()}
                className="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
              />
              <Button size="sm" variant="secondary" loading={tarjetaBuscando} onClick={buscarTarjeta}>
                <Search className="w-3.5 h-3.5" />
                Buscar
              </Button>
            </div>
            {tarjeta && (
              <div className="mt-2 flex items-center gap-2 bg-green-50 rounded-lg px-3 py-2">
                <CheckCircle className="w-4 h-4 text-green-600 shrink-0" />
                <span className="text-sm font-medium text-green-800">{tarjeta.hijo_nombre}</span>
                <span className="text-xs text-green-600 ml-auto">Saldo: {formatGs(tarjeta.saldo_actual)}</span>
                <button onClick={() => { setTarjeta(null); setTarjetaSearch('') }} className="text-slate-400 hover:text-red-500 cursor-pointer">
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          <div>
            <label className={labelClass}>Estudiante *</label>
            <select
              value={hijoId}
              onChange={e => setHijoId(Number(e.target.value) || '')}
              className={inputClass}
            >
              <option value="">Seleccionar...</option>
              {hijos.map(h => (
                <option key={h.id} value={h.id}>
                  {h.nombre_completo ?? `${h.nombre} ${h.apellido}`} — {h.grado}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelClass}>Tipo de Almuerzo (opcional)</label>
            <select
              value={tipoAlmuerzoId}
              onChange={e => setTipoAlmuerzoId(Number(e.target.value) || '')}
              className={inputClass}
            >
              <option value="">Sin especificar</option>
              {tiposAlmuerzo.filter(t => t.activo).map(t => (
                <option key={t.id} value={t.id}>{t.nombre} — {formatGs(t.precio_unitario)}</option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelClass}>Fecha</label>
            <input
              type="date"
              value={fechaConsumo}
              onChange={e => setFechaConsumo(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>
      </Modal>

      {/* ── Tipo almuerzo modal ───────────────────────────────────── */}
      <Modal
        open={tipoModalOpen}
        title={editingTipo ? 'Editar Tipo de Almuerzo' : 'Nuevo Tipo de Almuerzo'}
        onOk={handleSaveTipo}
        onCancel={() => setTipoModalOpen(false)}
        okText={editingTipo ? 'Guardar' : 'Crear'}
        confirmLoading={savingTipo}
        width={480}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={tipoForm.nombre} onChange={e => setTipoForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea
              value={tipoForm.descripcion}
              onChange={e => setTipoForm(f => ({ ...f, descripcion: e.target.value }))}
              rows={2}
              className={`${inputClass} resize-none`}
            />
          </div>
          <div>
            <label className={labelClass}>Precio Unitario (Gs.)</label>
            <input type="number" min={0} step={500}
              value={tipoForm.precio_unitario}
              onChange={e => setTipoForm(f => ({ ...f, precio_unitario: e.target.value }))}
              className={inputClass}
            />
          </div>
          <div className="space-y-2">
            {toggleSwitch(tipoForm.incluye_plato_principal, v => setTipoForm(f => ({ ...f, incluye_plato_principal: v })), 'Incluye plato principal')}
            {toggleSwitch(tipoForm.incluye_postre, v => setTipoForm(f => ({ ...f, incluye_postre: v })), 'Incluye postre')}
            {toggleSwitch(tipoForm.incluye_bebida, v => setTipoForm(f => ({ ...f, incluye_bebida: v })), 'Incluye bebida')}
            {toggleSwitch(tipoForm.activo, v => setTipoForm(f => ({ ...f, activo: v })), 'Activo')}
          </div>
        </div>
      </Modal>

      {/* ── Plan almuerzo modal ───────────────────────────────────── */}
      <Modal
        open={planModalOpen}
        title={editingPlan ? 'Editar Plan de Almuerzo' : 'Nuevo Plan de Almuerzo'}
        onOk={handleSavePlan}
        onCancel={() => setPlanModalOpen(false)}
        okText={editingPlan ? 'Guardar' : 'Crear'}
        confirmLoading={savingPlan}
        width={520}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={planForm.nombre} onChange={e => setPlanForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Tipo</label>
              <select value={planForm.tipo} onChange={e => setPlanForm(f => ({ ...f, tipo: e.target.value }))} className={inputClass}>
                <option value="CANTIDAD">Por Cantidad</option>
                <option value="SIN_LIMITE">Sin Límite</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Precio Mensual (Gs.)</label>
              <input type="number" min={0} step={1000}
                value={planForm.precio_mensual}
                onChange={e => setPlanForm(f => ({ ...f, precio_mensual: e.target.value }))}
                className={inputClass}
              />
            </div>
          </div>
          {planForm.tipo === 'CANTIDAD' && (
            <div>
              <label className={labelClass}>Almuerzos por Mes</label>
              <input type="number" min={1}
                value={planForm.cantidad_almuerzos_mes}
                onChange={e => setPlanForm(f => ({ ...f, cantidad_almuerzos_mes: e.target.value }))}
                className={inputClass}
              />
            </div>
          )}
          <div>
            <label className={labelClass}>Días de la semana incluidos</label>
            <div className="flex flex-wrap gap-2">
              {DIAS.map((dia, idx) => {
                const num = idx + 1
                const checked = planForm.dias_semana_incluidos.includes(num)
                return (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setPlanForm(f => ({
                      ...f,
                      dias_semana_incluidos: checked
                        ? f.dias_semana_incluidos.filter(d => d !== num)
                        : [...f.dias_semana_incluidos, num],
                    }))}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                      checked
                        ? 'bg-green-600 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {dia}
                  </button>
                )
              })}
            </div>
          </div>
          {toggleSwitch(planForm.activo, v => setPlanForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>

      {/* ── Suscripción modal ─────────────────────────────────────── */}
      <Modal
        open={suscModalOpen}
        title="Nueva Suscripción"
        onOk={handleSaveSusc}
        onCancel={() => setSuscModalOpen(false)}
        okText="Suscribir"
        confirmLoading={savingSusc}
        width={440}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Estudiante *</label>
            <select value={suscForm.hijo} onChange={e => setSuscForm(f => ({ ...f, hijo: e.target.value }))} className={inputClass}>
              <option value="">Seleccionar...</option>
              {hijos.map(h => (
                <option key={h.id} value={h.id}>
                  {h.nombre_completo ?? `${h.nombre} ${h.apellido}`} — {h.grado}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Plan *</label>
            <select value={suscForm.plan} onChange={e => setSuscForm(f => ({ ...f, plan: e.target.value }))} className={inputClass}>
              <option value="">Seleccionar...</option>
              {planes.filter(p => p.activo).map(p => (
                <option key={p.id} value={p.id}>{p.nombre} — {formatGs(p.precio_mensual)}/mes</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Fecha de Inicio</label>
            <input type="date" value={suscForm.fecha_inicio} onChange={e => setSuscForm(f => ({ ...f, fecha_inicio: e.target.value }))} className={inputClass} />
          </div>
        </div>
      </Modal>

      {/* ── Menú modal ────────────────────────────────────────────── */}
      <Modal
        open={menuModalOpen}
        title="Agregar al Menú"
        onOk={handleSaveMenu}
        onCancel={() => setMenuModalOpen(false)}
        okText="Guardar"
        confirmLoading={savingMenu}
        width={440}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Fecha *</label>
            <input type="date" value={menuForm.fecha} onChange={e => setMenuForm(f => ({ ...f, fecha: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Tipo de Almuerzo *</label>
            <select value={menuForm.tipo_almuerzo} onChange={e => setMenuForm(f => ({ ...f, tipo_almuerzo: e.target.value }))} className={inputClass}>
              <option value="">Seleccionar...</option>
              {tiposAlmuerzo.filter(t => t.activo).map(t => (
                <option key={t.id} value={t.id}>{t.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea
              value={menuForm.descripcion}
              onChange={e => setMenuForm(f => ({ ...f, descripcion: e.target.value }))}
              rows={2}
              placeholder="Descripción del menú del día..."
              className={`${inputClass} resize-none`}
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}
