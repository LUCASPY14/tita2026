import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, CreditCard, AlertTriangle, Wallet, UtensilsCrossed } from 'lucide-react'
import { useAuthenticatedImage } from '../../hooks/useAuthenticatedImage'
import { gs, type Tarjeta, type ClienteBasico, type ModoPago } from './shared'

interface Props {
  tarjeta: Tarjeta | null
  saldoDisponible: number | null
  saldoTrasCompra: number | null
  hasItems: boolean
  modoPago: ModoPago
  tarjetaInput: string
  buscandoTarjeta: boolean
  clienteDirecto: ClienteBasico | null
  clienteSearch: string
  clienteResultados: ClienteBasico[]
  buscandoCliente: boolean
  scannerRef: React.RefObject<HTMLInputElement | null>
  onChangeTarjetaInput: (v: string) => void
  onScanEnter: () => void
  onChangeClienteSearch: (v: string) => void
  onSelectCliente: (c: ClienteBasico) => void
  onClearCliente: () => void
  onVentaStartTime: () => void
}

export default function PanelAlumno({
  tarjeta, saldoDisponible, saldoTrasCompra, hasItems, modoPago,
  tarjetaInput, buscandoTarjeta,
  clienteDirecto, clienteSearch, clienteResultados, buscandoCliente,
  scannerRef, onChangeTarjetaInput, onScanEnter,
  onChangeClienteSearch, onSelectCliente, onClearCliente, onVentaStartTime,
}: Props) {
  const [focused, setFocused] = useState(false)
  const navigate = useNavigate()
  const fotoBlobUrl = useAuthenticatedImage(tarjeta?.hijo_foto)

  return (
    <aside className="w-64 lg:w-80 bg-white border-r-2 border-slate-200 flex flex-col shrink-0">

      <div className="p-3 border-b border-slate-100">
        <input
          ref={scannerRef}
          value={tarjetaInput}
          onChange={e => onChangeTarjetaInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter') onScanEnter() }}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Escanear tarjeta o código…"
          disabled={buscandoTarjeta}
          className={[
            'w-full bg-slate-50 border-2 rounded-xl px-4 py-3 text-base text-slate-900 placeholder:text-slate-400 outline-none transition-all',
            focused ? 'border-blue-500 ring-4 ring-blue-400/20' : 'border-slate-300',
          ].join(' ')}
        />
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {tarjeta ? (
          <>
            <div className="text-center">
              {fotoBlobUrl ? (
                <img src={fotoBlobUrl} alt={tarjeta.hijo_nombre ?? undefined}
                  className="w-32 h-32 rounded-full object-cover border-4 border-blue-400 mx-auto mb-3 shadow-md" />
              ) : (
                <div className="w-32 h-32 rounded-full bg-slate-100 border-4 border-blue-300 flex items-center justify-center mx-auto mb-3">
                  <User size={64} className="text-slate-400" />
                </div>
              )}
              <p className="text-2xl font-black text-slate-900 leading-tight">{tarjeta.hijo_nombre ?? tarjeta.cliente_nombre}</p>
              {tarjeta.hijo_grado
                ? <p className="text-slate-500 text-base mt-0.5">{tarjeta.hijo_grado}</p>
                : <p className="text-slate-400 text-sm mt-0.5">Docente / Funcionario</p>
              }
              <p className="text-slate-300 text-xs mt-1 font-mono tracking-wider">{tarjeta.nro_tarjeta}</p>
            </div>

            {tarjeta.es_alumno && tarjeta.hijo_cumple_hoy && (
              <div className="bg-pink-50 border-2 border-pink-300 rounded-xl p-3 text-center">
                <span className="text-pink-700 text-sm font-black">🎂 ¡Hoy cumple años!</span>
              </div>
            )}

            {tarjeta.es_alumno && tarjeta.hijo_restricciones?.length > 0 && (
              <div className="bg-red-50 border-2 border-red-300 rounded-xl p-3 space-y-2">
                <div className="flex items-center gap-1.5">
                  <AlertTriangle size={15} className="text-red-500 shrink-0" />
                  <span className="text-red-700 text-sm font-black uppercase tracking-wide">
                    {tarjeta.hijo_restricciones.length} Restricción{tarjeta.hijo_restricciones.length > 1 ? 'es' : ''}
                  </span>
                </div>
                {tarjeta.hijo_restricciones.map(r => (
                  <div key={r.id_restriccion} className="flex items-center gap-2">
                    <span className="text-sm">🚫</span>
                    <span className="text-red-700 text-sm font-semibold leading-tight flex-1">{r.descripcion || r.tipo}</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                      r.severidad === 'CRITICA' ? 'bg-red-600 text-white' :
                      r.severidad === 'ALTA'    ? 'bg-orange-500 text-white' : 'bg-slate-200 text-slate-600'
                    }`}>{r.severidad}</span>
                  </div>
                ))}
              </div>
            )}

            <div className={`rounded-2xl p-4 border-2 ${
              (saldoDisponible ?? 0) < 5000  ? 'bg-red-50 border-red-300' :
              (saldoDisponible ?? 0) < 15000 ? 'bg-yellow-50 border-yellow-300' : 'bg-green-50 border-green-300'
            }`}>
              <div className="flex items-baseline justify-between mb-1">
                <p className="text-slate-500 text-xs uppercase tracking-widest font-bold">Saldo actual</p>
                <p className={`text-3xl font-black tabular-nums leading-none ${
                  (saldoDisponible ?? 0) < 5000  ? 'text-red-600' :
                  (saldoDisponible ?? 0) < 15000 ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {gs(tarjeta.saldo_disponible || tarjeta.saldo_actual)}
                </p>
              </div>
              {hasItems && saldoTrasCompra !== null && modoPago === 'PREPAGO' && (
                <div className="flex items-baseline justify-between border-t border-current/20 pt-1.5 mt-1.5">
                  <p className="text-slate-500 text-xs uppercase tracking-widest font-bold">Tras compra</p>
                  <p className={`text-xl font-black tabular-nums ${saldoTrasCompra < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                    {gs(saldoTrasCompra)}
                  </p>
                </div>
              )}
              {Number(tarjeta.limite_credito) > 0 && (
                <p className="text-xs text-slate-400 mt-1.5">
                  Crédito disponible: <span className="font-bold">{gs(tarjeta.limite_credito)}</span>
                </p>
              )}
            </div>

            <div className={`grid gap-2 ${tarjeta.es_alumno ? 'grid-cols-2' : 'grid-cols-1'}`}>
              <button
                onClick={() => navigate(`/carga-saldo?tarjeta=${encodeURIComponent(tarjeta.nro_tarjeta)}&tipo=CANTINA`)}
                className="flex flex-col items-center justify-center gap-1 py-2.5 rounded-xl bg-blue-50 hover:bg-blue-100 border border-blue-200 text-blue-700 text-xs font-bold transition-colors cursor-pointer"
              >
                <Wallet size={18} />
                Cargar saldo cantina
              </button>
              {tarjeta.es_alumno && (
                <button
                  onClick={() => navigate(`/carga-saldo?tarjeta=${encodeURIComponent(tarjeta.nro_tarjeta)}&tipo=ALMUERZO`)}
                  className="flex flex-col items-center justify-center gap-1 py-2.5 rounded-xl bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-700 text-xs font-bold transition-colors cursor-pointer"
                >
                  <UtensilsCrossed size={18} />
                  Cargar saldo almuerzo
                </button>
              )}
            </div>

            <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-4 py-2">
              <div className="w-2.5 h-2.5 rounded-full bg-green-500 shrink-0" />
              <span className="text-green-700 text-sm font-bold">Tarjeta ACTIVA</span>
            </div>

            {tarjeta.es_alumno && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg px-4 py-2.5">
                <p className="text-slate-400 text-xs uppercase tracking-wide font-bold mb-0.5">Padre/Tutor</p>
                <p className="text-slate-800 text-sm font-semibold leading-tight">{tarjeta.cliente_nombre}</p>
              </div>
            )}
          </>
        ) : (modoPago === 'MEDIO' || modoPago === 'CREDITO') ? (
          <div className="space-y-3">
            {clienteDirecto ? (
              <>
                <div className="text-center pt-2">
                  <div className="w-20 h-20 rounded-full bg-emerald-100 border-4 border-emerald-400 flex items-center justify-center mx-auto mb-3">
                    <User size={44} className="text-emerald-600" />
                  </div>
                  <p className="text-xl font-black text-slate-900 leading-tight">{clienteDirecto.nombre_completo}</p>
                  <p className="text-slate-400 text-sm mt-0.5">{clienteDirecto.ruc_ci}</p>
                </div>
                <div className={`flex items-center gap-2 rounded-lg px-4 py-2 ${modoPago === 'CREDITO' ? 'bg-orange-50 border border-orange-200' : 'bg-emerald-50 border border-emerald-200'}`}>
                  <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${modoPago === 'CREDITO' ? 'bg-orange-500' : 'bg-emerald-500'}`} />
                  <span className={`text-sm font-bold ${modoPago === 'CREDITO' ? 'text-orange-700' : 'text-emerald-700'}`}>
                    {modoPago === 'CREDITO' ? 'Crédito / Cuenta corriente' : 'Venta directa'}
                  </span>
                </div>
                <button
                  onClick={onClearCliente}
                  className="w-full py-2 rounded-xl bg-slate-100 hover:bg-red-50 text-slate-500 hover:text-red-600 text-sm font-bold transition-colors cursor-pointer"
                >
                  Cambiar cliente
                </button>
              </>
            ) : (
              <>
                <p className="text-slate-500 text-sm font-bold uppercase tracking-wide">Buscar cliente</p>
                <input
                  value={clienteSearch}
                  onChange={e => onChangeClienteSearch(e.target.value)}
                  placeholder="Nombre o cédula..."
                  className="w-full bg-slate-50 border-2 border-slate-300 rounded-xl px-3 py-2.5 text-base text-slate-900 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-400/20"
                />
                {buscandoCliente && <p className="text-xs text-slate-400">Buscando...</p>}
                {clienteResultados.length > 0 && (
                  <ul className="border border-slate-200 rounded-xl overflow-hidden">
                    {clienteResultados.map(c => (
                      <li key={c.id_cliente}>
                        <button
                          type="button"
                          onClick={() => { onSelectCliente(c); onVentaStartTime() }}
                          className="w-full text-left px-3 py-2.5 hover:bg-emerald-50 cursor-pointer border-b border-slate-100 last:border-0"
                        >
                          <p className="text-sm font-semibold text-slate-800">{c.nombre_completo}</p>
                          <p className="text-xs text-slate-400">{c.ruc_ci}</p>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
                {!buscandoCliente && clienteSearch.length > 1 && clienteResultados.length === 0 && (
                  <p className="text-xs text-slate-400 text-center">Sin resultados</p>
                )}
                <p className="text-xs text-slate-300 text-center">O escanear tarjeta RFID</p>
              </>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-56 text-center">
            <CreditCard size={72} className="text-slate-200 mb-4" />
            <p className="text-slate-600 text-xl font-bold">Sin alumno</p>
            <p className="text-slate-400 text-base mt-1">Escanear tarjeta para comenzar</p>
          </div>
        )}
      </div>
    </aside>
  )
}
