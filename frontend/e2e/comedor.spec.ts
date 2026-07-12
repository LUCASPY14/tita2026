import { test, expect, type Page } from '@playwright/test'

// ─── Usuarios ─────────────────────────────────────────────────────────────────

const COCINA = { id: 3, email: 'cocina@cantina.com', nombre: 'Chef', apellido: 'Tita', rol: 'COCINA' }
const ADMIN  = { id: 1, email: 'admin@cantina.com',  nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

// ─── Mocks de datos ───────────────────────────────────────────────────────────

const TARJETA_OK = {
  nro_tarjeta: '11223344',
  estado: 'ACTIVA',
  hijo_nombre: 'Lucía Martínez',
  hijo: 5,
  saldo_actual: '85000',
}

const TARJETA_BLOQUEADA = {
  nro_tarjeta: '55667788',
  estado: 'BLOQUEADA',
  hijo_nombre: 'Pedro López',
  hijo: 6,
  saldo_actual: '0',
}

const HIJOS_MOCK = [
  { id: 5, nombre: 'Lucía', apellido: 'Martínez', grado: '2° A', nombre_completo: 'Lucía Martínez' },
  { id: 6, nombre: 'Pedro', apellido: 'López',    grado: '3° B', nombre_completo: 'Pedro López'    },
]

const SUSCRIPCIONES_MOCK = [
  { hijo: 5, hijo_nombre: 'Lucía Martínez', hijo_grado: '2° A', estado: 'ACTIVA' },
  { hijo: 6, hijo_nombre: 'Pedro López',    hijo_grado: '3° B', estado: 'ACTIVA' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function loginAs(page: Page, user: typeof ADMIN | typeof COCINA) {
  // LIFO: catch-all primero (menor prioridad), específicos después
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

async function setupComedor(page: Page, opts: { consumidosHoyIds?: number[] } = {}) {
  // Catch-all hijos
  await page.route(/\/api\/v1\/clientes\/hijos/, (route) =>
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ results: HIJOS_MOCK, count: 2 }),
    })
  )
  // Suscripciones activas (para panel Lista de hoy)
  await page.route(/\/api\/v1\/almuerzos\/suscripciones/, (route) =>
    route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ results: SUSCRIPCIONES_MOCK, count: 2 }),
    })
  )
  // Registros de consumo (GET = consumidosHoy para anti-doble-scan; POST = registro)
  const consumidos = (opts.consumidosHoyIds ?? []).map(id => ({ hijo: id }))
  await page.route(/\/api\/v1\/almuerzos\/registros-consumo/, (route) => {
    if (route.request().method() === 'POST') {
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id: 99 }) })
    }
    return route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ results: consumidos, count: consumidos.length }),
    })
  })
  // Tarjeta por defecto: no encontrada
  await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
  )
}

// ── Comedor: estado inicial ───────────────────────────────────────────────────

test.describe('Comedor — estado inicial', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, COCINA)
    await setupComedor(page)
    await page.goto('/comedor')
    await expect(page).toHaveURL('/comedor')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra el input de tarjeta con placeholder correcto', async ({ page }) => {
    await expect(page.getByPlaceholder('Nro. de tarjeta...')).toBeVisible()
  })

  test('muestra instrucción "Pasá la tarjeta" en estado idle', async ({ page }) => {
    await expect(page.getByText('Pasá la tarjeta')).toBeVisible({ timeout: 5000 })
  })

  test('muestra los botones de panel Recientes y Lista de hoy', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Recientes/ })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Lista de hoy' })).toBeVisible()
  })

  test('no muestra botón PDF cuando no hay registros', async ({ page }) => {
    await expect(page.getByRole('button', { name: /PDF/ })).not.toBeVisible()
  })
})

// ── Comedor: flujo de scan exitoso ────────────────────────────────────────────

test.describe('Comedor — scan exitoso', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, COCINA)
    await setupComedor(page)
    // LIFO: override tarjetas con TARJETA_OK
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ results: [TARJETA_OK], count: 1 }),
      })
    )
    await page.goto('/comedor')
    // Esperar que hijos carguen (hijosLoading = false) antes de escanear
    await expect(page.getByPlaceholder('Nro. de tarjeta...')).toBeVisible({ timeout: 8000 })
    const input = page.getByPlaceholder('Nro. de tarjeta...')
    await input.fill('11223344')
    await input.press('Enter')
  })

  test('muestra "Ingreso registrado"', async ({ page }) => {
    await expect(page.getByText('Ingreso registrado')).toBeVisible({ timeout: 6000 })
  })

  test('muestra el nombre del alumno en grande', async ({ page }) => {
    await expect(page.getByText('Lucía Martínez').first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra el grado del alumno', async ({ page }) => {
    await expect(page.getByText('2° A').first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra el saldo en tarjeta', async ({ page }) => {
    await expect(page.getByText(/Saldo en tarjeta/)).toBeVisible({ timeout: 6000 })
  })

  test('aparece el botón PDF tras el primer ingreso', async ({ page }) => {
    await expect(page.getByText('Ingreso registrado')).toBeVisible({ timeout: 6000 })
    await expect(page.getByRole('button', { name: /PDF/ })).toBeVisible()
  })
})

