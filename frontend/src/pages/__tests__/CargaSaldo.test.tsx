import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import CargaSaldo from '../CargaSaldo'

vi.mock('../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../services/api'
import toast from 'react-hot-toast'

const TARJETA = {
  nro_tarjeta: 'T-00001',
  codigo_barras: null,
  hijo_nombre: 'Juan Pérez',
  hijo_grado: '3° A',
  cliente_nombre: 'Carlos Pérez',
  saldo_actual: '50000',
  saldo_disponible: '50000',
  estado: 'ACTIVA',
}

function mockBuscarSuccess() {
  vi.mocked(api.get)
    .mockResolvedValueOnce({ data: { results: [TARJETA] } })
    .mockResolvedValueOnce({ data: { results: [] } })
    .mockResolvedValueOnce({ data: { results: [] } })
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ─── Búsqueda ──────────────────────────────────────────────────────────────────

describe('CargaSaldo — búsqueda', () => {
  it('muestra el formulario de búsqueda inicialmente', () => {
    render(<CargaSaldo />)
    expect(screen.getByText('Carga de Saldo')).toBeInTheDocument()
    expect(screen.getByText('Pasá la tarjeta')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Nro. de tarjeta...')).toBeInTheDocument()
  })

  it('muestra toast.error si busqueda está vacía', async () => {
    render(<CargaSaldo />)
    await userEvent.click(screen.getByRole('button'))
    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Ingresá el número de tarjeta')
  })

  it('busca al presionar Enter en el input', async () => {
    mockBuscarSuccess()
    render(<CargaSaldo />)
    const input = screen.getByPlaceholderText('Nro. de tarjeta...')
    await userEvent.type(input, 'T-00001')
    await userEvent.keyboard('{Enter}')
    await screen.findByText('Juan Pérez')
  })

  it('muestra toast.error si la tarjeta no se encuentra', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { results: [] } })
    render(<CargaSaldo />)
    await userEvent.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-99999')
    await userEvent.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Tarjeta no encontrada')
    })
  })

  it('muestra toast.error si la tarjeta está BLOQUEADA', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { results: [{ ...TARJETA, estado: 'BLOQUEADA' }] },
    })
    render(<CargaSaldo />)
    await userEvent.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    await userEvent.click(screen.getByRole('button'))
    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith(
        expect.stringContaining('bloqueada')
      )
    })
  })

  it('muestra los datos de la tarjeta al encontrarla', async () => {
    mockBuscarSuccess()
    render(<CargaSaldo />)
    await userEvent.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    await userEvent.click(screen.getByRole('button'))
    expect(await screen.findByText('Juan Pérez')).toBeInTheDocument()
    expect(screen.getByText('3° A · Carlos Pérez')).toBeInTheDocument()
    expect(screen.getByText('T-00001')).toBeInTheDocument()
  })
})

// ─── Formulario de carga ───────────────────────────────────────────────────────

describe('CargaSaldo — formulario de carga', () => {
  async function renderConTarjeta() {
    const user = userEvent.setup()
    mockBuscarSuccess()
    render(<CargaSaldo />)
    await user.type(screen.getByPlaceholderText('Nro. de tarjeta...'), 'T-00001')
    // único botón visible antes de encontrar tarjeta
    await user.click(screen.getByRole('button'))
    await screen.findByText('Juan Pérez')
    return user
  }

  it('muestra botones de monto rápido', async () => {
    await renderConTarjeta()
    expect(screen.getByRole('button', { name: '10.000' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '50.000' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '200.000' })).toBeInTheDocument()
  })

  it('al hacer click en monto rápido rellena el input', async () => {
    const user = await renderConTarjeta()
    await user.click(screen.getByRole('button', { name: '10.000' }))
    const montoInput = screen.getByPlaceholderText('0') as HTMLInputElement
    expect(montoInput.value).toBe('10000')
  })

  it('el método TRANSFERENCIA muestra "queda pendiente"', async () => {
    await renderConTarjeta()
    expect(screen.getByText('queda pendiente')).toBeInTheDocument()
  })

  it('aparece campo Referencia al seleccionar TRANSFERENCIA', async () => {
    const user = await renderConTarjeta()
    await user.click(screen.getByRole('button', { name: /Transferencia/i }))
    expect(screen.getByPlaceholderText('Nro. de transferencia...')).toBeInTheDocument()
  })

  it('muestra toast.error si monto es 0 al cargar', async () => {
    const user = await renderConTarjeta()
    await user.click(screen.getByRole('button', { name: /Cargar saldo/i }))
    expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Ingresá un monto válido')
  })

  it('registra carga exitosamente y muestra "Carga realizada"', async () => {
    const user = await renderConTarjeta()

    vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 99, estado: 'CONFIRMADA' } })
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { ...TARJETA, saldo_disponible: '60000' } })
      .mockResolvedValueOnce({ data: { results: [] } })
      .mockResolvedValueOnce({ data: { results: [] } })

    await user.click(screen.getByRole('button', { name: '10.000' }))
    await user.click(screen.getByRole('button', { name: /Cargar saldo/i }))

    await waitFor(() => {
      expect(vi.mocked(toast.success)).toHaveBeenCalledWith(
        expect.stringContaining('confirmada')
      )
    })
    await screen.findByText('Carga realizada')
  })
})
