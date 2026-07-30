import { useSearchParams } from 'react-router-dom'
import { CheckCircle2, XCircle, AlertCircle, ArrowLeft } from 'lucide-react'

function formatGs(n: number) {
  return 'Gs. ' + (Number(n) || 0).toLocaleString('es-PY')
}

export default function PagoCompletado() {
  const [searchParams] = useSearchParams()

  const estado = searchParams.get('estado') ?? 'error'
  const monto  = searchParams.get('monto')
  const tipo   = searchParams.get('tipo') ?? 'saldo'   // 'saldo' | 'almuerzo'

  const aprobado  = estado === 'aprobado'
  const cancelado = estado === 'cancelado'

  // Full page reload: garantiza datos frescos (saldo actualizado) y re-autenticación.
  const volverA = tipo === 'almuerzo' ? '/portal/pagar-almuerzo' : '/portal/carga-saldo'
  const handleVolver = () => { window.location.href = volverA }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-2xl border border-slate-100 shadow-sm p-8">

        {/* Logo */}
        <div className="flex justify-center mb-6">
          <img src="/logo_tita.png" alt="Cantina Tita" className="h-12 w-auto" />
        </div>

        {/* Estado */}
        {aprobado ? (
          <div className="flex flex-col items-center text-center space-y-3">
            <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">¡Pago aprobado!</h1>
            {monto && (
              <p className="text-xl font-semibold text-emerald-700">
                {formatGs(Number(monto))} acreditados
              </p>
            )}
            <p className="text-slate-500 text-sm">
              El saldo fue acreditado en la tarjeta del alumno.
            </p>
          </div>
        ) : cancelado ? (
          <div className="flex flex-col items-center text-center space-y-3">
            <div className="w-20 h-20 rounded-full bg-slate-100 flex items-center justify-center">
              <XCircle className="w-10 h-10 text-slate-400" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Pago cancelado</h1>
            <p className="text-slate-500 text-sm">No se realizó ningún cargo.</p>
          </div>
        ) : (
          <div className="flex flex-col items-center text-center space-y-3">
            <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="w-10 h-10 text-red-500" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Pago rechazado</h1>
            <p className="text-slate-500 text-sm">
              No se pudo procesar el pago. Verificá los datos de tu tarjeta e intentá nuevamente.
            </p>
          </div>
        )}

        {/* Botón volver */}
        <button
          type="button"
          onClick={handleVolver}
          className="mt-8 w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-green-600 hover:bg-green-700 text-white font-semibold transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Volver al portal
        </button>
      </div>
    </div>
  )
}
