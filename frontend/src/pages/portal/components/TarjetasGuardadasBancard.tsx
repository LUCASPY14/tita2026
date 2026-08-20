import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { CreditCard, Plus, Trash2, Loader2 } from 'lucide-react'
import api from '../../../services/api'

declare global {
  interface Window {
    Bancard?: {
      Checkout: {
        createForm: (containerId: string, processId: string) => void
      }
      Cards: {
        createForm: (containerId: string, processId: string) => void
      }
      Charge3DS: {
        createForm: (containerId: string, processId: string) => void
      }
    }
  }
}

interface TarjetaGuardada {
  card_id: number
  card_masked_number: string
  card_brand: string
  expiration_date: string
}

interface Props {
  selectedCardId: number | null
  onSeleccionar: (cardId: number | null) => void
  accent?: 'green' | 'orange' | 'red'
  containerIdPrefix: string
}

const ACCENTOS = {
  green:  { border: 'border-green-500', bg: 'bg-green-50', text: 'text-green-700', btn: 'bg-green-600 hover:bg-green-700' },
  orange: { border: 'border-orange-500', bg: 'bg-orange-50', text: 'text-orange-700', btn: 'bg-orange-600 hover:bg-orange-700' },
  red:    { border: 'border-red-500', bg: 'bg-red-50', text: 'text-red-700', btn: 'bg-red-600 hover:bg-red-700' },
}

export default function TarjetasGuardadasBancard({ selectedCardId, onSeleccionar, accent = 'green', containerIdPrefix }: Props) {
  const [tarjetas, setTarjetas] = useState<TarjetaGuardada[] | null>(null)
  const [eliminando, setEliminando] = useState<number | null>(null)
  const [agregando, setAgregando] = useState(false)
  const [catastroEnProceso, setCatastroEnProceso] = useState(false)
  const [processId, setProcessId] = useState<string | null>(null)
  const [scriptUrl, setScriptUrl] = useState<string | null>(null)
  const scriptRef = useRef<HTMLScriptElement | null>(null)

  const colores = ACCENTOS[accent]
  const containerId = `${containerIdPrefix}-catastro-container`

  const cargarTarjetas = useCallback(async () => {
    try {
      const { data } = await api.get('/core/bancard/tarjetas/')
      setTarjetas(data.tarjetas ?? [])
    } catch {
      toast.error('No se pudieron cargar tus tarjetas guardadas')
      setTarjetas([])
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    cargarTarjetas()
  }, [cargarTarjetas])

  const handleAgregarTarjeta = useCallback(async () => {
    if (agregando) return
    setAgregando(true)
    try {
      const { data } = await api.post('/core/bancard/tarjetas/catastro/')
      setProcessId(data.process_id)
      setScriptUrl(data.script_url)
      setCatastroEnProceso(true)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail ?? 'Error al iniciar el catastro de la tarjeta'
      toast.error(msg)
      setAgregando(false)
    }
  }, [agregando])

  const handleEliminar = useCallback(async (cardId: number) => {
    setEliminando(cardId)
    try {
      await api.delete(`/core/bancard/tarjetas/${cardId}/`)
      if (selectedCardId === cardId) onSeleccionar(null)
      await cargarTarjetas()
    } catch {
      toast.error('No se pudo eliminar la tarjeta')
    } finally {
      setEliminando(null)
    }
  }, [selectedCardId, onSeleccionar, cargarTarjetas])

  // ── Cargar script Bancard y renderizar iframe de catastro embebido ──────────
  useEffect(() => {
    if (!catastroEnProceso || !processId || !scriptUrl) return

    if (scriptRef.current) {
      scriptRef.current.remove()
      scriptRef.current = null
    }

    const script = document.createElement('script')
    script.src = scriptUrl
    script.async = true
    script.onload = () => {
      window.Bancard?.Cards.createForm(containerId, processId)
    }
    script.onerror = () => {
      toast.error('Error al cargar el formulario de catastro')
      setCatastroEnProceso(false)
      setProcessId(null)
      setScriptUrl(null)
      setAgregando(false)
    }
    scriptRef.current = script
    document.body.appendChild(script)

    return () => {
      scriptRef.current?.remove()
      scriptRef.current = null
    }
  }, [catastroEnProceso, processId, scriptUrl, containerId])

  if (catastroEnProceso) {
    return (
      <div className="p-5">
        <p className="text-sm text-slate-500 mb-3">
          Ingresá los datos de la nueva tarjeta. Al finalizar, volverás a esta página.
        </p>
        <div id={containerId} className="min-h-[380px]" />
        <button
          type="button"
          onClick={() => {
            setCatastroEnProceso(false)
            setProcessId(null)
            setScriptUrl(null)
            setAgregando(false)
          }}
          className="mt-4 text-sm text-slate-500 hover:text-slate-700 transition-colors cursor-pointer"
        >
          ← Cancelar
        </button>
      </div>
    )
  }

  if (tarjetas === null) {
    return (
      <div className="p-8 flex justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    )
  }

  return (
    <div className="p-5 space-y-3">
      {tarjetas.length === 0 && (
        <p className="text-sm text-slate-500">Todavía no guardaste ninguna tarjeta.</p>
      )}

      {tarjetas.map(t => (
        <div
          key={t.card_id}
          className={[
            'flex items-center justify-between px-4 py-3 rounded-xl border-2 transition-colors cursor-pointer',
            selectedCardId === t.card_id
              ? `${colores.border} ${colores.bg}`
              : 'border-slate-200 hover:border-slate-300',
          ].join(' ')}
          onClick={() => onSeleccionar(t.card_id)}
        >
          <div className="flex items-center gap-3">
            <CreditCard className={`w-5 h-5 shrink-0 ${selectedCardId === t.card_id ? colores.text : 'text-slate-400'}`} />
            <div>
              <p className="text-sm font-semibold text-slate-800">
                {t.card_brand || 'Tarjeta'} {t.card_masked_number}
              </p>
              {t.expiration_date && (
                <p className="text-xs text-slate-400">Vence {t.expiration_date}</p>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); handleEliminar(t.card_id) }}
            disabled={eliminando === t.card_id}
            className="p-1.5 text-slate-400 hover:text-red-500 transition-colors cursor-pointer disabled:opacity-50"
            aria-label="Eliminar tarjeta"
          >
            {eliminando === t.card_id
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Trash2 className="w-4 h-4" />}
          </button>
        </div>
      ))}

      <button
        type="button"
        onClick={handleAgregarTarjeta}
        disabled={agregando}
        className={[
          'w-full flex items-center justify-center gap-2 py-3 rounded-xl border-2 border-dashed',
          'text-sm font-semibold transition-colors cursor-pointer',
          'border-slate-300 text-slate-500 hover:border-slate-400 hover:text-slate-700 disabled:opacity-50',
        ].join(' ')}
      >
        {agregando
          ? <><Loader2 className="w-4 h-4 animate-spin" />Iniciando…</>
          : <><Plus className="w-4 h-4" />Agregar tarjeta</>}
      </button>
    </div>
  )
}
