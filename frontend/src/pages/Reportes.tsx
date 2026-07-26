import { useState } from 'react'
import {
  BarChart2, Trophy, UserCheck, Users, CreditCard, ShoppingBag,
  Package, UtensilsCrossed, FileText, ShoppingCart, AlertTriangle,
  Search, LogIn, Shield, DollarSign,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { type TabKey } from './reportes/shared'
import TabVentas from './reportes/TabVentas'
import TabProductos from './reportes/TabProductos'
import TabCajeros from './reportes/TabCajeros'
import TabCuentaCorriente from './reportes/TabCuentaCorriente'
import TabTarjetas from './reportes/TabTarjetas'
import TabConsumo from './reportes/TabConsumo'
import TabStock from './reportes/TabStock'
import TabAlmuerzos from './reportes/TabAlmuerzos'
import TabNotasCredito from './reportes/TabNotasCredito'
import TabAgingProveedores from './reportes/TabAgingProveedores'
import TabComprasProveedores from './reportes/TabComprasProveedores'
import TabDiferenciasCaja from './reportes/TabDiferenciasCaja'
import TabMediosPago from './reportes/TabMediosPago'
import TabConsumoGrado from './reportes/TabConsumoGrado'
import TabCobranzaAlmuerzos from './reportes/TabCobranzaAlmuerzos'
import TabAuditoria from './reportes/TabAuditoria'
import TabIntentosLogin from './reportes/TabIntentosLogin'
import TabPersonalInactivo from './reportes/TabPersonalInactivo'

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: 'ventas',              label: 'Ventas y Cierres',   icon: <BarChart2 className="w-4 h-4" /> },
  { key: 'productos',           label: 'Productos',           icon: <Trophy className="w-4 h-4" /> },
  { key: 'cajeros',             label: 'Cajeros',             icon: <UserCheck className="w-4 h-4" /> },
  { key: 'cuenta_corriente',    label: 'Cuenta Corriente',    icon: <Users className="w-4 h-4" /> },
  { key: 'tarjetas',            label: 'Tarjetas',            icon: <CreditCard className="w-4 h-4" /> },
  { key: 'consumo',             label: 'Consumo',             icon: <ShoppingBag className="w-4 h-4" /> },
  { key: 'stock',               label: 'Inventario',          icon: <Package className="w-4 h-4" /> },
  { key: 'almuerzos',           label: 'Almuerzos',           icon: <UtensilsCrossed className="w-4 h-4" /> },
  { key: 'notas_credito',       label: 'Notas de Crédito',    icon: <FileText className="w-4 h-4" /> },
  { key: 'aging_proveedores',   label: 'Aging Proveedores',   icon: <ShoppingCart className="w-4 h-4" /> },
  { key: 'compras_proveedores', label: 'Compras',             icon: <ShoppingBag className="w-4 h-4" /> },
  { key: 'diferencias_caja',    label: 'Diferencias Caja',    icon: <AlertTriangle className="w-4 h-4" /> },
  { key: 'medios_pago',         label: 'Medios de Pago',      icon: <CreditCard className="w-4 h-4" /> },
  { key: 'consumo_grado',       label: 'Consumo por Grado',   icon: <UtensilsCrossed className="w-4 h-4" /> },
  { key: 'cobranza_almuerzos',  label: 'Cobranza Almuerzos',  icon: <DollarSign className="w-4 h-4" /> },
  { key: 'auditoria',           label: 'Auditoría',           icon: <Shield className="w-4 h-4" /> },
  { key: 'intentos_login',      label: 'Intentos Login',      icon: <LogIn className="w-4 h-4" /> },
  { key: 'personal_inactivo',   label: 'Personal Inactivo',   icon: <Search className="w-4 h-4" /> },
]

export default function Reportes() {
  const { t } = useTranslation()
  const [tab, setTab] = useState<TabKey>('ventas')

  const tabClass = (k: TabKey) =>
    `flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
      tab === k
        ? 'border-green-600 text-green-700'
        : 'border-transparent text-slate-500 hover:text-slate-700'
    }`

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{t('reportes.title')}</h1>
        <p className="text-base text-slate-500 mt-0.5">{t('reportes.subtitle')}</p>
      </div>

      <div className="border-b border-slate-200 overflow-x-auto">
        <div className="flex gap-0 min-w-max">
          {TABS.map(({ key, label, icon }) => (
            <button key={key} onClick={() => setTab(key)} className={tabClass(key)}>
              {icon}{label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {tab === 'ventas'              && <TabVentas />}
        {tab === 'productos'           && <TabProductos />}
        {tab === 'cajeros'             && <TabCajeros />}
        {tab === 'cuenta_corriente'    && <TabCuentaCorriente />}
        {tab === 'tarjetas'            && <TabTarjetas />}
        {tab === 'consumo'             && <TabConsumo />}
        {tab === 'stock'               && <TabStock />}
        {tab === 'almuerzos'           && <TabAlmuerzos />}
        {tab === 'notas_credito'       && <TabNotasCredito />}
        {tab === 'aging_proveedores'   && <TabAgingProveedores />}
        {tab === 'compras_proveedores' && <TabComprasProveedores />}
        {tab === 'diferencias_caja'    && <TabDiferenciasCaja />}
        {tab === 'medios_pago'         && <TabMediosPago />}
        {tab === 'consumo_grado'       && <TabConsumoGrado />}
        {tab === 'cobranza_almuerzos'  && <TabCobranzaAlmuerzos />}
        {tab === 'auditoria'           && <TabAuditoria />}
        {tab === 'intentos_login'      && <TabIntentosLogin />}
        {tab === 'personal_inactivo'   && <TabPersonalInactivo />}
      </div>
    </div>
  )
}
