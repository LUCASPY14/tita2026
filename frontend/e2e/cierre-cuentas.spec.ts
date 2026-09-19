import { test, expect, type Page } from '@playwright/test'

const usuario = (rol: string) => ({ id_usuario: 1, email: `${rol.toLowerCase()}@cantina.com`, nombre: rol, apellido: 'Test', rol })

const BASE_CIERRE = {
  hijo_activo: true, cliente_id: 1, cliente_nombre: 'María Torres', cliente_permite_cuenta_corriente: true,
  anio: new Date().getFullYear(), estado: 'ABIERTO', estado_display: 'Abierto',
  saldo_cantina_inicial: 0, saldo_almuerzo_inicial: 0, resoluciones_pendientes: 0,
  fecha_apertura: '2026-10-01T10:00:00Z', fecha_cierre: null, motivo_cierre: '',
}

const FAVOR = {
  ...BASE_CIERRE, id_cierre_cuenta: 1, hijo: 1, hijo_nombre: 'Ana Favor', hijo_grado: '3° AÑO SOCIALES',
  nro_tarjeta: 'T-001', saldo_cantina_actual: 80000, saldo_almuerzo_actual: 50000,
  saldo_cantina_inicial: 80000, saldo_almuerzo_inicial: 50000, deuda_pendiente: 0, a_favor_pendiente: 130000,
}
const DEUDOR = {
  ...BASE_CIERRE, id_cierre_cuenta: 2, hijo: 2, hijo_nombre: 'Beto Deudor', hijo_grado: '3° AÑO BATAN',
  nro_tarjeta: 'T-002', saldo_cantina_actual: -30000, saldo_almuerzo_actual: -60000,
  saldo_cantina_inicial: -30000, saldo_almuerzo_inicial: -60000, deuda_pendiente: 90000, a_favor_pendiente: 0,
}
const HERMANOS = [{ id_hijo: 9, nombre_completo: 'Carla Hermana', grado: '2° Grado', nro_tarjeta: 'T-009' }]

const RESUMEN = {
  anio: new Date().getFullYear(), alumnos: 2,
  por_estado: { ABIERTO: 2, PARCIAL: 0, RESUELTO: 0, CERRADO_CON_SALDO: 0 },
  saldo_a_devolver: 130000, deuda_a_cobrar: 90000, resoluciones_pendientes: 1,
}

const PENDIENTE = {
  id_resolucion: 5, cierre: 1, hijo: 1, hijo_nombre: 'Ana Favor', tipo: 'DEVOLUCION', tipo_display: 'Devolución',
  estado: 'SOLICITADA', estado_display: 'Pendiente de aprobación', bolsillo_origen: 'CANTINA', bolsillo_destino: '',
  hijo_destino: null, hijo_destino_nombre: null, monto: '30000', metodo_pago: 'TRANSFERENCIA', referencia: 'TR-1',
  motivo: 'Egresó', solicitado_por_nombre: 'Sup Test', fecha_solicitud: '2026-10-05T12:00:00Z',
  decidido_por_nombre: null, fecha_decision: null, motivo_rechazo: '', fecha_ejecucion: null,
}

const json = (body: unknown, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) })

async function entrar(page: Page, rol: string) {
  const user = usuario(rol)
  await page.route(/\/api\/v1\//, (route) => route.fulfill(json({ results: [], count: 0 })))
  await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) => route.fulfill(json(user)))
  await page.route(/\/api\/token/, (route) => route.fulfill(json({ access: 'tok', refresh: 'ref', user })))
  await page.goto('/login')
  await page.getByPlaceholder('Tu CI o RUC').fill('1234567')
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await page.waitForURL('/dashboard')

  await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/resumen/, (route) => route.fulfill(json(RESUMEN)))
  await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/(\?|$)/, (route) =>
    route.fulfill(json({ results: [FAVOR, DEUDOR], count: 2 })))
  await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/1\/$/, (route) =>
    route.fulfill(json({ ...FAVOR, resoluciones: [], hermanos: HERMANOS })))
  await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/2\/$/, (route) =>
    route.fulfill(json({ ...DEUDOR, resoluciones: [], hermanos: [] })))
}

