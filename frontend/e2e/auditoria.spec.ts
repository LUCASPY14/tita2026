import { test, expect } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }
const CAJERO = { id: 2, email: 'cajero@cantina.com', nombre: 'Cajero', apellido: 'Test', rol: 'CAJERO' }

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
  await page.getByPlaceholder('tu@email.com').fill(user.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await page.waitForURL('/dashboard')
}

const AUDIT_LOGS_MOCK = {
  results: [
    {
      id: 1,
      timestamp: '2026-06-15T10:30:00Z',
      usuario_email: 'cajero@cantina.com',
      accion: 'CREATE',
      modelo: 'Venta',
      objeto_id: '42',
      detalle: 'Venta creada por ₲15,000',
      ip_address: '192.168.1.100',
    },
    {
      id: 2,
      timestamp: '2026-06-15T11:00:00Z',
      usuario_email: 'admin@cantina.com',
      accion: 'UPDATE',
      modelo: 'MedioPago',
      objeto_id: '3',
      detalle: 'Medio de pago actualizado',
      ip_address: '192.168.1.1',
    },
    {
      id: 3,
      timestamp: '2026-06-15T11:15:00Z',
      usuario_email: 'cajero@cantina.com',
      accion: 'LOGIN',
      modelo: 'Usuario',
      objeto_id: '2',
      detalle: 'Inicio de sesión exitoso',
      ip_address: '192.168.1.100',
    },
  ],
  count: 3, next: null, previous: null,
}

// ── Listado ───────────────────────────────────────────────────────────────────

test.describe('Auditoría — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/audit-logs/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(AUDIT_LOGS_MOCK) })
    )
    await page.goto('/auditoria')
    await page.waitForLoadState('networkidle')
  })

  test('carga la página sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByText(/Auditoría|Auditoria|Audit/i).first()).toBeVisible()
  })

  test('muestra los registros de auditoría', async ({ page }) => {
    await expect(page.getByText('cajero@cantina.com').first()).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('admin@cantina.com').first()).toBeVisible({ timeout: 5000 })
  })

  test('muestra las acciones (CREATE, UPDATE, LOGIN)', async ({ page }) => {
    await expect(
      page.getByText(/CREATE|Crear/i).first()
        .or(page.getByText(/UPDATE|Actualizar/i).first())
    ).toBeVisible({ timeout: 5000 })
  })

  test('tiene filtros de fecha', async ({ page }) => {
    await expect(
      page.getByRole('textbox', { name: /fecha|desde|hasta/i })
        .or(page.getByLabel(/fecha|desde|hasta/i))
        .first()
    ).toBeVisible({ timeout: 5000 })
  })
})

// ── Control de acceso (solo ADMIN/SUPERVISOR) ─────────────────────────────────

test.describe('Auditoría — control de acceso', () => {
  test('sin sesión redirige a /login', async ({ page }) => {
    await page.goto('/auditoria')
    await expect(page).toHaveURL('/login')
  })

  test('CAJERO no puede acceder a /auditoria', async ({ page }) => {
    await loginAs(page, CAJERO)
    await page.goto('/auditoria')
    const url = page.url()
    const forbidden = await page.getByText(/acceso denegado|no autorizado|403|forbidden/i).isVisible()
    const redirected = !url.includes('/auditoria')
    expect(redirected || forbidden).toBe(true)
  })
})

// ── Búsqueda y filtros ────────────────────────────────────────────────────────

test.describe('Auditoría — filtros', () => {
  test('campo de búsqueda por usuario está presente', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/audit-logs/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(AUDIT_LOGS_MOCK) })
    )
    await page.goto('/auditoria')
    await expect(
      page.getByRole('searchbox')
        .or(page.getByPlaceholder(/buscar|usuario|email/i))
        .or(page.getByLabel(/usuario|acción/i))
    ).toBeVisible({ timeout: 5000 })
  })
})

// ── Exportar ──────────────────────────────────────────────────────────────────

test.describe('Auditoría — exportar', () => {
  test('botón de exportar está disponible', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/audit-logs/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(AUDIT_LOGS_MOCK) })
    )
    await page.goto('/auditoria')
    await page.waitForLoadState('networkidle')
    await expect(
      page.getByRole('button', { name: /exportar|csv|excel/i })
        .or(page.getByTitle(/exportar/i))
        .first()
    ).toBeVisible({ timeout: 5000 })
  })
})
