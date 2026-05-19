import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  Settings, Plus, Edit2, Tag, ListOrdered, CreditCard, Users,
  GraduationCap, Building2, History, Shield, Eye, EyeOff,
  CheckCircle2, XCircle, Copy,
} from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import api from '../services/api'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import Modal from '../components/ui/Modal'
import Combobox from '../components/ui/Combobox'

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

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Categoria {
  id: number
  nombre: string
  descripcion: string
}

interface TipoCliente {
  id: number
  nombre: string
  descripcion: string
  descuento_porcentaje: number | string
}

interface ListaPrecio {
  id: number
  nombre: string
  descripcion: string
  es_precio_base: boolean
}

interface MedioPago {
  id: number
  nombre: string
  tipo: string
  activo: boolean
}

interface Grado {
  id: number
  nombre: string
  nivel: number
  orden: number
  es_ultimo: boolean
  activo: boolean
}

interface DatosEmpresa {
  id: number
  ruc: string
  razon_social: string
  direccion: string
  ciudad: string
  pais: string
  telefono: string
  email: string
  activo: boolean
}

interface HistoricoPrecioItem {
  id: number
  producto: number
  producto_nombre: string
  precio_anterior: string
  precio_nuevo: string
  variacion_porcentual: string
  fecha_cambio: string
}

interface Producto {
  id: number
  descripcion: string
}

interface Estado2FA {
  habilitado: boolean
  fecha_activacion: string | null
  tiene_backup_codes: boolean
}

// ─── Types ────────────────────────────────────────────────────────────────────

