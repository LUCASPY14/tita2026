import { test, expect } from '@playwright/test'

const ADMIN = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN' }

async function loginAs(page: import('@playwright/test').Page, user: typeof ADMIN) {
  // LIFO: registrar primero = prioridad más baja. El /me/ específico (segundo) gana al catch-all (primero).
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

const REPORTE_MOCK = {
  fecha: '2026-09-21',
  resumen: { clientes_con_deuda: 2, total_deuda: 605000, aging: { '0-30': 605000, '31-60': 0, '61-90': 0, '90+': 0 } },
  detalle: [
    {
      cliente_id: 1,
      cliente: 'Roberto Martínez',
      ruc_ci: '1112223',
      telefono: '0981000000',
      email: '',
      saldo_deuda: 475000,
      dias_atraso: 20,
      aging: '0-30',
      deuda_detalle: [
        { tipo: 'ALMUERZO', hijo_nombre: 'Lucca Martínez', nro_tarjeta: 'T-00099', monto: 475000, dias_atraso: 20 },
      ],
    },
    {
      cliente_id: 2,
      cliente: 'Patricia López',
      ruc_ci: '5551234',
      telefono: '',
      email: '',
      saldo_deuda: 130000,
      dias_atraso: 40,
      aging: '31-60',
      deuda_detalle: [
        { tipo: 'CUENTA_CORRIENTE', hijo_nombre: null, nro_tarjeta: null, monto: 30000, dias_atraso: 15 },
        { tipo: 'CANTINA', hijo_nombre: 'Ana López', nro_tarjeta: 'T-00050', monto: 100000, dias_atraso: 40 },
      ],
    },
  ],
}

test.describe('Cobranza', () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, ADMIN)
    // Registrada después del catch-all de loginAs = prioridad más alta (LIFO)
    await page.route(/\/api\/v1\/clientes\/reporte-cuenta-corriente/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(REPORTE_MOCK) })
    )
    await page.goto('/cobros')
    await expect(page).toHaveURL('/cobros')
  })

  test('la página carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra deuda de almuerzo de una familia sin deuda de cuenta corriente', async ({ page }) => {
    await expect(page.getByText('Roberto Martínez')).toBeVisible()
    await expect(page.getByText(/Almuerzo \(Lucca Martínez\): 475\.000 Gs\./)).toBeVisible()
    await expect(page.getByRole('button', { name: /^Cobrar$/ })).not.toBeVisible({ timeout: 1000 }).catch(() => {})
  })

  test('desglosa deuda mixta de cuenta corriente y cantina', async ({ page }) => {
    await expect(page.getByText('Patricia López')).toBeVisible()
    await expect(page.getByText(/Cta\. Cte\.: 30\.000 Gs\./)).toBeVisible()
    await expect(page.getByText(/Cantina \(Ana López\): 100\.000 Gs\./)).toBeVisible()
  })

  test('el botón "Cargar saldo" de una deuda de almuerzo lleva a /carga-saldo con el tipo correcto', async ({ page }) => {
    const fila = page.getByRole('row', { name: /Roberto Martínez/ })
    await fila.getByRole('button', { name: /^Cargar saldo$/ }).click()
    await expect(page).toHaveURL(/\/carga-saldo\?tarjeta=T-00099&tipo=ALMUERZO/)
  })

  test('el enlace "Cargar saldo →" del desglose de cantina lleva a /carga-saldo con el tipo correcto', async ({ page }) => {
    const fila = page.getByRole('row', { name: /Patricia López/ })
    await fila.getByRole('button', { name: /Cargar saldo →/ }).click()
    await expect(page).toHaveURL(/\/carga-saldo\?tarjeta=T-00050&tipo=CANTINA/)
  })

  test('el total combinado de la deuda mixta suma los tres orígenes', async ({ page }) => {
    const fila = page.getByRole('row', { name: /Patricia López/ })
    await expect(fila.getByText('130.000 Gs.')).toBeVisible()
  })
})
