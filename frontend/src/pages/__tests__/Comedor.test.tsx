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

const mockUseOfflineQueue = vi.fn()
vi.mock('../../hooks/useOfflineQueue', () => ({
  useOfflineQueue: () => mockUseOfflineQueue(),
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

function setupMounts(tarjeta = TARJETA_ACTIVA, saldoAlmuerzo: number | null = null) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
    if (url === '/almuerzos/registros-consumo/') return Promise.resolve({ data: { results: [] } })
    if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [tarjeta] } })
    if (url === '/almuerzos/saldos/') {
      return Promise.resolve({
        data: { results: saldoAlmuerzo === null ? [] : [{ saldo_actual: saldoAlmuerzo }] },
      })
    }
    return Promise.resolve({ data: { results: [] } })
  })
  vi.mocked(api.post).mockResolvedValue({ data: { id: 99 } })
}

async function renderReady(tarjeta = TARJETA_ACTIVA, saldoAlmuerzo: number | null = null) {
  setupMounts(tarjeta, saldoAlmuerzo)
  render(<Comedor />)
  // Wait for both initial API calls (hijos + registros-consumo) to complete
  await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
}

async function scan(nro: string) {
  const input = screen.getByPlaceholderText('Nro. de tarjeta...')
  await userEvent.type(input, nro)
  await userEvent.keyboard('{Enter}')
}

// Devuelve un string "HH:MM:SS" que representa "hace `segundos` segundos",
// igual al formato que el backend serializa para hora_registro (TimeField).
function horaHace(segundos: number): string {
  return new Date(Date.now() - segundos * 1000).toTimeString().split(' ')[0]
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
  // Estado por defecto de la cola offline — online, sin pendientes
  mockUseOfflineQueue.mockReturnValue({
    isOnline: true, pendingCount: 0, syncing: false, syncNow: vi.fn(), enqueue: vi.fn(),
  })
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

  it('reintento a los pocos segundos → mensaje de escaneo duplicado (no llega al backend)', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/')
        return Promise.resolve({ data: { results: [{ hijo: 1, hora_registro: horaHace(3) }] } })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [TARJETA_ACTIVA] } })
      return Promise.resolve({ data: { results: [] } })
    })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
    await scan('T-001')
    await screen.findByText(/Escaneo duplicado/i)
    expect(api.post).not.toHaveBeenCalled()
  })

  it('2do intento entre 10s y 240s → mensaje "todavía muy pronto" (no llega al backend)', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/')
        return Promise.resolve({ data: { results: [{ hijo: 1, hora_registro: horaHace(60) }] } })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [TARJETA_ACTIVA] } })
      return Promise.resolve({ data: { results: [] } })
    })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
    await scan('T-001')
    await screen.findByText(/muy pronto/i)
    expect(api.post).not.toHaveBeenCalled()
  })

  it('2do intento después de 240s → se registra como "2do ingreso", sin cargo adicional', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/')
        return Promise.resolve({ data: { results: [{ hijo: 1, hora_registro: horaHace(300) }] } })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [TARJETA_ACTIVA] } })
      return Promise.resolve({ data: { results: [] } })
    })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
    await scan('T-001')
    await screen.findByText('2do ingreso registrado')
    expect(screen.getByText('Sin cargo adicional')).toBeInTheDocument()
    expect(api.post).toHaveBeenCalled()
  })

  it('3er intento (2 registros previos) pasa al backend y muestra su mensaje real', async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [HIJO] } })
      if (url === '/almuerzos/registros-consumo/')
        return Promise.resolve({
          data: {
            results: [
              { hijo: 1, hora_registro: horaHace(600) },
              { hijo: 1, hora_registro: horaHace(300) },
            ],
          },
        })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [TARJETA_ACTIVA] } })
      return Promise.resolve({ data: { results: [] } })
    })
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Limite alcanzado: Ya existen 2 registros de almuerzo para este alumno.' } },
    })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))
    await scan('T-001')
    await screen.findByText(/Limite alcanzado/i)
    expect(api.post).toHaveBeenCalled()
  })

  it('saldo de almuerzo negativo → se muestra en rojo con aviso "Debe"', async () => {
    await renderReady(TARJETA_ACTIVA, -15000)
    await scan('T-001')
    await screen.findByText('Ingreso registrado')
    expect(screen.getByText('Saldo de almuerzo')).toBeInTheDocument()
    expect(screen.getByText('-15.000 Gs.')).toBeInTheDocument()
    expect(screen.getByText(/Debe/i)).toBeInTheDocument()
  })

  it('saldo de almuerzo positivo → se muestra sin aviso de deuda', async () => {
    await renderReady(TARJETA_ACTIVA, 20000)
    await scan('T-001')
    await screen.findByText('Ingreso registrado')
    expect(screen.getByText('20.000 Gs.')).toBeInTheDocument()
    expect(screen.queryByText(/Debe/i)).not.toBeInTheDocument()
  })

  it('sin saldo de almuerzo registrado → no muestra la caja de saldo', async () => {
    await renderReady(TARJETA_ACTIVA, null)
    await scan('T-001')
    await screen.findByText('Ingreso registrado')
    expect(screen.queryByText('Saldo de almuerzo')).not.toBeInTheDocument()
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

describe('Comedor — aviso de cumpleaños', () => {
  // Se usa la fecha real de "hoy" (no freeze) para no depender de mockear Date
  // en un componente que además usa setInterval/Date.now() para el reloj y el
  // anti-doble-scan — construir el string a partir de "hoy" evita esos choques.
  function fechaNacimientoHoy(): string {
    const hoy = new Date()
    const mm = String(hoy.getMonth() + 1).padStart(2, '0')
    const dd = String(hoy.getDate()).padStart(2, '0')
    return `2015-${mm}-${dd}`
  }

  it('muestra "Hoy cumple años" cuando la fecha de nacimiento coincide con hoy', async () => {
    const hijoCumple = { ...HIJO, fecha_nacimiento: fechaNacimientoHoy() }
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/clientes/hijos/') return Promise.resolve({ data: { results: [hijoCumple] } })
      if (url === '/almuerzos/registros-consumo/') return Promise.resolve({ data: { results: [] } })
      if (url === '/core/tarjetas/') return Promise.resolve({ data: { results: [TARJETA_ACTIVA] } })
      return Promise.resolve({ data: { results: [] } })
    })
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<Comedor />)
    await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))

    await scan('T-001')
    await screen.findByText(/Hoy cumple años/i)
  })

  it('no muestra el aviso cuando la fecha de nacimiento no es hoy', async () => {
    await renderReady()
    await scan('T-001')
    await screen.findByText('Ingreso registrado')
    expect(screen.queryByText(/Hoy cumple años/i)).not.toBeInTheDocument()
  })
})

