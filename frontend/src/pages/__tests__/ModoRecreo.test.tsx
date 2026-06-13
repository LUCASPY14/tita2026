import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModoRecreo from '../ModoRecreo'

// ─── Globals ───────────────────────────────────────────────────────────────────

vi.stubGlobal('AudioContext', vi.fn(() => ({
  createOscillator: vi.fn(() => ({
    connect: vi.fn(), frequency: { value: 0 }, type: 'sine',
    start: vi.fn(), stop: vi.fn(),
  })),
  createGain: vi.fn(() => ({
    connect: vi.fn(),
    gain: { setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() },
  })),
  currentTime: 0,
  destination: {},
  close: vi.fn(),
})))

// ─── Mocks ─────────────────────────────────────────────────────────────────────

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

const mockGetProductos = vi.fn()
const mockGetCategorias = vi.fn()
vi.mock('../../store/catalogoStore', () => ({
  useCatalogoStore: () => ({ getProductos: mockGetProductos, getCategorias: mockGetCategorias }),
}))

import api from '../../services/api'

// ─── Fixtures ──────────────────────────────────────────────────────────────────

const PRODUCTOS = [
  { id: 1, codigo_barra: '001', descripcion: 'Jugo de naranja', precio_actual: '5000', categoria_nombre: 'bebidas' },
  { id: 2, codigo_barra: '002', descripcion: 'Sandwich de pollo', precio_actual: '8000', categoria_nombre: 'panaderia' },
]
const CATEGORIAS = [{ nombre: 'bebidas' }, { nombre: 'panaderia' }]
const CAJA = { id: 1, caja_nombre: 'Caja Principal', monto_inicial: '100000', fecha_apertura: '2026-06-13T08:00:00Z' }
const MEDIOS = [{ id: 1, descripcion: 'Efectivo', activo: true, requiere_validacion: false }]

function setupData() {
  // Ensure sales history is empty so favoritos don't appear unexpectedly
  localStorage.removeItem('recreo_sales_v2')
  localStorage.removeItem('recreo_daily_stats')
  mockGetProductos.mockResolvedValue(PRODUCTOS)
  mockGetCategorias.mockResolvedValue(CATEGORIAS)
  vi.mocked(api.get)
    .mockResolvedValueOnce({ data: { results: MEDIOS } })
    .mockResolvedValueOnce({ data: CAJA })
}

// Wait for products: use findAllByText to avoid failure on duplicates (favoritos + grid)
async function waitForProducts() {
  const matches = await screen.findAllByText('Jugo de naranja')
  expect(matches.length).toBeGreaterThan(0)
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.removeItem('recreo_sales_v2')
  localStorage.removeItem('recreo_daily_stats')
})

// ─── Tests ─────────────────────────────────────────────────────────────────────

describe('ModoRecreo — estado de carga', () => {
  it('muestra spinner mientras la caja está cargando', () => {
    mockGetProductos.mockReturnValue(new Promise(() => {}))
    mockGetCategorias.mockReturnValue(new Promise(() => {}))
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))

    const { container } = render(<ModoRecreo />)
    expect(container.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('muestra "Caja no iniciada" cuando no hay caja abierta', async () => {
    mockGetProductos.mockResolvedValue([])
    mockGetCategorias.mockResolvedValue([])
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockRejectedValueOnce(new Error('sin caja'))

    render(<ModoRecreo />)
    await screen.findByText('Caja no iniciada')
    expect(screen.getByText('Debés abrir una caja antes de usar el Modo Recreo.')).toBeInTheDocument()
  })
})

describe('ModoRecreo — interfaz POS', () => {
  it('muestra el catálogo de productos al cargar', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    expect(screen.queryAllByText('Sandwich de pollo').length).toBeGreaterThan(0)
  })

  it('muestra nombre de la caja en el header', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    expect(screen.getByText('Caja Principal')).toBeInTheDocument()
  })

  it('muestra "Sin productos" en el grid cuando no hay coincidencias en búsqueda', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    // "Sin productos" already appears once in the carrito vacío
    const initialCount = screen.queryAllByText('Sin productos').length
    await userEvent.type(screen.getByPlaceholderText(/Buscar producto/i), 'zzz')
    // After filtering, the product grid also shows "Sin productos" → count increases
    expect(screen.queryAllByText('Sin productos').length).toBeGreaterThan(initialCount)
  })

  it('filtra productos al escribir en el buscador', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    const initialCount = screen.queryAllByText('Sin productos').length
    await userEvent.type(screen.getByPlaceholderText(/Buscar producto/i), 'Jugo')
    // Grid has a matching result → count does NOT increase
    expect(screen.queryAllByText('Sin productos').length).toBe(initialCount)
    expect(screen.queryAllByText('Jugo de naranja').length).toBeGreaterThan(0)
  })

  it('muestra botones de categoría para todas las categorías', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    expect(screen.getByRole('button', { name: 'Todos' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'bebidas' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'panaderia' })).toBeInTheDocument()
  })

  it('filtra productos al seleccionar una categoría', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    const initialCount = screen.queryAllByText('Sin productos').length
    await userEvent.click(screen.getByRole('button', { name: 'bebidas' }))
    // Bebidas has matches → "Sin productos" count stays the same
    expect(screen.queryAllByText('Sin productos').length).toBe(initialCount)
    expect(screen.queryAllByText('Jugo de naranja').length).toBeGreaterThan(0)
  })
})

describe('ModoRecreo — navegación', () => {
  it('navega a /dashboard al hacer click en "Salir"', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    await userEvent.click(screen.getByText('Salir'))
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })

  it('navega a /cajas al hacer click en "Ir a Cajas" cuando no hay caja', async () => {
    mockGetProductos.mockResolvedValue([])
    mockGetCategorias.mockResolvedValue([])
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockRejectedValueOnce(new Error('no caja'))

    render(<ModoRecreo />)
    await screen.findByText('Ir a Cajas')
    await userEvent.click(screen.getByText('Ir a Cajas'))
    expect(mockNavigate).toHaveBeenCalledWith('/cajas')
  })

  it('navega a /dashboard desde pantalla sin caja', async () => {
    mockGetProductos.mockResolvedValue([])
    mockGetCategorias.mockResolvedValue([])
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockRejectedValueOnce(new Error('no caja'))

    render(<ModoRecreo />)
    await screen.findByText('Volver al inicio')
    await userEvent.click(screen.getByText('Volver al inicio'))
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
  })
})

describe('ModoRecreo — carrito', () => {
  it('muestra "0 productos" en el carrito al iniciar', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    expect(screen.getByText('0 productos')).toBeInTheDocument()
  })

  it('el input de búsqueda de producto está disponible', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    expect(screen.getByPlaceholderText(/Buscar producto/i)).toBeInTheDocument()
  })

  it('muestra etiqueta "Modo Recreo" en el header', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    expect(screen.getByText('Modo Recreo')).toBeInTheDocument()
  })
})
