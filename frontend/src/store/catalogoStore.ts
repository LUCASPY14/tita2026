import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import api from '../services/api'

const TTL_MS = 5 * 60 * 1000 // 5 minutos

interface Producto {
  id: number
  descripcion: string
  precio_venta: number
  categoria: number | null
  activo: boolean
  requiere_stock: boolean
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
        if (state.loadingProductos) {
          await new Promise((r) => setTimeout(r, 300))
          return get().productos?.data ?? []
        }
        set({ loadingProductos: true })
        try {
          const { data } = await api.get('/productos/productos/?activo=true&page_size=500')
          const items = data.results ?? data
          set({ productos: { data: items, fetchedAt: Date.now() }, loadingProductos: false })
          return items
        } catch {
          set({ loadingProductos: false })
          return get().productos?.data ?? []
        }
      },

      getCategorias: async () => {
        const state = get()
        if (!isExpired(state.categorias) && state.categorias) return state.categorias.data
        if (state.loadingCategorias) {
          await new Promise((r) => setTimeout(r, 300))
          return get().categorias?.data ?? []
        }
        set({ loadingCategorias: true })
        try {
          const { data } = await api.get('/productos/categorias/?page_size=200')
          const items = data.results ?? data
          set({ categorias: { data: items, fetchedAt: Date.now() }, loadingCategorias: false })
          return items
        } catch {
          set({ loadingCategorias: false })
          return get().categorias?.data ?? []
        }
      },

      getMediosPago: async () => {
        const state = get()
        if (!isExpired(state.mediosPago) && state.mediosPago) return state.mediosPago.data
        if (state.loadingMediosPago) {
          await new Promise((r) => setTimeout(r, 300))
          return get().mediosPago?.data ?? []
        }
        set({ loadingMediosPago: true })
        try {
          const { data } = await api.get('/core/medios-pago/?activo=true&page_size=100')
          const items = data.results ?? data
          set({ mediosPago: { data: items, fetchedAt: Date.now() }, loadingMediosPago: false })
          return items
        } catch {
          set({ loadingMediosPago: false })
          return get().mediosPago?.data ?? []
        }
      },

      invalidate: () => set({ productos: null, categorias: null, mediosPago: null }),
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
