import { test, expect } from '@playwright/test'

const ADMIN  = { id_usuario: 1, email: 'admin@cantina.com',  nombre: 'Admin',  apellido: 'Tita', rol: 'ADMIN' }
const CAJERO = { id_usuario: 2, email: 'cajero@cantina.com', nombre: 'Cajero', apellido: 'Test', rol: 'CAJERO' }

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN | typeof CAJERO) {
  await page.route(/\/api\/v1\//, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
  )
  await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(user) })
  )
  await page.route(/\/api\/token/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ access: 'tok', refresh: 'ref', user }) })
  )
  await page.goto('/login')
  await page.getByPlaceholder('Tu CI o RUC').fill('1234567')
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await page.waitForURL('/dashboard')
}

const TARJETAS_MOCK = {
  results: [
    {
      id: 1, nro_tarjeta: 'T-001234', saldo_actual: '50000', estado: 'ACTIVA',
      hijo_nombre: 'Lucas Pérez', hijo_grado: '3° A',
      cliente_directo_nombre: null, limite_credito: '0',
      notificar_saldo_bajo: false, saldo_alerta: null,
    },
    {
      id: 2, nro_tarjeta: 'T-005678', saldo_actual: '0', estado: 'BLOQUEADA',
      hijo_nombre: 'Ana García', hijo_grado: '2° B',
      cliente_directo_nombre: null, limite_credito: '0',
      notificar_saldo_bajo: false, saldo_alerta: null,
    },
  ],
  count: 2, next: null, previous: null,
}

const MOVIMIENTOS_MOCK = {
  results: [
    {
      id_movimiento_tarjeta: 10, tipo: 'RECARGA', monto: '20000',
      fecha: '2026-06-15T10:00:00Z', descripcion: 'Recarga manual',
      saldo_anterior: '30000', saldo_resultante: '50000',
    },
    {
      id_movimiento_tarjeta: 9, tipo: 'CONSUMO', monto: '5000',
      fecha: '2026-06-14T12:30:00Z', descripcion: 'Venta cantina',
      saldo_anterior: '35000', saldo_resultante: '30000',
    },
  ],
  count: 2, next: null, previous: null,
}

// ── Smoke tests ───────────────────────────────────────────────────────────────

test.describe('Tarjetas — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(TARJETAS_MOCK) })
    )
    await page.goto('/tarjetas')
    await page.waitForLoadState('networkidle')
  })

  test('carga la página sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByText('Tarjetas').first()).toBeVisible({ timeout: 8000 })
  })

  test('muestra tarjetas del listado', async ({ page }) => {
    await expect(page.getByText('T-001234')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('T-005678')).toBeVisible({ timeout: 5000 })
  })

  test('muestra los nombres de los alumnos', async ({ page }) => {
    await expect(page.getByText('Lucas Pérez')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Ana García')).toBeVisible({ timeout: 5000 })
  })

  test('muestra el botón Nueva Tarjeta', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Nueva Tarjeta/i })).toBeVisible({ timeout: 5000 })
  })

  test('muestra el campo de búsqueda', async ({ page }) => {
    await expect(page.getByRole('searchbox').or(page.getByPlaceholder(/buscar|tarjeta/i))).toBeVisible({ timeout: 5000 })
  })
})

test.describe('Tarjetas — control de acceso', () => {
  test('CAJERO puede acceder a /tarjetas', async ({ page }) => {
    await loginAs(page, CAJERO)
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.goto('/tarjetas')
    await expect(page).toHaveURL('/tarjetas')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('sin sesión redirige a /login', async ({ page }) => {
    await page.goto('/tarjetas')
    await expect(page).toHaveURL('/login')
  })
})

test.describe('Tarjetas — historial de movimientos', () => {
  test('muestra movimientos al ver el detalle', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(TARJETAS_MOCK) })
    )
    await page.route(/\/api\/v1\/core\/movimientos-tarjeta/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOVIMIENTOS_MOCK) })
    )
    await page.goto('/tarjetas')
    // Esperar que la tabla cargue, luego hacer click en "Ver" de la primera tarjeta
    await page.getByText('T-001234').waitFor({ state: 'visible', timeout: 5000 })
    await page.getByRole('button', { name: 'Ver' }).first().click()
    // El modal de historial muestra la pestaña "Movimientos" con los datos de RECARGA
    await expect(page.getByText(/Movimientos|RECARGA|Recarga/i).first()).toBeVisible({ timeout: 5000 })
  })
})

// ── Fase 1: ficha financiera, fecha de vencimiento y deuda ───────────────────

