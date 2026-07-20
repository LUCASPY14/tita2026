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

const USUARIOS_MOCK = {
  results: [
    {
      id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita',
      rol: 'ADMIN', activo: true, ultimo_login: '2026-06-15T08:00:00Z',
    },
    {
      id: 2, email: 'cajero@cantina.com', nombre: 'Cajero', apellido: 'Test',
      rol: 'CAJERO', activo: true, ultimo_login: '2026-06-15T09:00:00Z',
    },
    {
      id: 3, email: 'cobrador@cantina.com', nombre: 'Cobrador', apellido: 'Demo',
      rol: 'COBRADOR', activo: false, ultimo_login: null,
    },
  ],
  count: 3, next: null, previous: null,
}

// ── Listado ───────────────────────────────────────────────────────────────────

test.describe('Usuarios — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/usuarios/, (route) =>
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
    await expect(page.getByText(/ADMIN|Admin/i).first()).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/CAJERO|Cajero/i).first()).toBeVisible({ timeout: 5000 })
  })

  test('muestra botón Nuevo Usuario', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: /nuevo usuario|crear usuario/i })
    ).toBeVisible({ timeout: 5000 })
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
    // Según permisos: redirige o muestra 403/acceso denegado
    const url = page.url()
    const forbidden = await page.getByText(/acceso denegado|no autorizado|403|forbidden/i).isVisible()
    const redirected = !url.includes('/usuarios')
    expect(redirected || forbidden).toBe(true)
  })
})

// ── Formulario de creación ────────────────────────────────────────────────────

test.describe('Usuarios — crear', () => {
  test('abre el modal/formulario al hacer click en Nuevo Usuario', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/usuarios/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(USUARIOS_MOCK) })
    )
    await page.goto('/usuarios')
    const btn = page.getByRole('button', { name: /nuevo usuario|crear usuario/i })
    await btn.waitFor({ state: 'visible', timeout: 5000 })
    await btn.click()
    await expect(
      page.getByRole('dialog').or(page.getByRole('form')).or(page.getByText(/email|correo/i))
    ).toBeVisible({ timeout: 5000 })
  })
})

// ── Búsqueda y filtro ─────────────────────────────────────────────────────────

test.describe('Usuarios — filtros', () => {
  test('campo de búsqueda está presente', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/usuarios\/usuarios/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(USUARIOS_MOCK) })
    )
    await page.goto('/usuarios')
    await expect(
      page.getByRole('searchbox').or(page.getByPlaceholder(/buscar|usuario|email/i))
    ).toBeVisible({ timeout: 5000 })
  })
})
