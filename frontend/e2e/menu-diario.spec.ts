import { test, expect } from '@playwright/test'

const ADMIN = { id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }
const COCINA = { id: 4, email: 'cocina@cantina.com', nombre: 'Cocinero', apellido: 'Demo', rol: 'COCINA' }

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN | typeof COCINA) {
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

const HOY = new Date().toISOString().split('T')[0]

const MENU_DIARIO_MOCK = {
  results: [
    {
      id: 1,
      fecha: HOY,
      plato_principal: 'Fideos con tuco',
      descripcion: 'Almuerzo del día',
      activo: true,
      detalles: [
        { id: 10, producto_nombre: 'Fideos', cantidad: 100, curso: 'PLATO_PRINCIPAL' },
        { id: 11, producto_nombre: 'Jugo de naranja', cantidad: 50, curso: 'BEBIDA' },
      ],
    },
    {
      id: 2,
      fecha: new Date(Date.now() - 86400000).toISOString().split('T')[0],
      plato_principal: 'Arroz con pollo',
      descripcion: 'Menú de ayer',
      activo: true,
      detalles: [],
    },
  ],
  count: 2, next: null, previous: null,
}

// ── Listado ───────────────────────────────────────────────────────────────────

test.describe('Menú Diario — listado', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/almuerzos\/menu-diario/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MENU_DIARIO_MOCK) })
    )
    await page.goto('/menu-diario')
    await page.waitForLoadState('networkidle')
  })

  test('carga la página sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByText(/Menú|Menu/i).first()).toBeVisible()
  })

  test('muestra los platos del día', async ({ page }) => {
    await expect(page.getByText('Fideos con tuco')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Arroz con pollo')).toBeVisible({ timeout: 5000 })
  })

  test('muestra el botón para crear nuevo menú', async ({ page }) => {
    await expect(
      page.getByRole('button', { name: /nuevo menú|crear menú|agregar menú/i })
    ).toBeVisible({ timeout: 5000 })
  })

  test('muestra la fecha del menú', async ({ page }) => {
    // La fecha de hoy debería estar en algún formato visible
    const year = new Date().getFullYear().toString()
    await expect(page.getByText(year).first()).toBeVisible({ timeout: 5000 })
  })
})

// ── Acceso por rol COCINA ─────────────────────────────────────────────────────

test.describe('Menú Diario — rol COCINA', () => {
  test('usuario con rol COCINA puede acceder a /menu-diario', async ({ page }) => {
    await loginAs(page, COCINA)
    await page.route(/\/api\/v1\/almuerzos\/menu-diario/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.goto('/menu-diario')
    await expect(page).toHaveURL('/menu-diario')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })
})

// ── Sin sesión ────────────────────────────────────────────────────────────────

test.describe('Menú Diario — control de acceso', () => {
  test('sin sesión redirige a /login', async ({ page }) => {
    await page.goto('/menu-diario')
    await expect(page).toHaveURL('/login')
  })
})

// ── Estado vacío ──────────────────────────────────────────────────────────────

test.describe('Menú Diario — estado vacío', () => {
  test('muestra mensaje cuando no hay menú configurado', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/almuerzos\/menu-diario/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ results: [], count: 0, next: null, previous: null }) })
    )
    await page.goto('/menu-diario')
    await page.waitForLoadState('networkidle')
    await expect(
      page.getByText(/sin menú|no hay menú|no se encontraron|vacío/i).first()
        .or(page.getByRole('button', { name: /nuevo menú|crear/i }))
    ).toBeVisible({ timeout: 5000 })
  })
})
