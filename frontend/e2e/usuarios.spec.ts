import { test, expect } from '@playwright/test'

const ADMIN = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }
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

const USUARIOS_MOCK = {
  results: [
    {
      id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita',
      rol: 'ADMIN', activo: true, ultimo_login: '2026-06-15T08:00:00Z',
    },
    {
      id_usuario: 2, email: 'cajero@cantina.com', nombre: 'Cajero', apellido: 'Test',
      rol: 'CAJERO', activo: true, ultimo_login: '2026-06-15T09:00:00Z',
    },
    {
      id_usuario: 3, email: 'cobrador@cantina.com', nombre: 'Cobrador', apellido: 'Demo',
      rol: 'COBRADOR', activo: false, ultimo_login: null,
    },
  ],
  count: 3, next: null, previous: null,
}

// ── Listado ───────────────────────────────────────────────────────────────────

test.describe('Usuarios — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/usuarios\/(?!me)/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(USUARIOS_MOCK) })
    )
    await page.goto('/usuarios')
    await page.waitForLoadState('networkidle')
  })

  test('carga la página sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByText(/Usuarios/i).first()).toBeVisible()
  })

  test('muestra la lista de usuarios', async ({ page }) => {
    await expect(page.getByText('admin@cantina.com')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('cajero@cantina.com')).toBeVisible({ timeout: 5000 })
  })

  test('muestra roles de los usuarios', async ({ page }) => {
    // Scoped to table cells to avoid hidden <option> elements in modals
    await expect(page.getByRole('cell').filter({ hasText: 'Administrador' }).first()).toBeVisible({ timeout: 5000 })
    await expect(page.getByRole('cell').filter({ hasText: 'Cajero' }).first()).toBeVisible({ timeout: 5000 })
  })

  test('no muestra botón Nuevo Usuario — el alta de personal se hace desde Empleados', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: /nuevo usuario|crear usuario/i })
    ).not.toBeVisible()
  })
})

// ── Control de acceso ─────────────────────────────────────────────────────────

test.describe('Usuarios — control de acceso', () => {
  test('sin sesión redirige a /login', async ({ page }) => {
    await page.goto('/usuarios')
    await expect(page).toHaveURL('/login')
  })

  test('CAJERO es redirigido o ve acceso denegado', async ({ page }) => {
    await loginAs(page, CAJERO)
    await page.goto('/usuarios')
    // PrivateRoute roles={['ADMIN']} redirige a /dashboard cuando el rol no está autorizado
    await expect(page).not.toHaveURL(/\/usuarios$/, { timeout: 5000 })
  })
})

// ── Formulario de creación ────────────────────────────────────────────────────

const EMPLEADOS_MOCK = {
  results: [
    {
      id_empleado: 1, nombre: 'Sofía', apellido: 'Bogado', email: null, telefono: null,
      fecha_ingreso: '2026-01-10', fecha_nacimiento: null, direccion: null, ciudad: null,
      ciudad_nombre: null, estado: true, id_rol: 1, rol_nombre: 'Cocina', usuario_id: null,
    },
  ],
  count: 1, next: null, previous: null,
}

test.describe('Usuarios — crear', () => {
  test('Nuevo Empleado abre su formulario', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/empleados\//, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(EMPLEADOS_MOCK) })
    )
    await page.goto('/usuarios')
    await page.getByRole('button', { name: 'Empleados' }).click()
    await page.getByRole('button', { name: 'Nuevo Empleado' }).click()
    await expect(
      page.getByRole('dialog', { name: /nuevo empleado/i })
    ).toBeVisible({ timeout: 5000 })
  })

  test('Otorgar acceso abre el formulario de acceso ligado al empleado', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/empleados\//, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(EMPLEADOS_MOCK) })
    )
    await page.goto('/usuarios')
    await page.getByRole('button', { name: 'Empleados' }).click()
    await expect(page.getByText('Sofía Bogado')).toBeVisible({ timeout: 5000 })
    await page.getByRole('button', { name: 'Otorgar acceso' }).click()
    await expect(
      page.getByRole('dialog', { name: /otorgar acceso/i })
    ).toBeVisible({ timeout: 5000 })
  })
})

// ── Búsqueda y filtro ─────────────────────────────────────────────────────────

test.describe('Usuarios — filtros', () => {
  test('campo de búsqueda está presente', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/usuarios\/(?!me)/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(USUARIOS_MOCK) })
    )
    await page.goto('/usuarios')
    await expect(
      page.getByRole('searchbox').or(page.getByPlaceholder(/buscar|usuario|email/i))
    ).toBeVisible({ timeout: 5000 })
  })
})
