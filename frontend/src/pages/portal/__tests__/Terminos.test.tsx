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
    vi.mocked(api.get).mockResolvedValueOnce({ data: { razon_social: '', ruc: '', email: '', telefono: '' } })
    renderPage()
    expect(screen.getByText('Términos y Condiciones de Uso')).toBeInTheDocument()
    expect(screen.getByText(/Bancard — procesamiento de pagos/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /Atención al Usuario/ })).toBeInTheDocument()
    await waitFor(() => expect(api.get).toHaveBeenCalled())
  })

  it('pide los datos de empresa (razón social, RUC, contacto) y los muestra al resolver', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        razon_social: 'Cantina Tita S.A.', ruc: '80012345-6',
        email: 'administracion@cantinatita.com', telefono: '+595981410938',
      },
    })
    renderPage()

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/contabilidad/datos-empresa/publico/')
    })
    expect(await screen.findByText(/Cantina Tita S\.A\./)).toBeInTheDocument()
    expect(screen.getByText(/80012345-6/)).toBeInTheDocument()
    expect(screen.getByText('administracion@cantinatita.com')).toBeInTheDocument()
    // Formateado: "+595981410938" → "+595 981 410 938"
    expect(screen.getByText('+595 981 410 938')).toBeInTheDocument()
  })

  it('sin email ni teléfono cargados, muestra el estado de espera en contacto', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: { razon_social: '', ruc: '', email: '', telefono: '' } })
    renderPage()

    expect(await screen.findByText('Cargando datos de contacto…')).toBeInTheDocument()
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
