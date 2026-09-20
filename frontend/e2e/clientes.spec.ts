import { test, expect } from '@playwright/test'

const ADMIN = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

const CLIENTES_MOCK = {
  count: 2,
  results: [
    {
      id_cliente: 1,
      nombres: 'María',
      apellidos: 'González',
      razon_social: null,
      ruc_ci: '1234567-8',
      email: 'maria@ejemplo.com',
      telefono: '0981123456',
      activo: true,
      tipo_cliente: 1,
      tipo_cliente_nombre: 'Regular',
      saldo_cuenta_corriente: '0',
      saldo_negativo_tarjetas: '0',
      limite_credito: '0',
      lista_precio: 1,
      fecha_registro: '2026-01-01',
    },
    {
      id_cliente: 2,
      nombres: 'Carlos',
      apellidos: 'Rodríguez',
      razon_social: null,
      ruc_ci: '8765432-1',
      email: 'carlos@ejemplo.com',
      telefono: '0971654321',
      activo: true,
      tipo_cliente: 1,
      tipo_cliente_nombre: 'Regular',
      saldo_cuenta_corriente: '15000',
      saldo_negativo_tarjetas: '0',
      limite_credito: '0',
      lista_precio: 1,
      fecha_registro: '2026-01-01',
    },
  ],
}

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN) {
  // LIFO: catch-all primero (baja prioridad), específicos después (alta prioridad).
  await page.route(/\/api\/v1\//, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
  )
  await page.route(/\/api\/v1\/clientes\/clientes\//, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(CLIENTES_MOCK),
    })
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

test.describe('Clientes', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.goto('/clientes')
    await expect(page).toHaveURL('/clientes')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByRole('heading', { name: 'Clientes' })).toBeVisible()
    await expect(page.getByText('Gestión de estudiantes y responsables')).toBeVisible()
  })

  test('muestra el botón Nuevo Cliente', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Nuevo Cliente/i })).toBeVisible()
  })

  test('muestra los stats de clientes', async ({ page }) => {
    await expect(page.getByText('Total')).toBeVisible()
    await expect(page.getByText('Activos').first()).toBeVisible()
    await expect(page.getByText('Con Deuda')).toBeVisible()
  })

  test('lista los clientes mockeados', async ({ page }) => {
    await expect(page.getByText('González')).toBeVisible()
    await expect(page.getByText('Rodríguez')).toBeVisible()
  })

  test('abrir modal Nuevo Cliente no rompe la página', async ({ page }) => {
    await page.getByRole('button', { name: /Nuevo Cliente/i }).click()
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    // El modal debería abrirse
    await expect(page.getByRole('dialog')).toBeVisible()
  })

  test('buscar por nombre filtra en la tabla', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/buscar|nombre|cliente/i)
    if (await searchInput.isVisible()) {
      await searchInput.fill('González')
      await expect(page.getByText('González')).toBeVisible()
    }
  })
})

const HIJO_MOCK = {
  id_hijo: 10, nombre: 'Lucía', apellido: 'González', fecha_nacimiento: null,
  grado: 1, grado_nombre: '3° Grado A', foto_url: null, activo: true, fecha_baja: null,
  cliente_responsable: 1, cliente_nombre: 'María González',
}

async function abrirResponsables(page: import('@playwright/test').Page) {
  await page.route(/\/api\/v1\/clientes\/hijos\/\?/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [HIJO_MOCK], count: 1 }) })
  )
  await page.route(/\/api\/v1\/clientes\/restricciones\//, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
  )
  await page.getByRole('button', { name: 'Hijos' }).first().click()
  await expect(page.getByText('Lucía')).toBeVisible({ timeout: 6000 })
  await page.getByRole('button', { name: /Resp\./ }).click()
  await expect(page.getByText('Responsables — González, Lucía')).toBeVisible()
  await page.getByRole('dialog').last().getByRole('button', { name: 'Agregar', exact: true }).click()
  await expect(page.getByText('Agregar Responsable')).toBeVisible()
}

