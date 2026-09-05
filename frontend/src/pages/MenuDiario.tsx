import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Plus, Edit, AlertCircle, ChefHat, Trash2, AlertTriangle } from 'lucide-react'
import api from '../services/api'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import Table, { type Column } from '../components/ui/Table'
import Badge from '../components/ui/Badge'
import Combobox from '../components/ui/Combobox'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface DetalleMenu {
  id_detalle_menu: number
  producto: number
  producto_nombre: string
  curso: string
  curso_display: string
  cantidad: number
  es_opcional: boolean
}

interface MenuDiario {
  id_menu: number
  fecha: string
  plato_principal: string
  guarnicion: string
  postre: string
  bebida: string
  descripcion: string
  activo: boolean
  detalles: DetalleMenu[]
  tiene_alergenos: boolean
}

interface MenuFormFields {
  fecha: string
  plato_principal: string
  guarnicion: string
  postre: string
  bebida: string
  descripcion: string
}

interface Producto {
  id_producto: number
  descripcion: string
}

interface DetalleItem {
  producto: Producto | null
  curso: string
  cantidad: number
  es_opcional: boolean
}

const CURSOS = [
  { value: 'ENTRADA', label: 'Entrada' },
  { value: 'PLATO_PRINCIPAL', label: 'Plato principal' },
  { value: 'GUARNICION', label: 'Guarnición' },
  { value: 'POSTRE', label: 'Postre' },
  { value: 'BEBIDA', label: 'Bebida' },
  { value: 'EXTRA', label: 'Extra' },
]

