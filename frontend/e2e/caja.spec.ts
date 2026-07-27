import { test, expect } from '@playwright/test'

const ADMIN  = { id: 1, email: 'admin@cantina.com',  nombre: 'Admin',  apellido: 'Tita', rol: 'ADMIN' }
const CAJERO = { id: 2, email: 'cajero@cantina.com', nombre: 'Cajero', apellido: 'Test', rol: 'CAJERO' }

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN) {
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

// ── Mocks ────────────────────────────────────────────────────────────────────

const CAJAS_MOCK = [
  { id: 1, nombre: 'Caja Principal', ubicacion: 'Entrada', activo: true },
  { id: 2, nombre: 'Caja Comedor',   ubicacion: 'Comedor', activo: true },
]

const MEDIOS_PAGO_MOCK = [
  { id: 1, descripcion: 'Efectivo', activo: true },
  { id: 2, descripcion: 'Tarjeta',  activo: true },
]

const CIERRE_ABIERTO = {
  id: 10,
  caja: 1,
  caja_nombre: 'Caja Principal',
  empleado: 2,
  empleado_nombre: 'Cajero Test',
  fecha_apertura: new Date().toISOString(),
  fecha_cierre: null,
  monto_inicial: '50000',
  monto_contado_fisico: null,
  diferencia_efectivo: null,
  estado: 'ABIERTO',
  observaciones_conciliacion: null,
}

const CIERRE_CERRADO = {
  ...CIERRE_ABIERTO,
  id: 11,
  fecha_cierre: new Date().toISOString(),
  monto_contado_fisico: '150000',
  diferencia_efectivo: '0',
  estado: 'CERRADO',
}

const ARQUEO_MOCK = {
  monto_inicial: 50000,
  efectivo_esperado: 150000,
  efectivo_ingresos: 100000,
  efectivo_egresos: 0,
  pos_total: 30000,
  prepago_total: 20000,
  ingresos_total: 100000,
  egresos_total: 0,
  ingresos_por_medio: [{ medio: 'Efectivo', total: 100000 }],
  egresos_por_medio: [],
}

// Registra los mocks de caja en orden LIFO correcto.
// Los más específicos se registran DESPUÉS para ganar al catch-all del loginAs.
async function mockCajaBase(page: import('@playwright/test').Page) {
  await page.route(/\/api\/v1\/contabilidad\/cajas/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: CAJAS_MOCK, count: 2 }) })
  )
  await page.route(/\/api\/v1\/core\/medios-pago/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: MEDIOS_PAGO_MOCK }) })
  )
}

// ── Sin turno activo ──────────────────────────────────────────────────────────

test.describe('Caja — sin turno activo', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await mockCajaBase(page)

    // LIFO: cierres-caja genérico primero, mi-caja específico DESPUÉS (mayor prioridad)
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja\/mi-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: 'null' })
    )

    await page.goto('/caja')
    await expect(page).toHaveURL('/caja')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra las tres tarjetas de estado', async ({ page }) => {
    await expect(page.getByText('Abiertas').first()).toBeVisible()
    await expect(page.getByText('Cerradas').first()).toBeVisible()
    await expect(page.getByText('Conciliadas').first()).toBeVisible()
  })

  test('muestra el botón Abrir Caja', async ({ page }) => {
    await expect(page.locator('button', { hasText: 'Abrir Caja' })).toBeVisible()
  })

  test('el modal de Abrir Caja aparece al hacer click', async ({ page }) => {
    await page.locator('button', { hasText: 'Abrir Caja' }).click()
    // El modal se abre y el selector contiene ambas cajas disponibles
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByRole('dialog')).toContainText('Caja Principal')
    await expect(page.getByRole('dialog')).toContainText('Caja Comedor')
  })

  test('el modal de Abrir Caja tiene el campo de monto inicial', async ({ page }) => {
    await page.locator('button', { hasText: 'Abrir Caja' }).click()
    await expect(page.getByLabel('Monto Inicial (Gs.)')).toBeVisible()
  })

  test('el banner de turno activo no se muestra', async ({ page }) => {
    await expect(page.getByText(/Turno activo/)).not.toBeVisible()
  })
})

// ── Con turno activo ──────────────────────────────────────────────────────────

