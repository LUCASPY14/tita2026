import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import toast from 'react-hot-toast'
import ModalAjustarSaldo from '../ModalAjustarSaldo'
import tarjetasService from '../../../services/tarjetas'
import api from '../../../services/api'
import type { Tarjeta } from '../shared'

vi.mock('../../../services/tarjetas')
vi.mock('../../../services/api')
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

const TARJETA_ALUMNO: Tarjeta = {
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

const TARJETA_DOCENTE: Tarjeta = {
  ...TARJETA_ALUMNO,
  nro_tarjeta: 'T-DOC',
  es_alumno: false,
  hijo: null,
  hijo_nombre: 'Marta Profesora',
  saldo_almuerzo: null,
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ModalAjustarSaldo', () => {
  it('no renderiza nada si no hay tarjeta', () => {
    const { container } = render(
      <ModalAjustarSaldo tarjeta={null} onClose={vi.fn()} onSaved={vi.fn()} />
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('muestra el saldo de cantina por defecto', () => {
    render(<ModalAjustarSaldo tarjeta={TARJETA_ALUMNO} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.getByText('10.000 Gs.')).toBeInTheDocument()
  })

  it('cambia a saldo de almuerzo al hacer click, y muestra ese saldo', async () => {
    render(<ModalAjustarSaldo tarjeta={TARJETA_ALUMNO} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Saldo de almuerzo' }))
    expect(screen.getByText('-5.000 Gs.')).toBeInTheDocument()
  })

  it('deshabilita "Saldo de almuerzo" para tarjetas de docentes (no alumno)', () => {
    render(<ModalAjustarSaldo tarjeta={TARJETA_DOCENTE} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Saldo de almuerzo' })).toBeDisabled()
  })

  it('valida que el motivo sea obligatorio', async () => {
    render(<ModalAjustarSaldo tarjeta={TARJETA_ALUMNO} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.type(screen.getByPlaceholderText('0'), '5000')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar ajuste' }))
    expect(toast.error).toHaveBeenCalledWith('El motivo es obligatorio')
    expect(tarjetasService.ajustarSaldo).not.toHaveBeenCalled()
  })

  it('valida que el monto no sea cero', async () => {
    render(<ModalAjustarSaldo tarjeta={TARJETA_ALUMNO} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.type(screen.getByPlaceholderText(/corrección por reclamo/i), 'Motivo válido')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar ajuste' }))
    expect(toast.error).toHaveBeenCalledWith('Ingresá un monto distinto de cero')
  })

  it('ajusta el saldo de cantina llamando a tarjetasService.ajustarSaldo', async () => {
    vi.mocked(tarjetasService.ajustarSaldo).mockResolvedValue({
      data: { saldo_actual: 15000 },
    } as never)
    const onSaved = vi.fn()
    const onClose = vi.fn()

    render(<ModalAjustarSaldo tarjeta={TARJETA_ALUMNO} onClose={onClose} onSaved={onSaved} />)
    await userEvent.type(screen.getByPlaceholderText('0'), '5000')
    await userEvent.type(screen.getByPlaceholderText(/corrección por reclamo/i), 'Corrección por reclamo')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar ajuste' }))

    await waitFor(() => {
      expect(tarjetasService.ajustarSaldo).toHaveBeenCalledWith('T-001', 5000, 'Corrección por reclamo')
    })
    expect(onSaved).toHaveBeenCalledWith({ saldo_actual: 15000 })
    expect(onClose).toHaveBeenCalled()
  })

  it('ajusta el saldo de almuerzo llamando a /almuerzos/saldos/ajustar/ con hijo_id', async () => {
    vi.mocked(api.post).mockResolvedValue({ data: { saldo_actual: -2000 } } as never)
    const onSaved = vi.fn()

    render(<ModalAjustarSaldo tarjeta={TARJETA_ALUMNO} onClose={vi.fn()} onSaved={onSaved} />)
    await userEvent.click(screen.getByRole('button', { name: 'Saldo de almuerzo' }))
    await userEvent.type(screen.getByPlaceholderText('0'), '3000')
    await userEvent.type(screen.getByPlaceholderText(/corrección por reclamo/i), 'Ajuste de almuerzo')
    await userEvent.click(screen.getByRole('button', { name: 'Aplicar ajuste' }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/almuerzos/saldos/ajustar/', {
        hijo_id: 42, monto: 3000, motivo: 'Ajuste de almuerzo',
      })
    })
    expect(onSaved).toHaveBeenCalledWith({ saldo_almuerzo: -2000 })
  })

  it('muestra el saldo resultante como vista previa', async () => {
    render(<ModalAjustarSaldo tarjeta={TARJETA_ALUMNO} onClose={vi.fn()} onSaved={vi.fn()} />)
    await userEvent.type(screen.getByPlaceholderText('0'), '2500')
    expect(screen.getByText('12.500 Gs.')).toBeInTheDocument()
  })
})
