import { beforeEach, describe, it, expect, vi } from 'vitest'

vi.mock('../../services/api', () => ({
  default: { get: vi.fn() },
}))

import api from '../../services/api'
import { useCatalogoStore } from '../catalogoStore'

const PRODUCTO = {
  id: 1, descripcion: 'Agua', precio_venta: 1000, categoria: 1, activo: true, requiere_stock: true,
}
const CATEGORIA = { id: 1, nombre: 'Bebidas' }
const MEDIO = { id: 1, descripcion: 'Efectivo', activo: true }

beforeEach(() => {
  localStorage.clear()
  useCatalogoStore.getState().invalidate()
  vi.clearAllMocks()
})

describe('catalogoStore — getProductos', () => {
  it('fetches and caches data on first call', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [PRODUCTO] } })

    const result = await useCatalogoStore.getState().getProductos()

    expect(result).toEqual([PRODUCTO])
    expect(vi.mocked(api.get)).toHaveBeenCalledTimes(1)
    expect(useCatalogoStore.getState().productos?.data).toEqual([PRODUCTO])
  })

  it('returns cached data without another API call when cache is fresh', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { results: [PRODUCTO] } })

    await useCatalogoStore.getState().getProductos()
    await useCatalogoStore.getState().getProductos()

    expect(vi.mocked(api.get)).toHaveBeenCalledTimes(1)
  })

  it('re-fetches when cache is expired (fetchedAt = 0)', async () => {
    useCatalogoStore.setState({
      productos: { data: [PRODUCTO], fetchedAt: 0 },
    })
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [PRODUCTO] } })

    await useCatalogoStore.getState().getProductos()

    expect(vi.mocked(api.get)).toHaveBeenCalledTimes(1)
  })

  it('normalizes a paginated {results:[]} response', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [PRODUCTO], count: 1 } })
    const result = await useCatalogoStore.getState().getProductos()
    expect(result).toEqual([PRODUCTO])
  })

  it('normalizes a direct array response', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [PRODUCTO] })
    const result = await useCatalogoStore.getState().getProductos()
    expect(result).toEqual([PRODUCTO])
  })

  it('returns stale data on API error', async () => {
    useCatalogoStore.setState({
      productos: { data: [PRODUCTO], fetchedAt: 0 },
    })
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'))

    const result = await useCatalogoStore.getState().getProductos()
    expect(result).toEqual([PRODUCTO])
  })
})

describe('catalogoStore — getCategorias', () => {
  it('fetches and caches categorias', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [CATEGORIA] } })

    const result = await useCatalogoStore.getState().getCategorias()

    expect(result).toEqual([CATEGORIA])
    expect(useCatalogoStore.getState().categorias?.data).toEqual([CATEGORIA])
  })

  it('returns cached categorias without extra fetch', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [CATEGORIA] })

    await useCatalogoStore.getState().getCategorias()
    await useCatalogoStore.getState().getCategorias()

    expect(vi.mocked(api.get)).toHaveBeenCalledTimes(1)
  })
})

describe('catalogoStore — getMediosPago', () => {
  it('fetches and caches medios de pago', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [MEDIO] })

    const result = await useCatalogoStore.getState().getMediosPago()

    expect(result).toEqual([MEDIO])
  })

  it('devuelve array vacío y limpia loadingMediosPago al fallar la API sin caché', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'))

    const result = await useCatalogoStore.getState().getMediosPago()

    expect(result).toEqual([])
    expect(useCatalogoStore.getState().loadingMediosPago).toBe(false)
  })
})

describe('catalogoStore — getCategorias (error)', () => {
  it('devuelve array vacío y limpia loadingCategorias al fallar la API sin caché', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Network error'))

    const result = await useCatalogoStore.getState().getCategorias()

    expect(result).toEqual([])
    expect(useCatalogoStore.getState().loadingCategorias).toBe(false)
  })
})

describe('catalogoStore — invalidate', () => {
  it('clears all cached data and resets loading flags', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] })
    await useCatalogoStore.getState().getProductos()

    useCatalogoStore.getState().invalidate()

    const state = useCatalogoStore.getState()
    expect(state.productos).toBeNull()
    expect(state.categorias).toBeNull()
    expect(state.mediosPago).toBeNull()
    expect(state.loadingProductos).toBe(false)
    expect(state.loadingCategorias).toBe(false)
    expect(state.loadingMediosPago).toBe(false)
  })

  it('forces a new fetch after invalidation', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { results: [PRODUCTO] } })

    await useCatalogoStore.getState().getProductos()
    useCatalogoStore.getState().invalidate()
    await useCatalogoStore.getState().getProductos()

    expect(vi.mocked(api.get)).toHaveBeenCalledTimes(2)
  })
})
