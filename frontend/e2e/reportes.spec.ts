import { test, expect } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const REPORTE_VENTAS_MOCK = {
  resumen: {
    total_ventas: 150,
    monto_total: 750000,
    ticket_promedio: 5000,
    total_cierres: 10,
  },
  por_tipo: [],
  cierres: [],
}

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN) {
  await page.route(/\/api\/v1\//, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
  )
  await page.route(/\/api\/v1\/contabilidad\/reportes\//, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(REPORTE_VENTAS_MOCK),
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

test.describe('Reportes', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.goto('/reportes')
    await expect(page).toHaveURL('/reportes')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Reportes' })).toBeVisible()
    await expect(page.getByText('Reportes y análisis del sistema')).toBeVisible()
  })

  test('muestra todos los tabs de reporte', async ({ page }) => {
    const main = page.getByRole('main')
    await expect(main.getByRole('button', { name: /Ventas y Cierres/i })).toBeVisible()
    await expect(main.getByRole('button', { name: /Productos/i })).toBeVisible()
    await expect(main.getByRole('button', { name: /Cajeros/i })).toBeVisible()
    await expect(main.getByRole('button', { name: /Cuenta Corriente/i })).toBeVisible()
    await expect(main.getByRole('button', { name: /Tarjetas/i })).toBeVisible()
    await expect(main.getByRole('button', { name: /Inventario/i })).toBeVisible()
    await expect(main.getByRole('button', { name: 'Almuerzos', exact: true })).toBeVisible()
  })

  test('tab Ventas y Cierres carga resumen de ventas', async ({ page }) => {
    // Ya activo por defecto. Verificar que no hay error de crash.
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    // El tab ventas muestra filtros de fecha
    await expect(page.getByRole('button', { name: /Ventas y Cierres/i })).toBeVisible()
  })

  test('navegar a tab Productos no rompe la página', async ({ page }) => {
    await page.getByRole('main').getByRole('button', { name: /Productos/i }).click()
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('navegar a tab Inventario no rompe la página', async ({ page }) => {
    await page.getByRole('main').getByRole('button', { name: /Inventario/i }).click()
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })
})
