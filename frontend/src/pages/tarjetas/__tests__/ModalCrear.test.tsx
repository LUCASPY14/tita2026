import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import toast from 'react-hot-toast'
import ModalCrear from '../ModalCrear'
import tarjetasService from '../../../services/tarjetas'
import clientesService from '../../../services/clientes'
import { useAuthStore } from '../../../store/authStore'

vi.mock('../../../services/tarjetas')
vi.mock('../../../services/clientes')
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

beforeEach(() => {
  vi.clearAllMocks()
  useAuthStore.setState({ user: { rol: 'ADMIN' } as never })
  vi.mocked(clientesService.getHijos).mockResolvedValue({
    data: {
      results: [
        { id_hijo: 898, nombre: 'Paula Martina', apellido: 'Riveros Zena', grado_nombre: '2° Grado E', activo: true },
      ],
    },
  } as never)
})

describe('ModalCrear', () => {
  it('busca al estudiante por nombre en vez de precargar un combo', async () => {
    render(<ModalCrear open onClose={vi.fn()} onSaved={vi.fn()} />)

    await userEvent.type(screen.getByPlaceholderText('Buscar por nombre o apellido...'), 'Riveros')

    await waitFor(() => {
      expect(clientesService.getHijos).toHaveBeenCalledWith({ search: 'Riveros', activo: true, page_size: 8 })
    })
    expect(await screen.findByText('Paula Martina Riveros Zena')).toBeInTheDocument()
  })

  it('selecciona el estudiante de la lista y lo usa al crear la tarjeta', async () => {
    vi.mocked(tarjetasService.crear).mockResolvedValue({ data: {} } as never)
    const onSaved = vi.fn()

    render(<ModalCrear open onClose={vi.fn()} onSaved={onSaved} />)
    await userEvent.type(screen.getByPlaceholderText('0001234'), '00898')
    await userEvent.type(screen.getByPlaceholderText('Buscar por nombre o apellido...'), 'Riveros')
    await userEvent.click(await screen.findByText('Paula Martina Riveros Zena'))
    await userEvent.click(screen.getByRole('button', { name: 'Crear Tarjeta' }))

    await waitFor(() => {
      expect(tarjetasService.crear).toHaveBeenCalledWith(
        expect.objectContaining({ nro_tarjeta: '00898', hijo: 898, cliente_directo: null }),
      )
    })
    expect(onSaved).toHaveBeenCalled()
  })

  it('exige seleccionar un estudiante antes de crear', async () => {
    render(<ModalCrear open onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.type(screen.getByPlaceholderText('0001234'), '00898')
    await userEvent.click(screen.getByRole('button', { name: 'Crear Tarjeta' }))
    expect(toast.error).toHaveBeenCalledWith('Seleccioná el estudiante')
    expect(tarjetasService.crear).not.toHaveBeenCalled()
  })
})
