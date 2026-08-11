import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockLogin = vi.fn()
const mockVerify2FA = vi.fn()
const mockCancelPending2FA = vi.fn()
const mockNavigate = vi.fn()

let mockUser: Record<string, unknown> | null = null
let mockPending2FA: string | null = null

vi.mock('../../../store/authStore', () => {
  const useAuthStore = () => ({
    login: mockLogin,
    verify2FA: mockVerify2FA,
    cancelPending2FA: mockCancelPending2FA,
    pending2FA: mockPending2FA,
  })
  useAuthStore.getState = () => ({ user: mockUser })
  return { useAuthStore }
})

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

  it('sin 2FA activo navega a configurar-2fa', async () => {
    mockUser = { debe_cambiar_contrasena: false, tiene_2fa_activo: false }
    mockLogin.mockResolvedValueOnce(true)
    renderPortalLogin()
    await submitLogin()
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith('/portal/configurar-2fa', { replace: true })
    )
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
