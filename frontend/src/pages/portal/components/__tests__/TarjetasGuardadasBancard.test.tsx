import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../../services/api'
import toast from 'react-hot-toast'
import TarjetasGuardadasBancard from '../TarjetasGuardadasBancard'

const TARJETA_1 = {
  card_id: 1, card_masked_number: '5418********0014', card_brand: 'MasterCard', expiration_date: '08/26',
}
const TARJETA_2 = {
  card_id: 2, card_masked_number: '4907********0016', card_brand: 'Visa', expiration_date: '06/27',
}

function renderComponent(props: Partial<React.ComponentProps<typeof TarjetasGuardadasBancard>> = {}) {
  const onSeleccionar = vi.fn()
  const utils = render(
    <TarjetasGuardadasBancard
      selectedCardId={null}
      onSeleccionar={onSeleccionar}
      containerIdPrefix="test"
      {...props}
    />
  )
  return { onSeleccionar, ...utils }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('TarjetasGuardadasBancard — carga inicial', () => {
  it('muestra spinner mientras carga', () => {
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}))
    renderComponent()
    expect(document.querySelector('.animate-spin')).toBeInTheDocument()
  })

  it('sin tarjetas guardadas muestra estado vacío', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [] } })
    renderComponent()
    await screen.findByText(/Todavía no guardaste ninguna tarjeta/i)
  })

  it('muestra las tarjetas devueltas por la API', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [TARJETA_1, TARJETA_2] } })
    renderComponent()
    await screen.findByText(/5418\*+0014/)
    expect(screen.getByText(/4907\*+0016/)).toBeInTheDocument()
  })

  it('error al cargar muestra toast y lista vacía', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('500'))
    renderComponent()
    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('No se pudieron cargar tus tarjetas guardadas')
    })
    await screen.findByText(/Todavía no guardaste ninguna tarjeta/i)
  })
})

describe('TarjetasGuardadasBancard — selección', () => {
  it('click en una tarjeta llama onSeleccionar con su card_id', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [TARJETA_1] } })
    const { onSeleccionar } = renderComponent()
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByText(/5418\*+0014/))

    expect(onSeleccionar).toHaveBeenCalledWith(1)
  })
})

describe('TarjetasGuardadasBancard — eliminar', () => {
  it('elimina una tarjeta y refresca la lista', async () => {
    vi.mocked(api.get)
      .mockResolvedValueOnce({ data: { tarjetas: [TARJETA_1] } })
      .mockResolvedValueOnce({ data: { tarjetas: [] } })
    vi.mocked(api.delete).mockResolvedValue({ data: { status: 'success' } })

    renderComponent()
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByLabelText('Eliminar tarjeta'))

    await waitFor(() => {
      expect(vi.mocked(api.delete)).toHaveBeenCalledWith('/core/bancard/tarjetas/1/')
    })
    await waitFor(() => {
      expect(screen.queryByText(/5418\*+0014/)).not.toBeInTheDocument()
    })
  })

  it('deseleeciona la tarjeta eliminada si estaba seleccionada', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [TARJETA_1] } })
    vi.mocked(api.delete).mockResolvedValue({ data: { status: 'success' } })
    const { onSeleccionar } = renderComponent({ selectedCardId: 1 })
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByLabelText('Eliminar tarjeta'))

    await waitFor(() => expect(onSeleccionar).toHaveBeenCalledWith(null))
  })

  it('error al eliminar muestra toast', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [TARJETA_1] } })
    vi.mocked(api.delete).mockRejectedValue(new Error('500'))
    renderComponent()
    await screen.findByText(/5418\*+0014/)

    await userEvent.click(screen.getByLabelText('Eliminar tarjeta'))

    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('No se pudo eliminar la tarjeta')
    })
  })
})

describe('TarjetasGuardadasBancard — agregar tarjeta', () => {
  it('click en "Agregar tarjeta" inicia el catastro y muestra el contenedor del iframe', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [] } })
    vi.mocked(api.post).mockResolvedValue({
      data: { process_id: 'proc-cat-1', script_url: 'https://vpos.test/checkout.js', card_id: 1 },
    })
    renderComponent()
    await screen.findByText(/Todavía no guardaste ninguna tarjeta/i)

    await userEvent.click(screen.getByRole('button', { name: /Agregar tarjeta/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith('/core/bancard/tarjetas/catastro/')
    })
    await screen.findByText(/Ingresá los datos de la nueva tarjeta/i)
    expect(screen.getByRole('button', { name: /Cancelar/i })).toBeInTheDocument()
  })

  it('cancelar el catastro vuelve a la lista de tarjetas', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [] } })
    vi.mocked(api.post).mockResolvedValue({
      data: { process_id: 'proc-cat-1', script_url: 'https://vpos.test/checkout.js', card_id: 1 },
    })
    renderComponent()
    await screen.findByText(/Todavía no guardaste ninguna tarjeta/i)
    await userEvent.click(screen.getByRole('button', { name: /Agregar tarjeta/i }))
    await screen.findByText(/Ingresá los datos de la nueva tarjeta/i)

    await userEvent.click(screen.getByRole('button', { name: /Cancelar/i }))

    await screen.findByText(/Todavía no guardaste ninguna tarjeta/i)
  })

  it('error al iniciar el catastro muestra toast', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { tarjetas: [] } })
    vi.mocked(api.post).mockRejectedValue({
      response: { data: { detail: 'Ya alcanzaste el máximo de 5 tarjetas guardadas.' } },
    })
    renderComponent()
    await screen.findByText(/Todavía no guardaste ninguna tarjeta/i)

    await userEvent.click(screen.getByRole('button', { name: /Agregar tarjeta/i }))

    await waitFor(() => {
      expect(vi.mocked(toast.error)).toHaveBeenCalledWith('Ya alcanzaste el máximo de 5 tarjetas guardadas.')
    })
  })
})
