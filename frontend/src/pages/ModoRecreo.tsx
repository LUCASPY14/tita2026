import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Zap, X, AlertTriangle, Loader2, Clock, Store } from 'lucide-react'
import api from '../services/api'
import tarjetasService from '../services/tarjetas'
import ventasService from '../services/ventas'
import cajasService from '../services/cajas'
import { useCatalogoStore } from '../store/catalogoStore'
import { useOfflineQueue } from '../hooks/useOfflineQueue'
import CajaBlockedScreen from './modorecreo/CajaBlockedScreen'
import PanelAlumno from './modorecreo/PanelAlumno'
import PanelProductos from './modorecreo/PanelProductos'
import PanelCarrito from './modorecreo/PanelCarrito'
import {
  sfx, gs, extractError, detectInputType,
  getSalesMap, addSales, getDailyStats, updateDailyStats,
  type Producto, type RestriccionHijo, type Tarjeta, type ClienteBasico,
  type ItemCarrito, type MedioPagoDB, type ModoPago, type Flash, type DailyStats,
} from './modorecreo/shared'

export default function ModoRecreo() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { getProductos, getCategorias } = useCatalogoStore()

  const { isOnline, pendingCount, syncing, syncNow, enqueue } = useOfflineQueue()
  useEffect(() => {
    const offlineToastId = 'offline-warning'
    if (!isOnline) {
      toast.error('Sin conexión — ventas se guardan offline', { id: offlineToastId, duration: Infinity })
    } else {
      toast.dismiss(offlineToastId)
      if (pendingCount > 0) toast.success(`Conexión restaurada — sincronizando ${pendingCount} venta(s)...`)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOnline])

  interface CierreCajaInfo { id: number; caja_nombre: string; monto_inicial: string; fecha_apertura: string }
  const [cierreCaja, setCierreCaja] = useState<CierreCajaInfo | null | false>(null)

  const [productos, setProductos] = useState<Producto[]>([])
  const [loadingProductos, setLoadingProductos] = useState(true)
  const [categorias, setCategorias] = useState<string[]>([])
  const [mediosPago, setMediosPago] = useState<MedioPagoDB[]>([])

  const [tarjetaInput, setTarjetaInput] = useState('')
  const [tarjeta, setTarjeta] = useState<Tarjeta | null>(null)
  const [buscandoTarjeta, setBuscandoTarjeta] = useState(false)
  const [preciosCliente, setPreciosCliente] = useState<Record<number, number>>({})

  const [clienteDirecto, setClienteDirecto] = useState<ClienteBasico | null>(null)
  const [clienteSearch, setClienteSearch] = useState('')
  const [clienteResultados, setClienteResultados] = useState<ClienteBasico[]>([])
  const [buscandoCliente, setBuscandoCliente] = useState(false)
  const clienteSearchTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const [catFiltro, setCatFiltro] = useState('')
  const [prodSearch, setProdSearch] = useState('')

  const [carrito, setCarrito] = useState<ItemCarrito[]>([])

  const [cobrando, setCobrando] = useState(false)
  const [flash, setFlash] = useState<Flash>('none')
  const [flashMsg, setFlashMsg] = useState('')

  const [addedProductId, setAddedProductId] = useState<number | null>(null)
  const addedTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const [clock, setClock] = useState(() =>
    new Date().toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' })
  )

  const [salesMap, setSalesMap] = useState<Record<number, number>>(getSalesMap)
  const [dailyStats, setDailyStats] = useState<DailyStats>(getDailyStats)
  const ventaStartTime = useRef<number>(0)

  const [modoPago, setModoPago] = useState<ModoPago>('PREPAGO')
  const [medioPagoSelId, setMedioPagoSelId] = useState<number | null>(null)
  const [montoEfectivo, setMontoEfectivo] = useState('')
  const [referencia, setReferencia] = useState('')
  const [nroFacturaVenta, setNroFacturaVenta] = useState('')

  const scannerRef = useRef<HTMLInputElement>(null)
  const prodSearchRef = useRef<HTMLInputElement>(null)
  const flashTimer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const cobrandoRef = useRef(false)
  const productosFiltradosRef = useRef<Producto[]>([])
  const handleAgregarRef = useRef<(p: Producto) => void>(() => {})
  const handleCobrarRef = useRef<() => void>(() => {})
  const handleCancelarRef = useRef<() => void>(() => {})
  const lastScannedProduct = useRef<{ id: number; time: number } | null>(null)

  useEffect(() => {
    const t = setInterval(() =>
      setClock(new Date().toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' }))
    , 10000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    Promise.all([
      getProductos(),
      getCategorias(),
      api.get('/core/medios-pago/', { params: { activo: true } }),
    ])
      .then(([prods, cats, mpRes]) => {
        setProductos(prods as Producto[])
        setCategorias(cats.map((c: { nombre: string }) => c.nombre))
        const mp: MedioPagoDB[] = (mpRes.data.results ?? mpRes.data) as MedioPagoDB[]
        setMediosPago(mp.filter(m => m.activo))
      })
      .catch(() => toast.error('Error al cargar datos'))
      .finally(() => setLoadingProductos(false))

    cajasService.getMiCaja<CierreCajaInfo>()
      .then(res => setCierreCaja(res.data ?? false))
      .catch(() => setCierreCaja(false))
  }, [getProductos, getCategorias])

  // Búsqueda de cliente con debounce: limpiar resultados sincrónicamente ante
  // los guards (sin cliente/tarjeta activos, o búsqueda vacía) es intencional.
  useEffect(() => {
    if (tarjeta || clienteDirecto || (modoPago !== 'MEDIO' && modoPago !== 'CREDITO')) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setClienteResultados([]); return
    }
    clearTimeout(clienteSearchTimer.current)
    if (!clienteSearch.trim()) { setClienteResultados([]); return }
    clienteSearchTimer.current = setTimeout(() => {
      setBuscandoCliente(true)
      api.get<{ results?: ClienteBasico[] }>('/clientes/clientes/', {
        params: { search: clienteSearch, activo: true, page_size: 6 },
      })
        .then(({ data }) => setClienteResultados(data.results ?? []))
        .catch(() => setClienteResultados([]))
        .finally(() => setBuscandoCliente(false))
    }, 350)
    return () => clearTimeout(clienteSearchTimer.current)
  }, [clienteSearch, tarjeta, clienteDirecto, modoPago])

  useEffect(() => {
    const t = setTimeout(() => scannerRef.current?.focus(), 50)
    return () => clearTimeout(t)
  }, [])
  useEffect(() => {
    const handler = () => {
      if (document.activeElement?.tagName === 'BODY') scannerRef.current?.focus()
    }
    window.addEventListener('focus', handler)
    return () => window.removeEventListener('focus', handler)
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName.toLowerCase()
      const inInput = tag === 'input' || tag === 'textarea' || tag === 'select'

      if (e.key === 'F2') { e.preventDefault(); prodSearchRef.current?.focus(); return }
      if (e.key === 'F3') { e.preventDefault(); scannerRef.current?.focus(); return }
      if (e.key === 'F9') { e.preventDefault(); handleCobrarRef.current(); return }
      if (e.key === 'Escape') { e.preventDefault(); handleCancelarRef.current(); return }
      if (e.ctrlKey && e.key === 'Backspace') {
        e.preventDefault()
        setCarrito(prev => prev.slice(0, -1))
        return
      }
      if (!inInput && e.key === '+') {
        e.preventDefault()
        const last = carrito[carrito.length - 1]
        if (last) handleAgregarRef.current(last.producto)
        return
      }
      if (!inInput && e.key === '-') {
        e.preventDefault()
        const last = carrito[carrito.length - 1]
        if (last) {
          setCarrito(prev => {
            if (last.cantidad <= 1) return prev.slice(0, -1)
            return prev.map(i => i.producto.id === last.producto.id ? { ...i, cantidad: i.cantidad - 1 } : i)
          })
        }
        return
      }
      if (!inInput && /^[1-9]$/.test(e.key)) {
        const p = productosFiltradosRef.current[parseInt(e.key) - 1]
        if (p) handleAgregarRef.current(p)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [carrito])

  const productosFiltrados = useMemo(() => {
    let list = productos
    if (catFiltro) list = list.filter(p => p.categoria_nombre === catFiltro)
    if (prodSearch) list = list.filter(p =>
      p.descripcion.toLowerCase().includes(prodSearch.toLowerCase()) ||
      (p.codigo_barra?.includes(prodSearch) ?? false))
    const sorted = [...list].sort(
      (a, b) => ((salesMap[b.id] || 0) - (salesMap[a.id] || 0)) ||
                a.descripcion.localeCompare(b.descripcion)
    )
    // eslint-disable-next-line react-hooks/refs
    productosFiltradosRef.current = sorted
    return sorted
  }, [productos, catFiltro, prodSearch, salesMap])

  const favoritos = useMemo(() =>
    [...productos].sort((a, b) => (salesMap[b.id] || 0) - (salesMap[a.id] || 0)).slice(0, 5)
  , [productos, salesMap])

  const getPrecio = useCallback((p: Producto) =>
    preciosCliente[p.id] ?? (Number(p.precio_actual) || 0)
  , [preciosCliente])

  const total = useMemo(() =>
    carrito.reduce((s, i) => s + getPrecio(i.producto) * i.cantidad, 0)
  , [carrito, getPrecio])

  const saldoDisponible = tarjeta
    ? (Number(tarjeta.saldo_disponible) || Number(tarjeta.saldo_actual) || 0)
    : null
  const saldoTrasCompra = saldoDisponible !== null ? saldoDisponible - total : null

  const vuelto = useMemo(() => {
    const recibido = parseFloat(montoEfectivo.replace(/\./g, '').replace(',', '.')) || 0
    return recibido - total
  }, [montoEfectivo, total])

  const isRestricto = useCallback((producto: Producto): RestriccionHijo | null => {
    if (!tarjeta?.hijo_restricciones?.length) return null
    return tarjeta.hijo_restricciones.find(r => {
      const desc = (r.descripcion || '').toLowerCase()
      if (!desc) return false
      if (r.tipo === 'CATEGORIA') return producto.categoria_nombre.toLowerCase().includes(desc)
      if (r.tipo === 'PRODUTO')  return producto.descripcion.toLowerCase().includes(desc)
      return producto.descripcion.toLowerCase().includes(desc) ||
             producto.categoria_nombre.toLowerCase().includes(desc)
    }) ?? null
  }, [tarjeta])

  const clearCliente = useCallback(() => {
    setClienteDirecto(null); setClienteSearch(''); setClienteResultados([])
  }, [])

  const buscarTarjeta = useCallback(async (nro: string) => {
    if (!nro || buscandoTarjeta) return
    setBuscandoTarjeta(true)
    try {
      const { data } = await tarjetasService.buscar<Tarjeta>(nro)
      const found = (data.results ?? []).find((t) => t.nro_tarjeta === nro)
      if (!found) { sfx.error(); toast.error('Tarjeta no encontrada'); return }
      if (found.estado !== 'ACTIVA') { sfx.error(); toast.error(`Tarjeta ${found.estado.toLowerCase()}`); return }
      sfx.card()
      setTarjeta(found)
      setCarrito([])
      setClienteDirecto(null); setClienteSearch(''); setClienteResultados([])
      setPreciosCliente({})
      if (!found.lista_es_default && found.lista_precio_id) {
        try {
          const { data } = await api.get('/productos/productos/', {
            params: { lista_precio_id: found.lista_precio_id, activo: true },
          })
          const prods: Producto[] = data.results ?? data
          const mapa: Record<number, number> = {}
          prods.forEach(p => { mapa[p.id] = Number(p.precio_actual) || 0 })
          setPreciosCliente(mapa)
        } catch { /* precio por defecto como fallback */ }
      }
      const criticas = (found.hijo_restricciones ?? []).filter((r: RestriccionHijo) => r.severidad === 'CRITICA')
      if (criticas.length > 0) {
        sfx.restrict(); toast.error(`⚠️ ${criticas.length} restricción CRÍTICA`, { duration: 4000 })
      }
      if (Number(found.saldo_disponible || found.saldo_actual) < 5000) {
        sfx.lowBal(); toast(`Saldo bajo: ${gs(found.saldo_disponible || found.saldo_actual)}`, { icon: '⚠️' })
      }
      ventaStartTime.current = performance.now()
    } catch {
      sfx.error(); toast.error('Error al buscar tarjeta')
    } finally {
      setBuscandoTarjeta(false)
      setTarjetaInput('')
      setTimeout(() => scannerRef.current?.focus(), 50)
    }
  }, [buscandoTarjeta])

  const handleAgregar = useCallback((producto: Producto) => {
    const restriccion = isRestricto(producto)
    const bloqueado = restriccion && (restriccion.severidad === 'CRITICA' || restriccion.severidad === 'ALTA')
    if (bloqueado) {
      sfx.restrict()
      clearTimeout(flashTimer.current)
      setFlash('restrict')
      setFlashMsg(`🚫 RESTRINGIDO — ${producto.descripcion}`)
      flashTimer.current = setTimeout(() => setFlash('none'), 1800)
      return
    }
    if (modoPago === 'PREPAGO' && saldoDisponible !== null && !tarjeta?.permite_saldo_negativo) {
      const nuevoTotal = total + getPrecio(producto)
      if (nuevoTotal > saldoDisponible) { sfx.error(); toast.error('Saldo insuficiente'); return }
    }
    sfx.add()
    setCarrito(prev => {
      const ex = prev.find(i => i.producto.id === producto.id)
      if (ex) return prev.map(i => i.producto.id === producto.id ? { ...i, cantidad: i.cantidad + 1 } : i)
      return [...prev, { producto, cantidad: 1 }]
    })
    setAddedProductId(producto.id)
    clearTimeout(addedTimer.current)
    addedTimer.current = setTimeout(() => setAddedProductId(null), 200)
  }, [isRestricto, saldoDisponible, tarjeta, total, modoPago, getPrecio])

  const handleQuitar = useCallback((id: number) => {
    setCarrito(prev => {
      const item = prev.find(i => i.producto.id === id)
      if (!item) return prev
      return item.cantidad <= 1
        ? prev.filter(i => i.producto.id !== id)
        : prev.map(i => i.producto.id === id ? { ...i, cantidad: i.cantidad - 1 } : i)
    })
  }, [])

  const handleSetCantidad = useCallback((id: number, cantidad: number) => {
    const item = carrito.find(i => i.producto.id === id)
    if (!item) return
    if (modoPago === 'PREPAGO' && saldoDisponible !== null && !tarjeta?.permite_saldo_negativo) {
      const nuevoTotal = total - getPrecio(item.producto) * item.cantidad + getPrecio(item.producto) * cantidad
      if (nuevoTotal > saldoDisponible) { sfx.error(); toast.error('Saldo insuficiente'); return }
    }
    setCarrito(prev => prev.map(i => i.producto.id === id ? { ...i, cantidad } : i))
  }, [carrito, modoPago, saldoDisponible, tarjeta, total, getPrecio])

  const ejecutarCobro = useCallback(async () => {
    if (cobrandoRef.current || carrito.length === 0) return
    if (!tarjeta && !clienteDirecto) return
    cobrandoRef.current = true
    setCobrando(true)
    const inicio = ventaStartTime.current || performance.now()
    try {
      const clienteId = tarjeta ? tarjeta.cliente_id : clienteDirecto!.id
      const nombreDisplay = tarjeta
        ? (tarjeta.hijo_nombre ?? tarjeta.cliente_nombre)
        : clienteDirecto!.nombre_completo
      const payload: Record<string, unknown> = {
        cliente: clienteId,
        tipo: modoPago === 'CREDITO' ? 'CREDITO' : 'CONTADO',
        items: carrito.map(i => ({
          producto: i.producto.id,
          cantidad: i.cantidad,
          precio_unitario: getPrecio(i.producto),
          iva_10: 0, iva_5: 0, monto_exenta: 0,
        })),
      }
      if (modoPago === 'PREPAGO' && tarjeta) {
        payload.tarjeta = tarjeta.nro_tarjeta
        payload.medio_pago = null
      } else if (modoPago === 'CREDITO') {
        payload.tarjeta = null; payload.medio_pago = null
      } else {
        payload.tarjeta = null
        payload.medio_pago = medioPagoSelId
        if (referencia.trim()) payload.referencia = referencia.trim()
        payload.genera_factura_legal = true
        if (nroFacturaVenta.trim()) payload.nro_factura = nroFacturaVenta.trim()
      }
      if (!navigator.onLine) {
        await enqueue({
          url:     '/api/v1/ventas/ventas/',
          method:  'POST',
          body:    JSON.stringify(payload),
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${localStorage.getItem('access_token') ?? ''}`,
          },
        })
      } else {
        await ventasService.crear(payload as unknown as Parameters<typeof ventasService.crear>[0], 6000)
      }
      sfx.ok()
      addSales(carrito.map(i => i.producto.id))
      setSalesMap(getSalesMap())
      const tiempoMs = performance.now() - inicio
      updateDailyStats(tiempoMs)
      setDailyStats(getDailyStats())
      clearTimeout(flashTimer.current)
      setFlash('ok')
      setFlashMsg(
        navigator.onLine
          ? `✅  ${nombreDisplay}  —  ${gs(total)}`
          : `📶  ${nombreDisplay}  —  guardado offline`,
      )
      flashTimer.current = setTimeout(() => {
        setFlash('none'); setCarrito([]); setTarjeta(null); setPreciosCliente({})
        setClienteDirecto(null); setClienteSearch(''); setClienteResultados([])
        setMontoEfectivo(''); setReferencia(''); setNroFacturaVenta('')
        ventaStartTime.current = 0
        setTimeout(() => scannerRef.current?.focus(), 60)
      }, 2500)
    } catch (err) {
      sfx.error(); toast.error(extractError(err))
    } finally {
      cobrandoRef.current = false; setCobrando(false)
    }
  }, [carrito, tarjeta, clienteDirecto, total, modoPago, medioPagoSelId, referencia, nroFacturaVenta, enqueue, getPrecio])

  const handleCobrar = useCallback(async () => {
    if (cobrandoRef.current || carrito.length === 0) return
    if (!tarjeta && !clienteDirecto) {
      toast.error('Escanear tarjeta o seleccionar cliente'); scannerRef.current?.focus(); return
    }
    if (modoPago === 'MEDIO' && !medioPagoSelId) {
      toast.error('Seleccione un medio de pago'); return
    }
    if (modoPago === 'PREPAGO' && tarjeta && !tarjeta.permite_saldo_negativo) {
      const saldoAct = Number(tarjeta.saldo_actual) || 0
      if (total > saldoAct) {
        toast.error('Saldo insuficiente en la tarjeta'); return
      }
    }
    await ejecutarCobro()
  }, [carrito, tarjeta, clienteDirecto, total, modoPago, medioPagoSelId, ejecutarCobro])

  const handleCancelar = useCallback(() => {
    clearTimeout(flashTimer.current)
    setFlash('none'); setCarrito([]); setTarjeta(null); setPreciosCliente({})
    clearCliente()
    setTarjetaInput(''); setProdSearch('')
    setMontoEfectivo(''); setReferencia(''); setNroFacturaVenta('')
    ventaStartTime.current = 0
    setTimeout(() => scannerRef.current?.focus(), 60)
  }, [clearCliente])

  useEffect(() => {
    handleAgregarRef.current  = handleAgregar
    handleCobrarRef.current   = handleCobrar
    handleCancelarRef.current = handleCancelar
  })

  const processScan = useCallback(async (value: string) => {
    if (!value.trim()) return
    const trimmed = value.trim()
    setTarjetaInput('')
    if (detectInputType(trimmed) === 'card') {
      if (tarjeta) setCarrito([])
      await buscarTarjeta(trimmed)
    } else {
      const prod = productos.find(p => p.codigo_barra === trimmed)
      if (prod) {
        if (!tarjeta) {
          sfx.error(); toast.error('Escanee una tarjeta primero')
          setTimeout(() => scannerRef.current?.focus(), 100)
          return
        }
        const now = Date.now()
        if (lastScannedProduct.current?.id === prod.id && (now - lastScannedProduct.current.time) < 1000) { /* dup */ }
        lastScannedProduct.current = { id: prod.id, time: now }
        handleAgregarRef.current(prod)
        setTimeout(() => scannerRef.current?.focus(), 30)
      } else {
        if (tarjeta) setCarrito([])
        await buscarTarjeta(trimmed)
      }
    }
  }, [tarjeta, productos, buscarTarjeta])

  // ─── Derived values ───────────────────────────────────────────────────────────
  const flashCfg = {
    ok:       { overlay: 'bg-green-500/20', card: 'bg-white border-green-500 shadow-green-200' },
    error:    { overlay: 'bg-red-500/20',   card: 'bg-white border-red-500 shadow-red-200' },
    restrict: { overlay: 'bg-red-600/25',   card: 'bg-white border-red-600 shadow-red-200' },
    none:     { overlay: '', card: '' },
  }[flash]

  const avgTime = dailyStats.count > 0 ? (dailyStats.totalTime / dailyStats.count / 1000).toFixed(1) : '—'
  const medioPagoSeleccionado = mediosPago.find(m => m.id === medioPagoSelId) ?? null
  const tipoVenta: 'CONTADO' | 'CREDITO' = modoPago === 'CREDITO' ? 'CREDITO' : 'CONTADO'
  const clienteModalidad: 'INMEDIATA' | 'MENSUAL' =
    tarjeta?.cliente_modalidad_facturacion ?? clienteDirecto?.modalidad_facturacion ?? 'INMEDIATA'
  const referenciaRequerida = modoPago === 'MEDIO' && (medioPagoSeleccionado?.requiere_validacion ?? false)
  const tieneTitular = tarjeta !== null || ((modoPago === 'MEDIO' || modoPago === 'CREDITO') && clienteDirecto !== null)
  const canCobrar = carrito.length > 0 && !cobrando && tieneTitular &&
    (modoPago === 'PREPAGO' || modoPago === 'CREDITO' || (modoPago === 'MEDIO' && medioPagoSelId !== null)) &&
    (!referenciaRequerida || referencia.trim().length > 0)

  if (cierreCaja === false) return <CajaBlockedScreen />
  if (cierreCaja === null) return (
    <div className="fixed inset-0 bg-slate-100 flex items-center justify-center" style={{ zIndex: 100 }}>
      <Loader2 size={48} className="animate-spin text-slate-400" />
    </div>
  )

  return (
    <div className="fixed inset-0 bg-slate-100 text-slate-900 flex flex-col overflow-hidden" style={{ zIndex: 100 }} translate="no">

      {flash !== 'none' && (
        <div className={`absolute inset-0 flex items-center justify-center pointer-events-none ${flashCfg.overlay}`} style={{ zIndex: 200 }}>
          <div className={`border-4 rounded-3xl px-16 py-10 text-center shadow-2xl ${flashCfg.card}`}>
            <p className="text-5xl font-black text-slate-900">{flashMsg}</p>
            {flash === 'ok' && saldoTrasCompra !== null && modoPago === 'PREPAGO' && (
              <p className="text-slate-500 text-2xl mt-3 tabular-nums">Saldo restante: {gs(saldoTrasCompra)}</p>
            )}
          </div>
        </div>
      )}

      {!isOnline && (
        <div className="flex items-center justify-center gap-2 bg-red-600 text-white text-sm font-bold py-1.5 px-4 shrink-0">
          <AlertTriangle size={16} />
          SIN CONEXIÓN — los cobros están deshabilitados hasta restaurar la red
        </div>
      )}

      <header className="flex items-center justify-between px-3 md:px-5 py-2 bg-white border-b-2 border-slate-200 shadow-sm h-14 md:h-16 shrink-0">
        <div className="flex items-center gap-2 md:gap-4">
          <img src="/logo_tita.png" alt="" className="h-8 md:h-9 w-auto rounded" />
          <div className="flex items-center gap-2 bg-yellow-100 border border-yellow-300 rounded-full px-3 md:px-4 py-1.5">
            <Zap size={16} className="text-yellow-500" />
            <span className="text-yellow-700 text-xs md:text-sm font-black uppercase tracking-widest">{t('pos.title')}</span>
          </div>
          <div className="hidden md:flex items-center gap-3 ml-1 text-sm text-slate-500">
            <span className="flex items-center gap-1.5"><Clock size={15} className="text-slate-400" />{clock}</span>
            <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
              <Store size={15} className="text-emerald-500" />
              {cierreCaja.caja_nombre}
            </span>
            <span className="hidden lg:inline">{t('pos.todaySales')}: <strong className="text-slate-800">{dailyStats.count}</strong></span>
            <span className="hidden lg:inline">Promedio: <strong className="text-slate-800">{dailyStats.count > 0 ? `${avgTime}s` : '—'}</strong></span>
          </div>
        </div>
        <div className="flex items-center gap-2 md:gap-4">
          {pendingCount > 0 && (
            <button
              onClick={syncNow}
              disabled={syncing || !isOnline}
              title={isOnline ? 'Sincronizar ventas offline' : 'Sin conexión — se sincronizarán al reconectar'}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-100 border border-amber-300 text-amber-800 rounded-lg text-xs font-bold transition-colors cursor-pointer hover:bg-amber-200 disabled:opacity-60"
            >
              {syncing ? <Loader2 size={13} className="animate-spin" /> : <AlertTriangle size={13} />}
              {pendingCount} venta{pendingCount !== 1 ? 's' : ''} offline
            </button>
          )}
          <div className="hidden xl:flex items-center gap-3 text-xs text-slate-500">
            {[['F2','Buscar'],['F3','Escanear'],['F9','Cobrar'],['Esc','Cancelar'],['±','Cant']].map(([k, l]) => (
              <span key={k}>
                <kbd className={`rounded px-1.5 py-0.5 font-mono mr-1 text-[11px] ${k === 'F9' ? 'bg-green-100 text-green-700 border border-green-300' : 'bg-slate-100 text-slate-600 border border-slate-200'}`}>{k}</kbd>
                {l}
              </span>
            ))}
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-red-50 text-slate-600 hover:text-red-600 rounded-lg text-sm font-medium transition-colors cursor-pointer border border-slate-200"
          >
            <X size={14} />Salir
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <PanelAlumno
          tarjeta={tarjeta}
          saldoDisponible={saldoDisponible}
          saldoTrasCompra={saldoTrasCompra}
          hasItems={carrito.length > 0}
          modoPago={modoPago}
          tarjetaInput={tarjetaInput}
          buscandoTarjeta={buscandoTarjeta}
          clienteDirecto={clienteDirecto}
          clienteSearch={clienteSearch}
          clienteResultados={clienteResultados}
          buscandoCliente={buscandoCliente}
          scannerRef={scannerRef}
          onChangeTarjetaInput={setTarjetaInput}
          onScanEnter={() => processScan(tarjetaInput)}
          onChangeClienteSearch={setClienteSearch}
          onSelectCliente={(c) => { setClienteDirecto(c); setClienteSearch(c.nombre_completo); setClienteResultados([]) }}
          onClearCliente={clearCliente}
          onVentaStartTime={() => { ventaStartTime.current = performance.now() }}
        />
        <PanelProductos
          loadingProductos={loadingProductos}
          categorias={categorias}
          catFiltro={catFiltro}
          prodSearch={prodSearch}
          productosFiltrados={productosFiltrados}
          favoritos={favoritos}
          addedProductId={addedProductId}
          prodSearchRef={prodSearchRef}
          getPrecio={getPrecio}
          isRestricto={isRestricto}
          onCatFiltro={setCatFiltro}
          onProdSearch={setProdSearch}
          onAgregar={handleAgregar}
          onScannerFocus={() => scannerRef.current?.focus()}
        />
        <PanelCarrito
          carrito={carrito}
          total={total}
          saldoDisponible={saldoDisponible}
          saldoTrasCompra={saldoTrasCompra}
          tarjeta={tarjeta}
          clienteModalidad={clienteModalidad}
          modoPago={modoPago}
          tipoVenta={tipoVenta}
          medioPagoSelId={medioPagoSelId}
          mediosPago={mediosPago}
          medioPagoSeleccionado={medioPagoSeleccionado}
          montoEfectivo={montoEfectivo}
          vuelto={vuelto}
          referencia={referencia}
          nroFacturaVenta={nroFacturaVenta}
          canCobrar={canCobrar}
          cobrando={cobrando}
          dailyStats={dailyStats}
          avgTime={avgTime}
          getPrecio={getPrecio}
          onSetCarrito={setCarrito}
          onAgregar={handleAgregar}
          onQuitar={handleQuitar}
          onSetCantidad={handleSetCantidad}
          onModoPago={setModoPago}
          onMedioPagoId={setMedioPagoSelId}
          onMontoEfectivo={setMontoEfectivo}
          onReferencia={setReferencia}
          onNroFacturaVenta={setNroFacturaVenta}
          onClearCliente={clearCliente}
          onCobrar={handleCobrar}
          onCancelar={handleCancelar}
        />
      </div>
    </div>
  )
}
