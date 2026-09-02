import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalSuscripcion from '../ModalSuscripcion'
import type { Hijo, PlanAlmuerzo } from '../shared'

vi.mock('../../../services/api', () => ({
  default: { post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'

const HIJO: Hijo = { id: 1, nombre: 'Juan', apellido: 'Pérez', grado: '3° A', nombre_completo: 'Juan Pérez' }

const PLANES: PlanAlmuerzo[] = [
  { id: 1, nombre: 'Plan Estándar Mensual', tipo: 'SIN_LIMITE', precio_mensual: 270000, cantidad_almuerzos_mes: null, dias_semana_incluidos: [1, 2, 3, 4, 5], activo: true, es_predeterminado: true },
  { id: 3, nombre: 'Plan Básico 20 días', tipo: 'CANTIDAD', precio_mensual: 240000, cantidad_almuerzos_mes: 20, dias_semana_incluidos: [1, 2, 3, 4, 5], activo: false, es_predeterminado: false },
]

beforeEach(() => vi.clearAllMocks())

describe('ModalSuscripcion — selector de plan con predeterminado preseleccionado', () => {
  it('preselecciona el plan predeterminado y no muestra planes inactivos', () => {
    render(<ModalSuscripcion open hijos={[HIJO]} planes={PLANES} onClose={vi.fn()} onSaved={vi.fn()} />)

    expect(screen.getByDisplayValue(/Plan Estándar Mensual/)).toBeInTheDocument()
    expect(screen.queryByText('Plan Básico 20 días')).not.toBeInTheDocument()
  })

  it('al suscribir sin tocar el selector, envía el plan predeterminado', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<ModalSuscripcion open hijos={[HIJO]} planes={PLANES} onClose={vi.fn()} onSaved={vi.fn()} />)

    await userEvent.selectOptions(screen.getByLabelText('Estudiante *'), '1')
    await userEvent.click(screen.getByRole('button', { name: 'Suscribir' }))

    expect(api.post).toHaveBeenCalledWith('/almuerzos/suscripciones/', expect.objectContaining({
      hijo: 1,
      plan: 1,
    }))
  })

  it('permite elegir otro plan activo', async () => {
    const planes: PlanAlmuerzo[] = [
      ...PLANES,
      { id: 4, nombre: 'Plan Nuevo por Cantidad', tipo: 'CANTIDAD', precio_mensual: 200000, cantidad_almuerzos_mes: 15, dias_semana_incluidos: [1, 2, 3, 4, 5], activo: true, es_predeterminado: false },
    ]
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<ModalSuscripcion open hijos={[HIJO]} planes={planes} onClose={vi.fn()} onSaved={vi.fn()} />)

    await userEvent.selectOptions(screen.getByLabelText('Estudiante *'), '1')
    await userEvent.selectOptions(screen.getByLabelText('Plan *'), '4')
    await userEvent.click(screen.getByRole('button', { name: 'Suscribir' }))

    expect(api.post).toHaveBeenCalledWith('/almuerzos/suscripciones/', expect.objectContaining({
      plan: 4,
    }))
  })
})
