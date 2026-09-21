import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalSuscripcion from '../ModalSuscripcion'
import type { Hijo } from '../shared'

vi.mock('../../../services/api', () => ({
  default: { post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'

const HIJO: Hijo = { id_hijo: 1, nombre: 'Juan', apellido: 'Pérez', grado: '3° A', nombre_completo: 'Juan Pérez' }

beforeEach(() => vi.clearAllMocks())

describe('ModalSuscripcion — sin selector de plan (suprimido)', () => {
  it('no muestra ningún selector de plan', () => {
    render(<ModalSuscripcion open hijos={[HIJO]} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.queryByLabelText(/Plan/)).not.toBeInTheDocument()
  })

  it('al suscribir, envía solo el hijo y la fecha de inicio', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<ModalSuscripcion open hijos={[HIJO]} onClose={vi.fn()} onSaved={vi.fn()} />)

    await userEvent.selectOptions(screen.getByLabelText('Estudiante *'), '1')
    await userEvent.click(screen.getByRole('button', { name: 'Suscribir' }))

    expect(api.post).toHaveBeenCalledWith('/almuerzos/suscripciones/', expect.objectContaining({
      hijo: 1,
    }))
    expect(api.post).not.toHaveBeenCalledWith(expect.anything(), expect.objectContaining({
      plan: expect.anything(),
    }))
  })

  it('sin elegir estudiante, no llama a la API', async () => {
    render(<ModalSuscripcion open hijos={[HIJO]} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Suscribir' }))
    expect(api.post).not.toHaveBeenCalled()
  })
})
