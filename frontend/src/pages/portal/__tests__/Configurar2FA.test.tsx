import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockNavigate = vi.fn()
const mockLogout = vi.fn()
const mockLoadUser = vi.fn()
const mockPlatformAvailable = vi.fn()
const mockStartRegistration = vi.fn()

vi.mock('../../../store/authStore', () => ({
  useAuthStore: () => ({
    user: { nombre: 'Carlos' },
    logout: mockLogout,
    loadUser: mockLoadUser,
  }),
}))

vi.mock('@simplewebauthn/browser', () => ({
  browserSupportsWebAuthn: () => true,
  platformAuthenticatorIsAvailable: () => mockPlatformAvailable(),
  startRegistration: (...args: unknown[]) => mockStartRegistration(...args),
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
  mockPlatformAvailable.mockResolvedValue(false)
})

describe('Portal Configurar2FA — sin huella, WhatsApp por defecto', () => {
  it('al montar, ofrece enviar el código por WhatsApp (sin llamar a la API todavía)', async () => {
    renderPage()
    expect(await screen.findByRole('button', { name: /enviar código por whatsapp/i })).toBeInTheDocument()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('al enviar, muestra el campo de código y los backup codes', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { telefono: '••• •••4567', backup_codes: ['AAA111', 'BBB222'] },
    })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /enviar código por whatsapp/i }))

    expect(api.post).toHaveBeenCalledWith('/usuarios/2fa/whatsapp/enviar/')
    expect(await screen.findByLabelText(/código de 6 dígitos/i)).toBeInTheDocument()
    expect(screen.getByText(/al ••• •••4567/i)).toBeInTheDocument()
    expect(screen.getByText('AAA111')).toBeInTheDocument()
  })

  it('activar con código correcto refresca el usuario y navega a /portal', async () => {
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: { telefono: '••••', backup_codes: [] } })
      .mockResolvedValueOnce({ data: { detail: 'ok', backup_codes: [] } })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /enviar código por whatsapp/i }))
    await screen.findByLabelText(/código de 6 dígitos/i)

    await userEvent.type(screen.getByLabelText(/código de 6 dígitos/i), '123456')
    await userEvent.click(screen.getByRole('button', { name: /activar y continuar/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/usuarios/2fa/whatsapp/activar/', { codigo: '123456' })
      expect(mockLoadUser).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/portal', { replace: true })
    })
  })

  it('código incorrecto muestra error y no navega', async () => {
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: { telefono: '••••', backup_codes: [] } })
      .mockRejectedValueOnce({ response: { data: { error: 'Código inválido o expirado.' } } })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /enviar código por whatsapp/i }))
    await screen.findByLabelText(/código de 6 dígitos/i)

    await userEvent.type(screen.getByLabelText(/código de 6 dígitos/i), '000000')
    await userEvent.click(screen.getByRole('button', { name: /activar y continuar/i }))

    await waitFor(() => {
      expect(screen.getByText('Código inválido o expirado.')).toBeInTheDocument()
    })
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('"Reenviar código" vuelve a llamar al endpoint de envío', async () => {
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: { telefono: '••••', backup_codes: [] } })
      .mockResolvedValueOnce({ data: { telefono: '••••', backup_codes: [] } })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /enviar código por whatsapp/i }))
    await screen.findByLabelText(/código de 6 dígitos/i)

    await userEvent.click(screen.getByText(/reenviar código/i))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledTimes(2)
      expect(api.post).toHaveBeenNthCalledWith(2, '/usuarios/2fa/whatsapp/enviar/')
    })
  })

  it('si falla el envío, muestra un toast y no avanza de pantalla', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { error: 'No se pudo enviar el código por WhatsApp. Intentá de nuevo en un momento.' } },
    })
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /enviar código por whatsapp/i }))

    const toast = vi.mocked(await import('react-hot-toast')).default
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith(
        'No se pudo enviar el código por WhatsApp. Intentá de nuevo en un momento.',
      )
    })
    expect(screen.queryByLabelText(/código de 6 dígitos/i)).not.toBeInTheDocument()
  })

  it('"Prefiero usar una app de autenticación" cae al flujo de QR (TOTP)', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { otp_uri: 'otpauth://totp/x', secret: 'SECRET', backup_codes: [] },
    })
    renderPage()
    await userEvent.click(await screen.findByText(/prefiero usar una app de autenticación/i))

    expect(await screen.findByLabelText(/2\. ingresá el código de 6 dígitos/i)).toBeInTheDocument()
    expect(api.post).toHaveBeenCalledWith('/usuarios/2fa/configurar/')
  })

  it('botón "Ahora no" vuelve al portal sin cerrar sesión', async () => {
    renderPage()
    await screen.findByRole('button', { name: /enviar código por whatsapp/i })

    await userEvent.click(screen.getByText('Ahora no'))
    expect(mockLogout).not.toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/portal')
  })
})

