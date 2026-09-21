import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import Cobros from '../Cobros'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../services/api', () => ({
  default: { get: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../services/api'

function renderCobros() {
  return render(
    <MemoryRouter>
      <Cobros />
    </MemoryRouter>,
  )
}

const FILA_SOLO_CC = {
  cliente_id: 1,
  cliente: 'Juan Pérez',
  ruc_ci: '1234567',
  telefono: '0981111111',
  email: '',
  saldo_deuda: 50000,
  dias_atraso: 10,
  aging: '0-30',
  deuda_detalle: [
    { tipo: 'CUENTA_CORRIENTE', hijo_nombre: null, nro_tarjeta: null, monto: 50000, dias_atraso: 10 },
  ],
}

const FILA_SOLO_ALMUERZO = {
  cliente_id: 2,
  cliente: 'Roberto Martínez',
  ruc_ci: '7654321',
  telefono: '',
  email: '',
  saldo_deuda: 475000,
  dias_atraso: 20,
  aging: '0-30',
  deuda_detalle: [
    { tipo: 'ALMUERZO', hijo_nombre: 'Lucca Martínez', nro_tarjeta: 'T-00099', monto: 475000, dias_atraso: 20 },
  ],
}

const FILA_MIXTA = {
  cliente_id: 3,
  cliente: 'Patricia López',
  ruc_ci: '5551234',
  telefono: '',
  email: '',
  saldo_deuda: 130000,
  dias_atraso: 40,
  aging: '31-60',
  deuda_detalle: [
    { tipo: 'CUENTA_CORRIENTE', hijo_nombre: null, nro_tarjeta: null, monto: 30000, dias_atraso: 15 },
    { tipo: 'CANTINA', hijo_nombre: 'Ana López', nro_tarjeta: 'T-00050', monto: 100000, dias_atraso: 40 },
  ],
}

function mockReporte(detalle: object[]) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/clientes/reporte-cuenta-corriente/') {
      return Promise.resolve({
        data: {
          fecha: '2026-09-21',
          resumen: { clientes_con_deuda: detalle.length, total_deuda: 0, aging: {} },
          detalle,
        },
      })
    }
    if (url === '/contabilidad/facturas/pendiente-facturar/') {
      return Promise.resolve({ data: [] })
    }
    return Promise.reject(new Error(`unexpected url ${url}`))
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Cobros — deuda combinada cantina/almuerzo/cuenta corriente', () => {
  it('muestra "Cobrar" para deuda de cuenta corriente sin desglose', async () => {
    mockReporte([FILA_SOLO_CC])
    renderCobros()
    await waitFor(() => expect(screen.getByText('Juan Pérez')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: /Cobrar/ })).toBeInTheDocument()
    expect(screen.queryByText(/Cta\. Cte\./)).not.toBeInTheDocument()
  })

  it('muestra deuda de almuerzo sin deuda de cuenta corriente, con botón para cargar saldo', async () => {
    mockReporte([FILA_SOLO_ALMUERZO])
    renderCobros()
    await waitFor(() => expect(screen.getByText('Roberto Martínez')).toBeInTheDocument())
    expect(screen.getByText(/Almuerzo \(Lucca Martínez\): 475\.000 Gs\./)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Cobrar$/ })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /^Cargar saldo$/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/carga-saldo?tarjeta=T-00099&tipo=ALMUERZO')
  })

  it('desglosa deuda mixta (cta. cte. + cantina) y navega a carga de saldo por hijo', async () => {
    mockReporte([FILA_MIXTA])
    renderCobros()
    await waitFor(() => expect(screen.getByText('Patricia López')).toBeInTheDocument())
    expect(screen.getByText(/Cta\. Cte\.: 30\.000 Gs\./)).toBeInTheDocument()
    expect(screen.getByText(/Cantina \(Ana López\): 100\.000 Gs\./)).toBeInTheDocument()
    // El botón principal sigue siendo "Cobrar" (cuenta corriente)
    expect(screen.getByRole('button', { name: /Cobrar/ })).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Cargar saldo →/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/carga-saldo?tarjeta=T-00050&tipo=CANTINA')
  })

  it('el total combinado suma los tres orígenes', async () => {
    mockReporte([FILA_MIXTA])
    renderCobros()
    await waitFor(() => expect(screen.getByText('Patricia López')).toBeInTheDocument())
    expect(screen.getByText('130.000 Gs.')).toBeInTheDocument()
  })
})
