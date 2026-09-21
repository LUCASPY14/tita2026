import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import {
  UtensilsCrossed, Plus, Search, Edit2, X,
  CheckCircle, Calendar, Users, BarChart2,
  PauseCircle, Banknote, EyeOff, Eye, FileText, Trash2, Wallet,
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
import ModalConfirmarRecarga from './almuerzos/ModalConfirmarRecarga'
import ModalEditSusc from './almuerzos/ModalEditSusc'
import ModalMenu from './almuerzos/ModalMenu'
import ModalEditMenu from './almuerzos/ModalEditMenu'
import ModalConfirmarEliminar from './almuerzos/ModalConfirmarEliminar'
import ModalConfirmarAnular from './almuerzos/ModalConfirmarAnular'
import ModalTopeAlmuerzo from './almuerzos/ModalTopeAlmuerzo'
import {
  extractErrorMessage, formatGs, formatFecha, MESES,
  ESTADO_REGISTRO_COLOR, ESTADO_CUENTA_COLOR, ESTADO_SUSCRIPCION_COLOR,
  type TabKey, type Hijo, type TipoAlmuerzo, type Suscripcion,
  type MenuDiario, type RegistroConsumo, type CuentaMensual,
  type SaldoAlmuerzoItem, type ResumenSaldos, type CargaAlmuerzoTarget, type RecargaPendiente,
} from './almuerzos/shared'

export default function Almuerzos() {
  const { t } = useTranslation()
  const rolActual = useAuthStore(s => s.user?.rol)
  const isAdmin = rolActual === 'ADMIN'
  const puedeConfigurarTope = rolActual === 'ADMIN' || rolActual === 'SUPERVISOR'
  const [topeAlmuerzo, setTopeAlmuerzo] = useState<SaldoAlmuerzoItem | null>(null)
  const [tab, setTab] = useState<TabKey>('consumos')

  // ── Catálogos ─────────────────────────────────────────────────────
  const [hijos, setHijos] = useState<Hijo[]>([])
  const [tiposAlmuerzo, setTiposAlmuerzo] = useState<TipoAlmuerzo[]>([])

  // ── Consumos ─────────────────────────────────────────────────────
  const [registros, setRegistros] = useState<RegistroConsumo[]>([])
  const [loadingRegistros, setLoadingRegistros] = useState(false)
  const [searchRegistros, setSearchRegistros] = useState('')
  const [pageRegistros, setPageRegistros] = useState(1)
  const [totalRegistros, setTotalRegistros] = useState(0)
  const searchTimerReg = useRef<ReturnType<typeof setTimeout>>(undefined)

  // Calculado en el backend: no depende de la página ni del buscador del listado.
  const [consumosHoy, setConsumosHoy] = useState(0)

  // ── Modal open states ─────────────────────────────────────────────
  const [consumoOpen, setConsumoOpen] = useState(false)
  const [suscModalOpen, setSuscModalOpen] = useState(false)
  const [menuModalOpen, setMenuModalOpen] = useState(false)
  const [pagoCuenta, setPagoCuenta] = useState<CargaAlmuerzoTarget | null>(null)
  const [editingSusc, setEditingSusc] = useState<Suscripcion | null>(null)
  const [editingMenu, setEditingMenu] = useState<MenuDiario | null>(null)
  const [deleteConsumoId, setDeleteConsumoId] = useState<number | null>(null)
  const [anularConsumoId, setAnularConsumoId] = useState<number | null>(null)

  // ── Cuentas ───────────────────────────────────────────────────────
  const [cuentas, setCuentas] = useState<CuentaMensual[]>([])
  const [loadingCuentas, setLoadingCuentas] = useState(false)
  const [filtroCuentaMes, setFiltroCuentaMes] = useState<number | ''>('')
  const [filtroCuentaAnio, setFiltroCuentaAnio] = useState<number | ''>(new Date().getFullYear())
  const [searchCuentas, setSearchCuentas] = useState('')

  // ── Saldos (panel de cobranza) ────────────────────────────────────
  const [saldos, setSaldos] = useState<SaldoAlmuerzoItem[]>([])
  const [loadingSaldos, setLoadingSaldos] = useState(false)
  const [searchSaldos, setSearchSaldos] = useState('')
  const [soloDeuda, setSoloDeuda] = useState(true)
  const [pageSaldos, setPageSaldos] = useState(1)
  const [totalSaldos, setTotalSaldos] = useState(0)
  const [resumenSaldos, setResumenSaldos] = useState<ResumenSaldos | null>(null)
  const [recargasPendientes, setRecargasPendientes] = useState<RecargaPendiente[]>([])
  const [confirmarRecarga, setConfirmarRecarga] = useState<RecargaPendiente | null>(null)
  const searchTimerSaldos = useRef<ReturnType<typeof setTimeout>>(undefined)

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
    ]).then(([hRes, tRes]) => {
      setHijos(hRes.data.results ?? [])
      setTiposAlmuerzo(tRes.data.results ?? [])
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

  const loadConsumosHoy = useCallback(async () => {
    try {
      const { data } = await api.get('/almuerzos/registros-consumo/resumen-hoy/')
      setConsumosHoy(Number(data.almuerzos_hoy) || 0)
    } catch {
      // La tarjeta es informativa: si falla, conserva el último valor.
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadConsumosHoy()
  }, [loadConsumosHoy, registros])

  const handlePageChange = useCallback((page: number) => {
    setPageRegistros(page)
    loadRegistros(searchRegistros, page)
  }, [loadRegistros, searchRegistros])

  // ── Load cuentas ──────────────────────────────────────────────────
  // Calculado en vivo (estado-cuenta) — sin tabla intermedia que generar.
  const loadCuentas = useCallback(async () => {
    if (!filtroCuentaAnio) return
    setLoadingCuentas(true)
    try {
      const params: Record<string, unknown> = { anio: filtroCuentaAnio }
      if (filtroCuentaMes) params.mes = filtroCuentaMes
      const { data } = await api.get('/almuerzos/estado-cuenta/', { params })
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

  // ── Load saldos ───────────────────────────────────────────────────
  const loadSaldos = useCallback(async (q: string, deuda: boolean, p: number) => {
    setLoadingSaldos(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering: 'saldo_actual' }
      if (q) params.search = q
      if (deuda) params.con_deuda = true
      const [{ data }, { data: resumen }, pendientes] = await Promise.all([
        api.get('/almuerzos/saldos/', { params }),
        api.get('/almuerzos/saldos/resumen/'),
        // Roles sin permiso sobre recargas (403) simplemente no ven la sección.
        api.get('/almuerzos/recargas-saldo/', { params: { estado: 'PENDIENTE', page_size: 50, ordering: 'fecha_carga' } })
          .catch(() => ({ data: { results: [] } })),
      ])
      setSaldos(data.results ?? [])
      setTotalSaldos(data.count ?? 0)
      setResumenSaldos(resumen)
      setRecargasPendientes(pendientes.data.results ?? [])
    } catch {
      toast.error('Error al cargar saldos de almuerzo')
    } finally {
      setLoadingSaldos(false)
    }
  }, [])

  useEffect(() => {
    if (tab !== 'saldos') return
    clearTimeout(searchTimerSaldos.current)
    searchTimerSaldos.current = setTimeout(() => {
      setPageSaldos(1)
      loadSaldos(searchSaldos, soloDeuda, 1)
    }, 350)
    return () => clearTimeout(searchTimerSaldos.current)
  }, [tab, searchSaldos, soloDeuda, loadSaldos])

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
      loadConsumosHoy()
      if (tab === 'consumos') loadRegistros(searchRegistros, pageRegistros)
      if (tab === 'cuentas') loadCuentas()
      if (tab === 'saldos') loadSaldos(searchSaldos, soloDeuda, pageSaldos)
    }
    window.addEventListener('comedor:registro', handler)
    return () => window.removeEventListener('comedor:registro', handler)
  }, [tab, searchRegistros, pageRegistros, loadRegistros, loadCuentas, loadConsumosHoy, loadSaldos, searchSaldos, soloDeuda, pageSaldos])


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
      await api.patch(`/almuerzos/menu/${m.id_menu}/`, { activo: !m.activo })
      toast.success(m.activo ? 'Menú desactivado' : 'Menú activado')
      loadMenu()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    }
  }, [loadMenu])

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
  const stats = useMemo(() => {
    // "Estado" ahora es el saldo al cierre de CADA mes, no el de hoy — para
    // saber quién debe hoy hay que mirar la fila más reciente de cada alumno
    // (la de arrastre no cuenta: no tiene saldo propio).
    const ultimaPorHijo = new Map<number, CuentaMensual>()
    for (const c of cuentas) {
      if (c.es_arrastre || c.mes === null) continue
      const actual = ultimaPorHijo.get(c.hijo)
      if (!actual || c.anio > actual.anio || (c.anio === actual.anio && c.mes > (actual.mes ?? 0))) {
        ultimaPorHijo.set(c.hijo, c)
      }
    }
    return {
      consumosHoy,
      cuentasPendientes: [...ultimaPorHijo.values()].filter(c => c.estado === 'PENDIENTE').length,
      facturadoMes: cuentas.filter(c => c.mes === mesActual && c.anio === anioActual).reduce((s, c) => s + (Number(c.monto_total) || 0), 0),
    }
  }, [consumosHoy, cuentas, mesActual, anioActual])

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
            <Button size="sm" variant="danger" onClick={() => setAnularConsumoId(r.id_registro_consumo)}>
              <X className="w-3.5 h-3.5" />
              Anular
            </Button>
          )}
          {r.estado === 'ANULADO' && isAdmin && (
            <Button size="sm" variant="danger" onClick={() => setDeleteConsumoId(r.id_registro_consumo)}>
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
      render: (_, r) => r.es_arrastre ? (
        <span className="text-sm text-slate-500 italic">
          Antes de {r.arrastre_hasta_mes !== null ? MESES[r.arrastre_hasta_mes] : ''} {r.arrastre_hasta_anio}
        </span>
      ) : (
        <span className="text-sm text-slate-600">{r.mes !== null ? MESES[r.mes] : ''} {r.anio}</span>
      ),
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
      title: 'Saldo inicial',
      hint: 'Saldo con el que arrancó el mes — es el saldo al cierre del mes anterior.',
      key: 'saldo_inicial',
      render: (_, r) => r.saldo_inicial === null ? (
        <span className="text-sm text-slate-300">—</span>
      ) : (
        <span className="tabular-nums text-sm text-slate-500">{formatGs(r.saldo_inicial)}</span>
      ),
    },
    {
      title: 'Saldo al cierre',
      hint: 'Saldo del alumno al cerrar ESE mes (no el de hoy) — es el que se arrastra como saldo inicial del mes siguiente.',
      key: 'saldo',
      render: (_, r) => {
        if (r.saldo_final === null) return <span className="text-sm text-slate-300">—</span>
        const n = Number(r.saldo_final) || 0
        return (
          <span
            title="Saldo del alumno al cerrar este mes"
            className={`tabular-nums font-semibold text-sm ${n < 0 ? 'text-red-600' : n > 0 ? 'text-emerald-700' : 'text-slate-400'}`}
          >
            {formatGs(n)}
          </span>
        )
      },
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => r.estado ? <Badge color={ESTADO_CUENTA_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge> : <span className="text-slate-300 text-sm">—</span>,
    },
    {
      title: '',
      key: 'acc',
      width: 130,
      render: (_, r) => r.es_arrastre ? null : (
        <Button size="sm" variant="primary" onClick={() => setPagoCuenta({
          hijo: r.hijo,
          hijo_nombre: r.hijo_nombre,
          monto_sugerido: Number(r.saldo_pendiente) || 0,
          detalle: `${r.mes !== null ? MESES[r.mes] : ''} ${r.anio} — ${r.cantidad_almuerzos} almuerzos, total ${formatGs(r.monto_total)}`,
        })}>
          <Banknote className="w-3.5 h-3.5" />
          Cargar saldo
        </Button>
      ),
    },
  ]

  const colsSaldos: Column<SaldoAlmuerzoItem>[] = [
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
      render: (_, r) => <span className="font-mono text-xs text-slate-500">{r.nro_tarjeta || '—'}</span>,
    },
    {
      title: 'Saldo',
      key: 'saldo',
      render: (_, r) => {
        const n = Number(r.saldo_actual) || 0
        return (
          <span className={`tabular-nums font-semibold text-sm ${n < 0 ? 'text-red-600' : n > 0 ? 'text-emerald-700' : 'text-slate-400'}`}>
            {formatGs(n)}
          </span>
        )
      },
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => {
        const n = Number(r.saldo_actual) || 0
        return <Badge color={n < 0 ? 'red' : 'green'}>{n < 0 ? 'Pendiente' : 'Al día'}</Badge>
      },
    },
    {
      title: 'Tope',
      key: 'tope',
      render: (_, r) => (
        <span className="text-sm text-slate-500">
          {r.deuda_maxima === null ? 'Sin tope' : formatGs(r.deuda_maxima)}
        </span>
      ),
    },
    {
      title: 'Últ. movimiento',
      key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha_actualizacion.slice(0, 10))}</span>,
    },
    {
      title: '',
      key: 'acc',
      width: 200,
      render: (_, r) => {
        const n = Number(r.saldo_actual) || 0
        return (
          <div className="flex gap-1.5">
            <Button size="sm" variant="primary" onClick={() => setPagoCuenta({
              hijo: r.hijo,
              hijo_nombre: r.hijo_nombre,
              monto_sugerido: n < 0 ? -n : 0,
              detalle: n < 0 ? `Deuda actual: ${formatGs(-n)}` : `Saldo actual: ${formatGs(n)}`,
            })}>
              <Banknote className="w-3.5 h-3.5" />
              Cargar saldo
            </Button>
            {puedeConfigurarTope && (
              <Button size="sm" variant="secondary" onClick={() => setTopeAlmuerzo(r)} title="Configurar tope de deuda">
                <Edit2 className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        )
      },
    },
  ]

  const colsSusc: Column<Suscripcion>[] = [
    {
      title: 'Estudiante',
      key: 'hijo',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.hijo_nombre}</span>,
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
          <Button size="sm" variant="secondary" onClick={() => setEditingSusc(r)}>
            <Edit2 className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="secondary" onClick={() => suspenderSusc(r.id_suscripcion)}>
            <PauseCircle className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="danger" onClick={() => cancelarSusc(r.id_suscripcion)}>
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
    { key: 'saldos',        label: 'Saldos',            icon: Wallet },
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
            { label: 'Alumnos con Deuda', value: String(stats.cuentasPendientes), color: 'text-orange-700', bg: 'bg-orange-50', icon: BarChart2, iconColor: 'text-orange-600' },
            { label: 'Consumido este Mes', value: formatGs(stats.facturadoMes), color: 'text-emerald-700', bg: 'bg-emerald-50', icon: CheckCircle, iconColor: 'text-emerald-600' },
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
              <Table columns={colsRegistros} dataSource={registros} rowKey="id_registro_consumo" loading={loadingRegistros}
                pageSize={15} page={pageRegistros} onPageChange={handlePageChange} total={totalRegistros} />
            </div>
          </div>
        </>
      )}

      {/* ── Cuentas tab ──────────────────────────────────────────── */}
      {tab === 'cuentas' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-800">Cuentas Mensuales de Almuerzos</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Consumo por alumno y mes, con el arrastre real de saldo mes a mes. Los meses de antes de tener billetera de almuerzo
                se agrupan en una fila aparte. El detalle de cobranza está en el tab Saldos.
              </p>
            </div>
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

      {/* ── Saldos tab (panel de cobranza) ───────────────────────── */}
      {tab === 'saldos' && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { label: 'Deuda Total', value: formatGs(resumenSaldos?.deuda_total ?? 0), color: 'text-red-700', bg: 'bg-red-50', icon: Wallet, iconColor: 'text-red-600' },
              { label: 'Alumnos con Deuda', value: String(resumenSaldos?.alumnos_con_deuda ?? 0), color: 'text-orange-700', bg: 'bg-orange-50', icon: Users, iconColor: 'text-orange-600' },
              { label: 'Saldo a Favor', value: formatGs(resumenSaldos?.saldo_a_favor_total ?? 0), color: 'text-emerald-700', bg: 'bg-emerald-50', icon: CheckCircle, iconColor: 'text-emerald-600' },
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
          {recargasPendientes.length > 0 && (
            <div className="bg-amber-50 rounded-2xl border border-amber-200 overflow-hidden">
              <div className="px-6 py-3 border-b border-amber-200">
                <h2 className="text-sm font-semibold text-amber-800">
                  Recargas pendientes de confirmación ({recargasPendientes.length})
                </h2>
                <p className="text-xs text-amber-700 mt-0.5">
                  Transferencias u otros medios registrados que todavía no acreditaron saldo al alumno.
                </p>
              </div>
              <ul className="divide-y divide-amber-100">
                {recargasPendientes.map(r => (
                  <li key={r.id_recarga_almuerzo} className="px-6 py-3 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-slate-800">{r.hijo_nombre}</p>
                      <p className="text-xs text-slate-500">
                        {r.metodo_pago} · {formatFecha(r.fecha_carga.slice(0, 10))}
                        {r.referencia ? ` · Ref. ${r.referencia}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="tabular-nums font-semibold text-slate-800">{formatGs(r.monto_cargado)}</span>
                      <Button size="sm" variant="primary" onClick={() => setConfirmarRecarga(r)}>
                        <CheckCircle className="w-3.5 h-3.5" />
                        Confirmar
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-800">Saldos de Almuerzo por Alumno</h2>
                <p className="text-xs text-slate-400 mt-0.5">
                  Cuenta corriente real: cada almuerzo descuenta, cada recarga suma. Negativo = deuda a cobrar.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={soloDeuda}
                    onChange={e => setSoloDeuda(e.target.checked)}
                    className="w-4 h-4 rounded accent-green-600"
                  />
                  Solo con deuda
                </label>
                <input
                  placeholder="Buscar alumno o tarjeta..."
                  value={searchSaldos}
                  onChange={e => setSearchSaldos(e.target.value)}
                  className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 w-56"
                />
              </div>
            </div>
            <div className="p-1">
              <Table
                columns={colsSaldos}
                dataSource={saldos}
                rowKey="id_saldo_almuerzo"
                loading={loadingSaldos}
                pageSize={15}
                page={pageSaldos}
                onPageChange={p => { setPageSaldos(p); loadSaldos(searchSaldos, soloDeuda, p) }}
                total={totalSaldos}
              />
            </div>
          </div>
        </>
      )}

      {/* ── Suscripciones tab ─────────────────────────────────────── */}
      {tab === 'suscripciones' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-800">Suscripciones de Estudiantes</h2>
          </div>
          <div className="p-1">
            <Table columns={colsSusc} dataSource={suscripciones} rowKey="id_suscripcion" loading={loadingSusc} pageSize={15} />
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
            <Table columns={colsMenu} dataSource={menu} rowKey="id_menu" loading={loadingMenu} pageSize={15} />
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
        onClose={() => setSuscModalOpen(false)}
        onSaved={loadSuscripciones}
      />
      <ModalPagoCuenta
        cuenta={pagoCuenta}
        onClose={() => setPagoCuenta(null)}
        onSaved={() => {
          if (tab === 'cuentas') loadCuentas()
          if (tab === 'saldos') loadSaldos(searchSaldos, soloDeuda, pageSaldos)
        }}
      />
      <ModalConfirmarRecarga
        recarga={confirmarRecarga}
        onClose={() => setConfirmarRecarga(null)}
        onSaved={() => loadSaldos(searchSaldos, soloDeuda, pageSaldos)}
      />
      <ModalTopeAlmuerzo
        saldo={topeAlmuerzo}
        onClose={() => setTopeAlmuerzo(null)}
        onSaved={() => loadSaldos(searchSaldos, soloDeuda, pageSaldos)}
      />
      <ModalEditSusc
        susc={editingSusc}
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
    </div>
  )
}
