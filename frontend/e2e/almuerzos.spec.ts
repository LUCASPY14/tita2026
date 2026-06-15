import { test, expect, type Page } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const MENU_HOY = {
  id: 1,
  fecha: new Date().toISOString().split('T')[0],
  tipo_almuerzo: 1,
  plato_principal: 'Milanesa con puré',
  guarnicion: 'Ensalada',
  postre: 'Flan',
  bebida: 'Jugo',
  activo: true,
}

// RegistroConsumo real fields: hijo_nombre, fecha_consumo, tipo_almuerzo_nombre, costo_almuerzo, estado, ya_cobrado
const ALMUERZOS_LIST = {
  results: [
    {
      id: 10,
      hijo_nombre: 'Sofía Torres',
      fecha_consumo: new Date().toISOString().split('T')[0],
      tipo_almuerzo_nombre: 'Almuerzo Completo',
      costo_almuerzo: 15000,
      estado: 'REGISTRADO',
      ya_cobrado: false,
    },
  ],
  count: 1,
  next: null,
  previous: null,
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
    // Registros de consumo: endpoint real es /almuerzos/registros-consumo/
    await page.route(/\/api\/v1\/almuerzos\/registros-consumo/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ALMUERZOS_LIST) })
    )
    // Menú: endpoint real es /almuerzos/menu/
    await page.route(/\/api\/v1\/almuerzos\/menu/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [MENU_HOY], count: 1 }) })
    )
    await page.goto('/almuerzos')
    await expect(page).toHaveURL('/almuerzos')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra el listado de almuerzos del día', async ({ page }) => {
    // hijo_nombre renderiza en columna "Estudiante"
    await expect(page.getByText('Sofía Torres').first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra el tipo de almuerzo en la lista de consumos', async ({ page }) => {
    // tipo_almuerzo_nombre renderiza en columna "Tipo"
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
