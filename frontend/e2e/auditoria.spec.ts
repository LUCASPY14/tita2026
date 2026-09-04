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

// Auditoría se consolidó como tab dentro de /reportes (TabAuditoria.tsx) — ya no
// es una ruta propia. La forma de la respuesta coincide con AuditoriaData
// (frontend/src/pages/reportes/shared.tsx).
const AUDITORIA_MOCK = {
  resumen: { total_eventos: 3, por_resultado: { EXITO: 2, FALLA: 1 } },
  top_operaciones: [
    { operacion: 'CREATE', n: 2 },
    { operacion: 'UPDATE', n: 1 },
  ],
  top_tablas: [
    { tabla: 'ventas_venta', n: 2 },
    { tabla: 'usuarios_usuario', n: 1 },
  ],
  detalle: [
    {
      fecha: '2026-06-15T10:30:00Z', usuario: 'cajero@cantina.com',
      operacion: 'CREATE', tabla: 'ventas_venta', objeto_id: 42,
      resultado: 'EXITO', ip: '192.168.1.100',
      descripcion: 'Venta creada por ₲15,000', mensaje_error: null,
    },
    {
      fecha: '2026-06-15T11:00:00Z', usuario: 'admin@cantina.com',
      operacion: 'UPDATE', tabla: 'usuarios_usuario', objeto_id: 3,
      resultado: 'EXITO', ip: '192.168.1.1',
      descripcion: 'Medio de pago actualizado', mensaje_error: null,
    },
    {
      fecha: '2026-06-15T11:15:00Z', usuario: 'cajero@cantina.com',
      operacion: 'LOGIN', tabla: 'usuarios_usuario', objeto_id: 2,
      resultado: 'FALLA', ip: '192.168.1.100',
      descripcion: null, mensaje_error: 'Credenciales inválidas',
    },
  ],
}

const OPCIONES_MOCK = {
  operaciones: ['CREATE', 'UPDATE', 'LOGIN'],
  resultados: ['EXITO', 'FALLA'],
}

async function abrirTabAuditoria(page: import('@playwright/test').Page) {
  await page.route(/\/api\/v1\/usuarios\/reporte-auditoria\/opciones/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(OPCIONES_MOCK) })
  )
  await page.route(/\/api\/v1\/usuarios\/reporte-auditoria\/(?!opciones)/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(AUDITORIA_MOCK) })
  )
  await page.goto('/reportes')
  await page.getByRole('button', { name: 'Auditoría' }).click()
}

// ── Listado ───────────────────────────────────────────────────────────────────

test.describe('Auditoría — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await abrirTabAuditoria(page)
    await page.waitForLoadState('networkidle')
  })

  test('carga la página sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByRole('button', { name: 'Buscar' })).toBeVisible({ timeout: 5000 })
  })

  test('muestra los registros de auditoría', async ({ page }) => {
    await page.getByRole('button', { name: 'Buscar' }).click()
    await expect(page.getByText('cajero@cantina.com').first()).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('admin@cantina.com').first()).toBeVisible({ timeout: 5000 })
  })

  test('muestra las operaciones (CREATE, UPDATE)', async ({ page }) => {
    await page.getByRole('button', { name: 'Buscar' }).click()
    // Acotado a la tarjeta "Top operaciones" — 'CREATE'/'UPDATE' también existen
    // como <option> (ocultos) dentro del <select> del filtro de Operación.
    const topOperaciones = page.locator('div.bg-white').filter({ hasText: 'Top operaciones' })
    await expect(topOperaciones.getByText('CREATE')).toBeVisible({ timeout: 5000 })
    await expect(topOperaciones.getByText('UPDATE')).toBeVisible()
  })

  test('tiene filtros de fecha', async ({ page }) => {
    await expect(
      page.locator('input[type="date"]').first()
    ).toBeVisible({ timeout: 5000 })
  })
})

// ── Control de acceso (solo ADMIN/SUPERVISOR/COBRADOR, ver App.tsx roles de /reportes) ──

test.describe('Auditoría — control de acceso', () => {
  test('sin sesión redirige a /login', async ({ page }) => {
    await page.goto('/reportes')
    await expect(page).toHaveURL('/login')
  })

  test('CAJERO no puede acceder a /reportes', async ({ page }) => {
    await loginAs(page, CAJERO)
    await page.goto('/reportes')
    // PrivateRoute roles={['ADMIN','SUPERVISOR','COBRADOR']} redirige a /dashboard
    await expect(page).toHaveURL('/dashboard', { timeout: 5000 })
  })
})

// ── Búsqueda y filtros ────────────────────────────────────────────────────────

test.describe('Auditoría — filtros', () => {
  test('campo de filtro por operación está presente', async ({ page }) => {
    await loginAs(page, ADMIN)
    await abrirTabAuditoria(page)
    // El filtro de operación es un <select> (no un input de texto libre)
    await expect(page.getByText('Operación', { exact: true })).toBeVisible({ timeout: 5000 })
    await expect(page.locator('select').first()).toBeVisible()
  })
})
