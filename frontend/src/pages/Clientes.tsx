import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { Banknote, Edit2, Mail, Phone, Plus, Search, Users } from 'lucide-react'
import api from '../services/api'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import ModalCliente from './clientes/ModalCliente'
import ModalHijos from './clientes/ModalHijos'
import ModalPagarCC from './clientes/ModalPagarCC'
import { formatGs, type Cliente, type TipoCliente, type ListaPrecio, type Ciudad } from './clientes/shared'

const PAGE_SIZE = 20

export default function Clientes() {
  const { t } = useTranslation()
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [tiposCliente, setTiposCliente] = useState<TipoCliente[]>([])
  const [listasPrecios, setListasPrecios] = useState<ListaPrecio[]>([])
  const [ciudades, setCiudades] = useState<Ciudad[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [filterActivo, setFilterActivo] = useState('')
  const [filterTipo, setFilterTipo] = useState('')

  const [clienteModal, setClienteModal] = useState<{ open: boolean; cliente: Cliente | null }>({ open: false, cliente: null })
  const [hijosModal, setHijosModal] = useState<{ open: boolean; cliente: Cliente | null }>({ open: false, cliente: null })
  const [pagarCCModal, setPagarCCModal] = useState<{ open: boolean; cliente: Cliente | null }>({ open: false, cliente: null })

  const searchTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestIdRef = useRef(0)

  useEffect(() => {
    api.get('/clientes/tipos-cliente/').then(({ data }) => setTiposCliente(data.results ?? data)).catch(() => toast.error('Error al cargar tipos de cliente'))
    api.get('/productos/listas-precio/').then(({ data }) => setListasPrecios(data.results ?? data)).catch(() => toast.error('Error al cargar listas de precio'))
    api.get('/clientes/ciudades/', { params: { page_size: 200 } }).then(({ data }) => setCiudades(data.results ?? data)).catch(() => toast.error('Error al cargar ciudades'))
  }, [])

  const loadClientes = useCallback(async () => {
    const requestId = ++requestIdRef.current
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page, page_size: PAGE_SIZE }
      if (search) params.search = search
      if (filterActivo) params.activo = filterActivo
      if (filterTipo) params.tipo_cliente = filterTipo
      const { data } = await api.get('/clientes/clientes/', { params })
      if (requestId !== requestIdRef.current) return
      setClientes(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (requestId !== requestIdRef.current) return
      toast.error('Error al cargar clientes')
    } finally {
      if (requestId === requestIdRef.current) setLoading(false)
    }
  }, [page, search, filterActivo, filterTipo])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadClientes()
  }, [loadClientes])

  function handleSearchChange(value: string) {
    setSearchInput(value)
    clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => { setPage(1); setSearch(value) }, 350)
  }

  function handleFilterChange(setter: (v: string) => void) {
    return (e: React.ChangeEvent<HTMLSelectElement>) => { setter(e.target.value); setPage(1) }
  }

  const columns = useMemo<Column<Cliente>[]>(() => [
    {
      title: 'RUC / CI',
      key: 'ruc_ci',
      dataIndex: 'ruc_ci',
      render: (v) => <span className="font-mono text-sm bg-slate-100 text-slate-600 px-2 py-0.5 rounded-lg">{v as string}</span>,
    },
    {
      title: 'Cliente',
      key: 'cliente',
      render: (_, r) => (
        <div>
          <p className="text-base font-semibold text-slate-800">{r.apellidos}, {r.nombres}</p>
          {r.tipo_cliente_nombre && <p className="text-sm text-slate-400 mt-0.5">{r.tipo_cliente_nombre}</p>}
        </div>
      ),
    },
    {
      title: 'Contacto',
      key: 'contacto',
      render: (_, r) => (
        <div className="space-y-0.5 text-sm text-slate-500">
          {r.telefono && <div className="flex items-center gap-1"><Phone className="w-3 h-3 shrink-0" />{r.telefono}</div>}
          {r.email && <div className="flex items-center gap-1"><Mail className="w-3 h-3 shrink-0" />{r.email}</div>}
          {!r.telefono && !r.email && <span className="text-slate-300">—</span>}
        </div>
      ),
    },
    {
      title: 'Saldo CC',
      key: 'saldo',
      render: (_, r) => {
        const saldo = Number(r.saldo_cuenta_corriente) || 0
        const negTarjetas = Number(r.saldo_negativo_tarjetas) || 0
        return (
          <div className="space-y-0.5">
            <span className={['tabular-nums text-base font-semibold block', saldo > 0 ? 'text-red-600' : 'text-emerald-700'].join(' ')}>
              {saldo > 0 ? '+' : ''}{formatGs(saldo)}
            </span>
            {negTarjetas < 0 && (
              <span className="flex items-center gap-1 text-xs font-medium text-amber-600" title="Tarjeta(s) de hijos con saldo negativo">
                <svg className="w-3 h-3 shrink-0" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 3.5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4.5zm0 7a.875.875 0 1 1 0-1.75.875.875 0 0 1 0 1.75z"/>
                </svg>
                Tarjeta {formatGs(negTarjetas)}
              </span>
            )}
          </div>
        )
      },
    },
    {
      title: 'Límite Créd.',
      key: 'limite',
      render: (_, r) => <span className="tabular-nums text-base text-slate-600">{formatGs(r.limite_credito)}</span>,
    },
    {
      title: 'Estado',
      key: 'estado',
      render: (_, r) => <Badge color={r.activo ? 'green' : 'red'}>{r.activo ? 'Activo' : 'Inactivo'}</Badge>,
    },
    {
      title: '',
      key: 'acciones',
      render: (_, r) => (
        <div className="flex items-center gap-1.5 justify-end">
          {(Number(r.saldo_cuenta_corriente) || 0) > 0 && (
            <button onClick={() => setPagarCCModal({ open: true, cliente: r })}
              className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-orange-600 hover:bg-orange-50 rounded-lg transition-colors" title="Registrar pago de cuenta corriente">
              <Banknote className="w-3.5 h-3.5" />Cobrar CC
            </button>
          )}
          <button onClick={() => setHijosModal({ open: true, cliente: r })}
            className="flex items-center gap-1 px-2.5 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
            <Users className="w-3.5 h-3.5" />Hijos
          </button>
          <button onClick={() => setClienteModal({ open: true, cliente: r })}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors" title="Editar cliente">
            <Edit2 className="w-3.5 h-3.5" />
          </button>
        </div>
      ),
    },
  ], [])

  const stats = useMemo(() => ({
    activos: clientes.filter(c => c.activo).length,
    conDeuda: clientes.filter(c => (Number(c.saldo_cuenta_corriente) || 0) > 0 || (Number(c.saldo_negativo_tarjetas) || 0) < 0).length,
  }), [clientes])

  const selectClass = 'min-w-[140px] border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'

  return (
    <div className="p-4 md:p-6 space-y-5">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('clientes.title')}</h1>
          <p className="text-base text-slate-500 mt-0.5">{t('clientes.subtitle')}</p>
        </div>
        <Button variant="primary" onClick={() => setClienteModal({ open: true, cliente: null })}>
          <Plus className="w-4 h-4" />{t('clientes.newCliente')}
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total', value: total, color: 'text-slate-900' },
          { label: 'Activos', value: stats.activos, color: 'text-green-600' },
          { label: 'Con Deuda', value: stats.conDeuda, color: 'text-red-600' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3">
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
            <p className={`text-2xl font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-3 flex flex-wrap gap-3 items-center">
        <div className="flex-1 min-w-48 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          <input
            className="w-full border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-base text-slate-900 bg-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors"
            placeholder="Buscar por nombre, apellido o RUC/CI..."
            value={searchInput}
            onChange={e => handleSearchChange(e.target.value)}
          />
        </div>
        <select value={filterActivo} onChange={handleFilterChange(setFilterActivo)} className={selectClass}>
          <option value="">Todos los estados</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
        <select value={filterTipo} onChange={handleFilterChange(setFilterTipo)} className={selectClass}>
          <option value="">Todos los tipos</option>
          {tiposCliente.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
        </select>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden p-1">
        <Table columns={columns} dataSource={clientes} rowKey="id" loading={loading} pageSize={PAGE_SIZE} page={page} onPageChange={setPage} total={total} />
      </div>

      <ModalCliente
        open={clienteModal.open}
        cliente={clienteModal.cliente}
        tiposCliente={tiposCliente}
        listasPrecios={listasPrecios}
        ciudades={ciudades}
        onClose={() => setClienteModal({ open: false, cliente: null })}
        onSaved={loadClientes}
      />
      <ModalHijos
        open={hijosModal.open}
        cliente={hijosModal.cliente}
        onClose={() => setHijosModal({ open: false, cliente: null })}
      />
      <ModalPagarCC
        open={pagarCCModal.open}
        cliente={pagarCCModal.cliente}
        onClose={() => setPagarCCModal({ open: false, cliente: null })}
        onSaved={loadClientes}
      />
    </div>
  )
}