const DETALLE_ITEM_EMPTY: DetalleItem = { producto: null, curso: 'PLATO_PRINCIPAL', cantidad: 1, es_opcional: false }

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatFecha(iso: string) {
  return new Date(iso + 'T00:00:00').toLocaleDateString('es-PY', {
    weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

function todayIso() {
  return new Date().toISOString().split('T')[0]
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function MenuDiario() {
  const { t } = useTranslation()
  const [menus, setMenus] = useState<MenuDiario[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [menuHoy, setMenuHoy] = useState<MenuDiario | null | false>(null) // null=loading, false=no existe
  const [modalOpen, setModalOpen] = useState(false)
  const [editingMenu, setEditingMenu] = useState<MenuDiario | null>(null)
  const [saving, setSaving] = useState(false)
  const [togglingId, setTogglingId] = useState<number | null>(null)
  const [productos, setProductos] = useState<Producto[]>([])
  const [detalleItems, setDetalleItems] = useState<DetalleItem[]>([])

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<MenuFormFields>()

  // ── Load list ──────────────────────────────────────────────────────────────
  const loadMenus = useCallback(async (p: number) => {
    setLoading(true)
    try {
      const { data } = await api.get('/almuerzos/menu/', {
        params: { page: p, page_size: 15, ordering: '-fecha', activo: true },
      })
      setMenus(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      toast.error('Error al cargar menús')
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Load today ─────────────────────────────────────────────────────────────
  const loadHoy = useCallback(async () => {
    setMenuHoy(null)
    try {
      const { data } = await api.get('/almuerzos/menu/hoy/')
      setMenuHoy(data)
    } catch {
      setMenuHoy(false)
    }
  }, [])

  // ── Load productos (para vincular al menú) ────────────────────────────────
  const loadProductos = useCallback(async () => {
    try {
      const { data } = await api.get('/productos/productos/', {
        params: { activo: true, page_size: 200, ordering: 'descripcion' },
      })
      setProductos(data.results ?? data ?? [])
    } catch { /* el picker queda vacío, no bloquea la pantalla */ }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadMenus(1)
    loadHoy()
    loadProductos()
  }, [loadMenus, loadHoy, loadProductos])

  // ── Open modal ─────────────────────────────────────────────────────────────
  const openCreate = (fecha?: string) => {
    setEditingMenu(null)
    reset({
      fecha: fecha ?? todayIso(),
      plato_principal: '',
      guarnicion: '',
      postre: '',
      bebida: '',
      descripcion: '',
    })
    setDetalleItems([])
    setModalOpen(true)
  }

  const openEdit = (menu: MenuDiario) => {
    setEditingMenu(menu)
    reset({
      fecha: menu.fecha,
      plato_principal: menu.plato_principal,
      guarnicion: menu.guarnicion,
      postre: menu.postre,
      bebida: menu.bebida,
      descripcion: menu.descripcion,
    })
    setDetalleItems((menu.detalles ?? []).map(d => ({
      producto: productos.find(p => p.id_producto === d.producto) ?? { id_producto: d.producto, descripcion: d.producto_nombre },
      curso: d.curso,
      cantidad: d.cantidad,
      es_opcional: d.es_opcional,
    })))
    setModalOpen(true)
  }

  // ── Productos del menú ─────────────────────────────────────────────────────
  const agregarDetalleItem = () => setDetalleItems(prev => [...prev, { ...DETALLE_ITEM_EMPTY }])
  const quitarDetalleItem = (idx: number) => setDetalleItems(prev => prev.filter((_, i) => i !== idx))
  const actualizarDetalleItem = (idx: number, patch: Partial<DetalleItem>) =>
    setDetalleItems(prev => prev.map((it, i) => (i === idx ? { ...it, ...patch } : it)))

  const sincronizarDetalles = useCallback(async (idMenu: number) => {
    const items = detalleItems.filter(i => i.producto)
    try {
      if (editingMenu) {
        const { data } = await api.get('/almuerzos/detalle-menu/', { params: { menu: idMenu, page_size: 100 } })
        const existentes: DetalleMenu[] = data.results ?? data ?? []
        await Promise.allSettled(existentes.map(d => api.delete(`/almuerzos/detalle-menu/${d.id_detalle_menu}/`)))
      }
      await Promise.allSettled(items.map(i => api.post('/almuerzos/detalle-menu/', {
        menu: idMenu,
        producto: i.producto!.id_producto,
        curso: i.curso,
        cantidad: i.cantidad,
        es_opcional: i.es_opcional,
      })))
    } catch { /* el menú ya se guardó — los productos se pueden reintentar editando */ }
  }, [detalleItems, editingMenu])

  // ── Save ───────────────────────────────────────────────────────────────────
  const onSubmit = handleSubmit(async (fields) => {
    setSaving(true)
    try {
      let idMenu = editingMenu?.id_menu
      if (editingMenu) {
        await api.put(`/almuerzos/menu/${editingMenu.id_menu}/`, fields)
        toast.success('Menú actualizado')
      } else {
        const { data } = await api.post('/almuerzos/menu/', fields)
        idMenu = data.id_menu
        toast.success('Menú publicado')
      }
      if (idMenu) await sincronizarDetalles(idMenu)
      setModalOpen(false)
      loadMenus(page)
      loadHoy()
    } catch (err: unknown) {
      const e = err as { response?: { data?: unknown } }
      const d = e?.response?.data
      if (d && typeof d === 'object') {
        const msgs = Object.values(d as Record<string, string[]>).flat()
        toast.error(msgs[0] ?? 'Error al guardar')
      } else {
        toast.error('Error al guardar el menú')
      }
    } finally {
      setSaving(false)
    }
  })

  // ── Toggle activo ──────────────────────────────────────────────────────────
  const toggleActivo = async (menu: MenuDiario) => {
    setTogglingId(menu.id_menu)
    try {
      await api.patch(`/almuerzos/menu/${menu.id_menu}/`, { activo: !menu.activo })
      toast.success(menu.activo ? 'Menú archivado' : 'Menú activado')
      loadMenus(page)
      loadHoy()
    } catch {
      toast.error('Error al actualizar el menú')
    } finally {
      setTogglingId(null)
    }
  }

  // ── Columns ────────────────────────────────────────────────────────────────
  const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors w-full'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  const cols: Column<MenuDiario>[] = [
    {
      title: t('menuDiario.colFecha'),
      key: 'fecha',
      render: (_, r) => <span className="text-sm font-medium text-slate-800">{formatFecha(r.fecha)}</span>,
    },
    {
      title: t('menuDiario.colPlato'),
      key: 'plato',
      render: (_, r) => (
        <div className="flex items-center gap-2">
          <span className="text-sm text-slate-700">{r.plato_principal}</span>
          {r.tiene_alergenos && (
            <span title="Contiene productos con alérgenos registrados">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            </span>
          )}
        </div>
      ),
    },
    {
      title: t('menuDiario.colGuarn'),
      key: 'extras',
      render: (_, r) => (
        <div>
          {r.guarnicion && <p className="text-xs text-slate-600">{r.guarnicion}</p>}
          {r.postre && <p className="text-sm text-slate-400">{r.postre}</p>}
        </div>
      ),
    },
    {
      title: t('common.status'),
      key: 'estado',
      width: 90,
      render: (_, r) => <Badge color={r.activo ? 'green' : 'default'}>{r.activo ? t('common.active') : 'Archivado'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      width: 160,
      render: (_, r) => (
        <div className="flex items-center gap-1.5">
          <Button size="sm" variant="secondary" onClick={() => openEdit(r)}>
            <Edit className="w-3.5 h-3.5" />
            {t('common.edit')}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => toggleActivo(r)}
            disabled={togglingId === r.id_menu}
          >
            {r.activo ? t('menuDiario.archivar') : t('menuDiario.activar')}
          </Button>
        </div>
      ),
    },
  ]

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="p-4 md:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('menuDiario.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('menuDiario.subtitle')}</p>
        </div>
        <Button variant="primary" onClick={() => openCreate()}>
          <Plus className="w-4 h-4" />
          {t('menuDiario.newMenu')}
        </Button>
      </div>

      {/* Hoy card */}
      {menuHoy === null ? null : menuHoy === false ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-2xl px-5 py-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-500 shrink-0" />
            <p className="text-sm font-medium text-yellow-800">{t('menuDiario.noMenuHoy')}</p>
          </div>
          <Button size="sm" variant="primary" onClick={() => openCreate(todayIso())}>
            <Plus className="w-3.5 h-3.5" />
            {t('menuDiario.publicarHoy')}
          </Button>
        </div>
      ) : (
        <div className="bg-green-50 border border-green-200 rounded-2xl px-5 py-4">
          <div className="flex items-center gap-2 mb-3">
            <ChefHat className="w-4 h-4 text-green-600" />
            <p className="text-xs font-semibold text-green-700 uppercase tracking-wide">{t('menuDiario.menuHoy')}</p>
            {menuHoy.tiene_alergenos && (
              <span className="flex items-center gap-1 text-amber-600 text-xs font-semibold bg-amber-100 border border-amber-200 rounded-full px-2 py-0.5">
                <AlertTriangle className="w-3 h-3" /> Contiene alérgenos
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: t('menuDiario.platoP'), value: menuHoy.plato_principal },
              { label: t('menuDiario.guarnicion'), value: menuHoy.guarnicion || '—' },
              { label: t('menuDiario.postre'), value: menuHoy.postre || '—' },
              { label: t('menuDiario.bebida'), value: menuHoy.bebida || '—' },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs text-green-600 font-medium">{label}</p>
                <p className="text-sm font-semibold text-slate-800 mt-0.5">{value}</p>
              </div>
            ))}
          </div>
          {menuHoy.descripcion && (
            <p className="text-xs text-slate-500 mt-3 border-t border-green-200 pt-3">{menuHoy.descripcion}</p>
          )}
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="p-1">
          <Table
            columns={cols}
            dataSource={menus}
            rowKey="id_menu"
            loading={loading}
            pageSize={15}
            page={page}
            total={total}
            onPageChange={p => { setPage(p); loadMenus(p) }}
          />
        </div>
      </div>

      {/* Modal */}
      <Modal
        open={modalOpen}
        title={editingMenu ? `${t('common.edit')} — ${formatFecha(editingMenu.fecha)}` : t('menuDiario.newMenu')}
        onOk={onSubmit}
        onCancel={() => setModalOpen(false)}
        okText={editingMenu ? t('common.save') : t('menuDiario.publicarHoy')}
        confirmLoading={saving}
        width={640}
      >
        <div className="space-y-4">
          <div>
            <label className={labelClass}>Fecha *</label>
            <input
              type="date"
              className={inputClass}
              {...register('fecha', { required: 'La fecha es obligatoria' })}
            />
            {errors.fecha && <p className="text-xs text-red-500 mt-1">{errors.fecha.message}</p>}
          </div>

          <div>
            <label className={labelClass}>Plato Principal *</label>
            <input
              placeholder="Ej: Milanesa con arroz"
              className={inputClass}
              {...register('plato_principal', { required: 'El plato principal es obligatorio' })}
            />
            {errors.plato_principal && (
              <p className="text-xs text-red-500 mt-1">{errors.plato_principal.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Guarnición</label>
              <input
                placeholder="Ej: Ensalada mixta"
                className={inputClass}
                {...register('guarnicion')}
              />
            </div>
            <div>
              <label className={labelClass}>Postre</label>
              <input
                placeholder="Ej: Fruta de estación"
                className={inputClass}
                {...register('postre')}
              />
            </div>
          </div>

          <div>
            <label className={labelClass}>Bebida</label>
            <input
              placeholder="Ej: Jugo de naranja"
              className={inputClass}
              {...register('bebida')}
            />
          </div>

          <div>
            <label className={labelClass}>Descripción / Notas</label>
            <textarea
              rows={2}
              placeholder="Información adicional, alérgenos, etc."
              className={`${inputClass} resize-none`}
              {...register('descripcion')}
            />
          </div>

          <div className="border-t border-slate-200 pt-4">
            <div className="flex items-center justify-between mb-1">
              <label className={`${labelClass} mb-0`}>Productos del menú</label>
              <Button size="sm" variant="ghost" onClick={agregarDetalleItem}>
                <Plus className="w-3.5 h-3.5" /> Agregar producto
              </Button>
            </div>
            <p className="text-xs text-slate-400 mb-3">
              Vincular productos del catálogo permite alertar automáticamente si un alumno
              con restricciones alérgicas intenta ingresar al comedor.
            </p>
            {detalleItems.length === 0 ? (
              <p className="text-xs text-slate-400 italic">Sin productos vinculados todavía.</p>
            ) : (
              <div className="space-y-2">
                {detalleItems.map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className="flex-1">
                      <Combobox
                        options={productos.map(p => ({ value: p.id_producto, label: p.descripcion }))}
                        value={item.producto?.id_producto}
                        onChange={(v) => actualizarDetalleItem(idx, {
                          producto: productos.find(p => p.id_producto === v) ?? null,
                        })}
                        filterLocal
                        placeholder="Buscar producto..."
                      />
                    </div>
                    <select
                      className={`${inputClass} w-40`}
                      value={item.curso}
                      onChange={e => actualizarDetalleItem(idx, { curso: e.target.value })}
                    >
                      {CURSOS.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                    <input
                      type="number"
                      min={0.001}
                      step="0.001"
                      className={`${inputClass} w-20`}
                      value={item.cantidad}
                      onChange={e => actualizarDetalleItem(idx, { cantidad: Number(e.target.value) || 1 })}
                    />
                    <label className="flex items-center gap-1 text-xs text-slate-500 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={item.es_opcional}
                        onChange={e => actualizarDetalleItem(idx, { es_opcional: e.target.checked })}
                      />
                      Opcional
                    </label>
                    <button
                      type="button"
                      onClick={() => quitarDetalleItem(idx)}
                      className="p-1.5 text-slate-400 hover:text-red-500 transition-colors cursor-pointer"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Modal>
    </div>
  )
}
