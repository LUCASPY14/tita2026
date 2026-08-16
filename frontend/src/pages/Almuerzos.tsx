import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  UtensilsCrossed, Plus, Search, Edit2, X,
  CheckCircle, Calendar, Users, BarChart2,
  PauseCircle, Banknote, RefreshCw, EyeOff, Eye, FileText, Trash2,
} from 'lucide-react'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'
import { exportarCuentasMensualesPDF, type RegistroConsumoDetalle } from '../utils/pdf'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import ModalConsumo from './almuerzos/ModalConsumo'
import ModalSuscripcion from './almuerzos/ModalSuscripcion'
import ModalPagoCuenta from './almuerzos/ModalPagoCuenta'
import ModalEditSusc from './almuerzos/ModalEditSusc'
import ModalMenu from './almuerzos/ModalMenu'
import ModalEditMenu from './almuerzos/ModalEditMenu'
import ModalConfirmarEliminar from './almuerzos/ModalConfirmarEliminar'
import ModalConfirmarAnular from './almuerzos/ModalConfirmarAnular'
import ModalPagoMensual from './almuerzos/ModalPagoMensual'
import {
  extractErrorMessage, formatGs, formatFecha, todayISO, MESES,
  ESTADO_REGISTRO_COLOR, ESTADO_CUENTA_COLOR, ESTADO_SUSCRIPCION_COLOR,
  type TabKey, type Hijo, type TipoAlmuerzo, type PlanAlmuerzo, type Suscripcion,
  type MenuDiario, type RegistroConsumo, type CuentaMensual,
} from './almuerzos/shared'

