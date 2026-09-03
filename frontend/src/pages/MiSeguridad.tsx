import TabSeguridad from './configuracion/TabSeguridad'

export default function MiSeguridad() {
  return (
    <div className="p-4 md:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Mi seguridad</h1>
        <p className="text-base text-slate-500 mt-0.5">
          Configurá la verificación en dos pasos (2FA) para proteger tu cuenta.
        </p>
      </div>
      <TabSeguridad />
    </div>
  )
}