describe('Comedor — manifest PWA', () => {
  it('al montar, apunta el link de manifest a /comedor-manifest.webmanifest y lo revierte al desmontar', async () => {
    const link = document.createElement('link')
    link.setAttribute('rel', 'manifest')
    link.setAttribute('href', '/manifest.webmanifest')
    document.head.appendChild(link)

    try {
      setupMounts()
      const { unmount } = render(<Comedor />)
      await waitFor(() => expect(vi.mocked(api.get).mock.calls.length).toBeGreaterThanOrEqual(2))

      expect(link.getAttribute('href')).toBe('/comedor-manifest.webmanifest')

      unmount()
      expect(link.getAttribute('href')).toBe('/manifest.webmanifest')
    } finally {
      link.remove()
    }
  })
})

describe('Comedor — cola offline', () => {
  it('sin conexión → muestra el banner "SIN CONEXIÓN"', async () => {
    mockUseOfflineQueue.mockReturnValue({
      isOnline: false, pendingCount: 0, syncing: false, syncNow: vi.fn(), enqueue: vi.fn(),
    })
    await renderReady()
    expect(screen.getByText(/SIN CONEXIÓN/i)).toBeInTheDocument()
  })

  it('con conexión → no muestra el banner de offline', async () => {
    await renderReady()
    expect(screen.queryByText(/SIN CONEXIÓN/i)).not.toBeInTheDocument()
  })

  it('sin registros pendientes → no muestra el botón de sincronización', async () => {
    await renderReady()
    expect(screen.queryByText(/offline/i)).not.toBeInTheDocument()
  })

  it('con registros pendientes → muestra el contador y permite forzar la sincronización', async () => {
    const syncNow = vi.fn()
    mockUseOfflineQueue.mockReturnValue({
      isOnline: true, pendingCount: 3, syncing: false, syncNow, enqueue: vi.fn(),
    })
    await renderReady()

    const boton = screen.getByText('3 offline')
    expect(boton).toBeInTheDocument()

    await userEvent.click(boton)
    expect(syncNow).toHaveBeenCalled()
  })

  it('sincronizando → el botón queda deshabilitado', async () => {
    mockUseOfflineQueue.mockReturnValue({
      isOnline: true, pendingCount: 2, syncing: true, syncNow: vi.fn(), enqueue: vi.fn(),
    })
    await renderReady()
    expect(screen.getByText('2 offline').closest('button')).toBeDisabled()
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
