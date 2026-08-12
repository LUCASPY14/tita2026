import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockLogin = vi.fn()
const mockVerify2FA = vi.fn()
const mockVerifyWebAuthn = vi.fn()
const mockCancelPending2FA = vi.fn()
const mockNavigate = vi.fn()
const mockPlatformAvailable = vi.fn()
const mockStartAuthentication = vi.fn()

let mockUser: Record<string, unknown> | null = null
let mockPending2FA: string | null = null
let mockPendingTieneWebauthn = false

vi.mock('../../../store/authStore', () => {
  const useAuthStore = () => ({
    login: mockLogin,
    verify2FA: mockVerify2FA,
    verifyWebAuthn: mockVerifyWebAuthn,
    cancelPending2FA: mockCancelPending2FA,
    pending2FA: mockPending2FA,
    pendingTieneWebauthn: mockPendingTieneWebauthn,
  })
  useAuthStore.getState = () => ({ user: mockUser })
  return { useAuthStore }
})

vi.mock('@simplewebauthn/browser', () => ({
  browserSupportsWebAuthn: () => true,
  platformAuthenticatorIsAvailable: () => mockPlatformAvailable(),
  startAuthentication: (...args: unknown[]) => mockStartAuthentication(...args),
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
import PortalLogin from '../Login'

function renderPortalLogin() {
  return render(
    <MemoryRouter>
      <PortalLogin />
    </MemoryRouter>,
  )
}

async function submitLogin() {
  await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '3331234-2')
  await userEvent.type(screen.getByLabelText(/contraseña/i), 'secreto')
  await userEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
}

beforeEach(() => {
  vi.clearAllMocks()
  mockUser = null
  mockPending2FA = null
  mockPendingTieneWebauthn = false
  mockPlatformAvailable.mockResolvedValue(false)
})

describe('Portal Login — render', () => {
  it('muestra campos CI/RUC y contraseña', () => {
    renderPortalLogin()
    expect(screen.getByLabelText(/ci\/ruc/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ingresar' })).toBeInTheDocument()
  })
})

describe('Portal Login — redirect tras login exitoso', () => {
  it('con debe_cambiar_contrasena navega a cambiar-contrasena', async () => {
    mockUser = { debe_cambiar_contrasena: true, tiene_2fa_activo: false }
    mockLogin.mockResolvedValueOnce(true)
    renderPortalLogin()
    await submitLogin()
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/portal/cambiar-contrasena', { replace: true })
    )
  })

  it('sin 2FA activo igual navega a /portal — el 2FA es opcional', async () => {
    mockUser = { debe_cambiar_contrasena: false, tiene_2fa_activo: false }
    mockLogin.mockResolvedValueOnce(true)
    renderPortalLogin()
    await submitLogin()
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/portal'))
  })

  it('con contraseña ok y 2FA activo navega a /portal', async () => {
    mockUser = { debe_cambiar_contrasena: false, tiene_2fa_activo: true }
    mockLogin.mockResolvedValueOnce(true)
    renderPortalLogin()
    await submitLogin()
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/portal'))
  })
})

describe('Portal Login — segundo paso 2FA', () => {
  it('login() retornando false muestra el paso de código TOTP', async () => {
    mockLogin.mockImplementationOnce(async () => {
      mockPending2FA = 'preauth-token'
      return false
    })
    renderPortalLogin()
    await submitLogin()

    await waitFor(() => {
      expect(screen.getByText('Verificación en dos pasos')).toBeInTheDocument()
    })
  })

  it('código válido llama a verify2FA y redirige', async () => {
    mockPending2FA = 'preauth-token'
    mockUser = { debe_cambiar_contrasena: false, tiene_2fa_activo: true }
    mockVerify2FA.mockResolvedValueOnce(undefined)
    renderPortalLogin()

    await userEvent.type(screen.getByLabelText(/código totp/i), '123456')
    await userEvent.click(screen.getByRole('button', { name: 'Verificar' }))

    await waitFor(() => {
      expect(mockVerify2FA).toHaveBeenCalledWith('123456')
      expect(mockNavigate).toHaveBeenCalledWith('/portal')
    })
  })

  it('código inválido muestra error y no navega', async () => {
    mockPending2FA = 'preauth-token'
    mockVerify2FA.mockRejectedValueOnce(new Error('bad code'))
    renderPortalLogin()

    await userEvent.type(screen.getByLabelText(/código totp/i), '000000')
    await userEvent.click(screen.getByRole('button', { name: 'Verificar' }))

    await waitFor(() => {
      expect(screen.getByText('Código inválido o expirado')).toBeInTheDocument()
    })
    expect(mockNavigate).not.toHaveBeenCalled()
  })

  it('cancelar vuelve al formulario de login', async () => {
    mockPending2FA = 'preauth-token'
    mockCancelPending2FA.mockImplementationOnce(() => { mockPending2FA = null })
    renderPortalLogin()
    expect(screen.getByText('Verificación en dos pasos')).toBeInTheDocument()

    // Tipear un código primero: así setCodigo('') en el cancel realmente cambia
    // el estado y fuerza el re-render que hace que el mock de pending2FA se reevalúe.
    await userEvent.type(screen.getByLabelText(/código totp/i), '1')
    await userEvent.click(screen.getByText('Volver al inicio de sesión'))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Ingresar' })).toBeInTheDocument()
    })
  })
})

describe('Portal Login — segundo paso con huella', () => {
  it('cuenta con huella y plataforma compatible ofrece continuar con huella', async () => {
    mockPending2FA = 'preauth-token'
    mockPendingTieneWebauthn = true
    mockPlatformAvailable.mockResolvedValueOnce(true)
    renderPortalLogin()

    expect(await screen.findByRole('button', { name: /continuar con tu huella/i })).toBeInTheDocument()
  })

  it('continuar con huella exitoso llama a login-opciones/verificar y redirige', async () => {
    mockPending2FA = 'preauth-token'
    mockPendingTieneWebauthn = true
    mockUser = { debe_cambiar_contrasena: false, tiene_2fa_activo: false, tiene_webauthn: true }
    mockPlatformAvailable.mockResolvedValueOnce(true)
    vi.mocked(api.post).mockResolvedValueOnce({ data: { challenge: 'c' } })
    mockStartAuthentication.mockResolvedValueOnce({ id: 'cred-1' })
    mockVerifyWebAuthn.mockResolvedValueOnce(undefined)

    renderPortalLogin()
    await userEvent.click(await screen.findByRole('button', { name: /continuar con tu huella/i }))

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/usuarios/webauthn/login-opciones/', { pre_auth_token: 'preauth-token' })
      expect(mockVerifyWebAuthn).toHaveBeenCalledWith({ id: 'cred-1' })
      expect(mockNavigate).toHaveBeenCalledWith('/portal')
    })
  })

  it('"usar el código de mi app en su lugar" muestra el formulario de código', async () => {
    mockPending2FA = 'preauth-token'
    mockPendingTieneWebauthn = true
    mockPlatformAvailable.mockResolvedValueOnce(true)
    renderPortalLogin()

    await userEvent.click(await screen.findByText(/usar el código de mi app en su lugar/i))
    expect(screen.getByLabelText(/código totp/i)).toBeInTheDocument()
  })

  it('sin plataforma compatible, muestra directo el formulario de código', async () => {
    mockPending2FA = 'preauth-token'
    mockPendingTieneWebauthn = true
    mockPlatformAvailable.mockResolvedValueOnce(false)
    renderPortalLogin()

    expect(await screen.findByLabelText(/código totp/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /continuar con tu huella/i })).not.toBeInTheDocument()
  })
})
