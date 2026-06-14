import { test, expect } from '@playwright/test'

const ADMIN_USER = {
  id: 1,
  email: 'admin@cantina.com',
  nombre: 'Admin',
  apellido: 'Tita',
  rol: 'ADMIN',
}

const CAJERO_USER = {
  id: 2,
  email: 'cajero@cantina.com',
  nombre: 'Cajero',
  apellido: 'Test',
  rol: 'CAJERO',
}

function mockLoginSuccess(page: import('@playwright/test').Page, user: typeof ADMIN_USER) {
  return page.route('/api/token/', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access: 'fake-access-token',
        refresh: 'fake-refresh-token',
        user,
      }),
    })
  )
}

function mockMe(page: import('@playwright/test').Page, user: typeof ADMIN_USER) {
  return page.route('**/api/v1/usuarios/usuarios/me/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(user),
    })
  )
}

function mockDashboard(page: import('@playwright/test').Page) {
  // Stub any API calls the dashboard makes so it doesn't error
  return page.route('**/api/v1/**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  )
}

test.beforeEach(async ({ page }) => {
  await page.goto('/login')
})

test('muestra el formulario de login', async ({ page }) => {
  await expect(page.getByPlaceholder('tu@email.com')).toBeVisible()
  await expect(page.getByPlaceholder('••••••••')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Iniciar Sesión' })).toBeVisible()
})

test('valida email vacío', async ({ page }) => {
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await expect(page.getByText('El email es obligatorio')).toBeVisible()
})

test('valida formato de email inválido', async ({ page }) => {
  await page.getByPlaceholder('tu@email.com').fill('no-es-un-email')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await expect(page.getByText('Ingresá un email válido')).toBeVisible()
})

test('valida contraseña vacía', async ({ page }) => {
  await page.getByPlaceholder('tu@email.com').fill('admin@cantina.com')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await expect(page.getByText('La contraseña es obligatoria')).toBeVisible()
})

test('muestra error con credenciales inválidas', async ({ page }) => {
  await page.route('/api/token/', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"No active account"}' })
  )
  await page.getByPlaceholder('tu@email.com').fill('wrong@cantina.com')
  await page.getByPlaceholder('••••••••').fill('wrongpassword')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await expect(page.getByText('Email o contraseña incorrectos')).toBeVisible()
})

test('login exitoso como ADMIN redirige a /dashboard', async ({ page }) => {
  await mockLoginSuccess(page, ADMIN_USER)
  await mockMe(page, ADMIN_USER)
  await mockDashboard(page)

  await page.getByPlaceholder('tu@email.com').fill(ADMIN_USER.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()

  await expect(page).toHaveURL('/dashboard')
})

test('login exitoso como CAJERO redirige a /dashboard', async ({ page }) => {
  await mockLoginSuccess(page, CAJERO_USER)
  await mockMe(page, CAJERO_USER)
  await mockDashboard(page)

  await page.getByPlaceholder('tu@email.com').fill(CAJERO_USER.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()

  await expect(page).toHaveURL('/dashboard')
})

test('Enter en el campo dispara el submit', async ({ page }) => {
  await mockLoginSuccess(page, ADMIN_USER)
  await mockMe(page, ADMIN_USER)
  await mockDashboard(page)

  await page.getByPlaceholder('tu@email.com').fill(ADMIN_USER.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByPlaceholder('••••••••').press('Enter')

  await expect(page).toHaveURL('/dashboard')
})

test('ruta protegida sin auth redirige a /login', async ({ page }) => {
  // No tokens in localStorage, navigating to protected route should redirect
  await page.route('**/api/v1/usuarios/usuarios/me/**', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: '{}' })
  )
  await page.goto('/dashboard')
  await expect(page).toHaveURL('/login')
})

test('link a recuperar contraseña es visible', async ({ page }) => {
  await expect(page.getByRole('link', { name: '¿Olvidaste tu contraseña?' })).toBeVisible()
})
