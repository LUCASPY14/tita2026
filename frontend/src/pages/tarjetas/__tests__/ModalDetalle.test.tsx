import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import toast from 'react-hot-toast'
import ModalDetalle from '../ModalDetalle'
import tarjetasService from '../../../services/tarjetas'
import api from '../../../services/api'
import type { Tarjeta } from '../shared'

vi.mock('../../../services/tarjetas')
vi.mock('../../../services/api')
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

const TARJETA_ALUMNO: Tarjeta = {
  nro_tarjeta: '00914',
  codigo_barras: '',
  es_alumno: true,
  hijo: 42,
  hijo_nombre: 'Camila Torres Peralta',
  hijo_grado: '6° Grado J',
  cliente_nombre: 'María Carolina Peralta Peña',
  cliente_ruc: '1234567-8',
  saldo_actual: 87550,
  saldo_disponible: 87550,
  saldo_almuerzo: 40000,
  limite_credito: 0,
  estado: 'ACTIVA',
  fecha_vencimiento: null,
  permite_saldo_negativo: true,
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
  vi.mocked(tarjetasService.getMovimientos).mockResolvedValue({ data: { results: [] } } as never)
  vi.mocked(tarjetasService.getCargas).mockResolvedValue({ data: { results: [] } } as never)
  vi.mocked(api.get).mockResolvedValue({
    data: {
      results: [
        { id_recarga_almuerzo: 44, monto_cargado: 20000, metodo_pago: 'EFECTIVO', estado: 'CONFIRMADA', fecha_carga: '2026-10-29T09:31:00Z' },
      ],
    },
  } as never)
})

describe('ModalDetalle', () => {
  it('no muestra la pestaña de recargas de almuerzo para tarjetas sin alumno', async () => {
    render(
      <ModalDetalle tarjeta={TARJETA_DOCENTE} toggling={null} onToggleEstado={vi.fn()} onClose={vi.fn()} onTarjetaUpdated={vi.fn()} onListReload={vi.fn()} />
    )
    await waitFor(() => expect(tarjetasService.getMovimientos).toHaveBeenCalled())
    expect(screen.queryByRole('button', { name: 'Recargas de Almuerzo' })).not.toBeInTheDocument()
    expect(api.get).not.toHaveBeenCalled()
  })

  it('carga y muestra las recargas de almuerzo del alumno en su propia pestaña', async () => {
    render(
      <ModalDetalle tarjeta={TARJETA_ALUMNO} toggling={null} onToggleEstado={vi.fn()} onClose={vi.fn()} onTarjetaUpdated={vi.fn()} onListReload={vi.fn()} />
    )
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/almuerzos/recargas-saldo/', { params: { hijo: 42, page_size: 200 } })
    })
    await userEvent.click(await screen.findByRole('button', { name: 'Recargas de Almuerzo' }))
    expect(await screen.findByText('20.000 Gs.')).toBeInTheDocument()
  })

  it('no bloquea el historial si falla la carga de recargas de almuerzo', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('network'))
    render(
      <ModalDetalle tarjeta={TARJETA_ALUMNO} toggling={null} onToggleEstado={vi.fn()} onClose={vi.fn()} onTarjetaUpdated={vi.fn()} onListReload={vi.fn()} />
    )
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith('Error al cargar historial'))
  })
})
