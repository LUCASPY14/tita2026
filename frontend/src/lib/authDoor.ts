// "Puerta" de acceso por la que se logueó el usuario (/login, /pos, /cobranzas,
// /comedor-acceso) — cada una tiene su propio branding (ver Login.tsx). Se
// recuerda en localStorage para que, si la sesión se cierra sola (timeout de
// inactividad, sesión reemplazada desde otro dispositivo) o manualmente, la
// pantalla vuelva a la puerta correcta en vez de siempre a la genérica — clave
// en una PC dedicada (ej. la del comedor) que debe quedar identificada.

const DOOR_KEY = 'auth_door'

const DOOR_ROUTES: Record<string, string> = {
  admin: '/login',
  pos: '/pos',
  cobranzas: '/cobranzas',
  comedor: '/comedor-acceso',
}

export function setAuthDoor(variant: string): void {
  try {
    localStorage.setItem(DOOR_KEY, variant)
  } catch {
    // localStorage puede fallar (modo privado, cuota) — no es crítico
  }
}

export function getAuthDoorRoute(): string {
  try {
    const variant = localStorage.getItem(DOOR_KEY)
    if (variant && DOOR_ROUTES[variant]) return DOOR_ROUTES[variant]
  } catch {
    // ignorar
  }
  return '/login'
}
