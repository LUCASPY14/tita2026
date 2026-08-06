import type { ReactNode } from 'react'
import LogoSinFondo from './LogoSinFondo'

interface Badge {
  text: string
  className: string
}

interface Props {
  /** Texto opcional debajo del logo (ej: "Portal de Padres") */
  caption?: string
  /** Etiqueta de color opcional que identifica la puerta de acceso (Administración, Caja/POS, Cobranzas) */
  badge?: Badge
  children: ReactNode
}

/**
 * Fondo y logo compartidos por las pantallas de login/recuperación de
 * contraseña. Usa LogoSinFondo (mismo tratamiento que el home): el fondo
 * sólido del PNG se convierte a blanco puro por canvas y se combina con
 * mix-blend-mode:multiply, así el logo flota de verdad sin caja visible,
 * sin importar el color de fondo de la página.
 */
export default function AuthShell({ caption, badge, children }: Props) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#fef9f0] px-4 py-10">
      <div className="text-center mb-6">
        <LogoSinFondo
          src="/logo-cantina.png"
          alt="La Cantina de Tita"
          className="w-56 sm:w-64 h-auto mix-blend-multiply mx-auto"
        />
        {badge && (
          <span className={`inline-block mt-3 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${badge.className}`}>
            {badge.text}
          </span>
        )}
        {caption && <p className="text-sm text-slate-500 mt-2">{caption}</p>}
      </div>
      {children}
    </div>
  )
}
