/**
 * Fecha "de hoy" en hora local (Paraguay), como string "YYYY-MM-DD".
 *
 * `new Date().toISOString()` convierte a UTC antes de recortar la fecha —
 * en Paraguay (UTC-3), entre las 21:00 y 23:59 locales eso ya cae en el día
 * siguiente en UTC. Construir la fecha a mano con los getters locales evita
 * el corrimiento. Única fuente de verdad: no reimplementar esto en cada
 * archivo que necesite "hoy".
 */
export function todayISO(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** Fecha local `dias` días atrás (o adelante, con negativo), como "YYYY-MM-DD". */
export function isoDiasDesdeHoy(dias: number): string {
  const d = new Date()
  d.setDate(d.getDate() - dias)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
