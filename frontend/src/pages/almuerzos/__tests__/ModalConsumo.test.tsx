import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import ModalConsumo from '../ModalConsumo'
import type { Hijo, TipoAlmuerzo } from '../shared'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'

const HIJO: Hijo = { id_hijo: 1, nombre: 'Juan', apellido: 'Pérez', grado: '3° A', nombre_completo: 'Juan Pérez' }

const TARJETA = { nro_tarjeta: 'T-001', hijo_nombre: 'Juan Pérez', saldo_actual: 50000, estado: 'ACTIVA' }

const TIPOS: TipoAlmuerzo[] = [
  { id_tipo_almuerzo: 1, nombre: 'Almuerzo Completo', descripcion: '', precio_unitario: 25000, incluye_plato_principal: true, incluye_postre: true, incluye_bebida: true, activo: true, es_predeterminado: true },
  { id_tipo_almuerzo: 2, nombre: 'Almuerzo Simple', descripcion: '', precio_unitario: 20000, incluye_plato_principal: true, incluye_postre: false, incluye_bebida: false, activo: false, es_predeterminado: false },
]

beforeEach(() => vi.clearAllMocks())

async function buscarYSeleccionarTarjeta() {
  vi.mocked(api.get).mockResolvedValue({ data: { results: [TARJETA] } })
  await userEvent.type(screen.getByPlaceholderText('Nro. tarjeta'), 'T-001')
  await userEvent.click(screen.getByRole('button', { name: /Buscar/i }))
  await screen.findByText('Juan Pérez')
}

describe('ModalConsumo — selector de tipo de almuerzo con predeterminado preseleccionado', () => {
  it('preselecciona el tipo predeterminado y no muestra tipos inactivos', () => {
    render(<ModalConsumo open hijos={[HIJO]} tiposAlmuerzo={TIPOS} onClose={vi.fn()} onSaved={vi.fn()} />)

    expect(screen.getByDisplayValue(/Almuerzo Completo/)).toBeInTheDocument()
    expect(screen.queryByText(/Almuerzo Simple/)).not.toBeInTheDocument()
  })

  it('registra el consumo enviando el tipo_almuerzo predeterminado sin tocar el selector', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<ModalConsumo open hijos={[HIJO]} tiposAlmuerzo={TIPOS} onClose={vi.fn()} onSaved={vi.fn()} />)

    await buscarYSeleccionarTarjeta()
    await userEvent.click(screen.getByRole('button', { name: 'Registrar' }))

    expect(api.post).toHaveBeenCalledWith('/almuerzos/registros-consumo/', {
      hijo: 1,
      fecha_consumo: expect.any(String),
      nro_tarjeta: 'T-001',
      tipo_almuerzo: 1,
    })
  })

  it('permite elegir "Sin especificar" explícitamente y no envía tipo_almuerzo', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1 } })
    render(<ModalConsumo open hijos={[HIJO]} tiposAlmuerzo={TIPOS} onClose={vi.fn()} onSaved={vi.fn()} />)

    await buscarYSeleccionarTarjeta()
    await userEvent.selectOptions(screen.getByLabelText('Tipo de Almuerzo (opcional)'), '')
    await userEvent.click(screen.getByRole('button', { name: 'Registrar' }))

    expect(api.post).toHaveBeenCalledWith('/almuerzos/registros-consumo/', {
      hijo: 1,
      fecha_consumo: expect.any(String),
      nro_tarjeta: 'T-001',
    })
  })
})
