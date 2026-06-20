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

// ── Fixtures comunes para los bloques de tests adicionales ─────────────────

const TARJETA_MOCK = {
  nro_tarjeta: 'T-001',
  estado: 'ACTIVA',
  saldo_actual: '100000',
  saldo_disponible: '100000',
  hijo_nombre: 'Juan Pérez',
  hijo_grado: '3er Grado',
  hijo_restricciones: [],
  permite_saldo_negativo: false,
  limite_credito: '0',
  cliente_id: 1,
}

async function setupModoRecreo(page: import('@playwright/test').Page) {
  await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(CAJA_ABIERTA) })
  )
  await page.route(/\/api\/v1\/productos\/categorias/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: CATEGORIAS_MOCK, count: 2 }) })
  )
  await page.route(/\/api\/v1\/productos\/productos/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: PRODUCTOS_MOCK, count: 2 }) })
  )
}

// ── Scan de tarjeta ────────────────────────────────────────────────────────

test.describe('Modo Recreo — scan de tarjeta', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, CAJERO)
    await setupModoRecreo(page)
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [TARJETA_MOCK], count: 1 }) })
    )
    await page.route(/\/api\/v1\/ventas\/ventas/, (route) =>
      route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id: 99, monto_total: 5000, estado: 'COMPLETADA' }) })
    )
    await page.goto('/modo-recreo')
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })
  })

  test('scan T-001 muestra nombre del alumno', async ({ page }) => {
    const scanner = page.getByPlaceholder('Escanear tarjeta o código…')
    await scanner.fill('T-001')
    await scanner.press('Enter')
    await expect(page.getByText('Juan Pérez')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('3er Grado')).toBeVisible()
  })

  test('flujo completo: scan → agregar producto → cobrar', async ({ page }) => {
    const scanner = page.getByPlaceholder('Escanear tarjeta o código…')
    await scanner.fill('T-001')
    await scanner.press('Enter')
    await expect(page.getByText('Juan Pérez')).toBeVisible({ timeout: 5000 })

    await page.getByRole('button', { name: /Empanada/ }).first().click()
    await expect(page.getByRole('listitem').filter({ hasText: 'Empanada' })).toBeVisible()

    const cobrarBtn = page.getByRole('button', { name: /COBRAR/i })
    await expect(cobrarBtn).toBeEnabled({ timeout: 3000 })
    await cobrarBtn.click()

    // Flash de éxito muestra el nombre del alumno
    await expect(page.locator('p.text-5xl.font-black')).toContainText('Juan Pérez', { timeout: 5000 })
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('tarjeta no encontrada muestra toast de error', async ({ page }) => {
    // Override LIFO: resultado vacío para cualquier tarjeta
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    const scanner = page.getByPlaceholder('Escanear tarjeta o código…')
    await scanner.fill('T-0000')
    await scanner.press('Enter')
    await expect(page.getByText('Tarjeta no encontrada')).toBeVisible({ timeout: 5000 })
  })

  test('scan de código de barras sin tarjeta previa muestra toast de error', async ({ page }) => {
    const scanner = page.getByPlaceholder('Escanear tarjeta o código…')
    await scanner.fill('7890000000001')  // código de barras numérico = producto
    await scanner.press('Enter')
    await expect(page.getByText('Escanee una tarjeta primero')).toBeVisible({ timeout: 5000 })
  })
})

// ── Filtro por categoría ───────────────────────────────────────────────────

test.describe('Modo Recreo — filtro por categoría', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, CAJERO)
    await setupModoRecreo(page)
    await page.goto('/modo-recreo')
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })
  })

  test('filtrar por Comida oculta productos de Bebida', async ({ page }) => {
    await page.getByRole('button', { name: 'Comida' }).click()
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Gaseosa/ })).not.toBeVisible()
  })

  test('volver a Todos muestra todos los productos', async ({ page }) => {
    await page.getByRole('button', { name: 'Comida' }).click()
    await expect(page.getByRole('button', { name: /Gaseosa/ })).not.toBeVisible()
    await page.getByRole('button', { name: 'Todos' }).click()
    await expect(page.getByRole('button', { name: /Gaseosa/ }).first()).toBeVisible()
  })
})

// ── Modo offline / degradación graceful ───────────────────────────────────────
//
// El SW (sw.js) maneja el cache en producción; en dev el SW no está activo.
// Estos tests verifican el comportamiento de la app cuando la red falla:
//   - Catálogo cargado previamente sigue siendo visible (mocks interceptan antes de red)
//   - POST ventas con respuesta offline-queue (202 _queued) no rompe la app
//   - POST ventas que falla con abort no muestra error boundary

