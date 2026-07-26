import { test, expect } from '@playwright/test'

const ADMIN  = { id: 1, email: 'admin@cantina.com',  nombre: 'Admin',  apellido: 'Tita', rol: 'ADMIN' }
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

// La página espera { resumen: AuditoriaResumen, detalle: AuditoriaEntry[] }
const AUDITORIA_MOCK = {
  resumen: {
    total: 3,
    por_resultado: [
      { resultado: 'EXITO', count: 2 },
      { resultado: 'ERROR', count: 1 },
    ],
    top_operaciones: [
      { operacion: 'CREATE', count: 2 },
      { operacion: 'UPDATE', count: 1 },
    ],
    top_tablas: [
      { tabla_afectada: 'ventas_venta', count: 2 },
      { tabla_afectada: 'usuarios_usuario', count: 1 },
    ],
  },
  detalle: [
    {
      id_auditoria: 1,
      fecha_operacion: '2026-06-15T10:30:00Z',
      usuario__email: 'cajero@cantina.com',
      operacion: 'CREATE',
      tabla_afectada: 'ventas_venta',
      id_registro: 42,
      resultado: 'EXITO',
      ip_address: '192.168.1.100',
      descripcion: 'Venta creada por ₲15,000',
      mensaje_error: null,
    },
    {
      id_auditoria: 2,
      fecha_operacion: '2026-06-15T11:00:00Z',
      usuario__email: 'admin@cantina.com',
      operacion: 'UPDATE',
      tabla_afectada: 'usuarios_usuario',
      id_registro: 3,
      resultado: 'EXITO',
      ip_address: '192.168.1.1',
      descripcion: 'Medio de pago actualizado',
      mensaje_error: null,
    },
    {
      id_auditoria: 3,
      fecha_operacion: '2026-06-15T11:15:00Z',
      usuario__email: 'cajero@cantina.com',
      operacion: 'LOGIN',
      tabla_afectada: 'usuarios_usuario',
      id_registro: 2,
      resultado: 'ERROR',
      ip_address: '192.168.1.100',
      descripcion: null,
      mensaje_error: 'Credenciales inválidas',
    },
  ],
}

// ── Listado ───────────────────────────────────────────────────────────────────

test.describe('Auditoría — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/reporte-auditoria/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(AUDITORIA_MOCK) })
    )
    await page.goto('/auditoria')
    await page.waitForLoadState('networkidle')
  })

  test('carga la página sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByText('Auditoría del sistema')).toBeVisible({ timeout: 5000 })
  })

  test('muestra los registros de auditoría', async ({ page }) => {
    await expect(page.getByText('cajero@cantina.com').first()).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('admin@cantina.com').first()).toBeVisible({ timeout: 5000 })
  })

  test('muestra las operaciones (CREATE, UPDATE)', async ({ page }) => {
    await expect(
      page.getByText('CREATE').first()
    ).toBeVisible({ timeout: 5000 })
  })

  test('tiene filtros de fecha', async ({ page }) => {
    await expect(
      page.locator('input[type="date"]').first()
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
    // PrivateRoute roles={['ADMIN']} redirige a /dashboard cuando el rol no está autorizado
    await expect(page).not.toHaveURL(/\/auditoria$/, { timeout: 5000 })
  })
})

// ── Búsqueda y filtros ────────────────────────────────────────────────────────

test.describe('Auditoría — filtros', () => {
  test('campo de filtro por operación está presente', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/reporte-auditoria/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(AUDITORIA_MOCK) })
    )
    await page.goto('/auditoria')
    await expect(
      page.locator('input[placeholder="Filtrar..."]').first()
    ).toBeVisible({ timeout: 5000 })
  })
})
