import { test, expect } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

async function loginAsAdmin(page: import('@playwright/test').Page) {
  await page.route(/\/api\/v1\//, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
  )
  await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ADMIN) })
  )
  await page.route(/\/api\/token/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ access: 'tok', refresh: 'ref', user: ADMIN }) })
  )
  await page.goto('/login')
  await page.getByPlaceholder('tu@email.com').fill(ADMIN.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await page.waitForURL('/dashboard')
}

const VENTAS_MOCK = {
  results: [
    {
      id: 1,
      tipo: 'CONTADO',
      estado: 'COMPLETADA',
      monto_total: '15000',
      fecha: '2026-06-15T11:30:00Z',
      cajero_nombre: 'Cajero Test',
      cliente_nombre: 'Lucas Pérez',
      nro_items: 3,
    },
    {
      id: 2,
      tipo: 'CREDITO',
      estado: 'COMPLETADA',
      monto_total: '8500',
      fecha: '2026-06-14T10:00:00Z',
      cajero_nombre: 'Cajero Test',
      cliente_nombre: 'Ana García',
      nro_items: 2,
    },
  ],
  count: 2, next: null, previous: null,
}

const VENTA_DETAIL_MOCK = {
  id: 1,
  tipo: 'CONTADO',
  estado: 'COMPLETADA',
  monto_total: '15000',
  fecha: '2026-06-15T11:30:00Z',
  cajero_nombre: 'Cajero Test',
  cliente_nombre: 'Lucas Pérez',
  detalles: [
    { id: 10, producto_nombre: 'Empanada', cantidad: 2, precio_unitario: '5000', subtotal: '10000' },
    { id: 11, producto_nombre: 'Jugo', cantidad: 1, precio_unitario: '5000', subtotal: '5000' },
  ],
  pagos: [
    { id: 20, medio_pago_descripcion: 'Tarjeta Prepaga', monto: '15000' },
  ],
}

// ── Listado ───────────────────────────────────────────────────────────────────

test.describe('Ventas — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsAdmin(page)
    await page.route(/\/api\/v1\/ventas\/ventas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(VENTAS_MOCK) })
    )
    await page.goto('/ventas')
    await page.waitForLoadState('networkidle')
  })

  test('carga la página sin errores de crash', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByText(/Ventas/i).first()).toBeVisible()
  })

  test('muestra las ventas del listado', async ({ page }) => {
    await expect(page.getByText('Lucas Pérez')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Ana García')).toBeVisible({ timeout: 5000 })
  })

  test('muestra los montos en guaraníes', async ({ page }) => {
    await expect(page.getByText(/15[\.,]000|₲\s*15/i).first()).toBeVisible({ timeout: 5000 })
  })

  test('muestra filtros de fecha', async ({ page }) => {
    await expect(
      page.getByRole('textbox', { name: /fecha|desde|hasta/i })
        .or(page.getByLabel(/fecha|desde|hasta/i))
        .first()
    ).toBeVisible({ timeout: 5000 })
  })
})

// ── Estado vacío ──────────────────────────────────────────────────────────────

test.describe('Ventas — estado vacío', () => {
  test('muestra mensaje cuando no hay ventas', async ({ page }) => {
    await loginAsAdmin(page)
    await page.route(/\/api\/v1\/ventas\/ventas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ results: [], count: 0, next: null, previous: null }) })
    )
    await page.goto('/ventas')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText(/sin ventas|no hay ventas|no se encontraron/i).first()).toBeVisible({ timeout: 5000 })
  })
})

// ── Detalle de venta ──────────────────────────────────────────────────────────

test.describe('Ventas — detalle', () => {
  test('abre el detalle de una venta y muestra los ítems', async ({ page }) => {
    await loginAsAdmin(page)
    await page.route(/\/api\/v1\/ventas\/ventas\/[^/]+\/?$/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(VENTA_DETAIL_MOCK) })
    )
    await page.route(/\/api\/v1\/ventas\/ventas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(VENTAS_MOCK) })
    )
    await page.goto('/ventas')
    const firstRow = page.getByText('Lucas Pérez')
    await firstRow.waitFor({ state: 'visible', timeout: 5000 })
    await firstRow.click()
    await expect(page.getByText(/Empanada|detalle|items/i).first()).toBeVisible({ timeout: 5000 })
  })
})

// ── Control de acceso ─────────────────────────────────────────────────────────

test.describe('Ventas — control de acceso', () => {
  test('sin sesión redirige a /login', async ({ page }) => {
    await page.goto('/ventas')
    await expect(page).toHaveURL('/login')
  })
})

// ── Exportación ───────────────────────────────────────────────────────────────

test.describe('Ventas — exportación', () => {
  test('botón de exportar CSV está disponible', async ({ page }) => {
    await loginAsAdmin(page)
    await page.route(/\/api\/v1\/ventas\/ventas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(VENTAS_MOCK) })
    )
    await page.goto('/ventas')
    await page.waitForLoadState('networkidle')
    await expect(
      page.getByRole('button', { name: /csv|exportar|excel/i })
        .or(page.getByTitle(/csv|exportar/i))
        .first()
    ).toBeVisible({ timeout: 5000 })
  })
})
