import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import toast from 'react-hot-toast'
import ModalRenumerar from '../ModalRenumerar'
import tarjetasService from '../../../services/tarjetas'
import type { Tarjeta } from '../shared'

vi.mock('../../../services/tarjetas')
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

const TARJETA: Tarjeta = {
  nro_tarjeta: 'T-001',
  codigo_barras: '',
  es_alumno: true,
  hijo: 42,
  hijo_nombre: 'Juan García',
  hijo_grado: '3° A',
  cliente_nombre: 'Roberto García',
  cliente_ruc: '1234567-8',
  saldo_actual: 10000,
  saldo_disponible: 10000,
  saldo_almuerzo: -5000,
  limite_credito: 0,
  estado: 'ACTIVA',
  fecha_vencimiento: null,
  permite_saldo_negativo: false,
  saldo_alerta: null,
  notificar_saldo_bajo: true,
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ModalRenumerar', () => {
  it('no renderiza nada si no hay tarjeta', () => {
    const { container } = render(
      <ModalRenumerar tarjeta={null} onClose={vi.fn()} onSaved={vi.fn()} />
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('valida que el número nuevo sea obligatorio', async () => {
    render(<ModalRenumerar tarjeta={TARJETA} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Renumerar' }))
    expect(toast.error).toHaveBeenCalledWith('Ingresá el número nuevo')
    expect(tarjetasService.renumerar).not.toHaveBeenCalled()
  })

  it('valida que el motivo sea obligatorio', async () => {
    render(<ModalRenumerar tarjeta={TARJETA} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.type(screen.getByPlaceholderText('Nro. de la tarjeta física'), 'T-002')
    await userEvent.click(screen.getByRole('button', { name: 'Renumerar' }))
    expect(toast.error).toHaveBeenCalledWith('Seleccioná un motivo')
    expect(tarjetasService.renumerar).not.toHaveBeenCalled()
  })

  it('muestra el campo de detalle solo con motivo OTRO, y lo exige', async () => {
    render(<ModalRenumerar tarjeta={TARJETA} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.queryByPlaceholderText('Describí el motivo')).not.toBeInTheDocument()

    await userEvent.type(screen.getByPlaceholderText('Nro. de la tarjeta física'), 'T-002')
    await userEvent.selectOptions(screen.getByRole('combobox'), 'OTRO')
    expect(screen.getByPlaceholderText('Describí el motivo')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Renumerar' }))
    expect(toast.error).toHaveBeenCalledWith('Aclará el motivo en el detalle')
    expect(tarjetasService.renumerar).not.toHaveBeenCalled()
  })

  it('renumera la tarjeta llamando a tarjetasService.renumerar', async () => {
    vi.mocked(tarjetasService.renumerar).mockResolvedValue({ data: { nro_tarjeta: 'T-002' } } as never)
    const onSaved = vi.fn()
    const onClose = vi.fn()

    render(<ModalRenumerar tarjeta={TARJETA} onClose={onClose} onSaved={onSaved} />)
    await userEvent.type(screen.getByPlaceholderText('Nro. de la tarjeta física'), 'T-002')
    await userEvent.selectOptions(screen.getByRole('combobox'), 'EXTRAVIO')
    await userEvent.click(screen.getByRole('button', { name: 'Renumerar' }))

    await waitFor(() => {
      expect(tarjetasService.renumerar).toHaveBeenCalledWith('T-001', 'T-002', 'EXTRAVIO', '')
    })
    expect(onSaved).toHaveBeenCalled()
    expect(onClose).toHaveBeenCalled()
  })

  it('renumera con motivo OTRO enviando el detalle', async () => {
    vi.mocked(tarjetasService.renumerar).mockResolvedValue({ data: { nro_tarjeta: 'T-002' } } as never)

    render(<ModalRenumerar tarjeta={TARJETA} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.type(screen.getByPlaceholderText('Nro. de la tarjeta física'), 'T-002')
    await userEvent.selectOptions(screen.getByRole('combobox'), 'OTRO')
    await userEvent.type(screen.getByPlaceholderText('Describí el motivo'), 'Motivo particular')
    await userEvent.click(screen.getByRole('button', { name: 'Renumerar' }))

    await waitFor(() => {
      expect(tarjetasService.renumerar).toHaveBeenCalledWith('T-001', 'T-002', 'OTRO', 'Motivo particular')
    })
  })
})