test.describe('Cierre de cuentas — listado', () => {
  test('muestra los egresados con sus saldos y los totales', async ({ page }) => {
    await entrar(page, 'ADMIN')
    await page.goto('/cierre-cuentas')
    await expect(page.getByText('Ana Favor')).toBeVisible({ timeout: 6000 })
    await expect(page.getByText('Beto Deudor')).toBeVisible()
    await expect(page.getByText('A devolver')).toBeVisible()
    await expect(page.getByText('130.000 Gs.').first()).toBeVisible()
    await expect(page.getByText('90.000 Gs.').first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Abrir cierres del año/ })).toBeVisible()
  })

  test('el cajero no ve el botón para abrir cierres', async ({ page }) => {
    await entrar(page, 'CAJERO')
    await page.goto('/cierre-cuentas')
    await expect(page.getByText('Ana Favor')).toBeVisible({ timeout: 6000 })
    await expect(page.getByRole('button', { name: /Abrir cierres del año/ })).toHaveCount(0)
  })
})

test.describe('Cierre de cuentas — resolver', () => {
  test('el ADMIN devuelve un saldo por transferencia: se ejecuta con los datos correctos', async ({ page }) => {
    await entrar(page, 'ADMIN')
    let enviado: Record<string, unknown> | null = null
    await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/1\/resoluciones\/$/, (route) => {
      enviado = route.request().postDataJSON()
      return route.fulfill(json({ resolucion: { ...PENDIENTE, estado: 'EJECUTADA' } }, 201))
    })
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: 'Resolver' }).first().click()
    await expect(page.getByText('Nueva resolución')).toBeVisible({ timeout: 6000 })
    await expect(page.getByLabel('Acción')).toHaveValue('DEVOLUCION')
    await page.getByLabel('Forma de devolución').selectOption('TRANSFERENCIA')
    await page.getByLabel('Referencia *').fill('TR-1')
    await page.getByRole('button', { name: 'Registrar', exact: true }).click()
    await expect(async () => { expect(enviado).not.toBeNull() }).toPass({ timeout: 5000 })
    expect(enviado).toMatchObject({
      tipo: 'DEVOLUCION', bolsillo_origen: 'CANTINA', monto: 80000, metodo_pago: 'TRANSFERENCIA', referencia: 'TR-1',
    })
  })

  test('el SUPERVISOR solo solicita la devolución: queda pendiente de un administrador', async ({ page }) => {
    await entrar(page, 'SUPERVISOR')
    await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/1\/resoluciones\/$/, (route) =>
      route.fulfill(json({ resolucion: PENDIENTE }, 201)))
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: 'Resolver' }).first().click()
    await expect(page.getByText(/queda pendiente: un administrador debe aprobarla/i)).toBeVisible({ timeout: 6000 })
    await expect(page.getByRole('option', { name: /Devolución \(requiere aprobación\)/ })).toBeAttached()
    await page.getByLabel('Forma de devolución').selectOption('TRANSFERENCIA')
    await page.getByLabel('Referencia *').fill('TR-1')
    await page.getByRole('button', { name: 'Solicitar aprobación' }).click()
    await expect(page.getByText(/pendiente de aprobación de un administrador/i)).toBeVisible({ timeout: 5000 })
  })

  test('el CAJERO solo puede cobrar deudas', async ({ page }) => {
    await entrar(page, 'CAJERO')
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: 'Resolver' }).nth(1).click()
    await expect(page.getByLabel('Acción')).toHaveValue('COBRO')
    await expect(page.getByLabel('Acción').locator('option')).toHaveCount(1)
  })

  test('el CAJERO no puede resolver un saldo a favor', async ({ page }) => {
    await entrar(page, 'CAJERO')
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: 'Resolver' }).first().click()
    await expect(page.getByText(/solo permite cobrar deudas/i)).toBeVisible({ timeout: 6000 })
  })

  test('traspaso a hermano ofrece al hermano y envía el destino', async ({ page }) => {
    await entrar(page, 'SUPERVISOR')
    let enviado: Record<string, unknown> | null = null
    await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/1\/resoluciones\/$/, (route) => {
      enviado = route.request().postDataJSON()
      return route.fulfill(json({ resolucion: { ...PENDIENTE, tipo: 'TRASPASO_HERMANO', estado: 'EJECUTADA' } }, 201))
    })
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: 'Resolver' }).first().click()
    await page.getByLabel('Acción').selectOption('TRASPASO_HERMANO')
    await page.getByLabel('Hermano que recibe').selectOption('9')
    await page.getByRole('button', { name: 'Registrar', exact: true }).click()
    await expect(async () => { expect(enviado).not.toBeNull() }).toPass({ timeout: 5000 })
    expect(enviado).toMatchObject({ tipo: 'TRASPASO_HERMANO', hijo_destino: 9, bolsillo_destino: 'CANTINA' })
  })

  test('el historial muestra quién solicitó y quién autorizó, con comprobante', async ({ page }) => {
    await entrar(page, 'ADMIN')
    await page.route(/\/api\/v1\/cierre-cuentas\/cierres\/1\/$/, (route) =>
      route.fulfill(json({
        ...FAVOR,
        resoluciones: [{ ...PENDIENTE, estado: 'EJECUTADA', estado_display: 'Ejecutada', decidido_por_nombre: 'Admin Test' }],
        hermanos: HERMANOS,
      })))
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: 'Resolver' }).first().click()
    await expect(page.getByText('Historial de resoluciones')).toBeVisible({ timeout: 6000 })
    await expect(page.getByText(/Solicitó Sup Test/)).toBeVisible()
    await expect(page.getByText(/Autorizó Admin Test/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Comprobante' })).toBeVisible()
  })
})