// ── Comedor: casos de error ───────────────────────────────────────────────────

test.describe('Comedor — casos de error', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, COCINA)
    await setupComedor(page)
    await page.goto('/comedor')
    await expect(page.getByPlaceholder('Nro. de tarjeta...')).toBeVisible({ timeout: 8000 })
  })

  test('tarjeta no encontrada muestra error', async ({ page }) => {
    const input = page.getByPlaceholder('Nro. de tarjeta...')
    await input.fill('00000000')
    await input.press('Enter')
    await expect(page.getByText('Tarjeta no encontrada')).toBeVisible({ timeout: 5000 })
  })

  test('tarjeta bloqueada muestra mensaje de error', async ({ page }) => {
    // LIFO override: tarjeta bloqueada
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ results: [TARJETA_BLOQUEADA], count: 1 }),
      })
    )
    const input = page.getByPlaceholder('Nro. de tarjeta...')
    await input.fill('55667788')
    await input.press('Enter')
    await expect(page.getByText('bloqueada')).toBeVisible({ timeout: 5000 })
  })

  test('página no muestra error boundary al fallar la API', async ({ page }) => {
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 500, contentType: 'application/json', body: '{"detail":"server error"}' })
    )
    const input = page.getByPlaceholder('Nro. de tarjeta...')
    await input.fill('99999999')
    await input.press('Enter')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible({ timeout: 5000 })
  })
})

// ── Comedor: anti-doble-scan ──────────────────────────────────────────────────

test.describe('Comedor — anti-doble-scan', () => {
  test('alumno que ya almorzó hoy muestra error al intentar registrar de nuevo', async ({ page }) => {
    await loginAs(page, COCINA)
    // hijo 5 ya está en consumidosHoy desde el inicio
    await setupComedor(page, { consumidosHoyIds: [5] })
    // LIFO: tarjeta OK
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ results: [TARJETA_OK], count: 1 }),
      })
    )
    await page.goto('/comedor')
    await expect(page.getByPlaceholder('Nro. de tarjeta...')).toBeVisible({ timeout: 8000 })

    const input = page.getByPlaceholder('Nro. de tarjeta...')
    await input.fill('11223344')
    await input.press('Enter')
    await expect(page.getByText('ya registró almuerzo hoy')).toBeVisible({ timeout: 5000 })
  })
})

// ── Comedor: panel Lista de hoy ───────────────────────────────────────────────

test.describe('Comedor — panel Lista de hoy', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await setupComedor(page)
    await page.goto('/comedor')
    await expect(page.getByPlaceholder('Nro. de tarjeta...')).toBeVisible({ timeout: 8000 })
  })

  test('click en Lista de hoy muestra suscriptos activos', async ({ page }) => {
    await page.getByRole('button', { name: 'Lista de hoy' }).click()
    await expect(page.getByText('Lucía Martínez').first()).toBeVisible({ timeout: 6000 })
    await expect(page.getByText('Pedro López')).toBeVisible()
  })

  test('panel recientes vuelve al estado correcto', async ({ page }) => {
    await page.getByRole('button', { name: 'Lista de hoy' }).click()
    await expect(page.getByText('Lucía Martínez')).toBeVisible({ timeout: 5000 })
    // Volver a Recientes
    await page.getByRole('button', { name: /Recientes/ }).click()
    await expect(page.getByText('Sin ingresos aún')).toBeVisible({ timeout: 3000 })
  })
})

// ── Comedor: control de acceso ────────────────────────────────────────────────

test.describe('Comedor — acceso por rol', () => {
  test('CAJERO sin acceso a /comedor es redirigido', async ({ page }) => {
    const CAJERO = { id: 2, email: 'cajero@cantina.com', nombre: 'Cajero', apellido: 'Test', rol: 'CAJERO' }
    await loginAs(page, CAJERO as typeof ADMIN)
    await page.goto('/comedor')
    // CAJERO no tiene permiso para comedor — redirige a /login o /dashboard
    await expect(page).not.toHaveURL('/comedor')
  })
})
