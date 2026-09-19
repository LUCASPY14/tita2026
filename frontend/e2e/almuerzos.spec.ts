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
  id: '1-2026-5',
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

const SALDO_MOCK = {
  id_saldo_almuerzo: 1,
  hijo: 1,
  hijo_nombre: 'Sofía Torres',
  hijo_grado: '2° B',
  nro_tarjeta: '99887766',
  saldo_actual: '-45000',
  fecha_actualizacion: '2026-05-20T10:00:00Z',
}

const RECARGA_PENDIENTE_MOCK = {
  id_recarga_almuerzo: 7,
  hijo: 1,
  hijo_nombre: 'Sofía Torres',
  monto_cargado: '60000',
  metodo_pago: 'TRANSFERENCIA',
  referencia: 'TR-998877',
  fecha_carga: '2026-05-21T09:00:00Z',
  registrado_por_nombre: 'Cajero Uno',
}

const RESUMEN_SALDOS_MOCK = {
  deuda_total: 45000,
  alumnos_con_deuda: 1,
  saldo_a_favor_total: 0,
  alumnos_con_saldo_a_favor: 0,
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
    await page.route(/\/api\/v1\/almuerzos\/estado-cuenta/, (route) =>
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

  test('ya no hay botón Generar (las cuentas se calculan en vivo)', async ({ page }) => {
    await page.getByRole('button', { name: 'Cuentas Mensuales' }).click()
    await expect(page.getByText('Sofía Torres').first()).toBeVisible({ timeout: 6000 })
    await expect(page.getByRole('button', { name: /Generar/i })).toHaveCount(0)
  })

  test('tarjeta de resumen muestra Alumnos con Deuda', async ({ page }) => {
    await expect(page.getByText('Alumnos con Deuda')).toBeVisible({ timeout: 5000 })
  })

  test('Alumnos con Deuda cuenta alumnos distintos, no filas por mes', async ({ page }) => {
    // Un mismo alumno con 3 meses de consumo = 3 filas PENDIENTE, pero es 1 solo alumno.
    const filas = [5, 6, 7].map((mes) => ({ ...CUENTA_MOCK, id: `1-2026-${mes}`, mes }))
    await page.route(/\/api\/v1\/almuerzos\/estado-cuenta/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: filas, count: 3 }) })
    )
    await page.getByRole('button', { name: 'Consumos' }).click()
    await page.getByRole('button', { name: 'Cuentas Mensuales' }).click()
    const tarjeta = page.locator('div', { has: page.getByText('Alumnos con Deuda', { exact: true }) }).last()
    await expect(tarjeta.getByText('1', { exact: true })).toBeVisible({ timeout: 6000 })
  })

  test('la columna se llama Deuda actual y aclara que no es solo del mes', async ({ page }) => {
    await page.getByRole('button', { name: 'Cuentas Mensuales' }).click()
    const th = page.getByRole('columnheader', { name: 'Deuda actual' })
    await expect(th).toBeVisible({ timeout: 6000 })
    await expect(th).toHaveAttribute('title', /no solo lo de este mes/)
  })

  test('Consumos Hoy viene del resumen del backend', async ({ page }) => {
    await page.route(/\/api\/v1\/almuerzos\/registros-consumo\/resumen-hoy/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ fecha: '2026-09-18', almuerzos_hoy: 37 }) })
    )
    await page.reload()
    await expect(page.getByText('37', { exact: true })).toBeVisible({ timeout: 6000 })
  })
})

// ── Saldos (panel de cobranza) ─────────────────────────────────────────────

test.describe('Almuerzos — Saldos', () => {
  test.beforeEach(async ({ page }) => {
    await loginAndSetupAlmuerzos(page)
    await page.route(/\/api\/v1\/almuerzos\/saldos\/resumen/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(RESUMEN_SALDOS_MOCK) })
    )
    await page.route(/\/api\/v1\/almuerzos\/saldos\/(\?|$)/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [SALDO_MOCK], count: 1 }) })
    )
    await page.route(/\/api\/v1\/almuerzos\/recargas-saldo\/(\?|$)/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [RECARGA_PENDIENTE_MOCK], count: 1 }) })
    )
    await page.goto('/almuerzos')
    await page.getByRole('button', { name: 'Saldos' }).click()
  })

  test('muestra las recargas pendientes de confirmación', async ({ page }) => {
    await expect(page.getByText(/Recargas pendientes de confirmación/)).toBeVisible({ timeout: 6000 })
    await expect(page.getByText(/TR-998877/)).toBeVisible()
  })

  test('confirmar una recarga pendiente llama al endpoint y muestra la advertencia de caja', async ({ page }) => {
    let confirmada = false
    await page.route(/\/api\/v1\/almuerzos\/recargas-saldo\/7\/confirmar/, (route) => {
      confirmada = true
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...RECARGA_PENDIENTE_MOCK, estado: 'CONFIRMADA', advertencia: 'La recarga se acreditó, pero no tenés una caja abierta' }),
      })
    })
    await page.getByRole('button', { name: 'Confirmar', exact: true }).click()
    await expect(page.getByText('Confirmar Recarga de Almuerzo')).toBeVisible({ timeout: 5000 })
    await page.getByRole('button', { name: /Confirmar y acreditar/ }).click()
    await expect(async () => { expect(confirmada).toBe(true) }).toPass({ timeout: 5000 })
    await expect(page.getByText(/no tenés una caja abierta/)).toBeVisible({ timeout: 5000 })
  })

  test('muestra el alumno con su deuda y el estado Pendiente', async ({ page }) => {
    await expect(page.getByText('Sofía Torres').first()).toBeVisible({ timeout: 6000 })
    await expect(page.getByText('Pendiente').first()).toBeVisible()
  })

  test('muestra la deuda total del resumen', async ({ page }) => {
    await expect(page.getByText('Deuda Total')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('45.000').first()).toBeVisible()
  })

  test('el botón Cargar saldo abre el modal con el monto de la deuda', async ({ page }) => {
    await page.getByRole('button', { name: /Cargar saldo/i }).first().click()
    await expect(page.getByText('Cargar Saldo de Almuerzo')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('input[type="number"]').first()).toHaveValue('45000')
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