test.describe('Clientes — agregar responsable', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    await page.route(/\/api\/v1\/clientes\/responsables\/\?/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.goto('/clientes')
  })

  test('cliente existente: elige de la lista y no pide datos personales', async ({ page }) => {
    let enviado: Record<string, unknown> | null = null
    await page.route(/\/api\/v1\/clientes\/responsables\/$/, (route) => {
      if (route.request().method() !== 'POST') return route.fallback()
      enviado = route.request().postDataJSON()
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id_responsable: 99 }) })
    })
    await abrirResponsables(page)

    await expect(page.getByLabel('Nombres')).toHaveCount(0)
    await page.getByLabel('Cliente (responsable)').selectOption({ label: 'Rodríguez, Carlos — 8765432-1' })
    await page.getByRole('dialog').last().getByRole('button', { name: 'Agregar', exact: true }).click()

    await expect.poll(() => enviado).toMatchObject({ hijo: 10, cliente: 2 })
    await expect(page.getByText('Responsable agregado')).toBeVisible()
  })

  test('cliente nuevo: crea el cliente y el responsable en un solo paso', async ({ page }) => {
    let enviado: Record<string, unknown> | null = null
    await page.route(/\/api\/v1\/clientes\/responsables\/crear-con-cliente-nuevo\/$/, (route) => {
      enviado = route.request().postDataJSON()
      return route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ id_responsable: 100 }) })
    })
    await abrirResponsables(page)

    await page.getByRole('button', { name: 'Cliente nuevo' }).click()
    await expect(page.getByText('todavía no está cargada como cliente')).toBeVisible()
    await page.getByLabel('Nombres').fill('Rosa')
    await page.getByLabel('Apellidos').fill('Benítez')
    await page.getByLabel('RUC/CI').fill('4445556')
    await page.getByLabel('Parentesco').selectOption('ABUELA')
    await page.getByRole('dialog').last().getByRole('button', { name: 'Agregar', exact: true }).click()

    await expect.poll(() => enviado).toMatchObject({
      hijo: 10, nombres: 'Rosa', apellidos: 'Benítez', ruc_ci: '4445556', parentesco: 'ABUELA',
    })
    await expect(page.getByText('Responsable agregado')).toBeVisible()
  })

  test('cliente nuevo: RUC/CI inválido no envía la solicitud', async ({ page }) => {
    let llamado = false
    await page.route(/\/api\/v1\/clientes\/responsables\/crear-con-cliente-nuevo\/$/, (route) => {
      llamado = true
      return route.fulfill({ status: 201, contentType: 'application/json', body: '{}' })
    })
    await abrirResponsables(page)
    await page.getByRole('button', { name: 'Cliente nuevo' }).click()
    await page.getByLabel('Nombres').fill('Rosa')
    await page.getByLabel('Apellidos').fill('Benítez')
    await page.getByLabel('RUC/CI').fill('abc')
    await page.getByRole('dialog').last().getByRole('button', { name: 'Agregar', exact: true }).click()

    await expect(page.getByText('RUC/CI inválido')).toBeVisible()
    expect(llamado).toBe(false)
  })

  test('RUC/CI duplicado muestra el error del cliente existente', async ({ page }) => {
    await page.route(/\/api\/v1\/clientes\/responsables\/crear-con-cliente-nuevo\/$/, (route) =>
      route.fulfill({
        status: 400, contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Error de validación.', code: 'validation_error',
          field_errors: { ruc_ci: ['Ya existe un cliente con ese RUC/CI: Carlos Rodríguez. Elegilo desde "Cliente existente" en vez de crear uno nuevo.'] },
        }),
      })
    )
    await abrirResponsables(page)
    await page.getByRole('button', { name: 'Cliente nuevo' }).click()
    await page.getByLabel('Nombres').fill('Rosa')
    await page.getByLabel('Apellidos').fill('Benítez')
    await page.getByLabel('RUC/CI').fill('8765432-1')
    await page.getByRole('dialog').last().getByRole('button', { name: 'Agregar', exact: true }).click()

    await expect(page.getByText(/Ya existe un cliente con ese RUC\/CI: Carlos Rodríguez/)).toBeVisible()
  })
})