describe('Portal Configurar2FA — huella disponible', () => {
  it('con plataforma compatible, ofrece activar con huella en vez del QR o WhatsApp', async () => {
    mockPlatformAvailable.mockResolvedValueOnce(true)
    renderPage()

    expect(await screen.findByRole('button', { name: /activar con tu huella/i })).toBeInTheDocument()
    expect(api.post).not.toHaveBeenCalled()
  })

  it('activar con huella registra el dispositivo y navega a /portal', async () => {
    mockPlatformAvailable.mockResolvedValueOnce(true)
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: { challenge: 'c', rp: { id: 'x' } } })
      .mockResolvedValueOnce({ data: { detail: 'ok' } })
    mockStartRegistration.mockResolvedValueOnce({ id: 'cred-1' })

    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /activar con tu huella/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/usuarios/webauthn/registrar-opciones/')
      expect(api.post).toHaveBeenCalledWith('/usuarios/webauthn/registrar-verificar/', { credential: { id: 'cred-1' } })
      expect(mockLoadUser).toHaveBeenCalled()
      expect(mockNavigate).toHaveBeenCalledWith('/portal', { replace: true })
    })
  })

  it('"Prefiero un código por WhatsApp" muestra la pantalla de envío', async () => {
    mockPlatformAvailable.mockResolvedValueOnce(true)
    renderPage()
    await userEvent.click(await screen.findByText(/prefiero un código por whatsapp/i))

    expect(await screen.findByRole('button', { name: /enviar código por whatsapp/i })).toBeInTheDocument()
  })

  it('"Prefiero usar una app de autenticación" cae al flujo de QR existente', async () => {
    mockPlatformAvailable.mockResolvedValueOnce(true)
    vi.mocked(api.post).mockResolvedValueOnce({
      data: { otp_uri: 'otpauth://totp/x', secret: 'SECRET', backup_codes: [] },
    })

    renderPage()
    await userEvent.click(await screen.findByText(/prefiero usar una app de autenticación/i))

    expect(await screen.findByLabelText(/2\. ingresá el código de 6 dígitos/i)).toBeInTheDocument()
    expect(api.post).toHaveBeenCalledWith('/usuarios/2fa/configurar/')
  })

  it('si el usuario cancela el prompt nativo, no muestra error', async () => {
    mockPlatformAvailable.mockResolvedValueOnce(true)
    vi.mocked(api.post).mockResolvedValueOnce({ data: { challenge: 'c', rp: { id: 'x' } } })
    mockStartRegistration.mockRejectedValueOnce({ name: 'NotAllowedError' })

    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /activar con tu huella/i }))

    await waitFor(() => expect(mockStartRegistration).toHaveBeenCalled())
    expect(vi.mocked(await import('react-hot-toast')).default.error).not.toHaveBeenCalled()
    expect(mockNavigate).not.toHaveBeenCalled()
  })
})
