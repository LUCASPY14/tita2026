/** "+595981410938" → "+595 981 410 938". Si no matchea el formato, devuelve el valor tal cual. */
export function formatTelefonoPy(raw: string): string {
  const m = raw.match(/^(\+\d{3})(\d{3})(\d{3})(\d+)$/)
  return m ? m.slice(1).join(' ') : raw
}
