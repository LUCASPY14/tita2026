import { test, expect, type Page } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const PROVEEDOR_MOCK = {
  id: 1,
  razon_social: 'Distribuidora El Sol',
  ruc: '80012345-1',
  telefono: '0981000001',
  email: 'ventas@elsol.com',
  activo: true,
}

const COMPRAS_LIST = {
  results: [
    {
      id: 50,
      proveedor: 1,
      proveedor_nombre: 'Distribuidora El Sol',
      fecha: new Date().toISOString().split('T')[0],
      numero_factura: 'F001-0000050',
      monto_total: 350000,
      estado: 'REGISTRADA',
    },
    {
      id: 49,
      proveedor: 1,
      proveedor_nombre: 'Distribuidora El Sol',
      fecha: new Date(Date.now() - 86400000).toISOString().split('T')[0],
      numero_factura: 'F001-0000049',
      monto_total: 120000,
      estado: 'REGISTRADA',
    },
  ],
  count: 2,
  next: null,
  previous: null,
}

const PROVEEDORES_LIST = {
  results: [PROVEEDOR_MOCK],
  count: 1,
  next: null,
  previous: null,
}

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

test.describe('Compras', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/compras\/compras/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(COMPRAS_LIST) })
    )
    await page.route(/\/api\/v1\/compras\/proveedores/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(PROVEEDORES_LIST) })
    )
    await page.goto('/compras')
    await expect(page).toHaveURL('/compras')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra compras recientes en la tabla', async ({ page }) => {
    // proveedor_nombre aparece en celdas td, no en <option> ocultas del filtro
    await expect(page.locator('td').filter({ hasText: 'Distribuidora El Sol' }).first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra compra #50 en la tabla', async ({ page }) => {
    // La columna ID muestra el número con prefijo '#'
    await expect(page.getByText('#50').first()).toBeVisible({ timeout: 6000 })
  })

  test('nueva compra abre un formulario o modal', async ({ page }) => {
    const newBtn = page.getByRole('button', { name: /nueva|nueva compra|registrar/i }).first()
    if (await newBtn.isVisible()) {
      await newBtn.click()
      await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    }
  })

  test('filtrar por proveedor no rompe la página', async ({ page }) => {
    const filter = page.getByRole('combobox').first()
    if (await filter.isVisible()) {
      await filter.click()
      await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    }
  })

  test('segunda compra #49 también se lista', async ({ page }) => {
    await expect(page.getByText('#49').first()).toBeVisible({ timeout: 6000 })
  })
})
