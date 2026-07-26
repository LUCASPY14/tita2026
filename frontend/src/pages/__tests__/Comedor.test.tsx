import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import Comedor from '../Comedor'

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

vi.mock('../../utils/pdf', () => ({
  exportarIngresosComedorPDF: vi.fn(),
}))

import api from '../../services/api'
import { exportarIngresosComedorPDF } from '../../utils/pdf'

// ── Fixtures ──────────────────────────────────────────────────────────────────

const HIJO = { id: 1, nombre: 'Juan', apellido: 'Pérez', grado: '3° A', nombre_completo: 'Juan Pérez' }

const TARJETA_ACTIVA = {
  nro_tarjeta: 'T-001', hijo_nombre: 'Juan Pérez', hijo_grado: '3° A',
  saldo_actual: 50000, estado: 'ACTIVA', hijo: 1,
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function setupMounts(tarjeta = TARJETA_ACTIVA) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
    if (url === '/almuerzos/registros-consumo/') return Promise.resolve({ data: { results: [] } })
    if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [tarjeta] } })
    return Promise.resolve({ data: { results: [] } })
  })
  vi.mocked(api.post).mockResolvedValue({ data: { id: 99 } })
}

async function renderReady(tarjeta = TARJETA_ACTIVA) {
  setupMounts(tarjeta)
  render(<Comedor />)
  // Wait for both initial API calls (hijos + registros-consumo) to complete
  await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
}

async function scan(nro: string) {
  const input = screen.getByPlaceholderText('Nro. de tarjeta...')
  await userEvent.type(input, nro)
  await userEvent.keyboard('{Enter}')
}

// ── Fullscreen stubs ──────────────────────────────────────────────────────────

beforeAll(() => {
  Object.defineProperty(document.documentElement, 'requestFullscreen', {
    writable: true, configurable: true,
    value: vi.fn().mockResolvedValue(undefined),
  })
  Object.defineProperty(document, 'exitFullscreen', {
    writable: true, configurable: true,
    value: vi.fn().mockResolvedValue(undefined),
  })
  Object.defineProperty(document, 'fullscreenElement', {
    writable: true, configurable: true,
    value: null,
  })
})

beforeEach(() => {
  vi.clearAllMocks()
  // Reset fullscreen state between tests
  Object.defineProperty(document, 'fullscreenElement', { writable: true, configurable: true, value: null })
})

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('Comedor — renderizado', () => {
  it('muestra campo de escaneo y texto de instrucción', async () => {
    await renderReady()
    expect(screen.getByPlaceholderText('Nro. de tarjeta...')).toBeInTheDocument()
    expect(screen.getByText(/Pasá la tarjeta/i)).toBeInTheDocument()
  })
})

describe('Comedor — flujo de escaneo', () => {
  it('registra almuerzo exitoso → panel muestra "Ingreso registrado", nombre y grado', async () => {
    await renderReady()
    await scan('T-001')
    await screen.findByText('Ingreso registrado')
    expect(screen.getAllByText(/Juan Pérez/)[0]).toBeInTheDocument()
    expect(screen.getAllByText(/3° A/)[0]).toBeInTheDocument()
  })

  it('tarjeta no encontrada → panel de error "Tarjeta no encontrada"', async () => {
    setupMounts()
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/') return Promise.resolve({ data: { results: [] } })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [] } })
      return Promise.resolve({ data: { results: [] } })
    })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
    await scan('T-999')
    await screen.findByText('Tarjeta no encontrada')
  })

  it('tarjeta BLOQUEADA → panel de error con mensaje de bloqueo', async () => {
    const tarjetaBloqueada = { ...TARJETA_ACTIVA, estado: 'BLOQUEADA' }
    await renderReady(tarjetaBloqueada)
    await scan('T-001')
    await screen.findByText(/bloqueada/i)
  })

  it('alumno ya almorzó hoy → mensaje anti-doble-scan', async () => {
    // Seed consumidosHoy con el hijo ya registrado
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/')
        return Promise.resolve({ data: { results: [{ hijo: 1, fecha_consumo: '2026-07-24' }] } })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [TARJETA_ACTIVA] } })
      return Promise.resolve({ data: { results: [] } })
    })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
    await scan('T-001')
    await screen.findByText(/ya registró almuerzo hoy/i)
  })

  it('registro exitoso → el contador de Recientes sube a 1', async () => {
    await renderReady()
    await scan('T-001')
    // After a successful scan, the "Recientes (N)" tab counter increments
    await screen.findByText(/Recientes \(1\)/i)
  })

  it('Escape limpia el resultado y vacía el input', async () => {
    setupMounts()
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/') return Promise.resolve({ data: { results: [] } })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [] } }) // not found
      return Promise.resolve({ data: { results: [] } })
    })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))

    await scan('T-INEXISTENTE')
    await screen.findByText('Tarjeta no encontrada')

    await userEvent.keyboard('{Escape}')
    await waitFor(() => {
      expect(screen.queryByText('Tarjeta no encontrada')).not.toBeInTheDocument()
    })
  })
})

describe('Comedor — fullscreen', () => {
  it('botón fullscreen alterna el título entre "Pantalla completa" y "Salir de pantalla completa"', async () => {
    await renderReady()
    const btn = screen.getByTitle('Pantalla completa')
    await userEvent.click(btn)
    await screen.findByTitle('Salir de pantalla completa')
    expect(document.documentElement.requestFullscreen).toHaveBeenCalled()
  })
})

describe('Comedor — PDF', () => {
  it('botón PDF no visible cuando no hay registros recientes', async () => {
    await renderReady()
    expect(screen.queryByText(/PDF/)).not.toBeInTheDocument()
  })

  it('botón PDF visible y funcional luego de un registro exitoso', async () => {
    await renderReady()
    await scan('T-001')
    await screen.findByText(/PDF \(1\)/i)

    await userEvent.click(screen.getByText(/PDF \(1\)/i))
    expect(vi.mocked(exportarIngresosComedorPDF)).toHaveBeenCalled()
  })
})

describe('Comedor — modo lista', () => {
  it('click en "Lista de hoy" llama a la API de suscripciones', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/') return Promise.resolve({ data: { results: [] } })
      if (url === '/almuerzos/suscripciones/') return Promise.resolve({ data: { results: [] } })
      return Promise.resolve({ data: { results: [] } })
    })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))

    const listaBtn = screen.getByRole('button', { name: /Lista de hoy/i })
    await userEvent.click(listaBtn)

    await waitFor(() => {
      expect(vi.mocked(api.get)).toHaveBeenCalledWith(
        '/almuerzos/suscripciones/',
        expect.anything(),
      )
    })
  })
})
