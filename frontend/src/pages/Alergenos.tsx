import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { AlertTriangle, Plus, Edit2, Leaf } from 'lucide-react'
import api from '../services/api'
import { useCatalogoStore } from '../store/catalogoStore'
import Badge, { type BadgeColor } from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import Modal from '../components/ui/Modal'
import Combobox from '../components/ui/Combobox'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Alergeno {
  id: number
  nombre: string
  descripcion: string | null
  severidad: string
  icono: string | null
  activo: boolean
}

interface ProductoAlergeno {
  id: number
  producto: number
  alergeno: number
  producto_nombre: string
  alergeno_nombre: string
  contiene: boolean
}

interface Producto {
  id: number
  descripcion: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const SEVERIDAD_COLOR: Record<string, BadgeColor> = {
  BAJA: 'green',
  MEDIA: 'yellow',
  ALTA: 'orange',
  CRITICA: 'red',
}

type TabKey = 'alergenos' | 'asignacion'

// ─── Helpers ──────────────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  const e = err as { response?: { data?: unknown } }
  const d = e?.response?.data
  if (!d) return 'Error inesperado'
  if (typeof d === 'string') return d
  if (typeof d === 'object') {
    const obj = d as Record<string, unknown>
    if (obj.detail) return String(obj.detail)
    const first = Object.values(obj)[0]
    if (Array.isArray(first)) return String(first[0])
    return JSON.stringify(d)
  }
  return 'Error inesperado'
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function Alergenos() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<TabKey>('alergenos')
  const getProductos = useCatalogoStore(s => s.getProductos)
  const [productos, setProductos] = useState<Producto[]>([])

  useEffect(() => {
    getProductos().then(p => setProductos(p as Producto[])).catch(() => {})
  }, [getProductos])

  // ── Alérgenos CRUD ────────────────────────────────────────────────
  const [alergenos, setAlergenos] = useState<Alergeno[]>([])
  const [loadingAlg, setLoadingAlg] = useState(false)
  const [totalAlg, setTotalAlg] = useState(0)
  const [pageAlg, setPageAlg] = useState(1)
  const [algModalOpen, setAlgModalOpen] = useState(false)
  const [editingAlg, setEditingAlg] = useState<Alergeno | null>(null)
  const [savingAlg, setSavingAlg] = useState(false)
  const [algForm, setAlgForm] = useState({ nombre: '', descripcion: '', severidad: 'MEDIA', icono: '', activo: true })

  const loadAlergenos = useCallback(async (p: number) => {
    setLoadingAlg(true)
    try {
      const { data } = await api.get('/almuerzos/alergenos/', { params: { page: p, page_size: 15 } })
      setAlergenos(data.results ?? [])
      setTotalAlg(data.count ?? 0)
    } catch { toast.error('Error al cargar alérgenos') }
    finally { setLoadingAlg(false) }
  }, [])

  useEffect(() => { loadAlergenos(1) }, [loadAlergenos])

  const openCreateAlg = () => {
    setEditingAlg(null)
    setAlgForm({ nombre: '', descripcion: '', severidad: 'MEDIA', icono: '', activo: true })
    setAlgModalOpen(true)
  }
  const openEditAlg = (a: Alergeno) => {
    setEditingAlg(a)
    setAlgForm({ nombre: a.nombre, descripcion: a.descripcion ?? '', severidad: a.severidad, icono: a.icono ?? '', activo: a.activo })
    setAlgModalOpen(true)
  }
  const handleSaveAlg = async () => {
    if (!algForm.nombre) { toast.error('El nombre es obligatorio'); return }
    setSavingAlg(true)
    try {
      if (editingAlg) {
        await api.put(`/almuerzos/alergenos/${editingAlg.id}/`, algForm)
        toast.success('Alérgeno actualizado')
      } else {
        await api.post('/almuerzos/alergenos/', algForm)
        toast.success('Alérgeno creado')
      }
      setAlgModalOpen(false)
      loadAlergenos(pageAlg)
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingAlg(false) }
  }

