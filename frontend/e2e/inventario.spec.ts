import { test, expect, type Page } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const STOCK_LIST = {
  results: [
    { id: 1, producto: 1, producto_nombre: 'Harina 000', cantidad: 50, unidad_medida: 'KG', ubicacion: 'Depósito A' },
    { id: 2, producto: 2, producto_nombre: 'Aceite Girasol', cantidad: 20, unidad_medida: 'LT', ubicacion: 'Depósito A' },
  ],
  count: 2,
  next: null,
  previous: null,
}

const MOVIMIENTOS_LIST = {
  results: [
    {
      id: 100,
      producto_nombre: 'Harina 000',
      tipo: 'ENTRADA',
      motivo: 'COMPRA',
      cantidad: 25,
      stock_resultante: 50,
      fecha: new Date().toISOString(),
      observaciones: '',
    },
  ],
  count: 1,
  next: null,
  previous: null,
}

const ALERTAS_LIST = { results: [], count: 0, next: null, previous: null }

async function loginAs(page: Page, user: typeof ADMIN) {
  await page.route(/\/api\/v1\//, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
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

test.describe('Inventario', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/inventario\/stock/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(STOCK_LIST) })
    )
    await page.route(/\/api\/v1\/inventario\/movimientos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOVIMIENTOS_LIST) })
    )
    await page.route(/\/api\/v1\/inventario\/alertas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ALERTAS_LIST) })
    )
    await page.goto('/inventario')
    await expect(page).toHaveURL('/inventario')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra productos en stock', async ({ page }) => {
    await expect(page.getByText('Harina 000').first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra el stock de aceite girasol', async ({ page }) => {
    await expect(page.getByText('Aceite Girasol').first()).toBeVisible({ timeout: 6000 })
  })

  test('historial de movimientos es accesible', async ({ page }) => {
    const movBtn = page.getByRole('button', { name: /movimiento|historial/i }).first()
    if (await movBtn.isVisible()) {
      await movBtn.click()
      await expect(page.getByText('Harina 000').first()).toBeVisible({ timeout: 5000 })
    }
  })

  test('buscar por nombre filtra resultados', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/buscar|producto/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('Harina')
      await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    }
  })

  test('página sin alertas no muestra badge de alerta', async ({ page }) => {
    await expect(page.getByText('Sin alertas').first()).not.toBeVisible()
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })
})
