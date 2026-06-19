import { test, expect } from '@playwright/test'

// ─── Usuarios ─────────────────────────────────────────────────────────────────

const CLIENTE_WEB = {
  id: 10, email: 'papa@example.com', nombre: 'Carlos', apellido: 'García', rol: 'CLIENTE_WEB',
}
const ADMIN = {
  id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN',
}

// ─── Mocks de datos ───────────────────────────────────────────────────────────

const MI_HIJO_MOCK = {
  cliente: { id: 10, nombre: 'Carlos García', email: 'papa@example.com' },
  mes: { anio: 2026, mes: 6 },
  hijos: [{
    id: 1,
    nombre: 'Lucas García',
    grado: '3° A',
    tarjeta: {
      nro_tarjeta: '12345678',
      saldo_actual: 85000,
      estado: 'ACTIVA',
      en_alerta: false,
    },
    restricciones: [],
    consumos_mes: {
      total: 5,
      cobrados: 3,
      ultimos: [
        { fecha_consumo: '2026-06-10', costo_almuerzo: '15000', ya_cobrado: true },
        { fecha_consumo: '2026-06-11', costo_almuerzo: '15000', ya_cobrado: false },
      ],
    },
    cuenta_mensual: {
      cantidad_almuerzos: 5,
      monto_total: 75000,
      monto_pagado: 45000,
      monto_pendiente: 30000,
      estado: 'PARCIAL',
    },
  }],
}

const HISTORIAL_MOCK = {
  anio: 2026,
  mes: 6,
  hijo: { id: 1, nombre: 'Lucas García' },
  consumos: [
    { id: 1, fecha_consumo: '2026-06-10', costo_almuerzo: '15000', ya_cobrado: true },
    { id: 2, fecha_consumo: '2026-06-11', costo_almuerzo: '15000', ya_cobrado: false },
  ],
  total: 2,
  monto_total: 30000,
  cobrados: 1,
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function setupPortalAuth(page: import('@playwright/test').Page, user = CLIENTE_WEB) {
  // LIFO: catch-all primero, específicos después (mayor prioridad)
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
}

async function loginAsPortal(page: import('@playwright/test').Page) {
  await setupPortalAuth(page)

  // mi-hijo/ necesita responder para que el dashboard no muestre error
  await page.route(/\/api\/v1\/usuarios\/portal\/mi-hijo/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MI_HIJO_MOCK) })
  )

  await page.goto('/portal/login')
  await page.getByPlaceholder('tucorreo@email.com').fill(CLIENTE_WEB.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await page.waitForURL('/portal')
}

// ── Portal Login ──────────────────────────────────────────────────────────────

test.describe('Portal — Login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/portal/login')
  })

  test('muestra el formulario del portal de padres', async ({ page }) => {
    await expect(page.getByText('Portal de Padres')).toBeVisible()
    await expect(page.getByPlaceholder('tucorreo@email.com')).toBeVisible()
    await expect(page.getByPlaceholder('••••••••')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Ingresar' })).toBeVisible()
  })

  test('muestra el link a olvidé mi contraseña', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Olvidé mi contraseña' })).toBeVisible()
  })

  test('muestra el link a acceso empleados', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Acceso empleados' })).toBeVisible()
  })

  test('login exitoso redirige a /portal', async ({ page }) => {
    await setupPortalAuth(page)
    await page.route(/\/api\/v1\/usuarios\/portal\/mi-hijo/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MI_HIJO_MOCK) })
    )

    await page.getByPlaceholder('tucorreo@email.com').fill(CLIENTE_WEB.email)
    await page.getByPlaceholder('••••••••').fill('password123')
    await page.getByRole('button', { name: 'Ingresar' }).click()
    await expect(page).toHaveURL('/portal')
  })

  test('credenciales incorrectas muestra error', async ({ page }) => {
    await page.route(/\/api\/token/, (route) =>
      route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"No active account"}' })
    )
    await page.getByPlaceholder('tucorreo@email.com').fill('wrong@example.com')
    await page.getByPlaceholder('••••••••').fill('wrongpass')
    await page.getByRole('button', { name: 'Ingresar' }).click()
    await expect(page.getByText('Credenciales incorrectas')).toBeVisible()
  })

  test('el formulario de recuperación de contraseña aparece al hacer click', async ({ page }) => {
    await page.getByRole('button', { name: 'Olvidé mi contraseña' }).click()
    await expect(page.getByText('Recuperar contraseña')).toBeVisible()
    await expect(page.getByPlaceholder('tucorreo@email.com')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Enviar enlace' })).toBeVisible()
  })
})