  // ── Asignación producto-alérgeno ──────────────────────────────────
  const [asignaciones, setAsignaciones] = useState<ProductoAlergeno[]>([])
  const [loadingAsig, setLoadingAsig] = useState(false)
  const [totalAsig, setTotalAsig] = useState(0)
  const [pageAsig, setPageAsig] = useState(1)
  const [asigModalOpen, setAsigModalOpen] = useState(false)
  const [savingAsig, setSavingAsig] = useState(false)
  const [asigForm, setAsigForm] = useState<{ producto: number | null; alergeno: number | null; contiene: boolean }>({ producto: null, alergeno: null, contiene: true })

  const loadAsignaciones = useCallback(async (p: number) => {
    setLoadingAsig(true)
    try {
      const { data } = await api.get('/almuerzos/productos-alergenos/', { params: { page: p, page_size: 15 } })
      setAsignaciones(data.results ?? [])
      setTotalAsig(data.count ?? 0)
    } catch { toast.error('Error al cargar asignaciones') }
    finally { setLoadingAsig(false) }
  }, [])

  useEffect(() => { if (tab === 'asignacion') loadAsignaciones(1) }, [tab, loadAsignaciones])

  const handleSaveAsig = async () => {
    if (!asigForm.producto || !asigForm.alergeno) { toast.error('Seleccioná producto y alérgeno'); return }
    setSavingAsig(true)
    try {
      await api.post('/almuerzos/productos-alergenos/', asigForm)
      toast.success('Asignación creada')
      setAsigModalOpen(false)
      loadAsignaciones(pageAsig)
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSavingAsig(false) }
  }

  const handleDeleteAsig = async (id: number) => {
    try {
      await api.delete(`/almuerzos/productos-alergenos/${id}/`)
      toast.success('Asignación eliminada')
      loadAsignaciones(pageAsig)
    } catch { toast.error('Error al eliminar') }
  }