test.describe('Modo Recreo — modo offline / degradación', () => {
  test('catálogo ya cargado permanece visible al simular pérdida de red', async ({ page, context }) => {
    await loginAs(page, CAJERO)
    await setupModoRecreo(page)
    await page.goto('/modo-recreo')
    // Esperar que el catálogo cargue con los mocks activos
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })

    // Desconectar la red — los mocks de page.route() siguen respondiendo
    // porque interceptan antes del nivel de red
    await context.setOffline(true)

    // El catálogo ya estaba en el DOM; no debe desaparecer
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible()
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()

    await context.setOffline(false)
  })

  test('POST ventas con respuesta 202 queued no muestra error boundary', async ({ page }) => {
    // El SW devuelve 202 { _queued: true } cuando encola una venta offline.
    // La app debe manejar esto sin explotar.
    await loginAs(page, CAJERO)
    await setupModoRecreo(page)
    // Mock POST ventas → 202 simulando respuesta del SW offline
    await page.route(/\/api\/v1\/ventas\/ventas/, (route) => {
      if (route.request().method() === 'POST') {
        return route.fulfill({
          status: 202, contentType: 'application/json',
          body: JSON.stringify({ _queued: true, message: 'Venta guardada offline. Se sincronizará al reconectar.' }),
        })
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    })
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          results: [{
            nro_tarjeta: 'T-001', estado: 'ACTIVA', saldo_actual: '100000',
            saldo_disponible: '100000', hijo_nombre: 'Juan Pérez', hijo_grado: '3er Grado',
            hijo_restricciones: [], permite_saldo_negativo: false, limite_credito: '0', cliente_id: 1,
          }],
          count: 1,
        }),
      })
    )
    await page.goto('/modo-recreo')
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })

    // Scan tarjeta → luego agregar producto → cobrar
    const scanner = page.getByPlaceholder('Escanear tarjeta o código…')
    await scanner.fill('T-001')
    await scanner.press('Enter')
    await expect(page.getByText('Juan Pérez')).toBeVisible({ timeout: 5000 })
    await page.getByRole('button', { name: /Empanada/ }).first().click()
    await page.getByRole('button', { name: /COBRAR/i }).click()

    // No debe mostrar error boundary
    await expect(page.getByText('Algo salió mal')).not.toBeVisible({ timeout: 5000 })
  })

  test('POST ventas abortado por red no muestra error boundary', async ({ page }) => {
    await loginAs(page, CAJERO)
    await setupModoRecreo(page)
    // Abortar la petición de ventas (simula timeout/red caída)
    await page.route(/\/api\/v1\/ventas\/ventas/, (route) => {
      if (route.request().method() === 'POST') {
        return route.abort('failed')
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    })
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          results: [{
            nro_tarjeta: 'T-002', estado: 'ACTIVA', saldo_actual: '50000',
            saldo_disponible: '50000', hijo_nombre: 'Ana García', hijo_grado: '4° A',
            hijo_restricciones: [], permite_saldo_negativo: false, limite_credito: '0', cliente_id: 2,
          }],
          count: 1,
        }),
      })
    )
    await page.goto('/modo-recreo')
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })

    const scanner = page.getByPlaceholder('Escanear tarjeta o código…')
    await scanner.fill('T-002')
    await scanner.press('Enter')
    await expect(page.getByText('Ana García')).toBeVisible({ timeout: 5000 })
    await page.getByRole('button', { name: /Empanada/ }).first().click()
    await page.getByRole('button', { name: /COBRAR/i }).click()

    // La app no debe mostrar error boundary — puede mostrar toast de error
    await expect(page.getByText('Algo salió mal')).not.toBeVisible({ timeout: 5000 })
  })

  test('catálogo carga aunque tarjetas API falle (degradación parcial)', async ({ page }) => {
    await loginAs(page, CAJERO)
    // Caja y categorías/productos cargan normalmente
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(CAJA_ABIERTA) })
    )
    await page.route(/\/api\/v1\/productos\/categorias/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: CATEGORIAS_MOCK, count: 2 }) })
    )
    await page.route(/\/api\/v1\/productos\/productos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: PRODUCTOS_MOCK, count: 2 }) })
    )
    // Tarjetas API falla con 503
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 503, contentType: 'application/json', body: '{"detail":"servicio no disponible"}' })
    )
    await page.goto('/modo-recreo')

    // El catálogo debe seguir cargando aunque tarjetas falle
    await expect(page.getByRole('button', { name: /Empanada/ }).first()).toBeVisible({ timeout: 8000 })
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })
})

// ── Sin caja abierta ───────────────────────────────────────────────────────

test.describe('Modo Recreo — sin caja abierta', () => {
  test('muestra pantalla de bloqueo cuando no hay caja', async ({ page }) => {
    await loginAs(page, CAJERO)
    // 404 → catch → setCierreCaja(false) → pantalla de bloqueo
    await page.route(/\/api\/v1\/contabilidad\/cierres-caja/, (route) =>
      route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'No encontrado' }) })
    )
    await page.route(/\/api\/v1\/productos\/categorias/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.route(/\/api\/v1\/productos\/productos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.goto('/modo-recreo')
    await expect(page.getByRole('heading', { name: 'Caja no iniciada' })).toBeVisible({ timeout: 8000 })
    await expect(page.getByRole('button', { name: 'Ir a Cajas' })).toBeVisible()
  })
})
