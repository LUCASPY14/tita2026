/**
 * Locale-aware formatting helpers.
 *
 * Single source of truth for currency and date display.
 * To adapt for a different school/country, change LOCALE and CURRENCY_SUFFIX here.
 */

const LOCALE = 'es-PY'
const CURRENCY_SUFFIX = ' Gs.'

/** Formats a Guaraní amount: 150000 → "150.000 Gs." */
export function formatCurrency(amount: number): string {
  return amount.toLocaleString(LOCALE) + CURRENCY_SUFFIX
}

/** Formats an ISO date string: "2026-06-22T..." → "22/06/2026" */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(LOCALE, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

/** Formats an ISO date-time string: "2026-06-22T14:30:00Z" → "22/06/2026, 14:30" */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(LOCALE, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Short date for compact displays: "2026-06-22" → "22 jun." */
export function formatDateShort(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(LOCALE, { day: 'numeric', month: 'short' })
}
