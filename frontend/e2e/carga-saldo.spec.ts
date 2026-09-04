import { test, expect } from '@playwright/test'

const ADMIN = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN) {
  // LIFO: registrar primero = prioridad más baja. El /me/ específico (segundo) gana al catch-all (primero).
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
  await page.getByPlaceholder('Tu CI o RUC').fill('1234567')
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await page.waitForURL('/dashboard')
}

const TARJETA_MOCK = {
  results: [{
    nro_tarjeta: '12345678',
    codigo_barras: null,
    hijo_nombre: 'Juan Pérez',
    hijo_grado: '3° A',
    cliente_nombre: 'Responsable',
    saldo_actual: 50000,
    saldo_disponible: 50000,
    estado: 'ACTIVA',
  }],
  count: 1,
}

test.describe('Carga de Saldo', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.goto('/carga-saldo')
    await expect(page).toHaveURL('/carga-saldo')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra el input de búsqueda de tarjeta', async ({ page }) => {
    await expect(page.getByPlaceholder('Nro. de tarjeta...')).toBeVisible()
  })

  test('buscar tarjeta inexistente muestra error', async ({ page }) => {
    // La ruta tarjetas (registrada después de loginAs) tiene mayor prioridad que el catch-all
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.getByPlaceholder('Nro. de tarjeta...').fill('00000000')
    await page.getByPlaceholder('Nro. de tarjeta...').press('Enter')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('seleccionar tarjeta muestra el nombre del estudiante', async ({ page }) => {
    // Ruta específica registrada aquí = prioridad más alta (LIFO)
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(TARJETA_MOCK) })
    )
    await page.getByPlaceholder('Nro. de tarjeta...').fill('12345678')
    await page.getByPlaceholder('Nro. de tarjeta...').press('Enter')

    await expect(page.getByText('Juan Pérez', { exact: true })).toBeVisible({ timeout: 5000 })
  })
})
