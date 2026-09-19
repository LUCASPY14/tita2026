import { test, expect } from '@playwright/test'

const ADMIN = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN) {
  // LIFO: catch-all primero (prioridad baja), rutas específicas después (prioridad alta).
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

test.describe('Configuración', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.goto('/configuracion')
    await expect(page).toHaveURL('/configuracion')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Configuración' })).toBeVisible()
    await expect(page.getByText('Administración de catálogos del sistema')).toBeVisible()
  })

  test('muestra los tabs principales', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Categorías/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /Empresa/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /Impuestos/ })).toBeVisible()
  })

  test('la tab Categorías es la activa por defecto y el botón Nuevo está visible', async ({ page }) => {
    await expect(page.locator('button', { hasText: /Nueva categ/i })).toBeVisible()
  })

  test('navegar a tab Medios Pago carga el contenido', async ({ page }) => {
    await page.getByRole('button', { name: /Medios de Pago/ }).click()
    // El catch-all devuelve results:[] así que la tabla carga vacía, sin errores
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByRole('button', { name: /Medios de Pago/ })).toBeVisible()
  })

  test('navegar a tab Empresa muestra el formulario de datos', async ({ page }) => {
    await page.getByRole('button', { name: /Empresa/ }).click()
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    // El tab Empresa muestra campos de formulario, no tabla
    await expect(page.getByText(/RUC|Razón Social|Nombre de Fantasía/i).first()).toBeVisible()
  })
})

test.describe('Configuración — Año lectivo', () => {
  test('muestra el año en curso con los valores por defecto y permite configurarlo', async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.goto('/configuracion')
    await page.getByRole('button', { name: /Año lectivo/ }).click()
    const anio = new Date().getFullYear()
    await expect(page.getByText(`01/10/${anio}`)).toBeVisible({ timeout: 6000 })
    await expect(page.getByText(`31/12/${anio}`)).toBeVisible()
    await expect(page.getByText('Por defecto')).toBeVisible()
    await expect(page.getByText(/Cursos normales:/)).toBeVisible()
  })

  test('guardar el calendario llama al endpoint con las fechas', async ({ page }) => {
    await loginAs(page, ADMIN)
    let body: Record<string, unknown> | null = null
    await page.route(/\/api\/v1\/clientes\/calendarios-lectivos\/$/, (route) => {
      if (route.request().method() === 'POST') {
        body = route.request().postDataJSON()
        return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id_calendario: 1, ...body }) })
      }
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    })
    await page.goto('/configuracion')
    await page.getByRole('button', { name: /Año lectivo/ }).click()
    await page.getByRole('button', { name: /Configurar$/ }).first().click()
    await page.getByRole('button', { name: 'Guardar' }).click()
    await expect(async () => { expect(body).not.toBeNull() }).toPass({ timeout: 5000 })
    expect(body).toMatchObject({
      fecha_aviso_ultimo_curso: `${new Date().getFullYear()}-10-01`,
      fecha_cierre_lectivo: `${new Date().getFullYear()}-12-31`,
    })
  })
})
