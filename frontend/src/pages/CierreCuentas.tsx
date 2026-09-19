import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { useTranslation } from 'react-i18next'
import { Download, FolderOpen, GraduationCap, Search } from 'lucide-react'
import cierreCuentasService from '../services/cierreCuentas'
import { useAuthStore } from '../store/authStore'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Table, { type Column } from '../components/ui/Table'
import ModalCierre from './cierrecuentas/ModalCierre'
import TabPendientes from './cierrecuentas/TabPendientes'
import {
  ESTADO_CIERRE_COLOR, ESTADO_CIERRE_LABEL, extractErrorMessage, formatGs, puedeGestionar,
  type Cierre, type EstadoCierre, type ResumenCierres,
} from './cierrecuentas/shared'

const inputClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150 w-full'
const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

const saldoColor = (n: number) => (n < 0 ? 'text-red-600' : n > 0 ? 'text-emerald-700' : 'text-slate-400')

function descargarCsv(nombre: string, filas: (string | number)[][]) {
  const escapar = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`
  const contenido = '﻿' + filas.map(f => f.map(escapar).join(';')).join('\r\n')
  const url = URL.createObjectURL(new Blob([contenido], { type: 'text/csv;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = nombre
  a.click()
  URL.revokeObjectURL(url)
}

export default function CierreCuentas() {
  const { t } = useTranslation()
  const rol = useAuthStore(s => s.user?.rol)
  const [anio, setAnio] = useState(new Date().getFullYear())
  const [tab, setTab] = useState<'alumnos' | 'pendientes'>('alumnos')
  const [search, setSearch] = useState('')
  const [estado, setEstado] = useState('')
  const [page, setPage] = useState(1)
  const [cierres, setCierres] = useState<Cierre[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [resumen, setResumen] = useState<ResumenCierres | null>(null)
  const [abiertoId, setAbiertoId] = useState<number | null>(null)
  const [abriendo, setAbriendo] = useState(false)
  const [exportando, setExportando] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined)
  const requestId = useRef(0)

  const cargarResumen = useCallback(async (a: number) => {
    try {
      const { data } = await cierreCuentasService.resumen(a)
      setResumen(data)
    } catch {
      setResumen(null)
    }
  }, [])

  const cargarLista = useCallback(async (a: number, q: string, e: string, p: number) => {
    const id = ++requestId.current
    setLoading(true)
    try {
      const params: Record<string, unknown> = { anio: a, page: p, page_size: 15, ordering: 'hijo__apellido' }
      if (q) params.search = q
      if (e) params.estado = e
      const { data } = await cierreCuentasService.listar(params)
      if (id !== requestId.current) return
      setCierres(data.results ?? [])
      setTotal(data.count ?? 0)
    } catch {
      if (id === requestId.current) toast.error('Error al cargar los cierres de cuentas')
    } finally {
      if (id === requestId.current) setLoading(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      setPage(1)
      cargarLista(anio, search, estado, 1)
      cargarResumen(anio)
    }, 350)
    return () => clearTimeout(timer.current)
  }, [anio, search, estado, cargarLista, cargarResumen])

  const recargar = useCallback(() => {
    cargarLista(anio, search, estado, page)
    cargarResumen(anio)
  }, [anio, search, estado, page, cargarLista, cargarResumen])

  const abrirCierres = async () => {
    setAbriendo(true)
    try {
      const { data } = await cierreCuentasService.abrirMasivo(anio)
      toast.success(
        data.creados > 0
          ? `Se abrieron ${data.creados} expediente${data.creados !== 1 ? 's' : ''} (${data.existentes} ya existían)`
          : 'No había expedientes nuevos por abrir',
      )
      recargar()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setAbriendo(false)
    }
  }

  const exportar = async () => {
    setExportando(true)
    try {
      const { data } = await cierreCuentasService.listar({ anio, page_size: 1000, ordering: 'hijo__apellido' })
      const filas: (string | number)[][] = [[
        'Alumno', 'Grado', 'Responsable', 'Tarjeta', 'Saldo cantina', 'Saldo almuerzo',
        'Deuda pendiente', 'A favor pendiente', 'Estado', 'Resoluciones pendientes',
      ]]
      for (const c of data.results) {
        filas.push([
          c.hijo_nombre, c.hijo_grado ?? '', c.cliente_nombre, c.nro_tarjeta,
          c.saldo_cantina_actual, c.saldo_almuerzo_actual, c.deuda_pendiente, c.a_favor_pendiente,
          ESTADO_CIERRE_LABEL[c.estado], c.resoluciones_pendientes,
        ])
      }
      descargarCsv(`cierre_cuentas_${anio}.csv`, filas)
    } catch {
      toast.error('Error al exportar')
    } finally {
      setExportando(false)
    }
  }

  const columnas: Column<Cierre>[] = [
    {
      title: 'Alumno', key: 'alumno',
      render: (_, r) => (
        <div>
          <p className="text-base font-medium text-slate-800">{r.hijo_nombre}</p>
          <p className="text-sm text-slate-400">
            {r.hijo_grado ?? 'Sin grado'}{r.nro_tarjeta ? ` · ${r.nro_tarjeta}` : ''}{!r.hijo_activo ? ' · Baja' : ''}
          </p>
        </div>
      ),
    },
    { title: 'Responsable', key: 'cliente', render: (_, r) => <span className="text-base text-slate-700">{r.cliente_nombre}</span> },
    {
      title: 'Cantina', key: 'cantina',
      render: (_, r) => <span className={`tabular-nums font-semibold text-base ${saldoColor(r.saldo_cantina_actual)}`}>{formatGs(r.saldo_cantina_actual)}</span>,
    },
    {
      title: 'Almuerzo', key: 'almuerzo',
      render: (_, r) => <span className={`tabular-nums font-semibold text-base ${saldoColor(r.saldo_almuerzo_actual)}`}>{formatGs(r.saldo_almuerzo_actual)}</span>,
    },
    {
      title: 'Estado', key: 'estado',
      render: (_, r) => (
        <div className="flex flex-wrap gap-1.5">
          <Badge color={ESTADO_CIERRE_COLOR[r.estado]}>{ESTADO_CIERRE_LABEL[r.estado]}</Badge>
          {r.resoluciones_pendientes > 0 && <Badge color="yellow">{r.resoluciones_pendientes} por aprobar</Badge>}
        </div>
      ),
    },
    {
      title: '', key: 'acc', width: 120,
      render: (_, r) => (
        <Button size="sm" variant="primary" onClick={() => setAbiertoId(r.id_cierre_cuenta)}>
          <FolderOpen className="w-3.5 h-3.5" />
          {r.estado === 'RESUELTO' || r.estado === 'CERRADO_CON_SALDO' ? 'Ver' : 'Resolver'}
        </Button>
      ),
    },
  ]

  const tarjetas = [
    { label: 'Alumnos', value: String(resumen?.alumnos ?? 0), color: 'text-slate-800', bg: 'bg-slate-50' },
    { label: 'A devolver', value: formatGs(resumen?.saldo_a_devolver ?? 0), color: 'text-emerald-700', bg: 'bg-emerald-50' },
    { label: 'Deuda a cobrar', value: formatGs(resumen?.deuda_a_cobrar ?? 0), color: 'text-red-700', bg: 'bg-red-50' },
    {
      label: 'Resueltos',
      value: `${(resumen?.por_estado.RESUELTO ?? 0) + (resumen?.por_estado.CERRADO_CON_SALDO ?? 0)} de ${resumen?.alumnos ?? 0}`,
      color: 'text-blue-700', bg: 'bg-blue-50',
    },
  ]

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <GraduationCap className="w-6 h-6 text-slate-400" />
            {t('nav.cierreCuentas')}
          </h1>
          <p className="text-base text-slate-500 mt-0.5">
            Saldos y deudas de los alumnos que egresan: devolución, traspaso a hermanos, cobro y más, con registro de cada decisión.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="secondary" onClick={exportar} loading={exportando}>
            <Download className="w-4 h-4" />
            Exportar CSV
          </Button>
          {puedeGestionar(rol) && (
            <Button variant="primary" onClick={abrirCierres} loading={abriendo}>
              <FolderOpen className="w-4 h-4" />
              Abrir cierres del año
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {tarjetas.map(({ label, value, color, bg }) => (
          <div key={label} className={`${bg} rounded-2xl px-5 py-4`}>
            <p className="text-sm font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
            <p className={`text-xl font-bold mt-0.5 tabular-nums ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="border-b border-slate-200">
        <div className="flex">
          {([
            ['alumnos', 'Alumnos'],
            ['pendientes', `Aprobaciones pendientes${resumen && resumen.resoluciones_pendientes > 0 ? ` (${resumen.resoluciones_pendientes})` : ''}`],
          ] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                tab === key ? 'border-green-600 text-green-700' : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'alumnos' ? (
        <>
          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 flex flex-wrap items-end gap-4">
            <div className="w-28">
              <label className={labelClass} htmlFor="cc-anio">Año</label>
              <input
                id="cc-anio" type="number" min={2020} max={2100} value={anio}
                onChange={e => setAnio(Number(e.target.value) || new Date().getFullYear())}
                className={inputClass}
              />
            </div>
            <div className="flex-1 min-w-[200px]">
              <label className={labelClass} htmlFor="cc-buscar">Buscar</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  id="cc-buscar" placeholder="Alumno o nro. de tarjeta..." value={search}
                  onChange={e => setSearch(e.target.value)} className={`${inputClass} pl-9`}
                />
              </div>
            </div>
            <div>
              <label className={labelClass} htmlFor="cc-estado">Estado</label>
              <select id="cc-estado" value={estado} onChange={e => setEstado(e.target.value)} className={`${inputClass} w-auto`}>
                <option value="">Todos</option>
                {(Object.keys(ESTADO_CIERRE_LABEL) as EstadoCierre[]).map(k => (
                  <option key={k} value={k}>{ESTADO_CIERRE_LABEL[k]}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
            <div className="p-1">
              <Table
                columns={columnas}
                dataSource={cierres}
                rowKey="id_cierre_cuenta"
                loading={loading}
                pageSize={15}
                page={page}
                onPageChange={p => { setPage(p); cargarLista(anio, search, estado, p) }}
                total={total}
              />
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
          <TabPendientes anio={anio} rol={rol} onChanged={recargar} onAbrir={setAbiertoId} />
        </div>
      )}

      {abiertoId !== null && (
        <ModalCierre cierreId={abiertoId} onClose={() => setAbiertoId(null)} onChanged={recargar} />
      )}
    </div>
  )
}
