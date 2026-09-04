import { test, expect, type Page } from '@playwright/test'

const ADMIN = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const MENU_HOY = {
  id_menu: 1,
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
      id_registro_consumo: 10,
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
  await page.getByPlaceholder('Tu CI o RUC').fill('1234567')
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

// ── Mocks adicionales ──────────────────────────────────────────────────────

const CUENTA_MOCK = {
  id_cuenta_mensual: 1,
  hijo: 1,
  hijo_nombre: 'Sofía Torres',
  anio: 2026,
  mes: 5,
  cantidad_almuerzos: 3,
  monto_total: '45000',
  monto_pagado: '0',
  saldo_pendiente: '45000',
  estado: 'PENDIENTE',
}

const SUSCRIPCION_MOCK = {
  id_suscripcion: 1,
  hijo: 1,
  hijo_nombre: 'Sofía Torres',
  plan: 1,
  plan_nombre: 'Plan Básico',
  estado: 'ACTIVA',
  fecha_inicio: '2026-03-01',
  fecha_fin: null,
}

const PLAN_MOCK = {
  id_plan_almuerzo: 1,
  nombre: 'Plan Básico',
  tipo: 'MENSUAL',
  precio_mensual: '150000',
  cantidad_almuerzos_mes: 20,
  dias_semana_incluidos: [1, 2, 3, 4, 5],
  activo: true,
}

const HIJO_MOCK = {
  id_hijo: 1,
  nombre: 'Sofía',
  apellido: 'Torres',
  grado: '2° B',
  nombre_completo: 'Sofía Torres',
}

async function loginAndSetupAlmuerzos(page: Page) {
  await loginAs(page, ADMIN)
  // Catch-all ya registrado; datos específicos se agregan después (LIFO)
  await page.route(/\/api\/v1\/almuerzos\/registros-consumo/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ALMUERZOS_LIST) })
  )
  await page.route(/\/api\/v1\/almuerzos\/menu/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [MENU_HOY], count: 1 }) })
  )
  await page.route(/\/api\/v1\/almuerzos\/planes-almuerzo/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [PLAN_MOCK], count: 1 }) })
  )
  await page.route(/\/api\/v1\/clientes\/hijos/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [HIJO_MOCK], count: 1 }) })
  )
}

// ── Cuentas Mensuales ──────────────────────────────────────────────────────

test.describe('Almuerzos — Cuentas Mensuales', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndSetupAlmuerzos(page)
    await page.route(/\/api\/v1\/almuerzos\/cuentas-mensuales/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [CUENTA_MOCK], count: 1 }) })
    )
    await page.goto('/almuerzos')
    await expect(page).toHaveURL('/almuerzos')
  })

  test('tab Cuentas Mensuales muestra la tabla de cuentas', async ({ page }) => {
    await page.getByRole('button', { name: 'Cuentas Mensuales' }).click()
    await expect(page.getByText('Sofía Torres').first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra el estado PENDIENTE de la cuenta', async ({ page }) => {
    await page.getByRole('button', { name: 'Cuentas Mensuales' }).click()
    await expect(page.getByText('PENDIENTE').first()).toBeVisible({ timeout: 6000 })
  })

  test('muestra el botón Generar para crear cuentas del mes', async ({ page }) => {
    await page.getByRole('button', { name: 'Cuentas Mensuales' }).click()
    await expect(page.getByRole('button', { name: /Generar/i })).toBeVisible({ timeout: 5000 })
  })

  test('botón Generar llama al endpoint correcto', async ({ page }) => {
    let generarCalled = false
    await page.route(/\/api\/v1\/almuerzos\/cuentas-mensuales\/generar/, (route) => {
      generarCalled = true
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ cuentas_creadas: 1 }) })
    })
    await page.getByRole('button', { name: 'Cuentas Mensuales' }).click()

    // handleGenerarCuentas valida que filtroCuentaMes y filtroCuentaAnio estén definidos
    // antes de llamar al endpoint — hay que seleccionarlos primero
    const selectMes = page.locator('select').first()
    await selectMes.selectOption({ index: 1 })        // Enero (cualquier mes ≠ '')
    const inputAnio = page.getByPlaceholder('Año')
    await inputAnio.fill('2026')

    await page.getByRole('button', { name: /Generar/i }).click()
    await expect(async () => {
      expect(generarCalled).toBe(true)
    }).toPass({ timeout: 5000 })
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('tarjeta de resumen muestra Cuentas Pendientes', async ({ page }) => {
    await expect(page.getByText('Cuentas Pendientes')).toBeVisible({ timeout: 5000 })
  })
})

// ── Suscripciones ──────────────────────────────────────────────────────────

test.describe('Almuerzos — Suscripciones', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndSetupAlmuerzos(page)
    await page.route(/\/api\/v1\/almuerzos\/suscripciones/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [SUSCRIPCION_MOCK], count: 1 }) })
    )
    await page.goto('/almuerzos')
    await expect(page).toHaveURL('/almuerzos')
    // Navegar al tab
    await page.getByRole('button', { name: 'Suscripciones' }).click()
  })

  test('muestra la suscripción activa de Sofía Torres', async ({ page }) => {
    await expect(page.getByText('Sofía Torres').first()).toBeVisible({ timeout: 6000 })
    await expect(page.getByText('Plan Básico').first()).toBeVisible()
  })

  test('muestra el estado ACTIVA de la suscripción', async ({ page }) => {
    await expect(page.getByText('ACTIVA').first()).toBeVisible({ timeout: 6000 })
  })

  test('botón Nueva Suscripción abre modal', async ({ page }) => {
    await page.getByRole('button', { name: 'Nueva Suscripción' }).click()
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Nueva Suscripción').first()).toBeVisible()
  })

  test('modal muestra selectores de Estudiante y Plan', async ({ page }) => {
    await page.getByRole('button', { name: 'Nueva Suscripción' }).click()
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 })
    await expect(page.getByLabel(/Estudiante/i)).toBeVisible()
    await expect(page.getByLabel(/Plan/i)).toBeVisible()
  })

  test('Suscribir sin campos muestra toast de error', async ({ page }) => {
    await page.getByRole('button', { name: 'Nueva Suscripción' }).click()
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 })
    // Click Suscribir sin seleccionar nada
    await page.getByRole('button', { name: 'Suscribir' }).click()
    await expect(page.getByText('Completá todos los campos')).toBeVisible({ timeout: 5000 })
  })

  test('flujo completo: seleccionar hijo y plan crea suscripción', async ({ page }) => {
    let postCalled = false
    await page.route(/\/api\/v1\/almuerzos\/suscripciones/, (route) => {
      if (route.request().method() === 'POST') {
        postCalled = true
        return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(SUSCRIPCION_MOCK) })
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [SUSCRIPCION_MOCK], count: 1 }) })
    })
    await page.getByRole('button', { name: 'Nueva Suscripción' }).click()
    await expect(page.getByRole('dialog')).toBeVisible({ timeout: 5000 })

    // Seleccionar estudiante (primera opción disponible)
    await page.getByLabel(/Estudiante/i).selectOption({ index: 1 })
    // Seleccionar plan
    await page.getByLabel(/Plan/i).selectOption({ index: 1 })

    await page.getByRole('button', { name: 'Suscribir' }).click()
    await expect(async () => {
      expect(postCalled).toBe(true)
    }).toPass({ timeout: 5000 })
    await expect(page.getByText('Suscripción creada')).toBeVisible({ timeout: 5000 })
  })
})
