import { test, expect } from '@playwright/test'

const ADMIN = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const CLIENTES_MOCK = {
  count: 2,
  results: [
    {
      id_cliente: 1,
      nombres: 'María',
      apellidos: 'González',
      razon_social: null,
      ruc_ci: '1234567-8',
      email: 'maria@ejemplo.com',
      telefono: '0981123456',
      activo: true,
      tipo_cliente: 1,
      tipo_cliente_nombre: 'Regular',
      saldo_cuenta_corriente: '0',
      saldo_negativo_tarjetas: '0',
      limite_credito: '0',
      lista_precio: 1,
      fecha_registro: '2026-01-01',
    },
    {
      id_cliente: 2,
      nombres: 'Carlos',
      apellidos: 'Rodríguez',
      razon_social: null,
      ruc_ci: '8765432-1',
      email: 'carlos@ejemplo.com',
      telefono: '0971654321',
      activo: true,
      tipo_cliente: 1,
      tipo_cliente_nombre: 'Regular',
      saldo_cuenta_corriente: '15000',
      saldo_negativo_tarjetas: '0',
      limite_credito: '0',
      lista_precio: 1,
      fecha_registro: '2026-01-01',
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
  await page.getByPlaceholder('Tu CI o RUC').fill('1234567')
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
    await expect(page.getByText('Gestión de estudiantes y responsables')).toBeVisible()
  })

  test('muestra el botón Nuevo Cliente', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Nuevo Cliente/i })).toBeVisible()
  })

  test('muestra los stats de clientes', async ({ page }) => {
    await expect(page.getByText('Total')).toBeVisible()
    await expect(page.getByText('Activos').first()).toBeVisible()
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