export default function Almuerzos() {
  const { t } = useTranslation()
  const isAdmin = useAuthStore(s => s.user?.rol === 'ADMIN')
  const [tab, setTab] = useState<TabKey>('consumos')

  // ── Catálogos ─────────────────────────────────────────────────────
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

  // ── Modal open states ─────────────────────────────────────────────
  const [consumoOpen, setConsumoOpen] = useState(false)
  const [suscModalOpen, setSuscModalOpen] = useState(false)
  const [menuModalOpen, setMenuModalOpen] = useState(false)
  const [pagoCuenta, setPagoCuenta] = useState<CuentaMensual | null>(null)
  const [editingSusc, setEditingSusc] = useState<Suscripcion | null>(null)
  const [editingMenu, setEditingMenu] = useState<MenuDiario | null>(null)
  const [deleteConsumoId, setDeleteConsumoId] = useState<number | null>(null)
  const [anularConsumoId, setAnularConsumoId] = useState<number | null>(null)
  const [pagoMensualSusc, setPagoMensualSusc] = useState<Suscripcion | null>(null)

  // ── Cuentas ───────────────────────────────────────────────────────
  const [cuentas, setCuentas] = useState<CuentaMensual[]>([])
  const [loadingCuentas, setLoadingCuentas] = useState(false)
  const [filtroCuentaMes, setFiltroCuentaMes] = useState<number | ''>('')
  const [filtroCuentaAnio, setFiltroCuentaAnio] = useState<number | ''>(new Date().getFullYear())
  const [searchCuentas, setSearchCuentas] = useState('')
  const [generando, setGenerando] = useState(false)

  // ── Suscripciones ─────────────────────────────────────────────────
  const [suscripciones, setSuscripciones] = useState<Suscripcion[]>([])
  const [loadingSusc, setLoadingSusc] = useState(false)

  // ── Menú ──────────────────────────────────────────────────────────
  const [menu, setMenu] = useState<MenuDiario[]>([])
  const [loadingMenu, setLoadingMenu] = useState(false)

  const [exportandoPDF, setExportandoPDF] = useState(false)

  // ── Load catálogos ────────────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      api.get('/clientes/hijos/', { params: { page_size: 500 } }),
      api.get('/almuerzos/tipos-almuerzo/', { params: { page_size: 100 } }),
      api.get('/almuerzos/planes-almuerzo/', { params: { page_size: 100 } }),
    ]).then(([hRes, tRes, pRes]) => {
      setHijos(hRes.data.results ?? [])
      setTiposAlmuerzo(tRes.data.results ?? [])
      setPlanes(pRes.data.results ?? [])
    }).catch(() => toast.error('Error al cargar datos iniciales'))
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
    // eslint-disable-next-line react-hooks/set-state-in-effect
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
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (tab === 'suscripciones') loadSuscripciones()
  }, [tab, loadSuscripciones])

  // ── Load menú ─────────────────────────────────────────────────────
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
    // eslint-disable-next-line react-hooks/set-state-in-effect
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


  const cancelarSusc = useCallback(async (id: number) => {
    try {
      await api.patch(`/almuerzos/suscripciones/${id}/`, { estado: 'CANCELADA' })
      toast.success('Suscripción cancelada')
      loadSuscripciones()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadSuscripciones])

  const suspenderSusc = useCallback(async (id: number) => {
    try {
      await api.patch(`/almuerzos/suscripciones/${id}/`, { estado: 'SUSPENDIDA' })
      toast.success('Suscripción suspendida')
      loadSuscripciones()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadSuscripciones])

  const toggleMenuActivo = useCallback(async (m: MenuDiario) => {
    try {
      await api.patch(`/almuerzos/menu/${m.id}/`, { activo: !m.activo })
      toast.success(m.activo ? 'Menú desactivado' : 'Menú activado')
      loadMenu()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadMenu])

  // ── Generar cuentas ───────────────────────────────────────────────
  const handleGenerarCuentas = useCallback(async () => {
    if (!filtroCuentaMes) {
      toast.error('Seleccioná un mes específico para generar las cuentas')
      return
    }
    if (!filtroCuentaAnio) {
      toast.error('Ingresá el año para generar las cuentas')
      return
    }
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

  // ── Exportar PDF ──────────────────────────────────────────────────
  const cuentasFiltradas = useMemo(() => {
    const q = searchCuentas.trim().toLowerCase()
    if (!q) return cuentas
    return cuentas.filter(c =>
      c.hijo_nombre.toLowerCase().includes(q) ||
      (c.nro_tarjeta ?? '').toLowerCase().includes(q) ||
      (c.hijo_grado ?? '').toLowerCase().includes(q)
    )
  }, [cuentas, searchCuentas])

  const handleExportarPDF = useCallback(async () => {
    if (!filtroCuentaAnio) return
    setExportandoPDF(true)
    try {
      const anio = Number(filtroCuentaAnio)
      const mes = filtroCuentaMes !== '' ? Number(filtroCuentaMes) : undefined
      const fechaDesde = mes
        ? `${anio}-${String(mes).padStart(2, '0')}-01`
        : `${anio}-01-01`
      const fechaHasta = mes
        ? `${anio}-${String(mes).padStart(2, '0')}-${new Date(anio, mes, 0).getDate()}`
        : `${anio}-12-31`

      const { data } = await api.get('/almuerzos/registros-consumo/', {
        params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta, ya_cobrado: true, estado: 'REGISTRADO', ordering: 'hijo,fecha_consumo', page_size: 1000 },
      })
      const registrosData: (RegistroConsumoDetalle & { hijo: number })[] = data.results ?? []
      const detalleMap = new Map<number, RegistroConsumoDetalle[]>()
      for (const r of registrosData) {
        if (!detalleMap.has(r.hijo)) detalleMap.set(r.hijo, [])
        detalleMap.get(r.hijo)!.push(r)
      }
      exportarCuentasMensualesPDF(cuentasFiltradas, mes, Number(filtroCuentaAnio), detalleMap)
    } catch {
      toast.error('Error al generar PDF')
    } finally {
      setExportandoPDF(false)
    }
  }, [cuentasFiltradas, filtroCuentaMes, filtroCuentaAnio])

  // ── Stats ─────────────────────────────────────────────────────────
  const mesActual = new Date().getMonth() + 1
  const anioActual = new Date().getFullYear()
  const hoy = todayISO()

  const stats = useMemo(() => ({
    consumosHoy: registros.filter(r => r.fecha_consumo === hoy).length,
    cuentasPendientes: cuentas.filter(c => c.estado !== 'PAGADO' && c.estado !== 'ANULADO').length,
    facturadoMes: cuentas.filter(c => c.mes === mesActual && c.anio === anioActual).reduce((s, c) => s + (Number(c.monto_total) || 0), 0),
  }), [registros, cuentas, hoy, mesActual, anioActual])

  // ── Columnas ──────────────────────────────────────────────────────
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
      width: 120,
      render: (_, r) => (
        <div className="flex gap-1.5">
          {r.estado === 'REGISTRADO' && (
            <Button size="sm" variant="danger" onClick={() => setAnularConsumoId(r.id)}>
              <X className="w-3.5 h-3.5" />
              Anular
            </Button>
          )}
          {r.estado === 'ANULADO' && isAdmin && (
            <Button size="sm" variant="danger" onClick={() => setDeleteConsumoId(r.id)}>
              <Trash2 className="w-3.5 h-3.5" />
              Eliminar
            </Button>
          )}
        </div>
      ),
    },
  ]

  const colsCuentas: Column<CuentaMensual>[] = [
    {
      title: 'Estudiante',
      key: 'hijo',
      render: (_, r) => (
        <div>
          <p className="text-sm font-medium text-slate-800">{r.hijo_nombre}</p>
          {r.hijo_grado && <p className="text-xs text-slate-400">{r.hijo_grado}</p>}
        </div>
      ),
    },
    {
      title: 'Tarjeta',
      key: 'tarjeta',
      render: (_, r) => (
        <span className="font-mono text-xs text-slate-500">{r.nro_tarjeta || '—'}</span>
      ),
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
        <Button size="sm" variant="primary" onClick={() => setPagoCuenta(r)}>
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
      title: 'Tipo de cobro',
      key: 'tipo_cobro',
      render: (_, r) => (
        <Badge color={r.tipo_cobro === 'MENSUAL' ? 'blue' : 'orange'}>
          {r.tipo_cobro === 'MENSUAL' ? 'Cuota fija' : 'Por consumo'}
        </Badge>
      ),
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
      width: 200,
      render: (_, r) => r.estado === 'ACTIVA' ? (
        <div className="flex gap-1.5">
          {r.tipo_cobro === 'MENSUAL' && (
            <Button size="sm" variant="primary" onClick={() => setPagoMensualSusc(r)}>
              <Banknote className="w-3.5 h-3.5" />
              Cuota
            </Button>
          )}
          <Button size="sm" variant="secondary" onClick={() => setEditingSusc(r)}>
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
          <Button size="sm" variant="secondary" onClick={() => setEditingMenu(r)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant={r.activo ? 'danger' : 'secondary'} onClick={() => toggleMenuActivo(r)}>
            {r.activo ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
          </Button>
        </div>
      ),
    },
  ]

  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'

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
          <Button variant="primary" onClick={() => setSuscModalOpen(true)}>
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

      {/* Summary cards */}
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
              <input
                placeholder="Buscar alumno, tarjeta, grado..."
                value={searchCuentas}
                onChange={e => setSearchCuentas(e.target.value)}
                className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 w-52"
              />
              {cuentas.length > 0 && (
                <Button variant="secondary" size="sm" loading={exportandoPDF} onClick={handleExportarPDF}>
                  <FileText className="w-3.5 h-3.5" />
                  PDF
                </Button>
              )}
            </div>
          </div>
          <div className="p-1">
            <Table columns={colsCuentas} dataSource={cuentasFiltradas} rowKey="id" loading={loadingCuentas} pageSize={15} />
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

      {/* ── Modales ───────────────────────────────────────────────── */}
      <ModalConsumo
        open={consumoOpen}
        hijos={hijos}
        tiposAlmuerzo={tiposAlmuerzo}
        onClose={() => setConsumoOpen(false)}
        onSaved={() => { setPageRegistros(1); loadRegistros('', 1) }}
      />
      <ModalSuscripcion
        open={suscModalOpen}
        hijos={hijos}
        planes={planes}
        onClose={() => setSuscModalOpen(false)}
        onSaved={loadSuscripciones}
      />
      <ModalPagoCuenta
        cuenta={pagoCuenta}
        onClose={() => setPagoCuenta(null)}
        onSaved={loadCuentas}
      />
      <ModalEditSusc
        susc={editingSusc}
        planes={planes}
        onClose={() => setEditingSusc(null)}
        onSaved={loadSuscripciones}
      />
      <ModalMenu
        open={menuModalOpen}
        onClose={() => setMenuModalOpen(false)}
        onSaved={loadMenu}
      />
      <ModalEditMenu
        menu={editingMenu}
        onClose={() => setEditingMenu(null)}
        onSaved={loadMenu}
      />
      <ModalConfirmarEliminar
        consumoId={deleteConsumoId}
        onClose={() => setDeleteConsumoId(null)}
        onSaved={() => loadRegistros(searchRegistros, pageRegistros)}
      />
      <ModalConfirmarAnular
        consumoId={anularConsumoId}
        onClose={() => setAnularConsumoId(null)}
        onSaved={() => loadRegistros(searchRegistros, pageRegistros)}
      />
      <ModalPagoMensual
        susc={pagoMensualSusc}
        planes={planes}
        onClose={() => setPagoMensualSusc(null)}
        onSaved={loadSuscripciones}
      />
    </div>
  )
}
