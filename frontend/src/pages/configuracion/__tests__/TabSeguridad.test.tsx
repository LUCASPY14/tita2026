import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('qrcode.react', () => ({
  QRCodeSVG: () => <svg data-testid="qr-code" />,
}))

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'
import TabSeguridad from '../TabSeguridad'

// ── Helpers ──────────────────────────────────────────────────────────────────

const ESTADO_INACTIVO = { habilitado: false, fecha_activacion: null, tiene_backup_codes: false }
const ESTADO_ACTIVO   = { habilitado: true, fecha_activacion: '2026-07-01T00:00:00Z', tiene_backup_codes: true }

const SETUP_RESPONSE = {
  otp_uri: 'otpauth://totp/test@cantina:user?secret=ABCDEFGH',
  secret: 'ABCDEFGH',
  backup_codes: ['code1', 'code2', 'code3', 'code4', 'code5', 'code6', 'code7', 'code8'],
}

type EstadoFake = { habilitado: boolean; fecha_activacion: string | null; tiene_backup_codes: boolean }

function setupGet(estado: EstadoFake = ESTADO_INACTIVO) {
  vi.mocked(api.get).mockResolvedValue({ data: estado })
}

function setupPost(response = SETUP_RESPONSE) {
  vi.mocked(api.post).mockResolvedValue({ data: response })
}

beforeEach(() => {
  vi.clearAllMocks()
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: vi.fn().mockResolvedValue(undefined) },
    writable: true,
    configurable: true,
  })
})

// ── Carga inicial ─────────────────────────────────────────────────────────────

describe('TabSeguridad — carga inicial', () => {
  it('badge "Inactivo" cuando 2FA está desactivado', async () => {
    setupGet(ESTADO_INACTIVO)
    render(<TabSeguridad />)

    await screen.findByText('Inactivo')
  })

  it('"Configurar 2FA" visible cuando 2FA está desactivado', async () => {
    setupGet(ESTADO_INACTIVO)
    render(<TabSeguridad />)

    await screen.findByRole('button', { name: /Configurar 2FA/i })
  })

  it('badge "Activo" cuando 2FA está habilitado', async () => {
    setupGet(ESTADO_ACTIVO)
    render(<TabSeguridad />)

    await screen.findByText('Activo')
  })

  it('"Desactivar 2FA" visible cuando 2FA está habilitado', async () => {
    setupGet(ESTADO_ACTIVO)
    render(<TabSeguridad />)

    await screen.findByRole('button', { name: /Desactivar 2FA/i })
  })
})

// ── Flujo setup ───────────────────────────────────────────────────────────────

describe('TabSeguridad — flujo de configuración', () => {
  async function abrirSetup() {
    setupGet(ESTADO_INACTIVO)
    setupPost()
    render(<TabSeguridad />)
    await screen.findByRole('button', { name: /Configurar 2FA/i })
    await userEvent.click(screen.getByRole('button', { name: /Configurar 2FA/i }))
    await screen.findByTestId('qr-code')
  }

  it('click "Configurar 2FA" llama api.post y muestra QR', async () => {
    await abrirSetup()

    expect(vi.mocked(api.post)).toHaveBeenCalledWith('/usuarios/2fa/configurar/')
    expect(screen.getByTestId('qr-code')).toBeInTheDocument()
  })

  it('"Activar" está deshabilitado hasta ingresar 6 dígitos', async () => {
    await abrirSetup()

    const activarBtn = screen.getByRole('button', { name: /Activar/i })
    expect(activarBtn).toBeDisabled()

    const input = screen.getByPlaceholderText('123456')
    await userEvent.type(input, '12345')
    expect(activarBtn).toBeDisabled()

    await userEvent.type(input, '6')
    expect(activarBtn).not.toBeDisabled()
  })

  it('código de 6 dígitos + click "Activar" → api.post activar con el código', async () => {
    setupGet(ESTADO_INACTIVO)
    vi.mocked(api.post)
      .mockResolvedValueOnce({ data: SETUP_RESPONSE })  // configurar
      .mockResolvedValueOnce({ data: {} })               // activar

    render(<TabSeguridad />)
    await screen.findByRole('button', { name: /Configurar 2FA/i })
    await userEvent.click(screen.getByRole('button', { name: /Configurar 2FA/i }))
    await screen.findByTestId('qr-code')

    const input = screen.getByPlaceholderText('123456')
    await userEvent.type(input, '123456')
    await userEvent.click(screen.getByRole('button', { name: /Activar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/usuarios/2fa/activar/',
        { codigo: '123456' },
      )
    })
    expect(vi.mocked(toast.success)).toHaveBeenCalledWith('2FA activado correctamente')
  })

  it('"Cancelar" en setup vuelve al paso idle', async () => {
    await abrirSetup()

    await userEvent.click(screen.getByRole('button', { name: /Cancelar/i }))

    await screen.findByRole('button', { name: /Configurar 2FA/i })
    expect(screen.queryByTestId('qr-code')).toBeNull()
  })

  it('setup muestra los códigos de respaldo en la caja ámbar', async () => {
    await abrirSetup()

    expect(screen.getByText('code1')).toBeInTheDocument()
    expect(screen.getByText(/Guardá estos códigos de respaldo/i)).toBeInTheDocument()
  })

  it('botón copiar secret llama navigator.clipboard.writeText', async () => {
    await abrirSetup()

    // Hay dos icon buttons junto al secret: toggle show/hide + copy
    const btns = screen.getAllByRole('button')
    const iconBtns = btns.filter(b => !b.textContent?.trim())
    // El de copiar es el último de los dos
    await userEvent.click(iconBtns[iconBtns.length - 1])

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('ABCDEFGH')
    })
  })
})

// ── Flujo desactivación ───────────────────────────────────────────────────────

describe('TabSeguridad — flujo de desactivación', () => {
  async function abrirDisable() {
    setupGet(ESTADO_ACTIVO)
    vi.mocked(api.post).mockResolvedValue({ data: {} })
    render(<TabSeguridad />)
    await screen.findByRole('button', { name: /Desactivar 2FA/i })
    await userEvent.click(screen.getByRole('button', { name: /Desactivar 2FA/i }))
  }

  it('click "Desactivar 2FA" muestra input y "Confirmar"', async () => {
    await abrirDisable()

    expect(screen.getByPlaceholderText('123456')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Confirmar/i })).toBeInTheDocument()
  })

  it('"Confirmar" con 6 dígitos llama api.post desactivar', async () => {
    await abrirDisable()

    await userEvent.type(screen.getByPlaceholderText('123456'), '654321')
    await userEvent.click(screen.getByRole('button', { name: /Confirmar/i }))

    await waitFor(() => {
      expect(vi.mocked(api.post)).toHaveBeenCalledWith(
        '/usuarios/2fa/desactivar/',
        { codigo: '654321' },
      )
    })
    expect(vi.mocked(toast.success)).toHaveBeenCalledWith('2FA desactivado')
  })

  it('"Cancelar" en disable vuelve al paso idle', async () => {
    await abrirDisable()

    await userEvent.click(screen.getByRole('button', { name: /Cancelar/i }))

    await screen.findByRole('button', { name: /Desactivar 2FA/i })
    expect(screen.queryByRole('button', { name: /Confirmar/i })).toBeNull()
  })
})
