import { describe, it, expect, vi, afterEach } from 'vitest'
import { today } from '../reportesUtils'

afterEach(() => {
  vi.useRealTimers()
})

describe('reportesUtils — today()', () => {
  it('a media mañana, devuelve la fecha local de hoy', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-22T14:00:00-03:00')) // 14:00 Paraguay
    expect(today()).toBe('2026-09-22')
  })

  it('a las 21:30 hora Paraguay (00:30 UTC del día siguiente), sigue devolviendo la fecha de HOY, no la de mañana', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-22T21:30:00-03:00'))
    expect(today()).toBe('2026-09-22')
  })
})