type TabKey = 'categorias' | 'tipos_cliente' | 'listas_precio' | 'medios_pago'
            | 'grados' | 'datos_empresa' | 'historial_precios' | 'seguridad'

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Configuracion() {
  const [tab, setTab] = useState<TabKey>('categorias')

  // ── Categorías ────────────────────────────────────────────────────
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [loadingCat, setLoadingCat] = useState(false)
  const [catModal, setCatModal] = useState(false)
  const [editingCat, setEditingCat] = useState<Categoria | null>(null)
  const [catForm, setCatForm] = useState({ nombre: '', descripcion: '' })
  const [savingCat, setSavingCat] = useState(false)

  // ── Tipos de cliente ──────────────────────────────────────────────
  const [tiposCliente, setTiposCliente] = useState<TipoCliente[]>([])
  const [loadingTc, setLoadingTc] = useState(false)
  const [tcModal, setTcModal] = useState(false)
  const [editingTc, setEditingTc] = useState<TipoCliente | null>(null)
  const [tcForm, setTcForm] = useState({ nombre: '', descripcion: '', descuento_porcentaje: '' })
  const [savingTc, setSavingTc] = useState(false)

  // ── Listas de precio ──────────────────────────────────────────────
  const [listasPrecio, setListasPrecio] = useState<ListaPrecio[]>([])
  const [loadingLp, setLoadingLp] = useState(false)
  const [lpModal, setLpModal] = useState(false)
  const [editingLp, setEditingLp] = useState<ListaPrecio | null>(null)
  const [lpForm, setLpForm] = useState({ nombre: '', descripcion: '', es_precio_base: false })
  const [savingLp, setSavingLp] = useState(false)

  // ── Medios de pago ────────────────────────────────────────────────
  const [mediosPago, setMediosPago] = useState<MedioPago[]>([])
  const [loadingMp, setLoadingMp] = useState(false)
  const [mpModal, setMpModal] = useState(false)
  const [editingMp, setEditingMp] = useState<MedioPago | null>(null)
  const [mpForm, setMpForm] = useState({ nombre: '', tipo: 'EFECTIVO', activo: true })
  const [savingMp, setSavingMp] = useState(false)

  // ── Grados ────────────────────────────────────────────────────────
  const [grados, setGrados] = useState<Grado[]>([])
  const [loadingGr, setLoadingGr] = useState(false)
  const [grModal, setGrModal] = useState(false)
  const [editingGr, setEditingGr] = useState<Grado | null>(null)
  const [grForm, setGrForm] = useState({ nombre: '', nivel: 1, orden: 1, es_ultimo: false, activo: true })
  const [savingGr, setSavingGr] = useState(false)

  // ── Datos Empresa ─────────────────────────────────────────────────
  const [empresa, setEmpresa] = useState<DatosEmpresa | null>(null)
  const [loadingEmp, setLoadingEmp] = useState(false)
  const [empForm, setEmpForm] = useState({ ruc: '', razon_social: '', direccion: '', ciudad: '', pais: 'Paraguay', telefono: '', email: '', activo: true })
  const [savingEmp, setSavingEmp] = useState(false)

  // ── Historial Precios ─────────────────────────────────────────────
  const [historico, setHistorico] = useState<HistoricoPrecioItem[]>([])
  const [loadingHist, setLoadingHist] = useState(false)
  const [histTotal, setHistTotal] = useState(0)
  const [histPage, setHistPage] = useState(1)
  const [productosLookup, setProductosLookup] = useState<Producto[]>([])
  const [histProductoId, setHistProductoId] = useState<number | undefined>()
  const histTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  // ── Seguridad / 2FA ───────────────────────────────────────────────
  const [estado2fa, setEstado2fa] = useState<Estado2FA | null>(null)
  const [loading2fa, setLoading2fa] = useState(false)
  const [twoFAStep, setTwoFAStep] = useState<'idle' | 'setup' | 'verify' | 'disable'>('idle')
  const [otpUri, setOtpUri] = useState('')
  const [otpSecret, setOtpSecret] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [otpCode, setOtpCode] = useState('')
  const [showSecret, setShowSecret] = useState(false)

  // ── Load categorías ───────────────────────────────────────────────
  const loadCategorias = useCallback(async () => {
    setLoadingCat(true)
    try {
      const { data } = await api.get('/productos/categorias/', { params: { page_size: 100 } })
      setCategorias(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar categorías') }
    finally { setLoadingCat(false) }
  }, [])

  useEffect(() => { if (tab === 'categorias') loadCategorias() }, [tab, loadCategorias])

  // ── Load tipos cliente ────────────────────────────────────────────
  const loadTiposCliente = useCallback(async () => {
    setLoadingTc(true)
    try {
      const { data } = await api.get('/clientes/tipos-cliente/', { params: { page_size: 100 } })
      setTiposCliente(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar tipos de cliente') }
    finally { setLoadingTc(false) }
  }, [])

  useEffect(() => { if (tab === 'tipos_cliente') loadTiposCliente() }, [tab, loadTiposCliente])

  // ── Load listas precio ────────────────────────────────────────────
  const loadListasPrecio = useCallback(async () => {
    setLoadingLp(true)
    try {
      const { data } = await api.get('/productos/listas-precio/', { params: { page_size: 100 } })
      setListasPrecio(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar listas de precio') }
    finally { setLoadingLp(false) }
  }, [])

  useEffect(() => { if (tab === 'listas_precio') loadListasPrecio() }, [tab, loadListasPrecio])

  // ── Load medios pago ──────────────────────────────────────────────
  const loadMediosPago = useCallback(async () => {
    setLoadingMp(true)
    try {
      const { data } = await api.get('/ventas/medios-pago/', { params: { page_size: 100 } })
      setMediosPago(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar medios de pago') }
    finally { setLoadingMp(false) }
  }, [])

  useEffect(() => { if (tab === 'medios_pago') loadMediosPago() }, [tab, loadMediosPago])

  // ── Load grados ───────────────────────────────────────────────────
  const loadGrados = useCallback(async () => {
    setLoadingGr(true)
    try {
      const { data } = await api.get('/clientes/grados/', { params: { page_size: 100 } })
      setGrados(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar grados') }
    finally { setLoadingGr(false) }
  }, [])

  useEffect(() => { if (tab === 'grados') loadGrados() }, [tab, loadGrados])

  // ── Load empresa ──────────────────────────────────────────────────
  const loadEmpresa = useCallback(async () => {
    setLoadingEmp(true)
    try {
      const { data } = await api.get('/contabilidad/datos-empresa/', { params: { page_size: 1 } })
      const emp = (data.results ?? data ?? [])[0] ?? null
      setEmpresa(emp)
      if (emp) setEmpForm({ ruc: emp.ruc, razon_social: emp.razon_social, direccion: emp.direccion ?? '', ciudad: emp.ciudad ?? '', pais: emp.pais ?? 'Paraguay', telefono: emp.telefono ?? '', email: emp.email ?? '', activo: emp.activo })
    } catch { toast.error('Error al cargar datos de empresa') }
    finally { setLoadingEmp(false) }
  }, [])

  useEffect(() => { if (tab === 'datos_empresa') loadEmpresa() }, [tab, loadEmpresa])

  // ── Load historial precios ────────────────────────────────────────
  const loadHistorico = useCallback(async (productoId: number | undefined, p: number) => {
    setLoadingHist(true)
    try {
      const params: Record<string, unknown> = { page: p, page_size: 15, ordering: '-fecha_cambio' }
      if (productoId) params.producto = productoId
      const { data } = await api.get('/productos/historico-precios/', { params })
      setHistorico(data.results ?? [])
      setHistTotal(data.count ?? 0)
    } catch { toast.error('Error al cargar historial') }
    finally { setLoadingHist(false) }
  }, [])

  useEffect(() => {
    if (tab !== 'historial_precios') return
    clearTimeout(histTimer.current)
    histTimer.current = setTimeout(() => { setHistPage(1); loadHistorico(histProductoId, 1) }, 300)
    return () => clearTimeout(histTimer.current)
  }, [tab, histProductoId, loadHistorico])

  useEffect(() => {
    if (tab !== 'historial_precios') return
    loadHistorico(histProductoId, histPage)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [histPage])

  useEffect(() => {
    if (tab !== 'historial_precios') return
    api.get('/productos/productos/', { params: { page_size: 200 } })
      .then(({ data }) => setProductosLookup(data.results ?? []))
      .catch(() => {})
  }, [tab])

  // ── Load 2FA status ───────────────────────────────────────────────
  const load2FA = useCallback(async () => {
    setLoading2fa(true)
    try {
      const { data } = await api.get('/usuarios/2fa/estado/')
      setEstado2fa(data)
    } catch { toast.error('Error al cargar estado 2FA') }
    finally { setLoading2fa(false) }
  }, [])

  useEffect(() => { if (tab === 'seguridad') { load2FA(); setTwoFAStep('idle') } }, [tab, load2FA])

  // ── Categorías CRUD ───────────────────────────────────────────────
  const openCat = useCallback((c?: Categoria) => {
    setEditingCat(c ?? null)
    setCatForm(c ? { nombre: c.nombre, descripcion: c.descripcion } : { nombre: '', descripcion: '' })
    setCatModal(true)
  }, [])

  const saveCat = useCallback(async () => {
    if (!catForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingCat(true)
    try {
      if (editingCat) {
        await api.put(`/productos/categorias/${editingCat.id}/`, catForm)
        toast.success('Categoría actualizada')
      } else {
        await api.post('/productos/categorias/', catForm)
        toast.success('Categoría creada')
      }
      setCatModal(false)
      loadCategorias()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingCat(false) }
  }, [catForm, editingCat, loadCategorias])

  // ── Tipos cliente CRUD ────────────────────────────────────────────
  const openTc = useCallback((t?: TipoCliente) => {
    setEditingTc(t ?? null)
    setTcForm(t ? { nombre: t.nombre, descripcion: t.descripcion, descuento_porcentaje: String(Number(t.descuento_porcentaje) || 0) } : { nombre: '', descripcion: '', descuento_porcentaje: '0' })
    setTcModal(true)
  }, [])

  const saveTc = useCallback(async () => {
    if (!tcForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingTc(true)
    try {
      const payload = { ...tcForm, descuento_porcentaje: Number(tcForm.descuento_porcentaje) || 0 }
      if (editingTc) {
        await api.put(`/clientes/tipos-cliente/${editingTc.id}/`, payload)
        toast.success('Tipo de cliente actualizado')
      } else {
        await api.post('/clientes/tipos-cliente/', payload)
        toast.success('Tipo de cliente creado')
      }
      setTcModal(false)
      loadTiposCliente()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingTc(false) }
  }, [tcForm, editingTc, loadTiposCliente])

  // ── Listas precio CRUD ────────────────────────────────────────────
  const openLp = useCallback((l?: ListaPrecio) => {
    setEditingLp(l ?? null)
    setLpForm(l ? { nombre: l.nombre, descripcion: l.descripcion, es_precio_base: l.es_precio_base } : { nombre: '', descripcion: '', es_precio_base: false })
    setLpModal(true)
  }, [])

  const saveLp = useCallback(async () => {
    if (!lpForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingLp(true)
    try {
      if (editingLp) {
        await api.put(`/productos/listas-precio/${editingLp.id}/`, lpForm)
        toast.success('Lista de precio actualizada')
      } else {
        await api.post('/productos/listas-precio/', lpForm)
        toast.success('Lista de precio creada')
      }
      setLpModal(false)
      loadListasPrecio()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingLp(false) }
  }, [lpForm, editingLp, loadListasPrecio])

  // ── Grados CRUD ───────────────────────────────────────────────────
  const openGr = useCallback((g?: Grado) => {
    setEditingGr(g ?? null)
    setGrForm(g ? { nombre: g.nombre, nivel: g.nivel, orden: g.orden, es_ultimo: g.es_ultimo, activo: g.activo } : { nombre: '', nivel: 1, orden: 1, es_ultimo: false, activo: true })
    setGrModal(true)
  }, [])

  const saveGr = useCallback(async () => {
    if (!grForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingGr(true)
    try {
      if (editingGr) {
        await api.put(`/clientes/grados/${editingGr.id}/`, grForm)
        toast.success('Grado actualizado')
      } else {
        await api.post('/clientes/grados/', grForm)
        toast.success('Grado creado')
      }
      setGrModal(false); loadGrados()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingGr(false) }
  }, [grForm, editingGr, loadGrados])

  // ── Empresa CRUD (single instance) ───────────────────────────────
  const saveEmp = useCallback(async () => {
    if (!empForm.ruc || !empForm.razon_social) { toast.error('RUC y razón social son obligatorios'); return }
    setSavingEmp(true)
    try {
      if (empresa) {
        await api.put(`/contabilidad/datos-empresa/${empresa.id}/`, empForm)
      } else {
        await api.post('/contabilidad/datos-empresa/', empForm)
      }
      toast.success('Datos guardados')
      loadEmpresa()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingEmp(false) }
  }, [empForm, empresa, loadEmpresa])

  // ── 2FA actions ───────────────────────────────────────────────────
  const iniciarSetup2FA = async () => {
    try {
      const { data } = await api.post('/usuarios/2fa/configurar/')
      setOtpUri(data.otp_uri)
      setOtpSecret(data.secret)
      setBackupCodes(data.backup_codes ?? [])
      setOtpCode('')
      setTwoFAStep('setup')
    } catch (err) { toast.error(extractErrorMessage(err)) }
  }

  const activar2FA = async () => {
    if (otpCode.length !== 6) { toast.error('Ingresá el código de 6 dígitos'); return }
    try {
      await api.post('/usuarios/2fa/activar/', { codigo: otpCode })
      toast.success('2FA activado correctamente')
      setTwoFAStep('idle'); setOtpCode(''); load2FA()
    } catch (err) { toast.error(extractErrorMessage(err)) }
  }

  const desactivar2FA = async () => {
    if (otpCode.length < 6) { toast.error('Ingresá tu código TOTP actual para confirmar'); return }
    try {
      await api.post('/usuarios/2fa/desactivar/', { codigo: otpCode })
      toast.success('2FA desactivado')
      setTwoFAStep('idle'); setOtpCode(''); load2FA()
    } catch (err) { toast.error(extractErrorMessage(err)) }
  }

  // ── Medios pago CRUD ──────────────────────────────────────────────
  const openMp = useCallback((m?: MedioPago) => {
    setEditingMp(m ?? null)
    setMpForm(m ? { nombre: m.nombre, tipo: m.tipo, activo: m.activo } : { nombre: '', tipo: 'EFECTIVO', activo: true })
    setMpModal(true)
  }, [])

  const saveMp = useCallback(async () => {
    if (!mpForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingMp(true)
    try {
      if (editingMp) {
        await api.put(`/ventas/medios-pago/${editingMp.id}/`, mpForm)
        toast.success('Medio de pago actualizado')
      } else {
        await api.post('/ventas/medios-pago/', mpForm)
        toast.success('Medio de pago creado')
      }
      setMpModal(false)
      loadMediosPago()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingMp(false) }
  }, [mpForm, editingMp, loadMediosPago])

  // ── Columns ──────────────────────────────────────────────────────

  const colsCat: Column<Categoria>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Descripción', key: 'desc', render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span> },
    {
      title: '', key: 'acc', width: 80,
      render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openCat(r)}><Edit2 className="w-3.5 h-3.5" /></Button>,
    },
  ]

  const colsTc: Column<TipoCliente>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Descripción', key: 'desc', render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span> },
    {
      title: 'Descuento',
      key: 'desc_pct',
      render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{Number(r.descuento_porcentaje) || 0}%</span>,
    },
    {
      title: '', key: 'acc', width: 80,
      render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openTc(r)}><Edit2 className="w-3.5 h-3.5" /></Button>,
    },
  ]

  const colsLp: Column<ListaPrecio>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Descripción', key: 'desc', render: (_, r) => <span className="text-sm text-slate-500">{r.descripcion || '—'}</span> },
    {
      title: 'Precio Base',
      key: 'base',
      render: (_, r) => <Badge color={r.es_precio_base ? 'green' : 'default'}>{r.es_precio_base ? 'Sí' : 'No'}</Badge>,
    },
    {
      title: '', key: 'acc', width: 80,
      render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openLp(r)}><Edit2 className="w-3.5 h-3.5" /></Button>,
    },
  ]

  const colsMp: Column<MedioPago>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Tipo', key: 'tipo', render: (_, r) => <Badge color="blue">{r.tipo}</Badge> },
    {
      title: 'Estado',
      key: 'activo',
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '', key: 'acc', width: 80,
      render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openMp(r)}><Edit2 className="w-3.5 h-3.5" /></Button>,
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

  const colsGr: Column<Grado>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Nivel', key: 'nivel', width: 70, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{r.nivel}</span> },
    { title: 'Orden', key: 'orden', width: 70, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">{r.orden}</span> },
    { title: 'Último', key: 'ultimo', width: 80, render: (_, r) => <Badge color={r.es_ultimo ? 'purple' : 'default'}>{r.es_ultimo ? 'Sí' : 'No'}</Badge> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    { title: '', key: 'acc', width: 80, render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openGr(r)}><Edit2 className="w-3.5 h-3.5" /></Button> },
  ]

  const colsHist: Column<HistoricoPrecioItem>[] = [
    { title: 'Producto', key: 'prod', render: (_, r) => <span className="text-sm text-slate-800">{r.producto_nombre}</span> },
    {
      title: 'Precio anterior', key: 'ant', width: 150,
      render: (_, r) => <span className="tabular-nums text-sm text-slate-500">Gs. {(Number(r.precio_anterior) || 0).toLocaleString('es-PY')}</span>,
    },
    {
      title: 'Precio nuevo', key: 'nuevo', width: 150,
      render: (_, r) => <span className="tabular-nums text-sm font-semibold text-emerald-700">Gs. {(Number(r.precio_nuevo) || 0).toLocaleString('es-PY')}</span>,
    },
    {
      title: 'Variación', key: 'var', width: 100,
      render: (_, r) => {
        const v = Number(r.variacion_porcentual) || 0
        return <Badge color={v >= 0 ? 'orange' : 'green'}>{v >= 0 ? '+' : ''}{v}%</Badge>
      },
    },
    {
      title: 'Fecha', key: 'fecha', width: 140,
      render: (_, r) => <span className="text-xs text-slate-400 tabular-nums">{new Date(r.fecha_cambio).toLocaleDateString('es-PY')}</span>,
    },
  ]

  const TABS: { key: TabKey; label: string; icon: typeof Settings }[] = [
    { key: 'categorias',       label: 'Categorías',       icon: Tag },
    { key: 'tipos_cliente',    label: 'Tipos de Cliente', icon: Users },
    { key: 'listas_precio',    label: 'Listas de Precio', icon: ListOrdered },
    { key: 'medios_pago',      label: 'Medios de Pago',   icon: CreditCard },
    { key: 'grados',           label: 'Grados',           icon: GraduationCap },
    { key: 'datos_empresa',    label: 'Empresa',          icon: Building2 },
    { key: 'historial_precios',label: 'Hist. Precios',    icon: History },
    { key: 'seguridad',        label: 'Seguridad',        icon: Shield },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Configuración</h1>
          <p className="text-sm text-slate-500 mt-0.5">Administración de catálogos del sistema</p>
        </div>
        {['categorias','tipos_cliente','listas_precio','medios_pago','grados'].includes(tab) && (
          <Button variant="primary" onClick={() => {
            if (tab === 'categorias') openCat()
            else if (tab === 'tipos_cliente') openTc()
            else if (tab === 'listas_precio') openLp()
            else if (tab === 'grados') openGr()
            else openMp()
          }}>
            <Plus className="w-4 h-4" />
            Nuevo
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex flex-wrap gap-0">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tables — catálogos simples */}
      {['categorias','tipos_cliente','listas_precio','medios_pago','grados'].includes(tab) && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            {tab === 'categorias'    && <Table columns={colsCat} dataSource={categorias}    rowKey="id" loading={loadingCat} pageSize={20} />}
            {tab === 'tipos_cliente' && <Table columns={colsTc}  dataSource={tiposCliente}  rowKey="id" loading={loadingTc}  pageSize={20} />}
            {tab === 'listas_precio' && <Table columns={colsLp}  dataSource={listasPrecio}  rowKey="id" loading={loadingLp}  pageSize={20} />}
            {tab === 'medios_pago'   && <Table columns={colsMp}  dataSource={mediosPago}    rowKey="id" loading={loadingMp}  pageSize={20} />}
            {tab === 'grados'        && <Table columns={colsGr}  dataSource={grados}        rowKey="id" loading={loadingGr}  pageSize={20} />}
          </div>
        </div>
      )}

      {/* Datos empresa */}
      {tab === 'datos_empresa' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 max-w-2xl space-y-4">
          {loadingEmp ? <div className="text-sm text-slate-400">Cargando...</div> : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>RUC *</label>
                  <input value={empForm.ruc} onChange={e => setEmpForm(f => ({ ...f, ruc: e.target.value }))} className={inputClass} placeholder="80012345-1" />
                </div>
                <div>
                  <label className={labelClass}>Razón Social *</label>
                  <input value={empForm.razon_social} onChange={e => setEmpForm(f => ({ ...f, razon_social: e.target.value }))} className={inputClass} />
                </div>
              </div>
              <div>
                <label className={labelClass}>Dirección</label>
                <input value={empForm.direccion} onChange={e => setEmpForm(f => ({ ...f, direccion: e.target.value }))} className={inputClass} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>Ciudad</label>
                  <input value={empForm.ciudad} onChange={e => setEmpForm(f => ({ ...f, ciudad: e.target.value }))} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>País</label>
                  <input value={empForm.pais} onChange={e => setEmpForm(f => ({ ...f, pais: e.target.value }))} className={inputClass} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={labelClass}>Teléfono</label>
                  <input value={empForm.telefono} onChange={e => setEmpForm(f => ({ ...f, telefono: e.target.value }))} className={inputClass} />
                </div>
                <div>
                  <label className={labelClass}>Email</label>
                  <input type="email" value={empForm.email} onChange={e => setEmpForm(f => ({ ...f, email: e.target.value }))} className={inputClass} />
                </div>
              </div>
              <div className="pt-2">
                <Button variant="primary" loading={savingEmp} onClick={saveEmp}>Guardar cambios</Button>
              </div>
            </>
          )}
        </div>
      )}

      {/* Historial precios */}
      {tab === 'historial_precios' && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4">
            <label className={labelClass}>Filtrar por producto</label>
            <div className="max-w-sm">
              <Combobox
                options={productosLookup.map(p => ({ value: p.id, label: p.descripcion }))}
                value={histProductoId}
                onChange={v => { setHistProductoId(v as number | undefined); setHistPage(1) }}
                placeholder="Todos los productos..."
              />
            </div>
          </div>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={colsHist}
                dataSource={historico}
                rowKey="id"
                loading={loadingHist}
                pageSize={15}
                page={histPage}
                onPageChange={setHistPage}
                total={histTotal}
              />
            </div>
          </div>
        </div>
      )}

      {/* Seguridad / 2FA */}
      {tab === 'seguridad' && (
        <div className="max-w-lg space-y-5">
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${estado2fa?.habilitado ? 'bg-green-50' : 'bg-slate-100'}`}>
                <Shield className={`w-5 h-5 ${estado2fa?.habilitado ? 'text-green-600' : 'text-slate-400'}`} />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-800">Autenticación de dos factores</p>
                <p className="text-xs text-slate-500">TOTP — compatible con Google Authenticator, Authy, etc.</p>
              </div>
              {loading2fa ? null : (
                <Badge color={estado2fa?.habilitado ? 'green' : 'default'}>
                  {estado2fa?.habilitado ? 'Activo' : 'Inactivo'}
                </Badge>
              )}
            </div>

            {/* Estado idle */}
            {twoFAStep === 'idle' && !loading2fa && (
              <div className="space-y-3">
                {estado2fa?.fecha_activacion && (
                  <p className="text-xs text-slate-400">
                    Activado el {new Date(estado2fa.fecha_activacion).toLocaleDateString('es-PY')}
                  </p>
                )}
                {estado2fa?.habilitado ? (
                  <Button variant="danger" onClick={() => { setOtpCode(''); setTwoFAStep('disable') }}>
                    <XCircle className="w-4 h-4" /> Desactivar 2FA
                  </Button>
                ) : (
                  <Button variant="primary" onClick={iniciarSetup2FA}>
                    <Shield className="w-4 h-4" /> Configurar 2FA
                  </Button>
                )}
              </div>
            )}

            {/* Setup — mostrar QR + secret */}
            {twoFAStep === 'setup' && (
              <div className="space-y-4">
                <p className="text-sm text-slate-600">
                  1. Escaneá este código con tu app de autenticación, o copiá el secret manualmente.
                </p>
                <div className="bg-slate-50 rounded-xl p-4 flex flex-col items-center gap-3">
                  <QRCodeSVG
                    value={otpUri}
                    size={180}
                    level="H"
                    className="rounded-lg border border-slate-200 p-2 bg-white"
                  />
                  <div className="flex items-center gap-2 text-xs bg-white border border-slate-200 rounded-lg px-3 py-2 w-full">
                    <code className="flex-1 break-all text-slate-700 select-all">
                      {showSecret ? otpSecret : '•'.repeat(otpSecret.length)}
                    </code>
                    <button onClick={() => setShowSecret(s => !s)} className="text-slate-400 hover:text-slate-600 cursor-pointer shrink-0">
                      {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                    <button onClick={() => { navigator.clipboard.writeText(otpSecret); toast.success('Copiado') }} className="text-slate-400 hover:text-slate-600 cursor-pointer shrink-0">
                      <Copy className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-sm text-slate-600">2. Ingresá el código de 6 dígitos para confirmar.</p>
                <div className="flex gap-2">
                  <input
                    value={otpCode}
                    onChange={e => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="123456"
                    className={`${inputClass} text-center tracking-widest text-lg font-mono`}
                    maxLength={6}
                  />
                  <Button variant="primary" onClick={activar2FA} disabled={otpCode.length !== 6}>
                    <CheckCircle2 className="w-4 h-4" /> Activar
                  </Button>
                </div>
                {backupCodes.length > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <p className="text-xs font-semibold text-amber-800 mb-2">Guardá estos códigos de respaldo (úsalos si perdés acceso a tu app)</p>
                    <div className="grid grid-cols-4 gap-1">
                      {backupCodes.map(c => (
                        <code key={c} className="text-xs bg-white border border-amber-200 rounded px-2 py-1 text-center">{c}</code>
                      ))}
                    </div>
                  </div>
                )}
                <Button variant="secondary" onClick={() => setTwoFAStep('idle')}>Cancelar</Button>
              </div>
            )}

            {/* Disable — confirmar con código */}
            {twoFAStep === 'disable' && (
              <div className="space-y-3">
                <p className="text-sm text-slate-600">Ingresá tu código TOTP actual para desactivar el 2FA.</p>
                <div className="flex gap-2">
                  <input
                    value={otpCode}
                    onChange={e => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    placeholder="123456"
                    className={`${inputClass} text-center tracking-widest text-lg font-mono`}
                    maxLength={6}
                  />
                  <Button variant="danger" onClick={desactivar2FA} disabled={otpCode.length !== 6}>
                    Confirmar
                  </Button>
                </div>
                <Button variant="secondary" onClick={() => setTwoFAStep('idle')}>Cancelar</Button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Categoría modal ────────────────────────────────────────── */}
      <Modal
        open={catModal}
        title={editingCat ? 'Editar Categoría' : 'Nueva Categoría'}
        onOk={saveCat}
        onCancel={() => setCatModal(false)}
        okText={editingCat ? 'Guardar' : 'Crear'}
        confirmLoading={savingCat}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={catForm.nombre} onChange={e => setCatForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={catForm.descripcion} onChange={e => setCatForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
        </div>
      </Modal>

      {/* ── Tipo cliente modal ─────────────────────────────────────── */}
      <Modal
        open={tcModal}
        title={editingTc ? 'Editar Tipo de Cliente' : 'Nuevo Tipo de Cliente'}
        onOk={saveTc}
        onCancel={() => setTcModal(false)}
        okText={editingTc ? 'Guardar' : 'Crear'}
        confirmLoading={savingTc}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={tcForm.nombre} onChange={e => setTcForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={tcForm.descripcion} onChange={e => setTcForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          <div>
            <label className={labelClass}>Descuento (%)</label>
            <input type="number" min={0} max={100} step={0.5}
              value={tcForm.descuento_porcentaje}
              onChange={e => setTcForm(f => ({ ...f, descuento_porcentaje: e.target.value }))}
              className={inputClass}
            />
          </div>
        </div>
      </Modal>

      {/* ── Lista precio modal ─────────────────────────────────────── */}
      <Modal
        open={lpModal}
        title={editingLp ? 'Editar Lista de Precio' : 'Nueva Lista de Precio'}
        onOk={saveLp}
        onCancel={() => setLpModal(false)}
        okText={editingLp ? 'Guardar' : 'Crear'}
        confirmLoading={savingLp}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={lpForm.nombre} onChange={e => setLpForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={lpForm.descripcion} onChange={e => setLpForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          {toggleSwitch(lpForm.es_precio_base, v => setLpForm(f => ({ ...f, es_precio_base: v })), 'Es precio base')}
        </div>
      </Modal>

      {/* ── Medio pago modal ───────────────────────────────────────── */}
      <Modal
        open={mpModal}
        title={editingMp ? 'Editar Medio de Pago' : 'Nuevo Medio de Pago'}
        onOk={saveMp}
        onCancel={() => setMpModal(false)}
        okText={editingMp ? 'Guardar' : 'Crear'}
        confirmLoading={savingMp}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={mpForm.nombre} onChange={e => setMpForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Tipo</label>
            <select value={mpForm.tipo} onChange={e => setMpForm(f => ({ ...f, tipo: e.target.value }))} className={inputClass}>
              <option value="EFECTIVO">Efectivo</option>
              <option value="TARJETA">Tarjeta</option>
              <option value="TRANSFERENCIA">Transferencia</option>
              <option value="CHEQUE">Cheque</option>
              <option value="OTRO">Otro</option>
            </select>
          </div>
          {toggleSwitch(mpForm.activo, v => setMpForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>

      {/* ── Grado modal ────────────────────────────────────────────── */}
      <Modal
        open={grModal}
        title={editingGr ? 'Editar Grado' : 'Nuevo Grado'}
        onOk={saveGr}
        onCancel={() => setGrModal(false)}
        okText={editingGr ? 'Guardar' : 'Crear'}
        confirmLoading={savingGr}
        width={420}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={grForm.nombre} onChange={e => setGrForm(f => ({ ...f, nombre: e.target.value }))} placeholder="1° Grado" className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nivel (1-12)</label>
              <input type="number" min={1} max={12} value={grForm.nivel}
                onChange={e => setGrForm(f => ({ ...f, nivel: Number(e.target.value) }))} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Orden de visualización</label>
              <input type="number" min={1} value={grForm.orden}
                onChange={e => setGrForm(f => ({ ...f, orden: Number(e.target.value) }))} className={inputClass} />
            </div>
          </div>
          <div className="flex flex-col gap-3">
            {toggleSwitch(grForm.es_ultimo, v => setGrForm(f => ({ ...f, es_ultimo: v })), 'Es el último grado')}
            {toggleSwitch(grForm.activo, v => setGrForm(f => ({ ...f, activo: v })), 'Activo')}
          </div>
        </div>
      </Modal>
    </div>
  )
}
