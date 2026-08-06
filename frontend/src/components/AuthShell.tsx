import type { ReactNode } from 'react'

interface Props {
  /** Texto opcional debajo del logo (ej: "Portal de Padres", "Sistema de Gestión") */
  caption?: string
  children: ReactNode
}

/**
 * Fondo y logo compartidos por las pantallas de login/recuperación de
 * contraseña. El logo flota directamente sobre el mismo degradé crema del
 * home (sin caja blanca detrás) usando mix-blend-multiply.
 */
export default function AuthShell({ caption, children }: Props) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[radial-gradient(ellipse_110%_120%_at_50%_-10%,_#fef3c7_0%,_#fef9f0_55%,_#fffbf0_100%)] px-4 py-10">
      <div className="text-center mb-6">
        <img
          src="/logo-cantina.png"
          alt="La Cantina de Tita"
          className="w-56 sm:w-64 h-auto mix-blend-multiply mx-auto"
        />
        {caption && <p className="text-sm text-slate-500 mt-1">{caption}</p>}
      </div>
      {children}
    </div>
  )
}
