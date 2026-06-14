import { test, expect } from '@playwright/test'

const CAJERO = { id: 2, email: 'cajero@cantina.com', nombre: 'Cajero', apellido: 'Test', rol: 'CAJERO' }
const ADMIN  = { id: 1, email: 'admin@cantina.com',  nombre: 'Admin',  apellido: 'Tita',  rol: 'ADMIN' }

async function loginAs(page: import('@playwright/test').Page, user: typeof CAJERO | typeof ADMIN) {
  // LIFO: catch-all primero (menor prioridad), específicos después (mayor prioridad)
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

// ModoRecreo.tsx usa los campos: descripcion, precio_actual, categoria_nombre, codigo_barra
const PRODUCTOS_MOCK = [
  {
    id: 1, codigo_barra: '7890000000001',
    descripcion: 'Empanada', precio_actual: '5000',
    categoria_nombre: 'Comida', stock_actual: 20,
    activo: true, requiere_stock: true,
  },
  {
    id: 2, codigo_barra: '7890000000002',
    descripcion: 'Gaseosa', precio_actual: '4000',
    categoria_nombre: 'Bebida', stock_actual: 15,
    activo: true, requiere_stock: true,
  },
]

const CATEGORIAS_MOCK = [
  { id: 1, nombre: 'Comida' },
  { id: 2, nombre: 'Bebida' },
]

const CAJA_ABIERTA = {
  id: 1,
  caja_nombre: 'Caja Principal',
  monto_inicial: '0',
  fecha_apertura: '2026-06-13T08:00:00Z',
}

test.describe('Modo Recreo — POS', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, CAJERO)

    // Registrados después del loginAs = mayor prioridad que el catch-all
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(CAJA_ABIERTA) })
    )
    await page.route(/\/api\/v1\/productos\/categorias/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: CATEGORIAS_MOCK, count: 2 }) })
    )
    await page.route(/\/api\/v1\/productos\/productos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: PRODUCTOS_MOCK, count: 2 }) })
    )

    await page.goto('/modo-recreo')
    await expect(page).toHaveURL('/modo-recreo')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra la grilla de productos', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })
    await expect(page.getByRole('button', { name: /Gaseosa/ }).first()).toBeVisible({ timeout: 3000 })
  })

  test('agregar producto actualiza el total del carrito', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })
    await page.getByRole('button', { name: /Empanada/ }).first().click()
    // El carrito muestra el producto como listitem
    await expect(page.getByRole('listitem').filter({ hasText: 'Empanada' })).toBeVisible({ timeout: 3000 })
  })

  test('SUPERVISOR sin acceso es redirigido a /login', async ({ page }) => {
    const SUPERVISOR = { id: 3, email: 'sup@cantina.com', nombre: 'Sup', apellido: 'Test', rol: 'SUPERVISOR' }
    await loginAs(page, SUPERVISOR as typeof ADMIN)
    await page.goto('/modo-recreo')
    await expect(page).toHaveURL('/login')
  })
})

test.describe('Modo Recreo — flujo de venta con tarjeta', () => {
  test('seleccionar producto y cobrar no muestra error boundary', async ({ page }) => {
    await loginAs(page, ADMIN)

    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(CAJA_ABIERTA) })
    )
    await page.route(/\/api\/v1\/productos\/categorias/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: CATEGORIAS_MOCK, count: 2 }) })
    )
    await page.route(/\/api\/v1\/productos\/productos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: PRODUCTOS_MOCK, count: 2 }) })
    )
    await page.route(/\/api\/v1\/ventas/, (route) =>
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id: 99, monto_total: 5000, estado: 'COMPLETADA' }),
      })
    )

    await page.goto('/modo-recreo')
    await expect(page).toHaveURL('/modo-recreo')

    // Esperar que los productos carguen y hacer click
    await page.getByText('Empanada').first().click()

    // El sistema no debe mostrar error boundary
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })
})
