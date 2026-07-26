import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Store } from 'lucide-react'

export default function CajaBlockedScreen() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  return (
    <div className="fixed inset-0 bg-slate-100 flex flex-col items-center justify-center" style={{ zIndex: 100 }}>
      <div className="bg-white rounded-3xl shadow-2xl p-12 max-w-md w-full mx-4 text-center">
        <div className="w-24 h-24 rounded-full bg-orange-100 flex items-center justify-center mx-auto mb-6">
          <Store size={52} className="text-orange-500" />
        </div>
        <h2 className="text-3xl font-black text-slate-900 mb-2">Caja no iniciada</h2>
        <p className="text-slate-500 text-lg mb-8">{t('pos.cashRegister')}</p>
        <div className="flex flex-col gap-3">
          <button
            onClick={() => navigate('/cajas')}
            className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white font-black text-lg rounded-2xl transition-colors cursor-pointer"
          >
            Ir a Cajas
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full py-3 bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold rounded-2xl transition-colors cursor-pointer"
          >
            Volver al inicio
          </button>
        </div>
      </div>
    </div>
  )
}
