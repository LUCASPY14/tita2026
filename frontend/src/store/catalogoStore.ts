import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import api from '../services/api'

const TTL_MS = 5 * 60 * 1000 // 5 minutos

interface Producto {
  id: number
  descripcion: string
  precio_venta: number
  precio_actual?: string | number
  categoria: number | null
  categoria_nombre?: string
  codigo_barra?: string | null
  codigo?: string | null
  activo: boolean
  requiere_stock: boolean
  es_servicio?: boolean
}

interface Categoria {
  id: number
  nombre: string
}

interface MedioPago {
  id: number
  descripcion: string
  activo: boolean
}

interface CacheEntry<T> {
  data: T[]
  fetchedAt: number
}

interface CatalogoState {
  productos: CacheEntry<Producto> | null
  categorias: CacheEntry<Categoria> | null
  mediosPago: CacheEntry<MedioPago> | null
  loadingProductos: boolean
  loadingCategorias: boolean
  loadingMediosPago: boolean

  getProductos: () => Promise<Producto[]>
  getCategorias: () => Promise<Categoria[]>
  getMediosPago: () => Promise<MedioPago[]>
  invalidate: () => void
}

function isExpired(entry: CacheEntry<unknown> | null): boolean {
  if (!entry) return true
  return Date.now() - entry.fetchedAt > TTL_MS
}

function normalize<T>(data: unknown): T[] {
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    const paged = data as { results?: unknown }
    if (Array.isArray(paged.results)) return paged.results as T[]
  }
  return Array.isArray(data) ? (data as T[]) : []
}

// Module-level pending promises deduplicate concurrent callers during a single fetch
let pendingProductos: Promise<Producto[]> | null = null
let pendingCategorias: Promise<Categoria[]> | null = null
let pendingMediosPago: Promise<MedioPago[]> | null = null

export const useCatalogoStore = create<CatalogoState>()(
  persist(
    (set, get) => ({
      productos: null,
      categorias: null,
      mediosPago: null,
      loadingProductos: false,
      loadingCategorias: false,
      loadingMediosPago: false,

      getProductos: async () => {
        const state = get()
        if (!isExpired(state.productos) && state.productos) return state.productos.data
        if (pendingProductos) return pendingProductos
        pendingProductos = (async () => {
          set({ loadingProductos: true })
          try {
            const { data } = await api.get('/productos/productos/?activo=true&page_size=500')
            const items = normalize<Producto>(data)
            set({ productos: { data: items, fetchedAt: Date.now() }, loadingProductos: false })
            return items
          } catch {
            set({ loadingProductos: false })
            return get().productos?.data ?? []
          } finally {
            pendingProductos = null
          }
        })()
        return pendingProductos
      },

      getCategorias: async () => {
        const state = get()
        if (!isExpired(state.categorias) && state.categorias) return state.categorias.data
        if (pendingCategorias) return pendingCategorias
        pendingCategorias = (async () => {
          set({ loadingCategorias: true })
          try {
            const { data } = await api.get('/productos/categorias/?page_size=200')
            const items = normalize<Categoria>(data)
            set({ categorias: { data: items, fetchedAt: Date.now() }, loadingCategorias: false })
            return items
          } catch {
            set({ loadingCategorias: false })
            return get().categorias?.data ?? []
          } finally {
            pendingCategorias = null
          }
        })()
        return pendingCategorias
      },

      getMediosPago: async () => {
        const state = get()
        if (!isExpired(state.mediosPago) && state.mediosPago) return state.mediosPago.data
        if (pendingMediosPago) return pendingMediosPago
        pendingMediosPago = (async () => {
          set({ loadingMediosPago: true })
          try {
            const { data } = await api.get('/core/medios-pago/?activo=true&page_size=100')
            const items = normalize<MedioPago>(data)
            set({ mediosPago: { data: items, fetchedAt: Date.now() }, loadingMediosPago: false })
            return items
          } catch {
            set({ loadingMediosPago: false })
            return get().mediosPago?.data ?? []
          } finally {
            pendingMediosPago = null
          }
        })()
        return pendingMediosPago
      },

      invalidate: () => set({
        productos: null,
        categorias: null,
        mediosPago: null,
        loadingProductos: false,
        loadingCategorias: false,
        loadingMediosPago: false,
      }),
    }),
    {
      name: 'catalogo-cache',
      storage: createJSONStorage(() => localStorage),
      // Solo persistir los datos, no los estados de loading
      partialize: (state) => ({
        productos: state.productos,
        categorias: state.categorias,
        mediosPago: state.mediosPago,
      }),
    }
  )
)
