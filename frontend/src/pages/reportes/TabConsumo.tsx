import { useState } from 'react'
import toast from 'react-hot-toast'
import { ShoppingBag, Search, Download, FileText, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../../services/api'
import { exportarConsumoPDF } from '../../utils/pdf'
import Button from '../../components/ui/Button'
import {
  formatGs, formatFecha, descargaBlob, today,
  FilterBar, EmptyState, KpiCard,
  type VentaConsumoRep,
} from './shared'

const PAGE_CONSUMO = 30

export default function TabConsumo() {
  const t0 = today()
  const [desdeConsumo, setDesdeConsumo] = useState(t0)
  const [hastaConsumo, setHastaConsumo] = useState(t0)
  const [tarjetaConsumo, setTarjetaConsumo] = useState('')
  const [consumos, setConsumos] = useState<VentaConsumoRep[]>([])
  const [totalConsumo, setTotalConsumo] = useState(0)
  const [loadingConsumo, setLoadingConsumo] = useState(false)
  const [loadingMoreConsumo, setLoadingMoreConsumo] = useState(false)
  const [pageConsumo, setPageConsumo] = useState(1)
  const [expandedConsumoId, setExpandedConsumoId] = useState<number | null>(null)
  const [consumoGenerated, setConsumoGenerated] = useState(false)

  const inputDateClass = 'border border-slate-200 rounded-xl px-3 py-2 text-base text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 transition-colors duration-150'
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  async function buscarConsumo() {
    if (!desdeConsumo || !hastaConsumo) { toast.error('Seleccioná ambas fechas'); return }
    if (desdeConsumo > hastaConsumo) { toast.error('La fecha Desde no puede ser mayor a Hasta'); return }
    setLoadingConsumo(true)
    setPageConsumo(1)
    setExpandedConsumoId(null)
    setConsumoGenerated(false)
    try {
      const params: Record<string, string | number> = {
        estado: 'ACTIVA', ordering: '-fecha', page: 1, page_size: PAGE_CONSUMO,
        fecha_desde: desdeConsumo, fecha_hasta: hastaConsumo,
      }
      if (tarjetaConsumo.trim()) params.tarjeta = tarjetaConsumo.trim()
      const { data: res } = await api.get('/ventas/ventas/', { params })
      setTotalConsumo(res.count ?? 0)
      setConsumos(res.results ?? [])
      setConsumoGenerated(true)
    } catch { toast.error('Error al cargar consumos') }
    finally { setLoadingConsumo(false) }
  }

  async function cargarMasConsumo() {
    const next = pageConsumo + 1
    setPageConsumo(next)
    setLoadingMoreConsumo(true)
    try {
      const params: Record<string, string | number> = {
        estado: 'ACTIVA', ordering: '-fecha', page: next, page_size: PAGE_CONSUMO,
        fecha_desde: desdeConsumo, fecha_hasta: hastaConsumo,
      }
      if (tarjetaConsumo.trim()) params.tarjeta = tarjetaConsumo.trim()
      const { data: res } = await api.get('/ventas/ventas/', { params })
      setConsumos(prev => [...prev, ...(res.results ?? [])])
    } catch { toast.error('Error al cargar más registros') }
    finally { setLoadingMoreConsumo(false) }
  }

  function exportarConsumoCSV() {
    if (!consumos.length) return
    const filas: string[][] = [
      ['Fecha', 'Alumno', 'Grado', 'Tarjeta', 'Producto', 'Cantidad', 'Precio Unit. (Gs)', 'Subtotal (Gs)', 'Total Venta (Gs)'],
    ]
    for (const v of consumos) {
      const alumno = v.hijo_nombre ?? v.cliente_nombre
      if (v.detalles.length === 0) {
        filas.push([formatFecha(v.fecha), alumno, v.hijo_grado ?? '', v.tarjeta ?? '', '—', '', '', '', v.monto_total])
      } else {
        for (const d of v.detalles) {
          filas.push([formatFecha(v.fecha), alumno, v.hijo_grado ?? '', v.tarjeta ?? '', d.producto_nombre, d.cantidad, d.precio_unitario, d.subtotal, v.monto_total])
        }
      }
    }
    const csv = filas.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
    descargaBlob(blob, `consumo_${desdeConsumo}_${hastaConsumo}.csv`)
    toast.success('CSV descargado')
  }

  const totalCargado = consumos.reduce((s, v) => s + Number(v.monto_total), 0)

  function handleConsumoPDF() {
    if (!consumos.length) return
    try {
      exportarConsumoPDF(
        consumos.map(v => ({
          fecha: v.fecha,
          alumno: v.hijo_nombre ?? v.cliente_nombre,
          grado: v.hijo_grado,
          tarjeta: v.tarjeta,
          monto_total: v.monto_total,
          detalles: v.detalles,
        })),
        desdeConsumo,
        hastaConsumo,
        tarjetaConsumo.trim() || undefined,
      )
      toast.success('PDF descargado')
    } catch { toast.error('Error al generar PDF') }
  }

  return (
    <>
      <FilterBar>
        <div>
          <label className={labelClass}>Desde</label>
          <input type="date" value={desdeConsumo} onChange={e => setDesdeConsumo(e.target.value)} className={inputDateClass} />
        </div>
        <div>
          <label className={labelClass}>Hasta</label>
          <input type="date" value={hastaConsumo} onChange={e => setHastaConsumo(e.target.value)} className={inputDateClass} />
        </div>
        <div>
          <label className={labelClass}>Tarjeta (opcional)</label>
          <input
            placeholder="Nro. de tarjeta..."
            value={tarjetaConsumo}
            onChange={e => setTarjetaConsumo(e.target.value)}
            className={`${inputDateClass} w-44`}
          />
        </div>
        <Button variant="primary" loading={loadingConsumo} onClick={buscarConsumo}>
          <Search className="w-4 h-4" />Generar Reporte
        </Button>
        {consumos.length > 0 && (
          <>
            <Button variant="secondary" onClick={exportarConsumoCSV} disabled={loadingConsumo}>
              <Download className="w-4 h-4" />CSV
            </Button>
            <Button variant="secondary" onClick={handleConsumoPDF} disabled={loadingConsumo}>
              <FileText className="w-4 h-4" />PDF
            </Button>
          </>
        )}
      </FilterBar>

      {consumoGenerated && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <KpiCard label="Total en período" value={`${totalConsumo} compras`} />
            <KpiCard
              label={`Total cargado (${consumos.length} reg.)`}
              value={formatGs(totalCargado)}
              color="text-emerald-700"
            />
            <KpiCard
              label="Filtro activo"
              value={tarjetaConsumo.trim() ? `Tarjeta: ${tarjetaConsumo.trim()}` : `${desdeConsumo} — ${hastaConsumo}`}
            />
          </div>

          {consumos.length === 0 ? (
            <EmptyState icon={<ShoppingBag className="w-full h-full" />} text="Sin consumos en el período seleccionado" />
          ) : (
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-100">
                <h2 className="text-sm font-semibold text-slate-800">
                  {`Detalle de consumos — ${desdeConsumo} al ${hastaConsumo}`}
                </h2>
              </div>
              <ul className="divide-y divide-slate-100">
                {consumos.map(v => {
                  const isExp = expandedConsumoId === v.id
                  const alumno = v.hijo_nombre ?? v.cliente_nombre
                  return (
                    <li key={v.id}>
                      <button
                        type="button"
                        onClick={() => setExpandedConsumoId(isExp ? null : v.id)}
                        className="w-full flex items-center gap-4 px-5 py-3.5 text-left hover:bg-slate-50 transition-colors group"
                      >
                        <div className="w-8 h-8 rounded-full bg-green-50 border border-green-100 flex items-center justify-center shrink-0">
                          <ShoppingBag className="w-3.5 h-3.5 text-green-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-slate-800 truncate">
                            {alumno}
                            {v.hijo_grado && (
                              <span className="ml-1.5 text-slate-400 font-normal">{v.hijo_grado}</span>
                            )}
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {`${formatFecha(v.fecha)}${v.tarjeta ? ` · ${v.tarjeta}` : ''}`}
                          </p>
                        </div>
                        <div className="flex items-center gap-3 shrink-0">
                          <span className="text-sm font-bold tabular-nums text-slate-800">
                            {formatGs(Number(v.monto_total))}
                          </span>
                          {isExp
                            ? <ChevronUp className="w-4 h-4 text-slate-400" />
                            : <ChevronDown className="w-4 h-4 text-slate-400" />}
                        </div>
                      </button>
                      {isExp && v.detalles.length > 0 && (
                        <ul className="px-5 pb-3 ml-12 space-y-1.5">
                          {v.detalles.map(d => (
                            <li key={d.id} className="flex items-center justify-between text-sm text-slate-600">
                              <span>
                                <span className="font-semibold text-slate-700 tabular-nums">{d.cantidad}×</span>
                                {' '}{d.producto_nombre}
                                <span className="text-slate-400 ml-1.5">{`${formatGs(Number(d.precio_unitario))} c/u`}</span>
                              </span>
                              <span className="tabular-nums font-semibold text-slate-700 shrink-0">
                                {formatGs(Number(d.subtotal))}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  )
                })}
              </ul>
              {consumos.length < totalConsumo && (
                <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between">
                  <p className="text-sm text-slate-400">
                    {`Mostrando ${consumos.length} de ${totalConsumo}`}
                  </p>
                  <Button variant="secondary" loading={loadingMoreConsumo} onClick={cargarMasConsumo}>
                    Ver más
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
      {!consumoGenerated && !loadingConsumo && (
        <EmptyState icon={<ShoppingBag className="w-full h-full" />} text='Seleccioná un período y hacé clic en "Generar Reporte"' />
      )}
    </>
  )
}