// ── Portal Dashboard ──────────────────────────────────────────────────────────

test.describe('Portal — Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsPortal(page)
    await expect(page).toHaveURL('/portal')
  })

  test('carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra el saludo con el nombre del padre', async ({ page }) => {
    await expect(page.getByText(`Hola, ${CLIENTE_WEB.nombre}`)).toBeVisible({ timeout: 5000 })
  })

  test('muestra el nombre y grado del hijo', async ({ page }) => {
    await expect(page.getByText('Lucas García')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('3° A')).toBeVisible()
  })

  test('muestra el saldo de la tarjeta', async ({ page }) => {
    // 85000 → formateado como "Gs. 85.000"
    await expect(page.getByText(/85\.000/)).toBeVisible({ timeout: 5000 })
  })

  test('muestra las pestañas de navegación del hijo', async ({ page }) => {
    await expect(page.getByRole('tab', { name: 'Resumen' })).toBeVisible({ timeout: 5000 })
    await expect(page.getByRole('tab', { name: /Historial/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Cantina/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Plan/ })).toBeVisible()
  })

  test('muestra el botón Cargar saldo con tarjeta', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Cargar saldo con tarjeta' })).toBeVisible({ timeout: 5000 })
  })

  test('muestra la cuenta mensual de almuerzos', async ({ page }) => {
    await expect(page.getByText('Almuerzos tomados')).toBeVisible({ timeout: 5000 })
    // Pendiente de pago: 30000
    await expect(page.getByText('Pendiente de pago')).toBeVisible()
  })

  test('la barra de navegación inferior muestra todas las secciones', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Recargar' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Historial' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Facturas' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Alertas' })).toBeVisible()
  })

  test('click en Recargar navega a /portal/carga-saldo', async ({ page }) => {
    await page.getByRole('button', { name: 'Recargar' }).click()
    await expect(page).toHaveURL('/portal/carga-saldo')
  })

  test('click en Historial navega a /portal/historial', async ({ page }) => {
    await page.route(/\/api\/v1\/usuarios\/portal\/historial-consumos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(HISTORIAL_MOCK) })
    )
    await page.getByRole('button', { name: 'Historial' }).click()
    await expect(page).toHaveURL('/portal/historial')
  })
})

// ── Portal Carga de Saldo ─────────────────────────────────────────────────────

test.describe('Portal — Carga de Saldo', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsPortal(page)
    await page.goto('/portal/carga-saldo')
    await expect(page).toHaveURL('/portal/carga-saldo')
  })

  test('carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra la página de carga de saldo con título', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Carga de Saldo' })).toBeVisible({ timeout: 5000 })
  })

  test('muestra el alumno y saldo actual', async ({ page }) => {
    await expect(page.getByText('Lucas García')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/85\.000/)).toBeVisible()
  })

  test('muestra los botones de monto rápido', async ({ page }) => {
    await expect(page.getByRole('button', { name: '50k' })).toBeVisible({ timeout: 5000 })
    await expect(page.getByRole('button', { name: '100k' })).toBeVisible()
    await expect(page.getByRole('button', { name: '150k' })).toBeVisible()
  })

  test('el botón Ir a pagar está deshabilitado sin monto seleccionado', async ({ page }) => {
    const btn = page.getByRole('button', { name: /Ir a pagar/ })
    await expect(btn).toBeVisible({ timeout: 5000 })
    await expect(btn).toBeDisabled()
  })

  test('seleccionar monto habilita el botón Ir a pagar', async ({ page }) => {
    await page.getByRole('button', { name: '100k' }).click()
    const btn = page.getByRole('button', { name: /Ir a pagar/ })
    await expect(btn).toBeEnabled({ timeout: 3000 })
  })

  test('muestra el resumen antes de pagar al seleccionar monto', async ({ page }) => {
    await page.getByRole('button', { name: '100k' }).click()
    await expect(page.getByText('Resumen')).toBeVisible({ timeout: 3000 })
    await expect(page.getByText('Lucas García')).toBeVisible()
    await expect(page.getByText('12345678')).toBeVisible()
  })

  test('muestra resultado aprobado cuando Bancard redirige con estado=aprobado', async ({ page }) => {
    await page.goto('/portal/carga-saldo?estado=aprobado&monto=100000')
    await expect(page.getByText('¡Pago aprobado!')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/100\.000/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Realizar otra carga' })).toBeVisible()
  })

  test('muestra resultado cancelado cuando Bancard redirige con estado=cancelado', async ({ page }) => {
    await page.goto('/portal/carga-saldo?estado=cancelado')
    await expect(page.getByText('Pago cancelado')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('No se realizó ningún cargo.')).toBeVisible()
  })

  test('muestra resultado rechazado cuando Bancard redirige con estado=rechazado', async ({ page }) => {
    await page.goto('/portal/carga-saldo?estado=rechazado')
    await expect(page.getByText('Pago rechazado')).toBeVisible({ timeout: 5000 })
  })

  test('flujo completo — Ir a pagar llama a Bancard y procesa el retorno con aprobado', async ({ page }) => {
    // El beforeEach ya cargó /mi-hijo/ con un hijo (Lucas García, tarjeta 12345678, saldo 85000).
    // Al ser el único hijo se auto-selecciona. Mock del endpoint de iniciación Bancard:
    await page.route(/\/api\/v1\/core\/bancard\/iniciar/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          redirect_url: 'http://localhost:5173/portal/carga-saldo?estado=aprobado&monto=100000',
        }),
      })
    )

    await page.getByRole('button', { name: '100k' }).click()
    await expect(page.getByRole('button', { name: /Ir a pagar/ })).toBeEnabled({ timeout: 3000 })
    await page.getByRole('button', { name: /Ir a pagar/ }).click()

    // window.location.href redirige a la URL de retorno de Bancard
    await expect(page).toHaveURL(/estado=aprobado/, { timeout: 8000 })
    await expect(page.getByText('¡Pago aprobado!')).toBeVisible()
    await expect(page.getByText(/100\.000/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Realizar otra carga' })).toBeVisible()
  })
})

