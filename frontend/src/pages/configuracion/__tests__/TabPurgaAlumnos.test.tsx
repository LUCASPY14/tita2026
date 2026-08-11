import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'
import TabPurgaAlumnos from '../TabPurgaAlumnos'

const PENDIENTE = {
  id: 42,
  nombre: 'Marta',
  apellido: 'Díaz',
  cliente_nombre: 'Carlos Díaz',
  fecha_baja: '2027-01-10T00:00:00Z',
  purga_solicitada_en: '2028-01-15T00:00:00Z',
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('TabPurgaAlumnos — lista', () => {
  it('sin pendientes muestra el estado vacío', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [] })
    render(<TabPurgaAlumnos />)
    await screen.findByText('No hay alumnos pendientes de purga')
  })

  it('con pendientes muestra el alumno en la tabla', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [PENDIENTE] })
    render(<TabPurgaAlumnos />)
    await screen.findByText('Díaz, Marta')
    expect(screen.getByText('Carlos Díaz')).toBeInTheDocument()
  })

  it('error al cargar muestra toast.error', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('fail'))
    render(<TabPurgaAlumnos />)
    await waitFor(() => expect(vi.mocked(toast.error)).toHaveBeenCalled())
  })
})

describe('TabPurgaAlumnos — aprobar purga', () => {
  it('click en Aprobar purga abre el modal de confirmación', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [PENDIENTE] })
    render(<TabPurgaAlumnos />)
    await screen.findByText('Díaz, Marta')

    await userEvent.click(screen.getByRole('button', { name: /Aprobar purga/i }))
    expect(await screen.findByText('Aprobar purga de datos')).toBeInTheDocument()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('confirmar en el modal llama a aprobar-purga y recarga la lista', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: [PENDIENTE] })
      .mockResolvedValueOnce({ data: [] })
    vi.mocked(api.post).mockResolvedValueOnce({ data: { id: 42, datos_purgados: true } })

    render(<TabPurgaAlumnos />)
    await screen.findByText('Díaz, Marta')
    await userEvent.click(screen.getByRole('button', { name: /Aprobar purga/i }))
    await screen.findByText('Aprobar purga de datos')

    await userEvent.click(screen.getByRole('button', { name: 'Sí, anonimizar' }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/clientes/hijos/42/aprobar-purga/')
    })
    expect(vi.mocked(toast.success)).toHaveBeenCalled()
  })

  it('cancelar en el modal no llama a la API', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [PENDIENTE] })
    render(<TabPurgaAlumnos />)
    await screen.findByText('Díaz, Marta')
    await userEvent.click(screen.getByRole('button', { name: /Aprobar purga/i }))
    await screen.findByText('Aprobar purga de datos')

    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    await waitFor(() => {
      expect(screen.queryByText('Aprobar purga de datos')).not.toBeInTheDocument()
    })
    expect(api.post).not.toHaveBeenCalled()
  })

  it('si la aprobación falla muestra toast.error', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: [PENDIENTE] })
    vi.mocked(api.post).mockRejectedValueOnce(new Error('fail'))

    render(<TabPurgaAlumnos />)
    await screen.findByText('Díaz, Marta')
    await userEvent.click(screen.getByRole('button', { name: /Aprobar purga/i }))
    await screen.findByText('Aprobar purga de datos')
    await userEvent.click(screen.getByRole('button', { name: 'Sí, anonimizar' }))

    await waitFor(() => expect(vi.mocked(toast.error)).toHaveBeenCalled())
  })
})
