import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import api from '../api'
import clientesService, { type Hijo, type PaginatedResponse } from '../clientes'

const PAGINATED_EMPTY: PaginatedResponse<Hijo> = { count: 0, results: [], next: null, previous: null }

describe('clientesService', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getHijos — llama al endpoint correcto sin params', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
    await clientesService.getHijos()
    expect(api.get).toHaveBeenCalledWith('/clientes/hijos/', { params: undefined })
  })

  it('getHijos — pasa params al endpoint', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: PAGINATED_EMPTY })
    await clientesService.getHijos({ activo: true, page: 2 })
    expect(api.get).toHaveBeenCalledWith('/clientes/hijos/', { params: { activo: true, page: 2 } })
  })

  it('getHijos — devuelve la respuesta paginada del servidor', async () => {
    const hijo: Hijo = {
      id: 1, nombre: 'Lucas', apellido: 'García',
      nombre_completo: 'Lucas García',
      grado: 3, grado_nombre: '3° A',
      cliente_responsable: 10, activo: true,
    }
    const mockData: PaginatedResponse<Hijo> = { count: 1, results: [hijo], next: null, previous: null }
    vi.mocked(api.get).mockResolvedValue({ data: mockData })
    const result = await clientesService.getHijos()
    expect(result.data.count).toBe(1)
    expect(result.data.results[0]).toEqual(hijo)
  })
})
