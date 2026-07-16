import { render, screen, waitFor, within } from '@testing-library/react'
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
  default: { error: vi.fn(), success: vi.fn(), dismiss: vi.fn() },
}))

vi.mock('../../hooks/useOfflineQueue', () => ({
  useOfflineQueue: () => ({ isOnline: true, pendingCount: 0, syncing: false, syncNow: vi.fn(), enqueue: vi.fn() }),
}))

const mockGetProductos = vi.fn()
const mockGetCategorias = vi.fn()
vi.mock('../../store/catalogoStore', () => ({
  useCatalogoStore: () => ({ getProductos: mockGetProductos, getCategorias: mockGetCategorias }),
}))

const mockTarjetasBuscar = vi.fn()
vi.mock('../../services/tarjetas', () => ({
  default: { buscar: (...args: unknown[]) => mockTarjetasBuscar(...args) },
}))

const mockVentasCrear = vi.fn()
vi.mock('../../services/ventas', () => ({
  default: { crear: (...args: unknown[]) => mockVentasCrear(...args) },
}))

import api from '../../services/api'
import toast from 'react-hot-toast'

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

// ─── Fixtures tarjeta ─────────────────────────────────────────────────────────

const TARJETA_ACTIVA = {
  nro_tarjeta: 'T-00001',
  hijo_nombre: 'Ana López',
  hijo_grado: '4° A',
  cliente_id: 10,
  cliente_nombre: 'María López',
  saldo_actual: '80000',
  saldo_disponible: '80000',
  estado: 'ACTIVA',
  es_alumno: true,
  permite_saldo_negativo: false,
  lista_es_default: true,
  lista_precio_id: null,
  hijo_restricciones: [],
}

function setupDataConTarjeta() {
  setupData()
  mockTarjetasBuscar.mockResolvedValueOnce({
    data: { results: [TARJETA_ACTIVA] },
  })
}

async function escanearTarjeta() {
  const input = screen.getByPlaceholderText(/T-\|código/i)
    ?? screen.getByRole('textbox', { name: '' })
  // Buscar el input del scanner (primer input en el header del carrito)
  const inputs = document.querySelectorAll('input')
  const scannerInput = Array.from(inputs).find(
    (el) => el.placeholder?.includes('T-') || el.closest('[data-scanner]')
  )
  if (scannerInput) {
    await userEvent.type(scannerInput, 'T-00001{Enter}')
  }
  return screen.findByText('Ana López')
}

// ─── Tests: agregar al carrito ────────────────────────────────────────────────

describe('ModoRecreo — agregar productos al carrito', () => {
  it('agrega producto al carrito al hacer click en el botón del grid', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    // Los botones del grid de productos contienen el nombre del producto
    const botonesJugo = screen.getAllByText('Jugo de naranja')
    // Click en el primero que sea un button (grid, no carrito)
    const boton = botonesJugo.map(el => el.closest('button')).find(b => b)
    expect(boton).toBeTruthy()
    await userEvent.click(boton!)
    // El carrito pasa de "0 productos" a "1 producto"
    expect(screen.getByText(/1 producto/)).toBeInTheDocument()
  })

  it('incrementa la cantidad al agregar el mismo producto dos veces', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const boton = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(boton)
    await userEvent.click(boton)
    // El reducer de cantidad total muestra "2 productos"
    expect(screen.getByText('2 productos')).toBeInTheDocument()
  })

  it('actualiza el total al agregar un producto', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    // Antes de agregar: el precio del grid ya muestra "5.000 Gs." (precio del producto)
    const antesCount = screen.queryAllByText('5.000 Gs.').length
    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const boton = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(boton)
    // Después de agregar: el precio aparece también en el total del carrito
    expect(screen.queryAllByText('5.000 Gs.').length).toBeGreaterThan(antesCount)
  })
})

// ─── Tests: cobro sin tarjeta ─────────────────────────────────────────────────

describe('ModoRecreo — validaciones de cobro', () => {
  it('el botón COBRAR está deshabilitado con items pero sin tarjeta/cliente', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()

    // Agregar producto al carrito
    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const boton = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(boton)

    // Con items en carrito pero sin tarjeta, el botón sigue deshabilitado
    const btnCobrar = screen.getByRole('button', { name: /cobrar/i })
    expect(btnCobrar).toBeDisabled()
  })

  it('el botón COBRAR está deshabilitado con carrito vacío', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()
    const btnCobrar = screen.getByRole('button', { name: /cobrar/i })
    expect(btnCobrar).toBeDisabled()
  })
})

// ─── Tests: buscarTarjeta via mock directo ────────────────────────────────────