// ── Portal Historial ──────────────────────────────────────────────────────────

test.describe('Portal — Historial de Almuerzos', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsPortal(page)

    await page.route(/\/api\/v1\/usuarios\/portal\/historial-consumos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(HISTORIAL_MOCK) })
    )

    await page.goto('/portal/historial')
    await expect(page).toHaveURL('/portal/historial')
  })

  test('carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra el título y el navegador de meses', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Historial de Almuerzos' })).toBeVisible()
    // Navegador de meses con chevrons
    await expect(page.locator('button').filter({ has: page.locator('svg') }).first()).toBeVisible()
  })

  test('muestra las estadísticas del mes', async ({ page }) => {
    await expect(page.getByText('Almuerzos')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Cobrados')).toBeVisible()
    await expect(page.getByText('Total')).toBeVisible()
  })

  test('muestra la lista de consumos con badges', async ({ page }) => {
    // Badge "Cobrado" para consumo cobrado
    await expect(page.getByText('Cobrado').first()).toBeVisible({ timeout: 5000 })
    // Badge "Pendiente" para consumo no cobrado
    await expect(page.getByText('Pendiente')).toBeVisible()
  })
})

// ── Control de acceso ─────────────────────────────────────────────────────────

test.describe('Portal — Control de acceso', () => {
  test('ADMIN no puede acceder a /portal — redirige a /login', async ({ page }) => {
    await setupPortalAuth(page, ADMIN)
    await page.route(/\/api\/v1\//, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    )
    // Simular que el store ya tiene al ADMIN autenticado
    await page.goto('/portal/login')
    await page.getByPlaceholder('tucorreo@email.com').fill(ADMIN.email)
    await page.getByPlaceholder('••••••••').fill('password123')
    await page.getByRole('button', { name: 'Ingresar' }).click()
    // El ADMIN no tiene rol CLIENTE_WEB → PrivateRoute redirige a /login
    await expect(page).toHaveURL('/login')
  })

  test('usuario sin autenticar en /portal redirige a /login', async ({ page }) => {
    await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) =>
      route.fulfill({ status: 401, contentType: 'application/json', body: '{}' })
    )
    await page.goto('/portal')
    await expect(page).toHaveURL('/login')
  })

  test('usuario sin autenticar en /portal/carga-saldo redirige a /login', async ({ page }) => {
    await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) =>
      route.fulfill({ status: 401, contentType: 'application/json', body: '{}' })
    )
    await page.goto('/portal/carga-saldo')
    await expect(page).toHaveURL('/login')
  })
})
