import { test, expect, type Page } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const MENU_HOY = {
  id: 1,
  fecha: new Date().toISOString().split('T')[0],
  tipo_almuerzo_nombre: 'Almuerzo Completo',
  plato_principal: 'Milanesa con puré',
  postre: 'Flan',
  bebida: 'Jugo',
  activo: true,
}

const TARJETA_MOCK = {
  id: 1,
  nro_tarjeta: '99887766',
  hijo_nombre: 'Sofía Torres',
  hijo_grado: '2° B',
  cliente_nombre: 'María Torres',
  saldo_actual: 120000,
  saldo_disponible: 120000,
  estado: 'ACTIVA',
}

const ALMUERZOS_LIST = {
  results: [
    {
      id: 10,
      tarjeta_nro: '99887766',
      hijo_nombre: 'Sofía Torres',
      menu_descripcion: 'Almuerzo Completo',
      fecha: new Date().toISOString().split('T')[0],
      monto: 15000,
      estado: 'REGISTRADO',
    },
  ],
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

test.describe('Almuerzos', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/almuerzos\/consumos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ALMUERZOS_LIST) })
    )
    await page.route(/\/api\/v1\/almuerzos\/menus/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [MENU_HOY], count: 1 }) })
    )
    await page.goto('/almuerzos')
    await expect(page).toHaveURL('/almuerzos')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra el listado de almuerzos del día', async ({ page }) => {
    await expect(page.getByText('Sofía Torres').first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra el nombre del menú del día', async ({ page }) => {
    await expect(page.getByText('Almuerzo Completo').first()).toBeVisible({ timeout: 6000 })
  })

  test('buscar tarjeta inexistente no rompe la página', async ({ page }) => {
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    const searchInput = page.getByPlaceholder(/tarjeta|nro\.|buscar/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('00000000')
      await searchInput.press('Enter')
    }
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('tarjeta encontrada muestra datos del estudiante', async ({ page }) => {
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ results: [TARJETA_MOCK], count: 1 }),
      })
    )
    const searchInput = page.getByPlaceholder(/tarjeta|nro\.|buscar/i).first()
    if (await searchInput.isVisible()) {
      await searchInput.fill('99887766')
      await searchInput.press('Enter')
      await expect(page.getByText('Sofía Torres').first()).toBeVisible({ timeout: 5000 })
    }
  })
})
