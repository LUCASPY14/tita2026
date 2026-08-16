import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalConfirmarAnular from '../ModalConfirmarAnular'

vi.mock('../../../services/api', () => ({
  default: { post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'

beforeEach(() => vi.clearAllMocks())

describe('ModalConfirmarAnular', () => {
  it('no llama a la API hasta que se confirma', () => {
    render(<ModalConfirmarAnular consumoId={7} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(api.post).not.toHaveBeenCalled()
    expect(screen.getByText(/Confirmás anular este registro/i)).toBeInTheDocument()
  })

  it('confirmar llama a POST .../anular/ y avisa éxito', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 7, estado: 'ANULADO' } })
    const onSaved = vi.fn()
    const onClose = vi.fn()
    render(<ModalConfirmarAnular consumoId={7} onClose={onClose} onSaved={onSaved} />)

    await userEvent.click(screen.getByRole('button', { name: /Sí, anular/i }))

    expect(api.post).toHaveBeenCalledWith('/almuerzos/registros-consumo/7/anular/')
    expect(toast.success).toHaveBeenCalledWith('Consumo anulado')
    expect(onSaved).toHaveBeenCalled()
    expect(onClose).toHaveBeenCalled()
  })

  it('si falla, muestra el mensaje de error y no cierra el modal', async () => {
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Solo se pueden anular registros en estado REGISTRADO.' } },
    })
    const onClose = vi.fn()
    render(<ModalConfirmarAnular consumoId={7} onClose={onClose} onSaved={vi.fn()} />)

    await userEvent.click(screen.getByRole('button', { name: /Sí, anular/i }))

    expect(toast.error).toHaveBeenCalledWith('Solo se pueden anular registros en estado REGISTRADO.')
    expect(onClose).not.toHaveBeenCalled()
  })

  it('cerrado cuando consumoId es null', () => {
    render(<ModalConfirmarAnular consumoId={null} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.queryByText(/Confirmás anular este registro/i)).not.toBeInTheDocument()
  })
})
