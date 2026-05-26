import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import {
  Settings, Plus, Edit2, Tag, ListOrdered, CreditCard, Users,
  GraduationCap, Building2, History, Shield, Eye, EyeOff,
  CheckCircle2, XCircle, Copy,
  UtensilsCrossed, Calendar, Ruler, AlertTriangle, Percent,
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
  descripcion: string
  requiere_validacion: boolean
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
  nombre_fantasia: string
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
  tipo: 'CANTIDAD' | 'SIN_LIMITE'
  precio_mensual: string | number
  cantidad_almuerzos_mes: number | null
  dias_semana_incluidos: number[]
  activo: boolean
}

interface UnidadMedida {
  id: number
  nombre: string
  abreviatura: string
  activo: boolean
}

interface Alergeno {
  id: number
  nombre: string
  descripcion: string
  palabras_clave: string[]
  severidad: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA'
  icono: string
  activo: boolean
}

interface Impuesto {
  id: number
  nombre: string
  porcentaje: string | number
  vigente_desde: string | null
  vigente_hasta: string | null
  activo: boolean
}

// ─── Types ────────────────────────────────────────────────────────────────────

type TabKey = 'categorias' | 'tipos_cliente' | 'listas_precio' | 'medios_pago'
            | 'grados' | 'datos_empresa' | 'historial_precios' | 'seguridad'
            | 'tipos_almuerzo' | 'planes_almuerzo' | 'unidades_medida' | 'alergenos' | 'impuestos'

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
  const [mpForm, setMpForm] = useState({ descripcion: '', requiere_validacion: false, activo: true })
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
  const [empForm, setEmpForm] = useState({ ruc: '', razon_social: '', nombre_fantasia: '', direccion: '', ciudad: '', pais: 'Paraguay', telefono: '', email: '', activo: true })
  const [savingEmp, setSavingEmp] = useState(false)
  const savedEmpRef = useRef<typeof empForm | null>(null)

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

  // ── Tipos Almuerzo ────────────────────────────────────────────────
  const [tiposAlmuerzo, setTiposAlmuerzo] = useState<TipoAlmuerzo[]>([])
  const [loadingTa, setLoadingTa] = useState(false)
  const [taModal, setTaModal] = useState(false)
  const [editingTa, setEditingTa] = useState<TipoAlmuerzo | null>(null)
  const [taForm, setTaForm] = useState({ nombre: '', descripcion: '', precio_unitario: '', incluye_plato_principal: true, incluye_postre: false, incluye_bebida: false, activo: true })
  const [savingTa, setSavingTa] = useState(false)

  // ── Planes Almuerzo ───────────────────────────────────────────────
  const [planesAlmuerzo, setPlanesAlmuerzo] = useState<PlanAlmuerzo[]>([])
  const [loadingPa, setLoadingPa] = useState(false)
  const [paModal, setPaModal] = useState(false)
  const [editingPa, setEditingPa] = useState<PlanAlmuerzo | null>(null)
  const [paForm, setPaForm] = useState({ nombre: '', tipo: 'CANTIDAD' as 'CANTIDAD' | 'SIN_LIMITE', precio_mensual: '', cantidad_almuerzos_mes: '', dias_semana_incluidos: [] as number[], activo: true })
  const [savingPa, setSavingPa] = useState(false)

  // ── Unidades de Medida ────────────────────────────────────────────
  const [unidadesMedida, setUnidadesMedida] = useState<UnidadMedida[]>([])
  const [loadingUm, setLoadingUm] = useState(false)
  const [umModal, setUmModal] = useState(false)
  const [editingUm, setEditingUm] = useState<UnidadMedida | null>(null)
  const [umForm, setUmForm] = useState({ nombre: '', abreviatura: '', activo: true })
  const [savingUm, setSavingUm] = useState(false)

  // ── Alérgenos ─────────────────────────────────────────────────────
  const [alergenos, setAlergenos] = useState<Alergeno[]>([])
  const [loadingAl, setLoadingAl] = useState(false)
  const [alModal, setAlModal] = useState(false)
  const [editingAl, setEditingAl] = useState<Alergeno | null>(null)
  const [alForm, setAlForm] = useState({ nombre: '', descripcion: '', palabras_clave: '', severidad: 'MEDIA' as 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA', icono: '', activo: true })
  const [savingAl, setSavingAl] = useState(false)

  // ── Impuestos ─────────────────────────────────────────────────────
  const [impuestos, setImpuestos] = useState<Impuesto[]>([])
  const [loadingImp, setLoadingImp] = useState(false)
  const [impModal, setImpModal] = useState(false)
  const [editingImp, setEditingImp] = useState<Impuesto | null>(null)
  const [impForm, setImpForm] = useState({ nombre: '', porcentaje: '', vigente_desde: '', vigente_hasta: '', activo: true })
  const [savingImp, setSavingImp] = useState(false)

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
      const { data } = await api.get('/core/medios-pago/', { params: { page_size: 100 } })
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
      if (emp) {
        const f = { ruc: emp.ruc, razon_social: emp.razon_social, nombre_fantasia: emp.nombre_fantasia ?? '', direccion: emp.direccion ?? '', ciudad: emp.ciudad ?? '', pais: emp.pais ?? 'Paraguay', telefono: emp.telefono ?? '', email: emp.email ?? '', activo: emp.activo }
        setEmpForm(f)
        savedEmpRef.current = f
      }
    } catch { toast.error('Error al cargar datos de empresa') }
    finally { setLoadingEmp(false) }
  }, [])

  useEffect(() => { if (tab === 'datos_empresa') loadEmpresa() }, [tab, loadEmpresa])

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!savedEmpRef.current) return
      if (JSON.stringify(empForm) !== JSON.stringify(savedEmpRef.current)) {
        e.preventDefault()
        e.returnValue = ''
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [empForm])

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

  // ── Load tipos almuerzo ───────────────────────────────────────────
  const loadTiposAlmuerzo = useCallback(async () => {
    setLoadingTa(true)
    try {
      const { data } = await api.get('/almuerzos/tipos-almuerzo/', { params: { page_size: 100 } })
      setTiposAlmuerzo(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar tipos de almuerzo') }
    finally { setLoadingTa(false) }
  }, [])

  useEffect(() => { if (tab === 'tipos_almuerzo') loadTiposAlmuerzo() }, [tab, loadTiposAlmuerzo])

  // ── Load planes almuerzo ──────────────────────────────────────────
  const loadPlanesAlmuerzo = useCallback(async () => {
    setLoadingPa(true)
    try {
      const { data } = await api.get('/almuerzos/planes-almuerzo/', { params: { page_size: 100 } })
      setPlanesAlmuerzo(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar planes de almuerzo') }
    finally { setLoadingPa(false) }
  }, [])

  useEffect(() => { if (tab === 'planes_almuerzo') loadPlanesAlmuerzo() }, [tab, loadPlanesAlmuerzo])

  // ── Load unidades medida ──────────────────────────────────────────
  const loadUnidadesMedida = useCallback(async () => {
    setLoadingUm(true)
    try {
      const { data } = await api.get('/productos/unidades-medida/', { params: { page_size: 100 } })
      setUnidadesMedida(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar unidades de medida') }
    finally { setLoadingUm(false) }
  }, [])

  useEffect(() => { if (tab === 'unidades_medida') loadUnidadesMedida() }, [tab, loadUnidadesMedida])

  // ── Load alérgenos ────────────────────────────────────────────────
  const loadAlergenos = useCallback(async () => {
    setLoadingAl(true)
    try {
      const { data } = await api.get('/almuerzos/alergenos/', { params: { page_size: 100 } })
      setAlergenos(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar alérgenos') }
    finally { setLoadingAl(false) }
  }, [])

  useEffect(() => { if (tab === 'alergenos') loadAlergenos() }, [tab, loadAlergenos])

  // ── Load impuestos ────────────────────────────────────────────────
  const loadImpuestos = useCallback(async () => {
    setLoadingImp(true)
    try {
      const { data } = await api.get('/productos/impuestos/', { params: { page_size: 100 } })
      setImpuestos(data.results ?? data ?? [])
    } catch { toast.error('Error al cargar impuestos') }
    finally { setLoadingImp(false) }
  }, [])

  useEffect(() => { if (tab === 'impuestos') loadImpuestos() }, [tab, loadImpuestos])

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
      savedEmpRef.current = { ...empForm }
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

  // ── Tipos Almuerzo CRUD ───────────────────────────────────────────
  const openTa = useCallback((t?: TipoAlmuerzo) => {
    setEditingTa(t ?? null)
    setTaForm(t
      ? { nombre: t.nombre, descripcion: t.descripcion, precio_unitario: String(t.precio_unitario), incluye_plato_principal: t.incluye_plato_principal, incluye_postre: t.incluye_postre, incluye_bebida: t.incluye_bebida, activo: t.activo }
      : { nombre: '', descripcion: '', precio_unitario: '', incluye_plato_principal: true, incluye_postre: false, incluye_bebida: false, activo: true })
    setTaModal(true)
  }, [])

  const saveTa = useCallback(async () => {
    if (!taForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingTa(true)
    try {
      const payload = { ...taForm, precio_unitario: Number(taForm.precio_unitario) || 0 }
      if (editingTa) {
        await api.put(`/almuerzos/tipos-almuerzo/${editingTa.id}/`, payload)
        toast.success('Tipo de almuerzo actualizado')
      } else {
        await api.post('/almuerzos/tipos-almuerzo/', payload)
        toast.success('Tipo de almuerzo creado')
      }
      setTaModal(false); loadTiposAlmuerzo()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingTa(false) }
  }, [taForm, editingTa, loadTiposAlmuerzo])

  // ── Planes Almuerzo CRUD ──────────────────────────────────────────
  const openPa = useCallback((p?: PlanAlmuerzo) => {
    setEditingPa(p ?? null)
    setPaForm(p
      ? { nombre: p.nombre, tipo: p.tipo, precio_mensual: String(p.precio_mensual), cantidad_almuerzos_mes: p.cantidad_almuerzos_mes != null ? String(p.cantidad_almuerzos_mes) : '', dias_semana_incluidos: p.dias_semana_incluidos ?? [], activo: p.activo }
      : { nombre: '', tipo: 'CANTIDAD', precio_mensual: '', cantidad_almuerzos_mes: '', dias_semana_incluidos: [], activo: true })
    setPaModal(true)
  }, [])

  const savePa = useCallback(async () => {
    if (!paForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingPa(true)
    try {
      const payload = {
        ...paForm,
        precio_mensual: Number(paForm.precio_mensual) || 0,
        cantidad_almuerzos_mes: paForm.tipo === 'CANTIDAD' && paForm.cantidad_almuerzos_mes ? Number(paForm.cantidad_almuerzos_mes) : null,
      }
      if (editingPa) {
        await api.put(`/almuerzos/planes-almuerzo/${editingPa.id}/`, payload)
        toast.success('Plan actualizado')
      } else {
        await api.post('/almuerzos/planes-almuerzo/', payload)
        toast.success('Plan creado')
      }
      setPaModal(false); loadPlanesAlmuerzo()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingPa(false) }
  }, [paForm, editingPa, loadPlanesAlmuerzo])

  // ── Unidades Medida CRUD ──────────────────────────────────────────
  const openUm = useCallback((u?: UnidadMedida) => {
    setEditingUm(u ?? null)
    setUmForm(u ? { nombre: u.nombre, abreviatura: u.abreviatura, activo: u.activo } : { nombre: '', abreviatura: '', activo: true })
    setUmModal(true)
  }, [])

  const saveUm = useCallback(async () => {
    if (!umForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingUm(true)
    try {
      if (editingUm) {
        await api.put(`/productos/unidades-medida/${editingUm.id}/`, umForm)
        toast.success('Unidad actualizada')
      } else {
        await api.post('/productos/unidades-medida/', umForm)
        toast.success('Unidad creada')
      }
      setUmModal(false); loadUnidadesMedida()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingUm(false) }
  }, [umForm, editingUm, loadUnidadesMedida])

  // ── Alérgenos CRUD ────────────────────────────────────────────────
  const openAl = useCallback((a?: Alergeno) => {
    setEditingAl(a ?? null)
    setAlForm(a
      ? { nombre: a.nombre, descripcion: a.descripcion, palabras_clave: (a.palabras_clave ?? []).join(', '), severidad: a.severidad, icono: a.icono ?? '', activo: a.activo }
      : { nombre: '', descripcion: '', palabras_clave: '', severidad: 'MEDIA', icono: '', activo: true })
    setAlModal(true)
  }, [])

  const saveAl = useCallback(async () => {
    if (!alForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingAl(true)
    try {
      const palabras = alForm.palabras_clave ? alForm.palabras_clave.split(',').map(s => s.trim()).filter(Boolean) : []
      const payload = { ...alForm, palabras_clave: palabras }
      if (editingAl) {
        await api.put(`/almuerzos/alergenos/${editingAl.id}/`, payload)
        toast.success('Alérgeno actualizado')
      } else {
        await api.post('/almuerzos/alergenos/', payload)
        toast.success('Alérgeno creado')
      }
      setAlModal(false); loadAlergenos()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingAl(false) }
  }, [alForm, editingAl, loadAlergenos])

  // ── Impuestos CRUD ────────────────────────────────────────────────
  const openImp = useCallback((i?: Impuesto) => {
    setEditingImp(i ?? null)
    setImpForm(i
      ? { nombre: i.nombre, porcentaje: String(i.porcentaje), vigente_desde: i.vigente_desde ?? '', vigente_hasta: i.vigente_hasta ?? '', activo: i.activo }
      : { nombre: '', porcentaje: '', vigente_desde: '', vigente_hasta: '', activo: true })
    setImpModal(true)
  }, [])

  const saveImp = useCallback(async () => {
    if (!impForm.nombre) { toast.error('Ingresá el nombre'); return }
    setSavingImp(true)
    try {
      const payload = {
        nombre: impForm.nombre,
        porcentaje: Number(impForm.porcentaje) || 0,
        vigente_desde: impForm.vigente_desde || null,
        vigente_hasta: impForm.vigente_hasta || null,
        activo: impForm.activo,
      }
      if (editingImp) {
        await api.put(`/productos/impuestos/${editingImp.id}/`, payload)
        toast.success('Impuesto actualizado')
      } else {
        await api.post('/productos/impuestos/', payload)
        toast.success('Impuesto creado')
      }
      setImpModal(false); loadImpuestos()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingImp(false) }
  }, [impForm, editingImp, loadImpuestos])

  // ── Medios pago CRUD ──────────────────────────────────────────────
  const openMp = useCallback((m?: MedioPago) => {
    setEditingMp(m ?? null)
    setMpForm(m ? { descripcion: m.descripcion, requiere_validacion: m.requiere_validacion, activo: m.activo } : { descripcion: '', requiere_validacion: false, activo: true })
    setMpModal(true)
  }, [])

  const saveMp = useCallback(async () => {
    if (!mpForm.descripcion) { toast.error('Ingresá la descripción'); return }
    setSavingMp(true)
    try {
      if (editingMp) {
        await api.put(`/core/medios-pago/${editingMp.id}/`, mpForm)
        toast.success('Medio de pago actualizado')
      } else {
        await api.post('/core/medios-pago/', mpForm)
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
    { title: 'Descripción', key: 'descripcion', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.descripcion}</span> },
    {
      title: 'Requiere validación', key: 'req_val', width: 160,
      render: (_, r) => <Badge color={r.requiere_validacion ? 'blue' : 'default'}>{r.requiere_validacion ? 'Sí' : 'No'}</Badge>,
    },
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

  const DIAS_SEMANA = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
  const SEVERIDAD_COLOR: Record<string, 'blue' | 'orange' | 'red' | 'purple'> = { BAJA: 'blue', MEDIA: 'orange', ALTA: 'red', CRITICA: 'purple' }

  const colsTa: Column<TipoAlmuerzo>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Precio unit.', key: 'precio', width: 130, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">Gs. {(Number(r.precio_unitario) || 0).toLocaleString('es-PY')}</span> },
    { title: 'Plato Ppal', key: 'pp', width: 100, render: (_, r) => <Badge color={r.incluye_plato_principal ? 'green' : 'default'}>{r.incluye_plato_principal ? 'Sí' : 'No'}</Badge> },
    { title: 'Postre', key: 'pos', width: 80, render: (_, r) => <Badge color={r.incluye_postre ? 'green' : 'default'}>{r.incluye_postre ? 'Sí' : 'No'}</Badge> },
    { title: 'Bebida', key: 'beb', width: 80, render: (_, r) => <Badge color={r.incluye_bebida ? 'green' : 'default'}>{r.incluye_bebida ? 'Sí' : 'No'}</Badge> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    { title: '', key: 'acc', width: 80, render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openTa(r)}><Edit2 className="w-3.5 h-3.5" /></Button> },
  ]

  const colsPa: Column<PlanAlmuerzo>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Tipo', key: 'tipo', width: 120, render: (_, r) => <Badge color={r.tipo === 'SIN_LIMITE' ? 'blue' : 'orange'}>{r.tipo === 'SIN_LIMITE' ? 'Sin límite' : 'Por cantidad'}</Badge> },
    { title: 'Precio mensual', key: 'precio', width: 150, render: (_, r) => <span className="tabular-nums text-sm text-slate-700">Gs. {(Number(r.precio_mensual) || 0).toLocaleString('es-PY')}</span> },
    { title: 'Cant./mes', key: 'cant', width: 100, render: (_, r) => <span className="tabular-nums text-sm text-slate-500">{r.cantidad_almuerzos_mes ?? '—'}</span> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    { title: '', key: 'acc', width: 80, render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openPa(r)}><Edit2 className="w-3.5 h-3.5" /></Button> },
  ]

  const colsUm: Column<UnidadMedida>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Abreviatura', key: 'abrev', width: 130, render: (_, r) => <code className="text-sm text-slate-600 bg-slate-100 rounded px-2 py-0.5">{r.abreviatura}</code> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    { title: '', key: 'acc', width: 80, render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openUm(r)}><Edit2 className="w-3.5 h-3.5" /></Button> },
  ]

  const colsAl: Column<Alergeno>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Severidad', key: 'sev', width: 110, render: (_, r) => <Badge color={SEVERIDAD_COLOR[r.severidad] ?? 'default'}>{r.severidad}</Badge> },
    { title: 'Icono', key: 'icono', width: 70, render: (_, r) => <span className="text-lg">{r.icono || '—'}</span> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    { title: '', key: 'acc', width: 80, render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openAl(r)}><Edit2 className="w-3.5 h-3.5" /></Button> },
  ]

  const colsImp: Column<Impuesto>[] = [
    { title: 'Nombre', key: 'nombre', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.nombre}</span> },
    { title: 'Porcentaje', key: 'pct', width: 110, render: (_, r) => <span className="tabular-nums text-sm font-semibold text-slate-700">{Number(r.porcentaje) || 0}%</span> },
    { title: 'Desde', key: 'desde', width: 120, render: (_, r) => <span className="text-xs text-slate-500">{r.vigente_desde ? new Date(r.vigente_desde).toLocaleDateString('es-PY') : '—'}</span> },
    { title: 'Hasta', key: 'hasta', width: 120, render: (_, r) => <span className="text-xs text-slate-500">{r.vigente_hasta ? new Date(r.vigente_hasta).toLocaleDateString('es-PY') : '—'}</span> },
    { title: 'Estado', key: 'activo', width: 90, render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge> },
    { title: '', key: 'acc', width: 80, render: (_, r) => <Button size="sm" variant="secondary" onClick={() => openImp(r)}><Edit2 className="w-3.5 h-3.5" /></Button> },
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
    { key: 'tipos_almuerzo',   label: 'Tipos Almuerzo',   icon: UtensilsCrossed },
    { key: 'planes_almuerzo',  label: 'Planes Almuerzo',  icon: Calendar },
    { key: 'unidades_medida',  label: 'Unidades Medida',  icon: Ruler },
    { key: 'alergenos',        label: 'Alérgenos',        icon: AlertTriangle },
    { key: 'impuestos',        label: 'Impuestos',        icon: Percent },
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
        {['categorias','tipos_cliente','listas_precio','medios_pago','grados','tipos_almuerzo','planes_almuerzo','unidades_medida','alergenos','impuestos'].includes(tab) && (
          <Button variant="primary" onClick={() => {
            if (tab === 'categorias') openCat()
            else if (tab === 'tipos_cliente') openTc()
            else if (tab === 'listas_precio') openLp()
            else if (tab === 'grados') openGr()
            else if (tab === 'tipos_almuerzo') openTa()
            else if (tab === 'planes_almuerzo') openPa()
            else if (tab === 'unidades_medida') openUm()
            else if (tab === 'alergenos') openAl()
            else if (tab === 'impuestos') openImp()
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
      {['categorias','tipos_cliente','listas_precio','medios_pago','grados','tipos_almuerzo','planes_almuerzo','unidades_medida','alergenos','impuestos'].includes(tab) && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            {tab === 'categorias'     && <Table columns={colsCat} dataSource={categorias}    rowKey="id" loading={loadingCat} pageSize={20} />}
            {tab === 'tipos_cliente'  && <Table columns={colsTc}  dataSource={tiposCliente}  rowKey="id" loading={loadingTc}  pageSize={20} />}
            {tab === 'listas_precio'  && <Table columns={colsLp}  dataSource={listasPrecio}  rowKey="id" loading={loadingLp}  pageSize={20} />}
            {tab === 'medios_pago'    && <Table columns={colsMp}  dataSource={mediosPago}    rowKey="id" loading={loadingMp}  pageSize={20} />}
            {tab === 'grados'         && <Table columns={colsGr}  dataSource={grados}        rowKey="id" loading={loadingGr}  pageSize={20} />}
            {tab === 'tipos_almuerzo' && <Table columns={colsTa}  dataSource={tiposAlmuerzo} rowKey="id" loading={loadingTa}  pageSize={20} />}
            {tab === 'planes_almuerzo'&& <Table columns={colsPa}  dataSource={planesAlmuerzo}rowKey="id" loading={loadingPa}  pageSize={20} />}
            {tab === 'unidades_medida'&& <Table columns={colsUm}  dataSource={unidadesMedida}rowKey="id" loading={loadingUm}  pageSize={20} />}
            {tab === 'alergenos'      && <Table columns={colsAl}  dataSource={alergenos}     rowKey="id" loading={loadingAl}  pageSize={20} />}
            {tab === 'impuestos'      && <Table columns={colsImp} dataSource={impuestos}     rowKey="id" loading={loadingImp} pageSize={20} />}
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
                <label className={labelClass}>Nombre de Fantasía</label>
                <input value={empForm.nombre_fantasia} onChange={e => setEmpForm(f => ({ ...f, nombre_fantasia: e.target.value }))} className={inputClass} placeholder="Nombre comercial (opcional)" />
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
            <label className={labelClass}>Descripción *</label>
            <input value={mpForm.descripcion} onChange={e => setMpForm(f => ({ ...f, descripcion: e.target.value }))} className={inputClass} />
          </div>
          <div className="flex flex-col gap-3">
            {toggleSwitch(mpForm.requiere_validacion, v => setMpForm(f => ({ ...f, requiere_validacion: v })), 'Requiere validación')}
            {toggleSwitch(mpForm.activo, v => setMpForm(f => ({ ...f, activo: v })), 'Activo')}
          </div>
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

      {/* ── Tipo Almuerzo modal ─────────────────────────────────────── */}
      <Modal
        open={taModal}
        title={editingTa ? 'Editar Tipo de Almuerzo' : 'Nuevo Tipo de Almuerzo'}
        onOk={saveTa}
        onCancel={() => setTaModal(false)}
        okText={editingTa ? 'Guardar' : 'Crear'}
        confirmLoading={savingTa}
        width={440}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={taForm.nombre} onChange={e => setTaForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={taForm.descripcion} onChange={e => setTaForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          <div>
            <label className={labelClass}>Precio unitario (Gs.)</label>
            <input type="number" min={0} step={1000} value={taForm.precio_unitario} onChange={e => setTaForm(f => ({ ...f, precio_unitario: e.target.value }))} className={inputClass} />
          </div>
          <div className="flex flex-col gap-3">
            {toggleSwitch(taForm.incluye_plato_principal, v => setTaForm(f => ({ ...f, incluye_plato_principal: v })), 'Incluye plato principal')}
            {toggleSwitch(taForm.incluye_postre, v => setTaForm(f => ({ ...f, incluye_postre: v })), 'Incluye postre')}
            {toggleSwitch(taForm.incluye_bebida, v => setTaForm(f => ({ ...f, incluye_bebida: v })), 'Incluye bebida')}
            {toggleSwitch(taForm.activo, v => setTaForm(f => ({ ...f, activo: v })), 'Activo')}
          </div>
        </div>
      </Modal>

      {/* ── Plan Almuerzo modal ─────────────────────────────────────── */}
      <Modal
        open={paModal}
        title={editingPa ? 'Editar Plan de Almuerzo' : 'Nuevo Plan de Almuerzo'}
        onOk={savePa}
        onCancel={() => setPaModal(false)}
        okText={editingPa ? 'Guardar' : 'Crear'}
        confirmLoading={savingPa}
        width={480}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={paForm.nombre} onChange={e => setPaForm(f => ({ ...f, nombre: e.target.value }))} className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Tipo</label>
              <select value={paForm.tipo} onChange={e => setPaForm(f => ({ ...f, tipo: e.target.value as 'CANTIDAD' | 'SIN_LIMITE' }))} className={inputClass}>
                <option value="CANTIDAD">Por cantidad</option>
                <option value="SIN_LIMITE">Sin límite</option>
              </select>
            </div>
            <div>
              <label className={labelClass}>Precio mensual (Gs.)</label>
              <input type="number" min={0} step={1000} value={paForm.precio_mensual} onChange={e => setPaForm(f => ({ ...f, precio_mensual: e.target.value }))} className={inputClass} />
            </div>
          </div>
          {paForm.tipo === 'CANTIDAD' && (
            <div>
              <label className={labelClass}>Cantidad almuerzos/mes</label>
              <input type="number" min={1} value={paForm.cantidad_almuerzos_mes} onChange={e => setPaForm(f => ({ ...f, cantidad_almuerzos_mes: e.target.value }))} className={inputClass} />
            </div>
          )}
          <div>
            <label className={labelClass}>Días de semana incluidos</label>
            <div className="flex flex-wrap gap-2 mt-1">
              {DIAS_SEMANA.map((dia, i) => {
                const checked = paForm.dias_semana_incluidos.includes(i)
                return (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setPaForm(f => ({
                      ...f,
                      dias_semana_incluidos: checked
                        ? f.dias_semana_incluidos.filter(d => d !== i)
                        : [...f.dias_semana_incluidos, i],
                    }))}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-colors cursor-pointer ${
                      checked ? 'bg-green-500 text-white border-green-500' : 'bg-white text-slate-600 border-slate-200 hover:border-green-400'
                    }`}
                  >
                    {dia}
                  </button>
                )
              })}
            </div>
          </div>
          {toggleSwitch(paForm.activo, v => setPaForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>

      {/* ── Unidad Medida modal ─────────────────────────────────────── */}
      <Modal
        open={umModal}
        title={editingUm ? 'Editar Unidad de Medida' : 'Nueva Unidad de Medida'}
        onOk={saveUm}
        onCancel={() => setUmModal(false)}
        okText={editingUm ? 'Guardar' : 'Crear'}
        confirmLoading={savingUm}
        width={400}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={umForm.nombre} onChange={e => setUmForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Kilogramo" className={inputClass} />
          </div>
          <div>
            <label className={labelClass}>Abreviatura *</label>
            <input value={umForm.abreviatura} onChange={e => setUmForm(f => ({ ...f, abreviatura: e.target.value }))} placeholder="kg" className={inputClass} />
          </div>
          {toggleSwitch(umForm.activo, v => setUmForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>

      {/* ── Alérgeno modal ──────────────────────────────────────────── */}
      <Modal
        open={alModal}
        title={editingAl ? 'Editar Alérgeno' : 'Nuevo Alérgeno'}
        onOk={saveAl}
        onCancel={() => setAlModal(false)}
        okText={editingAl ? 'Guardar' : 'Crear'}
        confirmLoading={savingAl}
        width={460}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nombre *</label>
              <input value={alForm.nombre} onChange={e => setAlForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Gluten" className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Icono (emoji)</label>
              <input value={alForm.icono} onChange={e => setAlForm(f => ({ ...f, icono: e.target.value }))} placeholder="🌾" className={inputClass} />
            </div>
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea value={alForm.descripcion} onChange={e => setAlForm(f => ({ ...f, descripcion: e.target.value }))} rows={2} className={`${inputClass} resize-none`} />
          </div>
          <div>
            <label className={labelClass}>Severidad</label>
            <select value={alForm.severidad} onChange={e => setAlForm(f => ({ ...f, severidad: e.target.value as 'BAJA' | 'MEDIA' | 'ALTA' | 'CRITICA' }))} className={inputClass}>
              <option value="BAJA">Baja</option>
              <option value="MEDIA">Media</option>
              <option value="ALTA">Alta</option>
              <option value="CRITICA">Crítica</option>
            </select>
          </div>
          <div>
            <label className={labelClass}>Palabras clave (separadas por coma)</label>
            <input value={alForm.palabras_clave} onChange={e => setAlForm(f => ({ ...f, palabras_clave: e.target.value }))} placeholder="trigo, harina, cebada" className={inputClass} />
          </div>
          {toggleSwitch(alForm.activo, v => setAlForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>

      {/* ── Impuesto modal ──────────────────────────────────────────── */}
      <Modal
        open={impModal}
        title={editingImp ? 'Editar Impuesto' : 'Nuevo Impuesto'}
        onOk={saveImp}
        onCancel={() => setImpModal(false)}
        okText={editingImp ? 'Guardar' : 'Crear'}
        confirmLoading={savingImp}
        width={440}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nombre *</label>
              <input value={impForm.nombre} onChange={e => setImpForm(f => ({ ...f, nombre: e.target.value }))} placeholder="IVA 10%" className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Porcentaje (%)</label>
              <input type="number" min={0} max={100} step={0.5} value={impForm.porcentaje} onChange={e => setImpForm(f => ({ ...f, porcentaje: e.target.value }))} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Vigente desde</label>
              <input type="date" value={impForm.vigente_desde} onChange={e => setImpForm(f => ({ ...f, vigente_desde: e.target.value }))} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Vigente hasta</label>
              <input type="date" value={impForm.vigente_hasta} onChange={e => setImpForm(f => ({ ...f, vigente_hasta: e.target.value }))} className={inputClass} />
            </div>
          </div>
          {toggleSwitch(impForm.activo, v => setImpForm(f => ({ ...f, activo: v })), 'Activo')}
        </div>
      </Modal>
    </div>
  )
}
