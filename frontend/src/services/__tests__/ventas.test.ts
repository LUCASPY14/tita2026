import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import api from '../api'
import ventasService, { type VentaPayload, type Venta } from '../ventas'

const PAYLOAD: VentaPayload = {
  tarjeta: 'CARD001',
  detalles: [{ producto: 1, cantidad: 2 }],
  medio_pago: 'TARJETA',
}

describe('ventasService', () => {
  beforeEach(() => vi.clearAllMocks())

  it('crear — llama al endpoint correcto con el payload', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} })
    await ventasService.crear(PAYLOAD)
    expect(api.post).toHaveBeenCalledWith('/ventas/ventas/', PAYLOAD, { timeout: 6000 })
  })

  it('crear — usa timeout por defecto de 6000ms', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} })
    await ventasService.crear(PAYLOAD)
    expect(api.post).toHaveBeenCalledWith(expect.any(String), expect.any(Object), { timeout: 6000 })
  })

  it('crear — acepta timeout personalizado', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {} })
    await ventasService.crear(PAYLOAD, 12_000)
    expect(api.post).toHaveBeenCalledWith('/ventas/ventas/', PAYLOAD, { timeout: 12_000 })
  })

  it('crear — devuelve la venta creada por el servidor', async () => {
    const venta: Venta = { id: 42, tarjeta: 'CARD001', total: 6_000, fecha: '2026-06-18', estado: 'COMPLETADA' }
    vi.mocked(api.post).mockResolvedValue({ data: venta })
    const result = await ventasService.crear(PAYLOAD)
    expect(result.data).toEqual(venta)
  })
})
