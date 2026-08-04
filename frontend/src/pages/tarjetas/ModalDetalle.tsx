import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Lock, Unlock, ArrowUp, ArrowDown } from 'lucide-react'
import tarjetasService from '../../services/tarjetas'
import { METODO_PAGO_LABEL } from '../../constants/mediosPago'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import Table, { type Column } from '../../components/ui/Table'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, formatGs, formatFecha, formatFechaCorta,
  type Tarjeta, type MovimientoTarjeta, type CargaSaldo,
  ESTADO_COLOR, TIPO_MOV_LABEL, TIPO_MOV_COLOR, ESTADO_CARGA_COLOR,
} from './shared'

interface Props {
  tarjeta: Tarjeta | null
  toggling: string | null
  onToggleEstado: (t: Tarjeta) => void
  onClose: () => void
  onTarjetaUpdated: (t: Tarjeta) => void
  onListReload: () => void
}

const inputClass = 'border border-slate-200 rounded-xl px-3 py-1.5 text-sm text-slate-700 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

export default function ModalDetalle({ tarjeta, toggling, onToggleEstado, onClose, onTarjetaUpdated, onListReload }: Props) {
  const [detailTab, setDetailTab] = useState<'movimientos' | 'cargas'>('movimientos')
  const [movimientos, setMovimientos] = useState<MovimientoTarjeta[]>([])
  const [cargas, setCargas] = useState<CargaSaldo[]>([])
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [tipoMovFilter, setTipoMovFilter] = useState('')

  const [confirmCargaId, setConfirmCargaId] = useState<number | null>(null)
  const [confirmFactura, setConfirmFactura] = useState({ emitir: false, nro: '' })
  const [confirmando, setConfirmando] = useState(false)

  const [prevNroTarjeta, setPrevNroTarjeta] = useState(tarjeta?.nro_tarjeta)
  if (tarjeta?.nro_tarjeta !== prevNroTarjeta) {
    setPrevNroTarjeta(tarjeta?.nro_tarjeta)
    if (tarjeta) {
      setDetailTab('movimientos')
      setTipoMovFilter('')
      setLoadingDetail(true)
    }
  }

  useEffect(() => {
    if (!tarjeta) return
    Promise.all([
      tarjetasService.getMovimientos<MovimientoTarjeta>(tarjeta.nro_tarjeta, 200),
      tarjetasService.getCargas<CargaSaldo>(tarjeta.nro_tarjeta, 200),
    ]).then(([movRes, cargaRes]) => {
      setMovimientos(movRes.data.results ?? [])
      setCargas(cargaRes.data.results ?? [])
    }).catch(() => toast.error('Error al cargar historial'))
      .finally(() => setLoadingDetail(false))
  }, [tarjeta?.nro_tarjeta]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleConfirmarCarga = async () => {
    if (!confirmCargaId || !tarjeta) return
    if (confirmFactura.emitir && !confirmFactura.nro.trim()) {
      toast.error('Ingresá el número de factura')
      return
    }
    setConfirmando(true)
    try {
      await tarjetasService.confirmarCarga(
        confirmCargaId,
        confirmFactura.emitir ? confirmFactura.nro.trim() : undefined,
      )
      toast.success('Carga confirmada')
      setConfirmCargaId(null)
      const [tarjetaRes, movRes, cargaRes] = await Promise.all([
        tarjetasService.getByNro<Tarjeta>(tarjeta.nro_tarjeta),
        tarjetasService.getMovimientos<MovimientoTarjeta>(tarjeta.nro_tarjeta, 200),
        tarjetasService.getCargas<CargaSaldo>(tarjeta.nro_tarjeta, 200),
      ])
      onTarjetaUpdated(tarjetaRes.data)
      setMovimientos(movRes.data.results ?? [])
      setCargas(cargaRes.data.results ?? [])
      onListReload()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setConfirmando(false)
    }
  }

  const movimientosFiltrados = useMemo(
    () => tipoMovFilter ? movimientos.filter(m => m.tipo === tipoMovFilter) : movimientos,
    [movimientos, tipoMovFilter],
  )

  const colsMovimientos: Column<MovimientoTarjeta>[] = [
    {
      title: 'Fecha', key: 'fecha',
      render: (_, r) => <span className="text-sm text-slate-500">{formatFecha(r.fecha)}</span>,
    },
    {
      title: 'Tipo', key: 'tipo',
      render: (_, r) => (
        <Badge color={TIPO_MOV_COLOR[r.tipo] ?? 'default'}>{TIPO_MOV_LABEL[r.tipo] ?? r.tipo}</Badge>
      ),
    },
    {
      title: 'Monto', key: 'monto',
      render: (_, r) => {
        const isEntry = r.tipo === 'RECARGA' || r.tipo === 'REVERSO'
        return (
          <span className={`tabular-nums font-semibold text-base flex items-center gap-0.5 ${isEntry ? 'text-emerald-700' : 'text-slate-700'}`}>
            {isEntry ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {formatGs(r.monto)}
          </span>
        )
      },
    },
    {
      title: 'Saldo ant.', key: 'saldo_ant',
      render: (_, r) => <span className="tabular-nums text-base text-slate-400">{formatGs(r.saldo_anterior)}</span>,
    },
    {
      title: 'Saldo result.', key: 'saldo_res',
      render: (_, r) => (
        <span className={`tabular-nums text-base font-medium ${Number(r.saldo_resultante) < 0 ? 'text-red-600' : 'text-slate-700'}`}>
          {formatGs(r.saldo_resultante)}
        </span>
      ),
    },
    {
      title: 'Descripción', key: 'desc',
      render: (_, r) => <span className="text-base text-slate-400">{r.descripcion || '—'}</span>,
    },
  ]

  const colsCargas: Column<CargaSaldo>[] = [
    {
      title: 'Fecha', key: 'fecha',
      render: (_, r) => <span className="text-xs text-slate-500">{formatFecha(r.fecha_carga ?? r.fecha)}</span>,
    },
    {
      title: 'Monto', key: 'monto',
      render: (_, r) => (
        <span className="tabular-nums font-semibold text-emerald-700">{formatGs(r.monto_cargado)}</span>
      ),
    },
    {
      title: 'Método', key: 'metodo',
      render: (_, r) => (
        <span className="text-base text-slate-600">{METODO_PAGO_LABEL[r.metodo_pago] ?? r.metodo_pago}</span>
      ),
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => <Badge color={ESTADO_CARGA_COLOR[r.estado] ?? 'default'}>{r.estado}</Badge>,
    },
    {
      title: 'Usuario', key: 'usuario',
      render: (_, r) => <span className="text-base text-slate-400">{r.usuario_nombre ?? '—'}</span>,
    },
    {
      title: '', key: 'accion', width: 110,
      render: (_, r) => r.estado === 'PENDIENTE' ? (
        <Button size="sm" variant="primary" onClick={() => { setConfirmCargaId(r.id); setConfirmFactura({ emitir: false, nro: '' }) }}>
          Confirmar
        </Button>
      ) : null,
    },
  ]

  if (!tarjeta) return null

  return (
    <>
      <Modal
        open
        title={`Tarjeta ${tarjeta.nro_tarjeta} — ${tarjeta.hijo_nombre ?? '—'}`}
        onCancel={onClose}
        width={820}
        footer={null}
      >
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
          {[
            { label: 'Saldo Actual', value: formatGs(tarjeta.saldo_actual), warn: Number(tarjeta.saldo_actual) < 0 },
            { label: 'Saldo Disponible', value: formatGs(tarjeta.saldo_disponible) },
            { label: 'Límite Crédito', value: formatGs(tarjeta.limite_credito) },
            { label: 'Vencimiento', value: formatFechaCorta(tarjeta.fecha_vencimiento) },
          ].map(({ label, value, warn }) => (
            <div key={label} className="bg-slate-50 rounded-xl px-3 py-3">
              <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
              <p className={`text-base font-bold mt-0.5 tabular-nums ${warn ? 'text-red-600' : 'text-slate-800'}`}>{value}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div className="flex items-center gap-2">
            <Badge color={ESTADO_COLOR[tarjeta.estado] ?? 'default'}>{tarjeta.estado}</Badge>
            {tarjeta.permite_saldo_negativo && <Badge color="yellow">Permite saldo negativo</Badge>}
            <span className="text-sm text-slate-400">Cliente: {tarjeta.cliente_nombre}</span>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={tarjeta.estado === 'ACTIVA' ? 'danger' : 'primary'}
              onClick={() => onToggleEstado(tarjeta)}
              loading={toggling === tarjeta.nro_tarjeta}
              disabled={!!toggling || tarjeta.estado === 'VENCIDA' || tarjeta.estado === 'CANCELADA'}
            >
              {tarjeta.estado === 'ACTIVA' ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
              {tarjeta.estado === 'ACTIVA' ? 'Bloquear' : 'Activar'}
            </Button>
          </div>
        </div>

        <div className="border-b border-slate-200 mb-4">
          <div className="flex">
            {(['movimientos', 'cargas'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setDetailTab(tab)}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  detailTab === tab
                    ? 'border-green-600 text-green-700'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                {tab === 'movimientos' ? 'Movimientos' : 'Cargas de Saldo'}
              </button>
            ))}
          </div>
        </div>

        {loadingDetail ? (
          <div className="py-10 text-center text-slate-400 text-sm">Cargando historial...</div>
        ) : detailTab === 'movimientos' ? (
          <>
            <div className="mb-3">
              <select
                value={tipoMovFilter}
                onChange={e => setTipoMovFilter(e.target.value)}
                className={inputClass}
              >
                <option value="">Todos los tipos</option>
                <option value="RECARGA">Recarga</option>
                <option value="CONSUMO">Consumo</option>
                <option value="AJUSTE">Ajuste</option>
                <option value="REVERSO">Reverso</option>
              </select>
            </div>
            <Table columns={colsMovimientos} dataSource={movimientosFiltrados} rowKey="id" pageSize={8} />
          </>
        ) : (
          <Table columns={colsCargas} dataSource={cargas} rowKey="id" pageSize={8} />
        )}

        <div className="flex justify-end mt-5">
          <Button variant="secondary" onClick={onClose}>Cerrar</Button>
        </div>
      </Modal>

      <Modal
        open={confirmCargaId !== null}
        title="Confirmar Carga de Saldo"
        onOk={handleConfirmarCarga}
        onCancel={() => setConfirmCargaId(null)}
        okText="Confirmar"
        confirmLoading={confirmando}
        width={400}
      >
        <div className="space-y-4">
          <p className="text-sm text-slate-600">¿Confirmás esta carga de saldo?</p>
          <div className="pt-1">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={confirmFactura.emitir}
                onChange={e => setConfirmFactura(f => ({ ...f, emitir: e.target.checked, nro: '' }))}
                className="w-4 h-4 rounded accent-green-600"
              />
              <span className="text-sm font-semibold text-slate-700">Emitir factura ahora</span>
            </label>
            {confirmFactura.emitir && (
              <div className="mt-2">
                <label className={labelClass}>Nro. Factura *</label>
                <input
                  value={confirmFactura.nro}
                  onChange={e => setConfirmFactura(f => ({ ...f, nro: e.target.value }))}
                  placeholder="001-001-0001234"
                  className="border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full"
                  autoFocus
                />
              </div>
            )}
          </div>
        </div>
      </Modal>
    </>
  )
}