const TARJETA_FICHA = {
  nro_tarjeta: '01024', es_alumno: true, hijo_nombre: 'Lucca Palau', hijo_grado: '1° Grado E',
  cliente_nombre: 'Luis Palau', cliente_ruc: '1234567-2', codigo_barras: '',
  saldo_actual: '77000', saldo_disponible: '77000', limite_credito: '0', estado: 'ACTIVA',
  permite_saldo_negativo: false, sobregiro_sin_tope: false, deuda_maxima: 0,
  fecha_vencimiento: '2026-11-30', saldo_alerta: '10000', notificar_saldo_bajo: true,
  saldo_almuerzo: 470000, cliente_saldo_cc: 0, cliente_permite_cuenta_corriente: false,
}

async function abrirFicha(page: import('@playwright/test').Page, tarjeta: Record<string, unknown>) {
  await loginAs(page, ADMIN)
  await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [tarjeta], count: 1 }) })
  )
  await page.route(/\/api\/v1\/core\/tarjetas\/resumen/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tarjetas_con_deuda: 0, deuda_total: 0 }) })
  )
  await page.route(/\/api\/v1\/core\/movimientos-tarjeta/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOVIMIENTOS_MOCK) })
  )
  await page.goto('/tarjetas')
  await page.getByText('01024').first().waitFor({ state: 'visible', timeout: 6000 })
  await page.getByRole('button', { name: 'Ver' }).first().click()
}

test.describe('Tarjetas — ficha financiera', () => {
  test('muestra las cuatro cuentas por separado', async ({ page }) => {
    await abrirFicha(page, TARJETA_FICHA)
    await expect(page.getByText('Saldo cantina')).toBeVisible({ timeout: 6000 })
    await expect(page.getByText('Puede gastar hoy')).toBeVisible()
    await expect(page.getByText('Saldo almuerzo').last()).toBeVisible()
    await expect(page.getByText('Cuenta corriente familiar')).toBeVisible()
    await expect(page.getByText('Prepago: no puede quedar en negativo')).toBeVisible()
    await expect(page.getByText('Al día')).toBeVisible()
  })

  test('la fecha de vencimiento se muestra sin correrse un día', async ({ page }) => {
    await abrirFicha(page, TARJETA_FICHA)
    await expect(page.getByText('Vence 30/11/2026')).toBeVisible({ timeout: 6000 })
    await expect(page.getByText('29/11/2026')).toHaveCount(0)
  })

  test('sobregiro sin tope se muestra como "Sin tope"', async ({ page }) => {
    await abrirFicha(page, { ...TARJETA_FICHA, permite_saldo_negativo: true, sobregiro_sin_tope: true, deuda_maxima: null })
    await expect(page.getByText('Puede endeudarse sin límite')).toBeVisible({ timeout: 6000 })
  })

  test('sobregiro con tope informa cuánto puede gastar', async ({ page }) => {
    await abrirFicha(page, {
      ...TARJETA_FICHA, permite_saldo_negativo: true, sobregiro_sin_tope: false,
      limite_credito: '50000', deuda_maxima: 50000,
    })
    await expect(page.getByText(/Sobregiro autorizado hasta/)).toBeVisible({ timeout: 6000 })
    await expect(page.getByText(/127\.000/).first()).toBeVisible()
  })
})

test.describe('Tarjetas — deuda de cantina', () => {
  test('el filtro "Solo con deuda" consulta con con_deuda=true', async ({ page }) => {
    await loginAs(page, ADMIN)
    const urls: string[] = []
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) => {
      urls.push(route.request().url())
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(TARJETAS_MOCK) })
    })
    await page.route(/\/api\/v1\/core\/tarjetas\/resumen/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tarjetas_con_deuda: 2, deuda_total: 70000 }) })
    )
    await page.goto('/tarjetas')
    await page.getByText('T-001234').waitFor({ state: 'visible', timeout: 6000 })
    await page.getByLabel('Solo con deuda').check()
    await expect(async () => {
      expect(urls.some(u => u.includes('con_deuda=true'))).toBe(true)
    }).toPass({ timeout: 5000 })
  })

  test('muestra cuántas tarjetas tienen deuda y el total', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/core\/tarjetas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(TARJETAS_MOCK) })
    )
    await page.route(/\/api\/v1\/core\/tarjetas\/resumen/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ tarjetas_con_deuda: 2, deuda_total: 70000 }) })
    )
    await page.goto('/tarjetas')
    await expect(page.getByText(/2 con deuda/)).toBeVisible({ timeout: 6000 })
  })
})
