import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import api from '../api'
import cajasService, { type CierreCaja } from '../cajas'

describe('cajasService', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getMiCaja — llama al endpoint correcto', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: {} })
    await cajasService.getMiCaja()
    expect(api.get).toHaveBeenCalledWith('/contabilidad/cierres-caja/mi-caja/')
  })

  it('getMiCaja — devuelve el dato del servidor', async () => {
    const caja: CierreCaja = {
      id_cierre: 5,
      caja: 2,
      caja_nombre: 'Caja Principal',
      empleado: 3,
      monto_inicial: 100_000,
      monto_final: null,
      estado: 'ABIERTO',
      fecha_apertura: '2026-06-18T08:00:00Z',
      fecha_cierre: null,
    }
    vi.mocked(api.get).mockResolvedValue({ data: caja })
    const result = await cajasService.getMiCaja()
    expect(result.data).toEqual(caja)
  })
})