describe('ModoRecreo — búsqueda de tarjeta', () => {
  it('muestra error si la tarjeta no existe', async () => {
    setupData()
    mockTarjetasBuscar.mockResolvedValueOnce({ data: { results: [] } })
    render(<ModoRecreo />)
    await waitForProducts()

    const scannerInput = screen.getByPlaceholderText(/Escanear tarjeta/i)
    await userEvent.type(scannerInput, 'T-99999{Enter}')
    // Esperar la respuesta del mock
    expect(await screen.findByText('Modo Recreo')).toBeInTheDocument()
    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Tarjeta no encontrada')
  })

  it('muestra nombre del alumno al encontrar tarjeta activa', async () => {
    setupDataConTarjeta()
    render(<ModoRecreo />)
    await waitForProducts()

    const scannerInput = screen.getByPlaceholderText(/Escanear tarjeta/i)
    await userEvent.type(scannerInput, 'T-00001{Enter}')
    expect(await screen.findByText('Ana López')).toBeInTheDocument()
  })
})

// ─── Tests: quitar del carrito ────────────────────────────────────────────────

describe('ModoRecreo — quitar del carrito', () => {
  it('decrementa cantidad al presionar el botón − en el ítem del carrito', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()

    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const btnAgregar = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(btnAgregar)
    await userEvent.click(btnAgregar)
    expect(screen.getByText('2 productos')).toBeInTheDocument()

    // El <li> del carrito contiene: [X, Minus, Plus]
    const cartJugo = screen.getAllByText('Jugo de naranja').find(el => el.closest('li'))!
    const li = cartJugo.closest('li')!
    const btnsEnLi = within(li).getAllByRole('button')
    // btnsEnLi[0]=X(remove all), btnsEnLi[1]=Minus, btnsEnLi[2]=Plus
    await userEvent.click(btnsEnLi[1])
    expect(screen.getByText('1 productos')).toBeInTheDocument()
  })

  it('elimina el ítem cuando la cantidad llega a 0', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()

    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const btnAgregar = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(btnAgregar)
    expect(screen.getByText('1 productos')).toBeInTheDocument()

    const cartJugo = screen.getAllByText('Jugo de naranja').find(el => el.closest('li'))!
    const li = cartJugo.closest('li')!
    const btnsEnLi = within(li).getAllByRole('button')
    await userEvent.click(btnsEnLi[1]) // Minus: 1 → 0 → item desaparece
    expect(screen.getByText('0 productos')).toBeInTheDocument()
  })
})

// ─── Tests: cobro exitoso ─────────────────────────────────────────────────────

describe('ModoRecreo — cobro exitoso', () => {
  it('llama a ventasService.crear al cobrar con tarjeta activa y carrito con ítems', async () => {
    setupDataConTarjeta()
    mockVentasCrear.mockResolvedValueOnce({})
    render(<ModoRecreo />)
    await waitForProducts()

    // Escanear tarjeta
    const scannerInput = screen.getByPlaceholderText(/Escanear tarjeta/i)
    await userEvent.type(scannerInput, 'T-00001{Enter}')
    await screen.findByText('Ana López')

    // Agregar un producto
    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const btnAgregar = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(btnAgregar)

    // Botón COBRAR habilitado (tarjeta + PREPAGO + carrito)
    const btnCobrar = screen.getByRole('button', { name: /cobrar/i })
    expect(btnCobrar).toBeEnabled()

    await userEvent.click(btnCobrar)

    await waitFor(() => {
      expect(mockVentasCrear).toHaveBeenCalledOnce()
    })
    expect(mockVentasCrear).toHaveBeenCalledWith(
      expect.objectContaining({ tarjeta: 'T-00001', tipo: 'CONTADO' }),
      expect.any(Number),
    )
  })

  it('muestra toast.error si ventasService.crear lanza error', async () => {
    setupDataConTarjeta()
    mockVentasCrear.mockRejectedValueOnce(new Error('Error de red'))
    render(<ModoRecreo />)
    await waitForProducts()

    const scannerInput = screen.getByPlaceholderText(/Escanear tarjeta/i)
    await userEvent.type(scannerInput, 'T-00001{Enter}')
    await screen.findByText('Ana López')

    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const btnAgregar = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(btnAgregar)

    await userEvent.click(screen.getByRole('button', { name: /cobrar/i }))

    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalled()
    })
  })
})

// ─── Tests: cancelar ─────────────────────────────────────────────────────────

describe('ModoRecreo — cancelar', () => {
  it('vacía el carrito al presionar "Cancelar (Esc)"', async () => {
    setupData()
    render(<ModoRecreo />)
    await waitForProducts()

    const botonesJugo = screen.getAllByText('Jugo de naranja')
    const btnAgregar = botonesJugo.map(el => el.closest('button')).find(b => b)!
    await userEvent.click(btnAgregar)
    expect(screen.getByText('1 productos')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Cancelar/i }))
    expect(screen.getByText('0 productos')).toBeInTheDocument()
  })
})
