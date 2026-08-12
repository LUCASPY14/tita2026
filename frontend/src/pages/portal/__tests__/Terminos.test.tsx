import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn() },
}))

import api from '../../../services/api'
import PortalTerminos from '../Terminos'

function renderPage() {
  return render(
    <MemoryRouter>
      <PortalTerminos />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Portal Terminos', () => {
  it('muestra el título y las secciones principales', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { razon_social: '', ruc: '' } })
    renderPage()
    expect(screen.getByText('Términos y Condiciones de Uso')).toBeInTheDocument()
    expect(screen.getByText(/Bancard — procesamiento de pagos/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Atención al Usuario/ })).toBeInTheDocument()
    await waitFor(() => expect(api.get).toHaveBeenCalled())
  })

  it('muestra el email y teléfono de contacto', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { razon_social: '', ruc: '' } })
    renderPage()
    expect(screen.getByText('admin@cantinatita.com')).toBeInTheDocument()
    expect(screen.getByText('+595 981 410 938')).toBeInTheDocument()
    await waitFor(() => expect(api.get).toHaveBeenCalled())
  })

  it('pide los datos de empresa y los muestra al resolver', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { razon_social: 'Cantina Tita S.A.', ruc: '80012345-6' },
    })
    renderPage()

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/contabilidad/datos-empresa/publico/')
    })
    expect(await screen.findByText(/Cantina Tita S\.A\./)).toBeInTheDocument()
    expect(screen.getByText(/80012345-6/)).toBeInTheDocument()
  })

  it('si falla la carga de datos de empresa, no rompe la página', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('network error'))
    renderPage()

    await waitFor(() => {
      expect(api.get).toHaveBeenCalled()
    })
    expect(screen.getByText('Términos y Condiciones de Uso')).toBeInTheDocument()
  })
})
