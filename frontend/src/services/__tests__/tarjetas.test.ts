import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}))

import api from '../api'
import tarjetasService from '../tarjetas'

const NRO = 'T1234567'
const PAGINATED_EMPTY = { count: 0, results: [], next: null, previous: null }

describe('tarjetasService', () => {
  beforeEach(() => vi.clearAllMocks())

  describe('buscar', () => {
    it('llama al endpoint con el parámetro search', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
      await tarjetasService.buscar('Lucas')
      expect(api.get).toHaveBeenCalledWith('/core/tarjetas/', { params: { search: 'Lucas' } })
    })
  })

  describe('listar', () => {
    it('llama al endpoint sin params cuando no se pasan', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
      await tarjetasService.listar()
      expect(api.get).toHaveBeenCalledWith('/core/tarjetas/', { params: undefined })
    })

    it('pasa params adicionales al endpoint', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
      await tarjetasService.listar({ estado: 'ACTIVA', page: 1 })
      expect(api.get).toHaveBeenCalledWith('/core/tarjetas/', { params: { estado: 'ACTIVA', page: 1 } })
    })
  })

  describe('getByNro', () => {
    it('llama al endpoint con el número de tarjeta', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: {} })
      await tarjetasService.getByNro(NRO)
      expect(api.get).toHaveBeenCalledWith(`/core/tarjetas/${NRO}/`)
    })
  })

  describe('crear', () => {
    it('envía los datos al endpoint de tarjetas', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: {} })
      const payload = { nro_tarjeta: NRO, hijo: 1 }
      await tarjetasService.crear(payload)
      expect(api.post).toHaveBeenCalledWith('/core/tarjetas/', payload)
    })
  })

  describe('actualizar', () => {
    it('envía PATCH con los datos al endpoint de la tarjeta', async () => {
      vi.mocked(api.patch).mockResolvedValue({ data: {} })
      const delta = { estado: 'BLOQUEADA' }
      await tarjetasService.actualizar(NRO, delta)
      expect(api.patch).toHaveBeenCalledWith(`/core/tarjetas/${NRO}/`, delta)
    })
  })

  describe('getMovimientos', () => {
    it('llama al endpoint con nro_tarjeta y page_size por defecto', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
      await tarjetasService.getMovimientos(NRO)
      expect(api.get).toHaveBeenCalledWith('/core/movimientos-tarjeta/', {
        params: { tarjeta: NRO, page_size: 20 },
      })
    })

    it('acepta page_size personalizado', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
      await tarjetasService.getMovimientos(NRO, 50)
      expect(api.get).toHaveBeenCalledWith('/core/movimientos-tarjeta/', {
        params: { tarjeta: NRO, page_size: 50 },
      })
    })
  })

  describe('getCargas', () => {
    it('llama al endpoint de cargas con nro_tarjeta', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
      await tarjetasService.getCargas(NRO)
      expect(api.get).toHaveBeenCalledWith('/core/cargas-saldo/', {
        params: { tarjeta: NRO, page_size: 20 },
      })
    })
  })

  describe('crearCarga', () => {
    it('envía la carga al endpoint de cargas-saldo', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: {} })
      const carga = { tarjeta: NRO, monto_cargado: 100_000, metodo_pago: 'EFECTIVO' }
      await tarjetasService.crearCarga(carga)
      expect(api.post).toHaveBeenCalledWith('/core/cargas-saldo/', carga)
    })
  })

  describe('confirmarCarga', () => {
    it('envía POST al endpoint de confirmación con el id', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: {} })
      await tarjetasService.confirmarCarga(7)
      expect(api.post).toHaveBeenCalledWith('/core/cargas-saldo/7/confirmar/', {})
    })

    it('incluye nro_factura en el body cuando se provee', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: {} })
      await tarjetasService.confirmarCarga(7, 'F-001')
      expect(api.post).toHaveBeenCalledWith('/core/cargas-saldo/7/confirmar/', { nro_factura: 'F-001' })
    })
  })
})
