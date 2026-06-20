import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5173'
const API_RECUPERAR = '**/api/v1/usuarios/recuperar-password/'
const API_CONFIRMAR = '**/api/v1/usuarios/recuperar-password/confirmar/'

// ─── RecuperarPassword (/recuperar-password) ─────────────────────────────────

test.describe('RecuperarPassword', () => {
  test('email en blanco muestra error de validación', async ({ page }) => {
    await page.goto(`${BASE}/recuperar-password`)
    await page.getByRole('button', { name: 'Enviar enlace' }).click()
    await expect(page.getByText('Ingresá tu email')).toBeVisible()
  })

  test('email con formato inválido muestra error de validación', async ({ page }) => {
    await page.goto(`${BASE}/recuperar-password`)
    await page.getByLabel('Email').fill('noesvalido')
    await page.getByRole('button', { name: 'Enviar enlace' }).click()
    await expect(page.getByText('Ingresá un email válido')).toBeVisible()
  })

  test('email válido y respuesta 200 → muestra pantalla de éxito', async ({ page }) => {
    // LIFO: catch-all primero, luego específico
    await page.route('**/api/**', route => route.abort('failed'))
    await page.route(API_RECUPERAR, route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ detail: 'Email enviado' }) })
    )

    await page.goto(`${BASE}/recuperar-password`)
    await page.getByLabel('Email').fill('usuario@test.com')
    await page.getByRole('button', { name: 'Enviar enlace' }).click()

    await expect(page.getByText('¡Revisá tu email!')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Volver al inicio de sesión' })).toBeVisible()
  })

  test('respuesta 400 también muestra pantalla de éxito (no revela existencia del email)', async ({ page }) => {
    await page.route('**/api/**', route => route.abort('failed'))
    await page.route(API_RECUPERAR, route =>
      route.fulfill({ status: 400, contentType: 'application/json', body: JSON.stringify({ error: 'Email no encontrado' }) })
    )

    await page.goto(`${BASE}/recuperar-password`)
    await page.getByLabel('Email').fill('noexiste@test.com')
    await page.getByRole('button', { name: 'Enviar enlace' }).click()

    // Por seguridad el frontend siempre muestra la pantalla de éxito
    await expect(page.getByText('¡Revisá tu email!')).toBeVisible()
  })

  test('error de red muestra toast de error sin mostrar pantalla de éxito', async ({ page }) => {
    await page.route(API_RECUPERAR, route => route.abort('failed'))

    await page.goto(`${BASE}/recuperar-password`)
    await page.getByLabel('Email').fill('usuario@test.com')
    await page.getByRole('button', { name: 'Enviar enlace' }).click()

    await expect(page.getByText('¡Revisá tu email!')).not.toBeVisible()
    // El toast de error y el campo de error deben ser visibles
    await expect(
      page.getByText(/Error de conexión|servidor|conectar/i).first()
    ).toBeVisible({ timeout: 5000 })
  })

  test('Enter en el campo de email dispara el envío', async ({ page }) => {
    await page.route('**/api/**', route => route.abort('failed'))
    await page.route(API_RECUPERAR, route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    )

    await page.goto(`${BASE}/recuperar-password`)
    await page.getByLabel('Email').fill('usuario@test.com')
    await page.getByLabel('Email').press('Enter')

    await expect(page.getByText('¡Revisá tu email!')).toBeVisible()
  })
})

// ─── RestablecerPassword (/reset-password) ───────────────────────────────────

test.describe('RestablecerPassword', () => {
  test('sin uid ni token en la URL muestra pantalla de enlace inválido', async ({ page }) => {
    await page.goto(`${BASE}/reset-password`)
    await expect(page.getByText('Enlace inválido')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Solicitar nuevo enlace' })).toBeVisible()
  })

  test('contraseña en blanco muestra error de validación', async ({ page }) => {
    await page.goto(`${BASE}/reset-password?uid=abc&token=tok`)
    await page.getByRole('button', { name: 'Restablecer contraseña' }).click()
    await expect(page.getByText('La contraseña es obligatoria')).toBeVisible()
  })

  test('contraseña demasiado corta muestra error de validación', async ({ page }) => {
    await page.goto(`${BASE}/reset-password?uid=abc&token=tok`)
    await page.getByLabel('Nueva contraseña').fill('abc')
    await page.getByLabel('Confirmar contraseña').fill('abc')
    await page.getByRole('button', { name: 'Restablecer contraseña' }).click()
    await expect(page.getByText('al menos 6 caracteres')).toBeVisible()
  })

  test('contraseñas que no coinciden muestran error de validación', async ({ page }) => {
    await page.goto(`${BASE}/reset-password?uid=abc&token=tok`)
    await page.getByLabel('Nueva contraseña').fill('nueva123')
    await page.getByLabel('Confirmar contraseña').fill('otraCosa')
    await page.getByRole('button', { name: 'Restablecer contraseña' }).click()
    await expect(page.getByText('Las contraseñas no coinciden')).toBeVisible()
  })

  test('token inválido del servidor muestra el mensaje de error en el formulario', async ({ page }) => {
    await page.route('**/api/**', route => route.abort('failed'))
    await page.route(API_CONFIRMAR, route =>
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'El enlace expiró o es inválido' }),
      })
    )

    await page.goto(`${BASE}/reset-password?uid=abc&token=expired`)
    await page.getByLabel('Nueva contraseña').fill('nueva123')
    await page.getByLabel('Confirmar contraseña').fill('nueva123')
    await page.getByRole('button', { name: 'Restablecer contraseña' }).click()

    await expect(page.getByText(/expiró|inválido/i)).toBeVisible()
  })

  test('restablecimiento exitoso muestra pantalla de confirmación', async ({ page }) => {
    await page.route('**/api/**', route => route.abort('failed'))
    await page.route(API_CONFIRMAR, route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    )

    await page.goto(`${BASE}/reset-password?uid=testuid&token=testtoken`)
    await page.getByLabel('Nueva contraseña').fill('NuevaPass123')
    await page.getByLabel('Confirmar contraseña').fill('NuevaPass123')
    await page.getByRole('button', { name: 'Restablecer contraseña' }).click()

    await expect(page.getByText('¡Contraseña restablecida!')).toBeVisible()
    await expect(page.getByRole('link', { name: 'Ir al inicio de sesión' })).toBeVisible()
  })

  test('botón de visibilidad alterna el tipo del campo de contraseña', async ({ page }) => {
    await page.goto(`${BASE}/reset-password?uid=abc&token=tok`)
    const campo = page.getByLabel('Nueva contraseña')
    await expect(campo).toHaveAttribute('type', 'password')
    // Click en el ojo (primer button sin texto)
    await page.locator('button[type="button"][tabindex="-1"]').click()
    await expect(campo).toHaveAttribute('type', 'text')
  })
})
