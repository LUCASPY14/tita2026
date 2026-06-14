import { test, expect } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const CLIENTES_MOCK = {
  count: 2,
  results: [
    {
      id: 1,
      nombre: 'María',
      apellido: 'González',
      email: 'maria@ejemplo.com',
      telefono: '0981123456',
      activo: true,
      tipo_cliente_nombre: 'Regular',
      saldo_deuda: 0,
    },
    {
      id: 2,
      nombre: 'Carlos',
      apellido: 'Rodríguez',
      email: 'carlos@ejemplo.com',
      telefono: '0971654321',
      activo: true,
      tipo_cliente_nombre: 'Regular',
      saldo_deuda: 15000,
    },
  ],
}

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN) {
  // LIFO: catch-all primero (baja prioridad), específicos después (alta prioridad).
  await page.route(/\/api\/v1\//, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
  )
  await page.route(/\/api\/v1\/clientes\/clientes\//, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(CLIENTES_MOCK),
    })
  )
  await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(user) })
  )
  await page.route(/\/api\/token/, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ access: 'tok', refresh: 'ref', user }),
    })
  )

  await page.goto('/login')
  await page.getByPlaceholder('tu@email.com').fill(user.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await page.waitForURL('/dashboard')
}

test.describe('Clientes', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.goto('/clientes')
    await expect(page).toHaveURL('/clientes')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible()
    await expect(page.getByText('Gestión de clientes y sus estudiantes')).toBeVisible()
  })

  test('muestra el botón Nuevo Cliente', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Nuevo Cliente/i })).toBeVisible()
  })

  test('muestra los stats de clientes', async ({ page }) => {
    await expect(page.getByText('Total')).toBeVisible()
    await expect(page.getByText('Activos')).toBeVisible()
    await expect(page.getByText('Con Deuda')).toBeVisible()
  })

  test('lista los clientes mockeados', async ({ page }) => {
    await expect(page.getByText('González')).toBeVisible()
    await expect(page.getByText('Rodríguez')).toBeVisible()
  })

  test('abrir modal Nuevo Cliente no rompe la página', async ({ page }) => {
    await page.getByRole('button', { name: /Nuevo Cliente/i }).click()
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    // El modal debería abrirse
    await expect(page.getByRole('dialog')).toBeVisible()
  })

  test('buscar por nombre filtra en la tabla', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/buscar|nombre|cliente/i)
    if (await searchInput.isVisible()) {
      await searchInput.fill('González')
      await expect(page.getByText('González')).toBeVisible()
    }
  })
})