test.describe('Caja — con turno activo', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, CAJERO)
    await mockCajaBase(page)

    // LIFO: genérico primero, luego arqueo específico, luego mi-caja (máxima prioridad)
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [CIERRE_ABIERTO], count: 1 }) })
    )
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja\/\d+\/arqueo/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ARQUEO_MOCK) })
    )
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja\/mi-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(CIERRE_ABIERTO) })
    )

    await page.goto('/caja')
    await expect(page).toHaveURL('/caja')
  })

  test('muestra el banner de turno activo con el nombre de la caja', async ({ page }) => {
    await expect(page.getByText(/Turno activo/)).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/Caja Principal/).first()).toBeVisible()
  })

  test('muestra el arqueo en vivo con los cuatro paneles', async ({ page }) => {
    await expect(page.getByText('Efectivo Caja')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('POS / Transferencia')).toBeVisible()
    await expect(page.getByText('Prepago RFID')).toBeVisible()
    await expect(page.getByText('Egresos').first()).toBeVisible()
  })

  test('la tabla muestra el botón Cerrar para la caja ABIERTO', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Cerrar' })).toBeVisible({ timeout: 5000 })
  })

  test('el modal de cierre abre con arqueo y campo de monto contado', async ({ page }) => {
    await page.getByRole('button', { name: 'Cerrar' }).click()
    await expect(page.getByText(/Cerrar Caja — Caja Principal/)).toBeVisible({ timeout: 3000 })
    await expect(page.getByText('Efectivo esperado')).toBeVisible({ timeout: 5000 })
    await expect(page.getByLabel('Monto Contado en Efectivo (Gs.)')).toBeVisible()
  })

  test('al tipear el monto contado muestra la diferencia en vivo', async ({ page }) => {
    await page.getByRole('button', { name: 'Cerrar' }).click()
    await expect(page.getByLabel('Monto Contado en Efectivo (Gs.)')).toBeVisible({ timeout: 3000 })
    await page.getByLabel('Monto Contado en Efectivo (Gs.)').fill('150000')
    // La diferencia debería mostrarse (150000 - 150000 = 0 → badge verde)
    await expect(page.getByText('Diferencia')).toBeVisible({ timeout: 2000 })
  })
})

// ── Conciliación ──────────────────────────────────────────────────────────────

test.describe('Caja — conciliación', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await mockCajaBase(page)

    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [CIERRE_CERRADO], count: 1 }) })
    )
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja\/mi-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: 'null' })
    )

    await page.goto('/caja')
    await expect(page).toHaveURL('/caja')
  })

  test('la tabla muestra el botón Conciliar para cierres CERRADO', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Conciliar' })).toBeVisible({ timeout: 5000 })
  })

  test('el modal de conciliación muestra el monto contado y la diferencia', async ({ page }) => {
    await page.getByRole('button', { name: 'Conciliar' }).click()
    await expect(page.getByText(/Conciliar Cierre — Caja Principal/)).toBeVisible({ timeout: 3000 })
    await expect(page.getByText('Monto contado:')).toBeVisible()
    await expect(page.getByText('Diferencia:')).toBeVisible()
  })

  test('el modal de conciliación tiene el campo de observaciones', async ({ page }) => {
    await page.getByRole('button', { name: 'Conciliar' }).click()
    await expect(page.getByPlaceholder('Notas de conciliación (opcional)...')).toBeVisible({ timeout: 3000 })
  })

  test('el botón no muestra Cerrar para cierres CERRADO', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Cerrar' })).not.toBeVisible({ timeout: 3000 })
  })
})

// ── Control de acceso ─────────────────────────────────────────────────────────

test.describe('Caja — control de acceso', () => {
  test('CAJERO puede acceder a /caja', async ({ page }) => {
    await loginAs(page, CAJERO)

    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja\/mi-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: 'null' })
    )

    await page.goto('/caja')
    await expect(page).toHaveURL('/caja')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.locator('button', { hasText: 'Abrir Caja' })).toBeVisible()
  })

  test('ADMIN puede acceder a /caja', async ({ page }) => {
    await loginAs(page, ADMIN)

    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja\/mi-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: 'null' })
    )

    await page.goto('/caja')
    await expect(page).toHaveURL('/caja')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })
})