  // ── Columns ───────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const colsAlg: Column<Alergeno>[] = [
    {
      title: t('alergenos.colAlergeno'),
      key: 'nombre',
      render: (_, r) => (
        <div className="flex items-center gap-2">
          {r.icono && <span className="text-xl">{r.icono}</span>}
          <p className="text-sm font-medium text-slate-800">{r.nombre}</p>
        </div>
      ),
    },
    { title: t('alergenos.colSeveridad'), key: 'severidad', render: (_, r) => <Badge color={SEVERIDAD_COLOR[r.severidad] ?? 'default'}>{r.severidad}</Badge> },
    { title: t('common.description'), key: 'desc', render: (_, r) => <span className="text-xs text-slate-500">{r.descripcion || '—'}</span> },
    { title: t('common.status'), key: 'activo', render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? t('common.active') : t('common.inactive')}</Badge> },
    {
      title: '', key: 'acc', width: 80,
      render: (_, r) => (
        <Button size="sm" variant="secondary" onClick={() => openEditAlg(r)}>
          <Edit2 className="w-3.5 h-3.5" /> {t('common.edit')}
        </Button>
      ),
    },
  ]

  const colsAsig: Column<ProductoAlergeno>[] = [
    { title: t('alergenos.colProducto'), key: 'prod', render: (_, r) => <span className="text-sm font-medium text-slate-800">{r.producto_nombre}</span> },
    { title: t('alergenos.colAlergeno'), key: 'alg', render: (_, r) => <span className="text-sm text-slate-700">{r.alergeno_nombre}</span> },
    {
      title: t('alergenos.colTipo'), key: 'contiene',
      render: (_, r) => <Badge color={r.contiene ? 'red' : 'orange'}>{r.contiene ? 'Contiene' : 'Trazas'}</Badge>,
    },
    {
      title: '', key: 'acc', width: 80,
      render: (_, r) => (
        <Button size="sm" variant="ghost" onClick={() => handleDeleteAsig(r.id)}>
          {t('common.delete')}
        </Button>
      ),
    },
  ]

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('alergenos.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('alergenos.subtitle')}</p>
        </div>
        {tab === 'alergenos' && (
          <Button variant="primary" onClick={openCreateAlg}>
            <Plus className="w-4 h-4" /> {t('alergenos.newAlergeno')}
          </Button>
        )}
        {tab === 'asignacion' && (
          <Button variant="primary" onClick={() => { setAsigForm({ producto: null, alergeno: null, contiene: true }); setAsigModalOpen(true) }}>
            <Plus className="w-4 h-4" /> {t('alergenos.asignar')}
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-0">
          {([['alergenos', t('alergenos.tabList'), Leaf], ['asignacion', t('alergenos.tabAsignacion'), AlertTriangle]] as const).map(([key, label, Icon]) => (
            <button key={key} type="button" onClick={() => setTab(key as TabKey)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'}`}>
              <Icon className="w-4 h-4" />{label}
            </button>
          ))}
        </div>
      </div>

      {/* Alérgenos table */}
      {tab === 'alergenos' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            <Table columns={colsAlg} dataSource={alergenos} rowKey="id" loading={loadingAlg}
              pageSize={15} page={pageAlg} total={totalAlg}
              onPageChange={p => { setPageAlg(p); loadAlergenos(p) }} />
          </div>
        </div>
      )}

      {/* Asignaciones table */}
      {tab === 'asignacion' && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <div className="p-1">
            <Table columns={colsAsig} dataSource={asignaciones} rowKey="id" loading={loadingAsig}
              pageSize={15} page={pageAsig} total={totalAsig}
              onPageChange={p => { setPageAsig(p); loadAsignaciones(p) }} />
          </div>
        </div>
      )}

      {/* Modal alérgeno */}
      <Modal open={algModalOpen} title={editingAlg ? t('alergenos.modalEdit') : t('alergenos.modalCreate')}
        onOk={handleSaveAlg} onCancel={() => setAlgModalOpen(false)}
        okText={editingAlg ? t('common.save') : t('common.create')} confirmLoading={savingAlg} width={480}>
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Nombre *</label>
              <input value={algForm.nombre} onChange={e => setAlgForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Ej: Gluten" className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Ícono (emoji)</label>
              <input value={algForm.icono} onChange={e => setAlgForm(f => ({ ...f, icono: e.target.value }))} placeholder="🌾" className={inputClass} />
            </div>
          </div>
          <div>
            <label className={labelClass}>Severidad</label>
            <select value={algForm.severidad} onChange={e => setAlgForm(f => ({ ...f, severidad: e.target.value }))} className={inputClass}>
              {['BAJA', 'MEDIA', 'ALTA', 'CRITICA'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Descripción</label>
            <textarea rows={2} value={algForm.descripcion} onChange={e => setAlgForm(f => ({ ...f, descripcion: e.target.value }))} placeholder="Opcional..." className={`${inputClass} resize-none`} />
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <div className="relative shrink-0">
              <input type="checkbox" className="sr-only peer" checked={algForm.activo} onChange={e => setAlgForm(f => ({ ...f, activo: e.target.checked }))} />
              <div className="w-9 h-5 bg-slate-200 rounded-full peer-checked:bg-green-500 transition-colors" />
              <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-4" />
            </div>
            <span className="text-sm text-slate-700">Activo</span>
          </label>
        </div>
      </Modal>

      {/* Modal asignación */}
      <Modal open={asigModalOpen} title={t('alergenos.modalAssign')}
        onOk={handleSaveAsig} onCancel={() => setAsigModalOpen(false)}
        okText={t('alergenos.asignar')} confirmLoading={savingAsig} width={440}>
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Producto *</label>
            <Combobox
              options={productos.map(p => ({ value: p.id, label: p.descripcion }))}
              value={asigForm.producto ?? undefined}
              onChange={v => setAsigForm(f => ({ ...f, producto: v as number }))}
              filterLocal placeholder="Buscar producto..."
            />
          </div>
          <div>
            <label className={labelClass}>Alérgeno *</label>
            <select value={asigForm.alergeno ?? ''} onChange={e => setAsigForm(f => ({ ...f, alergeno: Number(e.target.value) || null }))} className={inputClass}>
              <option value="">— Elegí un alérgeno —</option>
              {alergenos.map(a => <option key={a.id} value={a.id}>{a.icono ? `${a.icono} ` : ''}{a.nombre}</option>)}
            </select>
          </div>
          <div>
            <label className={labelClass}>Tipo</label>
            <select value={String(asigForm.contiene)} onChange={e => setAsigForm(f => ({ ...f, contiene: e.target.value === 'true' }))} className={inputClass}>
              <option value="true">{t('alergenos.optContiene')}</option>
              <option value="false">{t('alergenos.optTrazas')}</option>
            </select>
          </div>
        </div>
      </Modal>
    </div>
  )
}
