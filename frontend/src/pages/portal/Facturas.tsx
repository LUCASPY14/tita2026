import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { FileText, ExternalLink } from 'lucide-react'
import api from '../../services/api'
import Spinner from '../../components/ui/Spinner'

// ─── Interfaces ───────────────────────────────────────────────────────────────

interface Factura {
  id: number
  nro_factura: string
  fecha_emision: string
  monto_total: string | number
  iva_10: string | number
  estado: string
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatGs(n: number | string) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

function formatFecha(iso: string) {
  return new Date(iso).toLocaleDateString('es-PY', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function PortalFacturas() {
  const [facturas, setFacturas] = useState<Factura[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingPdf, setLoadingPdf] = useState<number | null>(null)

  useEffect(() => {
    api.get('/usuarios/portal/mis-facturas/')
      .then(res => setFacturas(res.data ?? []))
      .catch(() => toast.error('Error al cargar facturas'))
      .finally(() => setLoading(false))
  }, [])

  const abrirPdf = async (id: number) => {
    setLoadingPdf(id)
    try {
      const res = await api.get(`/contabilidad/facturas/${id}/pdf/`, {
        responseType: 'blob',
      })
      const blobUrl = URL.createObjectURL(
        new Blob([res.data], { type: 'text/html; charset=utf-8' })
      )
      const win = window.open(blobUrl, '_blank')
      if (win) setTimeout(() => URL.revokeObjectURL(blobUrl), 30_000)
    } catch {
      toast.error('No se pudo abrir la factura')
    } finally {
      setLoadingPdf(null)
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-bold text-slate-900">Mis Facturas</h1>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : facturas.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-slate-400">
            <FileText className="w-10 h-10 mb-3 opacity-40" />
            <p className="text-sm">Sin facturas emitidas</p>
          </div>
        ) : (
          <ul className="divide-y divide-slate-100">
            {facturas.map(f => (
              <li key={f.id} className="flex items-center justify-between px-4 py-3.5">
                <div>
                  <p className="text-sm font-semibold text-slate-800 font-mono">{f.nro_factura}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{formatFecha(f.fecha_emision)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm font-bold tabular-nums text-emerald-700">{formatGs(f.monto_total)}</p>
                    <p className="text-xs text-slate-400">IVA 10%: {formatGs(f.iva_10)}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => abrirPdf(f.id)}
                    disabled={loadingPdf === f.id}
                    className="flex items-center gap-1.5 text-xs font-medium text-green-700 border border-green-200 rounded-xl px-3 py-1.5 hover:bg-green-50 transition-colors cursor-pointer disabled:opacity-40"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    {loadingPdf === f.id ? '…' : 'PDF'}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
