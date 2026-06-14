import { useCallback, useState } from 'react'
import toast from 'react-hot-toast'
import {
  Settings, Tag, ListOrdered, CreditCard, Users,
  GraduationCap, Building2, History, Shield,
  UtensilsCrossed, Calendar, Ruler, AlertTriangle, Percent, Trash2,
} from 'lucide-react'
import api from '../services/api'
import Button from '../components/ui/Button'
import Modal from '../components/ui/Modal'
import { type DeleteTarget } from './configuracion/helpers'
import TabCategorias from './configuracion/TabCategorias'
import TabTiposCliente from './configuracion/TabTiposCliente'
import TabListasPrecio from './configuracion/TabListasPrecio'
import TabMediosPago from './configuracion/TabMediosPago'
import TabGrados from './configuracion/TabGrados'
import TabDatosEmpresa from './configuracion/TabDatosEmpresa'
import TabHistorialPrecios from './configuracion/TabHistorialPrecios'
import TabSeguridad from './configuracion/TabSeguridad'
import TabTiposAlmuerzo from './configuracion/TabTiposAlmuerzo'
import TabPlanesAlmuerzo from './configuracion/TabPlanesAlmuerzo'
import TabUnidadesMedida from './configuracion/TabUnidadesMedida'
import TabAlergenos from './configuracion/TabAlergenos'
import TabImpuestos from './configuracion/TabImpuestos'

type TabKey =
  | 'categorias' | 'tipos_cliente' | 'listas_precio' | 'medios_pago'
  | 'grados' | 'datos_empresa' | 'historial_precios' | 'seguridad'
  | 'tipos_almuerzo' | 'planes_almuerzo' | 'unidades_medida' | 'alergenos' | 'impuestos'

const TABS: { key: TabKey; label: string; icon: typeof Settings }[] = [
  { key: 'categorias',        label: 'Categorías',       icon: Tag },
  { key: 'tipos_cliente',     label: 'Tipos de Cliente', icon: Users },
  { key: 'listas_precio',     label: 'Listas de Precio', icon: ListOrdered },
  { key: 'medios_pago',       label: 'Medios de Pago',   icon: CreditCard },
  { key: 'grados',            label: 'Grados',           icon: GraduationCap },
  { key: 'datos_empresa',     label: 'Empresa',          icon: Building2 },
  { key: 'historial_precios', label: 'Hist. Precios',    icon: History },
  { key: 'seguridad',         label: 'Seguridad',        icon: Shield },
  { key: 'tipos_almuerzo',    label: 'Tipos Almuerzo',   icon: UtensilsCrossed },
  { key: 'planes_almuerzo',   label: 'Planes Almuerzo',  icon: Calendar },
  { key: 'unidades_medida',   label: 'Unidades Medida',  icon: Ruler },
  { key: 'alergenos',         label: 'Alérgenos',        icon: AlertTriangle },
  { key: 'impuestos',         label: 'Impuestos',        icon: Percent },
]

export default function Configuracion() {
  const [tab, setTab] = useState<TabKey>('categorias')
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null)
  const [deleting, setDeleting] = useState(false)

  const confirmDelete = useCallback((target: DeleteTarget) => {
    setDeleteTarget(target)
  }, [])

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await api.delete(deleteTarget.url)
      toast.success(`"${deleteTarget.label}" eliminado`)
      setDeleteTarget(null)
      deleteTarget.reloadFn()
    } catch {
      toast.error('No se pudo eliminar el registro')
    } finally {
      setDeleting(false)
    }
  }, [deleteTarget])

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Configuración</h1>
        <p className="text-base text-slate-500 mt-0.5">Administración de catálogos del sistema</p>
      </div>

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

      <div>
        {tab === 'categorias'        && <TabCategorias      onDelete={confirmDelete} />}
        {tab === 'tipos_cliente'     && <TabTiposCliente    onDelete={confirmDelete} />}
        {tab === 'listas_precio'     && <TabListasPrecio    onDelete={confirmDelete} />}
        {tab === 'medios_pago'       && <TabMediosPago      onDelete={confirmDelete} />}
        {tab === 'grados'            && <TabGrados          onDelete={confirmDelete} />}
        {tab === 'tipos_almuerzo'    && <TabTiposAlmuerzo   onDelete={confirmDelete} />}
        {tab === 'planes_almuerzo'   && <TabPlanesAlmuerzo  onDelete={confirmDelete} />}
        {tab === 'unidades_medida'   && <TabUnidadesMedida  onDelete={confirmDelete} />}
        {tab === 'alergenos'         && <TabAlergenos       onDelete={confirmDelete} />}
        {tab === 'impuestos'         && <TabImpuestos       onDelete={confirmDelete} />}
        {tab === 'datos_empresa'     && <TabDatosEmpresa />}
        {tab === 'historial_precios' && <TabHistorialPrecios />}
        {tab === 'seguridad'         && <TabSeguridad />}
      </div>

      <Modal
        open={!!deleteTarget}
        title="Confirmar eliminación"
        onOk={handleDelete}
        onCancel={() => setDeleteTarget(null)}
        okText="Eliminar"
        confirmLoading={deleting}
        width={400}
      >
        <div className="flex items-start gap-3 py-1">
          <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <Trash2 className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <p className="text-sm text-slate-700">
              ¿Eliminar <strong className="text-slate-900">"{deleteTarget?.label}"</strong>?
            </p>
            <p className="text-xs text-slate-400 mt-1">Esta acción no se puede deshacer.</p>
          </div>
        </div>
      </Modal>
    </div>
  )
}
