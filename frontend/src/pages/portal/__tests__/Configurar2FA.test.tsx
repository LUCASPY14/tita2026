import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockNavigate = vi.fn()
const mockLogout = vi.fn()
const mockLoadUser = vi.fn()

vi.mock('../../../store/authStore', () => ({
  useAuthStore: () => ({
    user: { nombre: 'Carlos' },
    logout: mockLogout,
    loadUser: mockLoadUser,
  }),
}))

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

vi.mock('../../../services/api', () => ({
  default: { post: vi.fn() },
}))

import api from '../../../services/api'
import PortalConfigurar2FA from '../Configurar2FA'

function renderPage() {
  return render(
    <MemoryRouter>
      <PortalConfigurar2FA />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Portal Configurar2FA', () => {
  it('al montar, pide el QR y muestra el campo de código', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { otp_uri: 'otpauth://totp/x', secret: 'SECRET123', backup_codes: ['AAA111', 'BBB222'] },
    })
    renderPage()
    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/usuarios/2fa/configurar/'))
    expect(await screen.findByLabelText(/código de 6 dígitos/i)).toBeInTheDocument()
    expect(screen.getByText('AAA111')).toBeInTheDocument()
  })

  it('activar con código correcto refresca el usuario y navega a /portal', async () => {
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: { otp_uri: 'otpauth://totp/x', secret: 'SECRET', backup_codes: [] } })
      .mockResolvedValueOnce({ data: { detail: 'ok' } })
    renderPage()
    await screen.findByLabelText(/código de 6 dígitos/i)

    await userEvent.type(screen.getByLabelText(/código de 6 dígitos/i), '123456')
    await userEvent.click(screen.getByRole('button', { name: /activar y continuar/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/usuarios/2fa/activar/', { codigo: '123456' })
      expect(mockLoadUser).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/portal', { replace: true })
    })
  })

  it('código incorrecto muestra error y no navega', async () => {
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: { otp_uri: 'otpauth://totp/x', secret: 'SECRET', backup_codes: [] } })
      .mockRejectedValueOnce({ response: { data: { error: 'Código inválido.' } } })
    renderPage()
    await screen.findByLabelText(/código de 6 dígitos/i)

    await userEvent.type(screen.getByLabelText(/código de 6 dígitos/i), '000000')
    await userEvent.click(screen.getByRole('button', { name: /activar y continuar/i }))

    await waitFor(() => {
      expect(screen.getByText('Código inválido.')).toBeInTheDocument()
    })
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('botón cerrar sesión llama a logout y navega al login del portal', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { otp_uri: 'otpauth://totp/x', secret: 'SECRET', backup_codes: [] },
    })
    renderPage()
    await screen.findByLabelText(/código de 6 dígitos/i)

    await userEvent.click(screen.getByText(/cerrar sesión y continuar después/i))
    expect(mockLogout).toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/portal/login', { replace: true })
  })
})