test.describe('Cierre de cuentas — aprobaciones', () => {
  test('el ADMIN aprueba una solicitud pendiente', async ({ page }) => {
    await entrar(page, 'ADMIN')
    await page.route(/\/api\/v1\/cierre-cuentas\/resoluciones\/\?/, (route) =>
      route.fulfill(json({ results: [PENDIENTE], count: 1 })))
    let aprobada = false
    await page.route(/\/api\/v1\/cierre-cuentas\/resoluciones\/5\/aprobar\/$/, (route) => {
      aprobada = true
      return route.fulfill(json({ resolucion: { ...PENDIENTE, estado: 'EJECUTADA' } }))
    })
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: /Aprobaciones pendientes/ }).click()
    await expect(page.getByText('Solicitó Sup Test', { exact: false })).toBeVisible({ timeout: 6000 })
    await page.getByRole('button', { name: 'Aprobar' }).click()
    await expect(async () => { expect(aprobada).toBe(true) }).toPass({ timeout: 5000 })
  })

  test('el ADMIN rechaza con motivo', async ({ page }) => {
    await entrar(page, 'ADMIN')
    await page.route(/\/api\/v1\/cierre-cuentas\/resoluciones\/\?/, (route) =>
      route.fulfill(json({ results: [PENDIENTE], count: 1 })))
    let cuerpo: Record<string, unknown> | null = null
    await page.route(/\/api\/v1\/cierre-cuentas\/resoluciones\/5\/rechazar\/$/, (route) => {
      cuerpo = route.request().postDataJSON()
      return route.fulfill(json({ resolucion: { ...PENDIENTE, estado: 'RECHAZADA' } }))
    })
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: /Aprobaciones pendientes/ }).click()
    await page.getByRole('button', { name: 'Rechazar' }).first().click()
    await page.getByLabel('Motivo *').fill('Falta documentación')
    await page.getByRole('button', { name: 'Rechazar' }).last().click()
    await expect(async () => { expect(cuerpo).not.toBeNull() }).toPass({ timeout: 5000 })
    expect(cuerpo).toMatchObject({ motivo: 'Falta documentación' })
  })

  test('el SUPERVISOR ve la solicitud pero no puede aprobarla', async ({ page }) => {
    await entrar(page, 'SUPERVISOR')
    await page.route(/\/api\/v1\/cierre-cuentas\/resoluciones\/\?/, (route) =>
      route.fulfill(json({ results: [PENDIENTE], count: 1 })))
    await page.goto('/cierre-cuentas')
    await page.getByRole('button', { name: /Aprobaciones pendientes/ }).click()
    await expect(page.getByText('Pendiente de un administrador')).toBeVisible({ timeout: 6000 })
    await expect(page.getByRole('button', { name: 'Aprobar' })).toHaveCount(0)
  })
})
