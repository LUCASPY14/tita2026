import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  UtensilsCrossed, Plus, Search, Edit2, X,
  CheckCircle, Calendar, Users, BarChart2,
  PauseCircle, Banknote, RefreshCw, EyeOff, Eye, FileText,
} from 'lucide-react'
import api from '../services/api'
import { exportarCuentasMensualesPDF } from '../utils/pdf'
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
  plato_principal: string
  guarnicion: string
  postre: string
  bebida: string
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

type TabKey = 'consumos' | 'cuentas' | 'suscripciones' | 'menu'

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Almuerzos() {
  const { t } = useTranslation()
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
  const [menuForm, setMenuForm] = useState({ fecha: todayISO(), plato_principal: '', guarnicion: '', postre: '', bebida: '', descripcion: '' })
  const [savingMenu, setSavingMenu] = useState(false)
  const [editingMenu, setEditingMenu] = useState<MenuDiario | null>(null)
  const [editMenuOpen, setEditMenuOpen] = useState(false)
  const [editMenuForm, setEditMenuForm] = useState({ fecha: '', plato_principal: '', guarnicion: '', postre: '', bebida: '', descripcion: '', activo: true })
  const [savingEditMenu, setSavingEditMenu] = useState(false)

  // ── Pago cuenta ───────────────────────────────────────────────────
  const [pagoOpen, setPagoOpen] = useState(false)
  const [pagoCuenta, setPagoCuenta] = useState<CuentaMensual | null>(null)
  const [pagoForm, setPagoForm] = useState({ monto: '', medio_pago: 'EFECTIVO', referencia: '' })
  const [savingPago, setSavingPago] = useState(false)

  // ── Filtros y generación de cuentas ──────────────────────────────
  const [filtroCuentaMes, setFiltroCuentaMes] = useState<number | ''>('')
  const [filtroCuentaAnio, setFiltroCuentaAnio] = useState<number | ''>(new Date().getFullYear())
  const [generando, setGenerando] = useState(false)

  // ── Edit suscripcion ──────────────────────────────────────────────
  const [editingSusc, setEditingSusc] = useState<Suscripcion | null>(null)
  const [editSuscOpen, setEditSuscOpen] = useState(false)
  const [editSuscForm, setEditSuscForm] = useState({ plan: '', fecha_fin: '' })
  const [savingEditSusc, setSavingEditSusc] = useState(false)

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

  const handlePageChange = useCallback((page: number) => {
    setPageRegistros(page)
    loadRegistros(searchRegistros, page)
  }, [loadRegistros, searchRegistros])

  // ── Load cuentas ──────────────────────────────────────────────────
  const loadCuentas = useCallback(async () => {
    setLoadingCuentas(true)
    try {
      const params: Record<string, unknown> = { ordering: '-anio,-mes', page_size: 200 }
      if (filtroCuentaMes) params.mes = filtroCuentaMes
      if (filtroCuentaAnio) params.anio = filtroCuentaAnio
      const { data } = await api.get('/almuerzos/cuentas-mensuales/', { params })
      setCuentas(data.results ?? [])
    } catch {
      toast.error('Error al cargar cuentas')
    } finally {
      setLoadingCuentas(false)
    }
  }, [filtroCuentaMes, filtroCuentaAnio])

  useEffect(() => {
    if (tab === 'cuentas') loadCuentas()
  }, [tab, loadCuentas])

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

  // Escuchar registros del Comedor para refrescar en tiempo real
  useEffect(() => {
    const handler = () => {
      if (tab === 'consumos') loadRegistros(searchRegistros, pageRegistros)
      if (tab === 'cuentas') loadCuentas()
    }
    window.addEventListener('comedor:registro', handler)
    return () => window.removeEventListener('comedor:registro', handler)
  }, [tab, searchRegistros, pageRegistros, loadRegistros, loadCuentas])

  // ── Tarjeta search ────────────────────────────────────────────────
  const buscarTarjeta = useCallback(async (nro?: string) => {
    const searchValue = nro ?? tarjetaSearch.trim()
    if (!searchValue) { toast.error('Ingresá un número de tarjeta'); return }
    setTarjetaBuscando(true)
    try {
      const { data } = await api.get('/core/tarjetas/', { params: { search: searchValue }, timeout: 6000 })
      const found = (data.results ?? []).find((t: TarjetaBusqueda) => t.nro_tarjeta === searchValue)
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
      setTarjetaSearch('')
    }
  }, [tarjetaSearch, hijos])

  const handleRegistrarConsumo = useCallback(async () => {
    if (!hijoId) { toast.error('Seleccioná un estudiante'); return }
    if (!tarjeta) { toast.error('Buscá la tarjeta del estudiante'); return }
    const h = hijos.find(x => x.id === Number(hijoId))
    if (h) {
      const coincide = tarjeta.hijo_nombre === `${h.nombre} ${h.apellido}` || tarjeta.hijo_nombre === h.nombre_completo
      if (!coincide) { toast.error('La tarjeta no pertenece al estudiante seleccionado'); return }
    }
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
  }, [hijoId, tarjeta, hijos, fechaConsumo, tipoAlmuerzoId, loadRegistros])

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
      await api.patch(`/almuerzos/suscripciones/${id}/`, { estado: 'CANCELADA' })
      toast.success('Suscripción cancelada')
      loadSuscripciones()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadSuscripciones])

  // ── Menú ───────────────────────────────────────────────────────────
  const handleSaveMenu = useCallback(async () => {
    if (!menuForm.fecha || !menuForm.plato_principal) { toast.error('Ingresá la fecha y el plato principal'); return }
    setSavingMenu(true)
    try {
      await api.post('/almuerzos/menu/', {
        fecha: menuForm.fecha,
        plato_principal: menuForm.plato_principal,
        guarnicion: menuForm.guarnicion,
        postre: menuForm.postre,
        bebida: menuForm.bebida,
        descripcion: menuForm.descripcion,
      })
      toast.success('Menú registrado')
      setMenuModalOpen(false)
      setMenuForm({ fecha: todayISO(), plato_principal: '', guarnicion: '', postre: '', bebida: '', descripcion: '' })
      loadMenu()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingMenu(false)
    }
  }, [menuForm, loadMenu])

  // ── Edit menú ─────────────────────────────────────────────────────
  const openEditMenu = useCallback((m: MenuDiario) => {
    setEditingMenu(m)
    setEditMenuForm({
      fecha: m.fecha,
      plato_principal: m.plato_principal,
      guarnicion: m.guarnicion,
      postre: m.postre,
      bebida: m.bebida,
      descripcion: m.descripcion,
      activo: m.activo,
    })
    setEditMenuOpen(true)
  }, [])

  const handleSaveEditMenu = useCallback(async () => {
    if (!editingMenu || !editMenuForm.plato_principal) { toast.error('Ingresá el plato principal'); return }
    setSavingEditMenu(true)
    try {
      await api.put(`/almuerzos/menu/${editingMenu.id}/`, editMenuForm)
      toast.success('Menú actualizado')
      setEditMenuOpen(false)
      loadMenu()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingEditMenu(false)
    }
  }, [editingMenu, editMenuForm, loadMenu])

  const toggleMenuActivo = useCallback(async (m: MenuDiario) => {
    try {
      await api.patch(`/almuerzos/menu/${m.id}/`, { activo: !m.activo })
      toast.success(m.activo ? 'Menú desactivado' : 'Menú activado')
      loadMenu()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadMenu])

  // ── Pago cuenta ───────────────────────────────────────────────────
  const openPagoCuenta = useCallback((c: CuentaMensual) => {
    setPagoCuenta(c)
    const pendiente = Number(c.saldo_pendiente) || (Number(c.monto_total) - Number(c.monto_pagado))
    setPagoForm({ monto: String(pendiente > 0 ? pendiente : ''), medio_pago: 'EFECTIVO', referencia: '' })
    setPagoOpen(true)
  }, [])

  const handlePagar = useCallback(async () => {
    if (!pagoCuenta) return
    if (!pagoForm.monto || Number(pagoForm.monto) <= 0) { toast.error('Ingresá el monto'); return }
    setSavingPago(true)
    try {
      await api.post('/almuerzos/pagos-cuenta/', {
        cuenta: pagoCuenta.id,
        monto: Number(pagoForm.monto),
        medio_pago: pagoForm.medio_pago,
        referencia: pagoForm.referencia || undefined,
      })
      toast.success('Pago registrado')
      setPagoOpen(false)
      loadCuentas()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingPago(false)
    }
  }, [pagoCuenta, pagoForm, loadCuentas])

  // ── Generar cuentas del mes ───────────────────────────────────────
  const handleGenerarCuentas = useCallback(async () => {
    setGenerando(true)
    try {
      const body: Record<string, unknown> = {}
      if (filtroCuentaAnio) body.anio = filtroCuentaAnio
      if (filtroCuentaMes) body.mes = filtroCuentaMes
      await api.post('/almuerzos/cuentas-mensuales/generar/', body)
      toast.success('Cuentas generadas')
      loadCuentas()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setGenerando(false)
    }
  }, [filtroCuentaAnio, filtroCuentaMes, loadCuentas])

  // ── Suspender suscripcion ─────────────────────────────────────────
  const suspenderSusc = useCallback(async (id: number) => {
    try {
      await api.patch(`/almuerzos/suscripciones/${id}/`, { estado: 'SUSPENDIDA' })
      toast.success('Suscripción suspendida')
      loadSuscripciones()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadSuscripciones])

  // ── Edit suscripcion ──────────────────────────────────────────────
  const openEditSusc = useCallback((s: Suscripcion) => {
    setEditingSusc(s)
    setEditSuscForm({ plan: String(s.plan), fecha_fin: s.fecha_fin ?? '' })
    setEditSuscOpen(true)
  }, [])

  const handleSaveEditSusc = useCallback(async () => {
    if (!editingSusc || !editSuscForm.plan) { toast.error('Seleccioná un plan'); return }
    setSavingEditSusc(true)
    try {
      await api.patch(`/almuerzos/suscripciones/${editingSusc.id}/`, {
        plan: Number(editSuscForm.plan),
        fecha_fin: editSuscForm.fecha_fin || null,
      })
      toast.success('Suscripción actualizada')
      setEditSuscOpen(false)
      loadSuscripciones()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSavingEditSusc(false)
    }
  }, [editingSusc, editSuscForm, loadSuscripciones])

  // ── Anular consumo ────────────────────────────────────────────────
  const anularConsumo = useCallback(async (id: number) => {
    try {
      await api.patch(`/almuerzos/registros-consumo/${id}/`, { estado: 'ANULADO' })
      toast.success('Consumo anulado')
      loadRegistros(searchRegistros, pageRegistros)
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadRegistros, searchRegistros, pageRegistros])

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
    {
      title: '',
      key: 'acc',
      width: 90,
      render: (_, r) => r.estado === 'REGISTRADO' ? (
        <Button size="sm" variant="danger" onClick={() => anularConsumo(r.id)}>
          <X className="w-3.5 h-3.5" />
          Anular
        </Button>
      ) : null,
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
    {
      title: '',
      key: 'acc',
      width: 80,
      render: (_, r) => (r.estado !== 'PAGADO' && r.estado !== 'ANULADO') ? (
        <Button size="sm" variant="primary" onClick={() => openPagoCuenta(r)}>
          <Banknote className="w-3.5 h-3.5" />
          Pagar
        </Button>
      ) : null,
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
      width: 160,
      render: (_, r) => r.estado === 'ACTIVA' ? (
        <div className="flex gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => openEditSusc(r)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="secondary" onClick={() => suspenderSusc(r.id)}>
            <PauseCircle className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="danger" onClick={() => cancelarSusc(r.id)}>
            <X className="w-3.5 h-3.5" />
          </Button>
        </div>
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
      title: 'Plato principal',
      key: 'plato',
      render: (_, r) => <span className="text-sm text-slate-700">{r.plato_principal}</span>,
    },
    {
      title: 'Guarnición / Postre / Bebida',
      key: 'extras',
      render: (_, r) => (
        <span className="text-sm text-slate-500">
          {[r.guarnicion, r.postre, r.bebida].filter(Boolean).join(' · ') || '—'}
        </span>
      ),
    },
    {
      title: 'Notas',
      key: 'desc',
      render: (_, r) => <span className="text-sm text-slate-400">{r.descripcion || '—'}</span>,
    },
    {
      title: 'Estado',
      key: 'activo',
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acc',
      width: 100,
      render: (_, r) => (
        <div className="flex gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => openEditMenu(r)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant={r.activo ? 'danger' : 'secondary'} onClick={() => toggleMenuActivo(r)}>
            {r.activo ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </Button>
        </div>
      ),
    },
  ]

  // ── Styles ────────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

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
    { key: 'consumos',      label: 'Consumos',          icon: UtensilsCrossed },
    { key: 'cuentas',       label: 'Cuentas Mensuales', icon: BarChart2 },
    { key: 'suscripciones', label: 'Suscripciones',     icon: Users },
    { key: 'menu',          label: 'Menú',              icon: Calendar },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('almuerzos.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('almuerzos.subtitle')}</p>
        </div>
        {tab === 'consumos' && (
          <Button variant="primary" onClick={() => setConsumoOpen(true)}>
            <Plus className="w-4 h-4" />
            Registrar Consumo
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
                <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
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
                pageSize={15} page={pageRegistros} onPageChange={handlePageChange} total={totalRegistros} />
            </div>
          </div>
        </>
      )}

      {/* ── Cuentas tab ──────────────────────────────────────────── */}
      {tab === 'cuentas' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-sm font-semibold text-slate-800">Cuentas Mensuales de Almuerzos</h2>
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={filtroCuentaMes}
                onChange={e => setFiltroCuentaMes(Number(e.target.value) || '')}
                className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30"
              >
                <option value="">Todos los meses</option>
                {MESES.slice(1).map((m, i) => <option key={i + 1} value={i + 1}>{m}</option>)}
              </select>
              <input
                type="number"
                placeholder="Año"
                value={filtroCuentaAnio}
                onChange={e => setFiltroCuentaAnio(Number(e.target.value) || '')}
                className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 w-24"
              />
              <Button variant="secondary" size="sm" loading={generando} onClick={handleGenerarCuentas}>
                <RefreshCw className="w-3.5 h-3.5" />
                Generar
              </Button>
              {cuentas.length > 0 && (
                <Button variant="secondary" size="sm" onClick={() => exportarCuentasMensualesPDF(cuentas, filtroCuentaMes !== '' ? filtroCuentaMes : undefined, filtroCuentaAnio !== '' ? filtroCuentaAnio : undefined)}>
                  <FileText className="w-3.5 h-3.5" />
                  PDF
                </Button>
              )}
            </div>
          </div>
          <div className="p-1">
            <Table columns={colsCuentas} dataSource={cuentas} rowKey="id" loading={loadingCuentas} pageSize={15} />
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
                onKeyDown={e => { if (e.key === 'Enter') { const v = e.currentTarget.value.trim(); if (v) buscarTarjeta(v) } }}
                className="flex-1 border border-slate-200 rounded-xl px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500"
              />
              <Button size="sm" variant="secondary" loading={tarjetaBuscando} onClick={() => buscarTarjeta()}>
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
              disabled={!!tarjeta}
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

      {/* ── Pago cuenta modal ─────────────────────────────────────── */}
      <Modal
        open={pagoOpen}
        title="Registrar Pago de Cuenta"
        onOk={handlePagar}
        onCancel={() => setPagoOpen(false)}
        okText="Registrar Pago"
        confirmLoading={savingPago}
        width={440}
      >
        {pagoCuenta && (
          <div className="space-y-4">
            <div className="bg-slate-50 rounded-xl p-4">
              <p className="text-sm font-semibold text-slate-800">{pagoCuenta.hijo_nombre}</p>
              <p className="text-xs text-slate-500 mt-1">{MESES[pagoCuenta.mes]} {pagoCuenta.anio} — {pagoCuenta.cantidad_almuerzos} almuerzos</p>
              <div className="flex gap-6 mt-3">
                <div>
                  <p className="text-sm text-slate-400">Total</p>
                  <p className="text-sm font-bold text-slate-800">{formatGs(pagoCuenta.monto_total)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Pagado</p>
                  <p className="text-sm font-bold text-emerald-700">{formatGs(pagoCuenta.monto_pagado)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Saldo</p>
                  <p className="text-sm font-bold text-red-600">{formatGs(pagoCuenta.saldo_pendiente)}</p>
                </div>
              </div>
            </div>
            <div>
              <label className={labelClass}>Monto (Gs.) *</label>
              <input
                type="number"
                min={1}
                step={1000}
                value={pagoForm.monto}
                onChange={e => setPagoForm(f => ({ ...f, monto: e.target.value }))}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Medio de Pago</label>
              <select
                value={pagoForm.medio_pago}
                onChange={e => setPagoForm(f => ({ ...f, medio_pago: e.target.value }))}
                className={inputClass}
              >
                <option value="EFECTIVO">Efectivo</option>
                <option value="TRANSFERENCIA">Transferencia</option>
                <option value="TARJETA">Tarjeta</option>
                <option value="CHEQUE">Cheque</option>
              </select>
            </div>
            {pagoForm.medio_pago !== 'EFECTIVO' && (
              <div>
                <label className={labelClass}>Referencia</label>
                <input
                  value={pagoForm.referencia}
                  onChange={e => setPagoForm(f => ({ ...f, referencia: e.target.value }))}
                  placeholder="Nro. de transferencia, cheque, etc."
                  className={inputClass}
                />
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* ── Edit suscripción modal ────────────────────────────────── */}
      <Modal
        open={editSuscOpen}
        title="Editar Suscripción"
        onOk={handleSaveEditSusc}
        onCancel={() => setEditSuscOpen(false)}
        okText="Guardar"
        confirmLoading={savingEditSusc}
        width={440}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Plan *</label>
            <select value={editSuscForm.plan} onChange={e => setEditSuscForm(f => ({ ...f, plan: e.target.value }))} className={inputClass}>
              <option value="">Seleccionar...</option>
              {planes.filter(p => p.activo).map(p => (
                <option key={p.id} value={p.id}>{p.nombre} — {formatGs(p.precio_mensual)}/mes</option>
              ))}
            </select>
          </div>
          <div>
            <label className={labelClass}>Fecha de Fin (opcional)</label>
            <input type="date" value={editSuscForm.fecha_fin} onChange={e => setEditSuscForm(f => ({ ...f, fecha_fin: e.target.value }))} className={inputClass} />
          </div>
        </div>
      </Modal>

      {/* ── Edit menú modal ───────────────────────────────────────── */}
      <Modal
        open={editMenuOpen}
        title="Editar Menú"
        onOk={handleSaveEditMenu}
        onCancel={() => setEditMenuOpen(false)}
        okText="Guardar"
        confirmLoading={savingEditMenu}
        width={560}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Fecha *</label>
            <input type="date" value={editMenuForm.fecha} onChange={e => setEditMenuForm(f => ({ ...f, fecha: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Plato principal *</label>
            <input value={editMenuForm.plato_principal} onChange={e => setEditMenuForm(f => ({ ...f, plato_principal: e.target.value }))} className={inputClass} />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className={labelClass}>Guarnición</label>
              <input value={editMenuForm.guarnicion} onChange={e => setEditMenuForm(f => ({ ...f, guarnicion: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Postre</label>
              <input value={editMenuForm.postre} onChange={e => setEditMenuForm(f => ({ ...f, postre: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Bebida</label>
              <input value={editMenuForm.bebida} onChange={e => setEditMenuForm(f => ({ ...f, bebida: e.target.value }))} className={inputClass} />
            </div>
          </div>
          <div>
            <label className={labelClass}>Notas</label>
            <textarea value={editMenuForm.descripcion} onChange={e => setEditMenuForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          {toggleSwitch(editMenuForm.activo, v => setEditMenuForm(f => ({ ...f, activo: v })), 'Activo')}
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
        width={560}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Fecha *</label>
            <input type="date" value={menuForm.fecha} onChange={e => setMenuForm(f => ({ ...f, fecha: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Plato principal *</label>
            <input
              value={menuForm.plato_principal}
              onChange={e => setMenuForm(f => ({ ...f, plato_principal: e.target.value }))}
              placeholder="Ej: Milanesa con papas"
              className={inputClass}
            />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className={labelClass}>Guarnición</label>
              <input
                value={menuForm.guarnicion}
                onChange={e => setMenuForm(f => ({ ...f, guarnicion: e.target.value }))}
                placeholder="Ej: Ensalada"
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Postre</label>
              <input
                value={menuForm.postre}
                onChange={e => setMenuForm(f => ({ ...f, postre: e.target.value }))}
                placeholder="Ej: Fruta"
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Bebida</label>
              <input
                value={menuForm.bebida}
                onChange={e => setMenuForm(f => ({ ...f, bebida: e.target.value }))}
                placeholder="Ej: Jugo"
                className={inputClass}
              />
            </div>
          </div>
          <div>
            <label className={labelClass}>Notas</label>
            <textarea
              value={menuForm.descripcion}
              onChange={e => setMenuForm(f => ({ ...f, descripcion: e.target.value }))}
              rows={2}
              placeholder="Información adicional..."
              className={`${inputClass} resize-none`}
            />
          </div>
        </div>
      </Modal>
    </div>
  )
}
