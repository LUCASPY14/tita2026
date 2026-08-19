import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockLogin = vi.fn()
const mockNavigate = vi.fn()

vi.mock('../../store/authStore', () => ({
  useAuthStore: () => ({
    login: mockLogin,
    pending2FA: null,
    verify2FA: vi.fn(),
    cancelPending2FA: vi.fn(),
  }),
}))

vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>()
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}))

import Login from '../Login'

function renderLogin(variant?: 'admin' | 'pos' | 'cobranzas') {
  return render(
    <MemoryRouter>
      <Login variant={variant} />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ─── render ───────────────────────────────────────────────────────────────────

describe('Login — render', () => {
  it('muestra campo de CI/RUC, contraseña y botón de submit', () => {
    renderLogin()
    expect(screen.getByLabelText(/ci\/ruc/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/contraseña/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('el campo de contraseña empieza con type="password"', () => {
    renderLogin()
    expect(screen.getByLabelText(/contraseña/i)).toHaveAttribute('type', 'password')
  })

  it('muestra el link de recuperar contraseña', () => {
    renderLogin()
    expect(screen.getByRole('link', { name: /olvidaste tu contraseña/i })).toBeInTheDocument()
  })
})

// ─── variant badge ──────────────────────────────────────────────────────────

describe('Login — variant', () => {
  it('sin variant explícito muestra el badge "Administración"', () => {
    renderLogin()
    expect(screen.getByText('Administración')).toBeInTheDocument()
  })

  it('variant="pos" muestra el badge "Caja / POS"', () => {
    renderLogin('pos')
    expect(screen.getByText('Caja / POS')).toBeInTheDocument()
    expect(screen.queryByText('Administración')).not.toBeInTheDocument()
  })

  it('variant="cobranzas" muestra el badge "Cobranzas"', () => {
    renderLogin('cobranzas')
    expect(screen.getByText('Cobranzas')).toBeInTheDocument()
  })
})

// ─── validación ───────────────────────────────────────────────────────────────

describe('Login — validación', () => {
  it('muestra error cuando el CI/RUC está vacío', async () => {
    renderLogin()
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(screen.getByText('El CI/RUC es obligatorio')).toBeInTheDocument()
  })

  it('muestra error cuando se ingresa un email en vez de CI/RUC', async () => {
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), 'user@test.com')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(screen.getByText('Ingresá tu CI o RUC, no un email')).toBeInTheDocument()
  })

  it('muestra error cuando la contraseña está vacía', async () => {
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '1234567')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(screen.getByText('La contraseña es obligatoria')).toBeInTheDocument()
  })

  it('limpia el error de CI/RUC al escribir en el campo', async () => {
    renderLogin()
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))
    expect(screen.getByText('El CI/RUC es obligatorio')).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '1')
    expect(screen.queryByText('El CI/RUC es obligatorio')).not.toBeInTheDocument()
  })
})

// ─── submit exitoso ───────────────────────────────────────────────────────────

describe('Login — submit exitoso', () => {
  it('llama a login() con CI/RUC y contraseña correctos', async () => {
    mockLogin.mockResolvedValueOnce(true)
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '2447330')
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'secreto123')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('2447330', 'secreto123')
    })
  })

  it('navega a /dashboard tras login exitoso', async () => {
    mockLogin.mockResolvedValueOnce(true)
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '2447330')
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'secreto123')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('el botón queda deshabilitado durante el submit', async () => {
    let resolve: (v: boolean) => void
    mockLogin.mockReturnValueOnce(new Promise<boolean>((r) => { resolve = r }))
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '2447330')
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'secreto123')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeDisabled()
    resolve!(true)
  })
})

// ─── submit con error ─────────────────────────────────────────────────────────

describe('Login — submit con error', () => {
  it('muestra "CI/RUC o contraseña incorrectos" cuando login falla', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'))
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '1234567')
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText('CI/RUC o contraseña incorrectos')).toBeInTheDocument()
    })
  })

  it('rehabilita el botón de submit tras el error', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Fail'))
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '1234567')
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'wrong')
    await userEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /iniciar sesión/i })).not.toBeDisabled()
    })
  })
})

// ─── UX ───────────────────────────────────────────────────────────────────────

describe('Login — UX', () => {
  it('alterna la visibilidad de la contraseña con el botón de ojo', async () => {
    const { container } = renderLogin()
    const passwordInput = screen.getByLabelText(/contraseña/i)
    expect(passwordInput).toHaveAttribute('type', 'password')

    const toggleButton = container.querySelector('button[tabindex="-1"]') as HTMLButtonElement
    await userEvent.click(toggleButton)

    expect(passwordInput).toHaveAttribute('type', 'text')

    await userEvent.click(toggleButton)
    expect(passwordInput).toHaveAttribute('type', 'password')
  })

  it('presionar Enter en el campo de contraseña ejecuta el submit', async () => {
    mockLogin.mockResolvedValueOnce(true)
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '1234567')
    await userEvent.type(screen.getByLabelText(/contraseña/i), 'pass{Enter}')

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('1234567', 'pass')
    })
  })

  it('presionar Enter en el campo de CI/RUC ejecuta el submit', async () => {
    mockLogin.mockResolvedValueOnce(true)
    renderLogin()
    await userEvent.type(screen.getByLabelText(/ci\/ruc/i), '1234567{Enter}')

    // Validación: password vacío muestra error (submit ejecutado)
    await waitFor(() => {
      expect(screen.getByText('La contraseña es obligatoria')).toBeInTheDocument()
    })
  })
})
