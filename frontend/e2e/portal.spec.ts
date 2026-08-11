import { test, expect } from '@playwright/test'

// ─── Usuarios ─────────────────────────────────────────────────────────────────

const CLIENTE_WEB = {
  id: 10, email: 'papa@example.com', nombre: 'Carlos', apellido: 'García', rol: 'CLIENTE_WEB',
  debe_cambiar_contrasena: false, tiene_2fa_activo: true,
}
const ADMIN = {
  id: 1, email: 'admin@cantina.com', nombre: 'Admin', apellido: 'Tita', rol: 'ADMIN',
}

// ─── Mocks de datos ───────────────────────────────────────────────────────────

const MI_HIJO_MOCK = {
  cliente: { id: 10, nombre: 'Carlos García', email: 'papa@example.com' },
  mes: { anio: 2026, mes: 6 },
  hijos: [{
    id: 1,
    nombre: 'Lucas García',
    grado: '3° A',
    tarjeta: {
      nro_tarjeta: '12345678',
      saldo_actual: 85000,
      estado: 'ACTIVA',
      en_alerta: false,
    },
    restricciones: [],
    consumos_mes: {
      total: 5,
      cobrados: 3,
      ultimos: [
        { fecha_consumo: '2026-06-10', costo_almuerzo: '15000', ya_cobrado: true },
        { fecha_consumo: '2026-06-11', costo_almuerzo: '15000', ya_cobrado: false },
      ],
    },
    cuenta_mensual: {
      cantidad_almuerzos: 5,
      monto_total: 75000,
      monto_pagado: 45000,
      monto_pendiente: 30000,
      estado: 'PARCIAL',
    },
  }],
}

const HISTORIAL_MOCK = {
  anio: 2026,
  mes: 6,
  hijo: { id: 1, nombre: 'Lucas García' },
  consumos: [
    { id: 1, fecha_consumo: '2026-06-10', costo_almuerzo: '15000', ya_cobrado: true },
    { id: 2, fecha_consumo: '2026-06-11', costo_almuerzo: '15000', ya_cobrado: false },
  ],
  total: 2,
  monto_total: 30000,
  cobrados: 1,
}

const CANTINA_MOCK = {
  count: 1,
  next: false,
  results: [
    {
      id: 1,
      fecha: '2026-06-10T12:30:00Z',
      monto_total: 12500,
      detalles: [
        { producto_nombre: 'Sandwich de milanesa', cantidad: 1, precio_unitario: 12500, subtotal: 12500 },
      ],
    },
  ],
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function setupPortalAuth(page: import('@playwright/test').Page, user = CLIENTE_WEB) {
  // LIFO: catch-all primero, específicos después (mayor prioridad)
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
}

async function loginAsPortal(page: import('@playwright/test').Page) {
  await setupPortalAuth(page)

  // mi-hijo/ necesita responder para que el dashboard no muestre error
  await page.route(/\/api\/v1\/usuarios\/portal\/mi-hijo/, (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MI_HIJO_MOCK) })
  )

  await page.goto('/portal/login')
  await page.getByPlaceholder('Ej: 3331234-2').fill(CLIENTE_WEB.email)
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Ingresar' }).click()
  await page.waitForURL('/portal')
}

// ── Portal Login ──────────────────────────────────────────────────────────────

test.describe('Portal — Login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/portal/login')
  })

  test('muestra el formulario del portal de padres', async ({ page }) => {
    await expect(page.getByText('Portal de Padres')).toBeVisible()
    await expect(page.getByPlaceholder('Ej: 3331234-2')).toBeVisible()
    await expect(page.getByPlaceholder('••••••••')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Ingresar' })).toBeVisible()
  })

  test('muestra el link a olvidé mi contraseña', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Olvidé mi contraseña' })).toBeVisible()
  })

  test('muestra el link a acceso empleados', async ({ page }) => {
    await expect(page.getByRole('link', { name: 'Acceso empleados' })).toBeVisible()
  })

  test('login exitoso redirige a /portal', async ({ page }) => {
    await setupPortalAuth(page)
    await page.route(/\/api\/v1\/usuarios\/portal\/mi-hijo/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MI_HIJO_MOCK) })
    )

    await page.getByPlaceholder('Ej: 3331234-2').fill(CLIENTE_WEB.email)
    await page.getByPlaceholder('••••••••').fill('password123')
    await page.getByRole('button', { name: 'Ingresar' }).click()
    await expect(page).toHaveURL('/portal')
  })

  test('credenciales incorrectas muestra error', async ({ page }) => {
    await page.route(/\/api\/token/, (route) =>
      route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"No active account"}' })
    )
    await page.getByPlaceholder('Ej: 3331234-2').fill('wrong@example.com')
    await page.getByPlaceholder('••••••••').fill('wrongpass')
    await page.getByRole('button', { name: 'Ingresar' }).click()
    await expect(page.getByText('Credenciales incorrectas')).toBeVisible()
  })

  test('el formulario de recuperación de contraseña aparece al hacer click', async ({ page }) => {
    await page.getByRole('button', { name: 'Olvidé mi contraseña' }).click()
    await expect(page.getByText('Recuperar contraseña')).toBeVisible()
    await expect(page.getByPlaceholder('tucorreo@email.com')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Enviar enlace' })).toBeVisible()
  })
})

// ── Portal — 2FA obligatorio ────────────────────────────────────────────────

test.describe('Portal — 2FA obligatorio', () => {
  test('sin 2FA activo, el login redirige a configurar-2fa en vez del dashboard', async ({ page }) => {
    const userSin2FA = { ...CLIENTE_WEB, tiene_2fa_activo: false }
    await setupPortalAuth(page, userSin2FA)
    await page.route(/\/api\/v1\/usuarios\/2fa\/configurar/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ otp_uri: 'otpauth://totp/x', secret: 'JBSWY3DPEHPK3PXP', backup_codes: ['AAA111'] }),
      })
    )

    await page.goto('/portal/login')
    await page.getByPlaceholder('Ej: 3331234-2').fill(userSin2FA.email)
    await page.getByPlaceholder('••••••••').fill('password123')
    await page.getByRole('button', { name: 'Ingresar' }).click()

    await expect(page).toHaveURL('/portal/configurar-2fa')
    await expect(page.getByText('Activá la verificación en dos pasos')).toBeVisible()
  })

  test('completar la activación navega a /portal', async ({ page }) => {
    const userSin2FA = { ...CLIENTE_WEB, tiene_2fa_activo: false }
    await setupPortalAuth(page, userSin2FA)
    await page.route(/\/api\/v1\/usuarios\/portal\/mi-hijo/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MI_HIJO_MOCK) })
    )
    await page.route(/\/api\/v1\/usuarios\/2fa\/configurar/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ otp_uri: 'otpauth://totp/x', secret: 'JBSWY3DPEHPK3PXP', backup_codes: [] }),
      })
    )
    await page.route(/\/api\/v1\/usuarios\/2fa\/activar/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ detail: 'ok' }) })
    )

    await page.goto('/portal/login')
    await page.getByPlaceholder('Ej: 3331234-2').fill(userSin2FA.email)
    await page.getByPlaceholder('••••••••').fill('password123')
    await page.getByRole('button', { name: 'Ingresar' }).click()
    await expect(page).toHaveURL('/portal/configurar-2fa')

    await page.getByLabel(/código de 6 dígitos/i).fill('123456')
    await page.getByRole('button', { name: /activar y continuar/i }).click()
    await expect(page).toHaveURL('/portal')
  })

  test('cuenta con 2FA habilitado pide el código en el login', async ({ page }) => {
    await page.route(/\/api\/v1\//, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.route(/\/api\/token/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ requires_2fa: true, pre_auth_token: 'fake-pre-auth' }),
      })
    )
    await page.route(/\/api\/v1\/usuarios\/2fa\/login/, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ access: 'tok', refresh: 'ref', user: CLIENTE_WEB, session_key: 'sk' }),
      })
    )
    await page.route(/\/api\/v1\/usuarios\/portal\/mi-hijo/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MI_HIJO_MOCK) })
    )

    await page.goto('/portal/login')
    await page.getByPlaceholder('Ej: 3331234-2').fill(CLIENTE_WEB.email)
    await page.getByPlaceholder('••••••••').fill('password123')
    await page.getByRole('button', { name: 'Ingresar' }).click()

    await expect(page.getByText('Verificación en dos pasos')).toBeVisible()
    await page.getByLabel(/código totp/i).fill('123456')
    await page.getByRole('button', { name: 'Verificar' }).click()

    await expect(page).toHaveURL('/portal')
  })
})

// ── Portal Dashboard ──────────────────────────────────────────────────────────

test.describe('Portal — Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsPortal(page)
    await expect(page).toHaveURL('/portal')
  })

  test('carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra el saludo con el nombre del padre', async ({ page }) => {
    await expect(page.getByText(`Hola, ${CLIENTE_WEB.nombre}`)).toBeVisible({ timeout: 5000 })
  })

  test('muestra el nombre y grado del hijo', async ({ page }) => {
    await expect(page.getByText('Lucas García')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('3° A')).toBeVisible()
  })

  test('muestra el saldo de la tarjeta', async ({ page }) => {
    // 85000 → formateado como "Gs. 85.000"
    await expect(page.getByText(/85\.000/)).toBeVisible({ timeout: 5000 })
  })

  test('muestra las pestañas de navegación del hijo', async ({ page }) => {
    await expect(page.getByRole('tab', { name: 'Resumen' })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Historial/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Cantina/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Almuerzo/i })).toBeVisible()
  })

  test('muestra el botón Cargar saldo con tarjeta', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Cargar saldo con tarjeta' })).toBeVisible({ timeout: 5000 })
  })

  test('muestra la cuenta mensual de almuerzos', async ({ page }) => {
    await expect(page.getByText('Almuerzos tomados')).toBeVisible({ timeout: 5000 })
    // Total del mes: monto_total 75000 → "Gs. 75.000"
    await expect(page.getByText('Total del mes')).toBeVisible()
    await expect(page.getByText(/75\.000/)).toBeVisible()
  })

  test('la barra de navegación inferior muestra todas las secciones', async ({ page }) => {
    // "Historial" se consolidó como tab dentro de la ficha del hijo, ya no es un ítem del nav inferior
    await expect(page.getByRole('button', { name: 'Inicio' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Recargar', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Facturas' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Alertas' })).toBeVisible()
  })

  test('click en Recargar navega a /portal/carga-saldo', async ({ page }) => {
    await page.getByRole('button', { name: 'Recargar', exact: true }).click()
    await expect(page).toHaveURL('/portal/carga-saldo')
  })

  test('click en el tab Historial muestra el historial de consumos del hijo', async ({ page }) => {
    await page.route(/\/api\/v1\/usuarios\/portal\/historial-consumos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(HISTORIAL_MOCK) })
    )
    // "Historial" ya no es una página aparte — es un tab dentro de la ficha del hijo (no cambia la URL)
    await page.getByRole('tab', { name: /Historial/ }).click()
    await expect(page).toHaveURL('/portal')
    await expect(page.getByText('Cobrados')).toBeVisible({ timeout: 5000 })
  })
})

// ── Portal Carga de Saldo ─────────────────────────────────────────────────────

test.describe('Portal — Carga de Saldo', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsPortal(page)
    await page.goto('/portal/carga-saldo')
    await expect(page).toHaveURL('/portal/carga-saldo')
  })

  test('carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra la página de carga de saldo con título', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Carga de Saldo' })).toBeVisible({ timeout: 5000 })
  })

  test('muestra el alumno y saldo actual', async ({ page }) => {
    await expect(page.getByText('Lucas García')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/85\.000/)).toBeVisible()
  })

  test('muestra los botones de monto rápido', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'Gs. 50.000', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Gs. 100.000', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Gs. 200.000', exact: true })).toBeVisible()
  })

  test('el botón Ir a pagar está deshabilitado sin monto seleccionado', async ({ page }) => {
    const btn = page.getByRole('button', { name: /Ir a pagar/ })
    await expect(btn).toBeVisible({ timeout: 5000 })
    await expect(btn).toBeDisabled()
  })

  test('seleccionar monto habilita el botón Ir a pagar', async ({ page }) => {
    await page.getByRole('button', { name: 'Gs. 100.000', exact: true }).click()
    const btn = page.getByRole('button', { name: /Ir a pagar/ })
    await expect(btn).toBeEnabled({ timeout: 3000 })
  })

  test('muestra el resumen antes de pagar al seleccionar monto', async ({ page }) => {
    await page.getByRole('button', { name: 'Gs. 100.000', exact: true }).click()
    await expect(page.getByText('Resumen')).toBeVisible()
    await expect(page.getByText('Lucas García').first()).toBeVisible()
    await expect(page.getByText('12345678').first()).toBeVisible()
  })

  test('muestra resultado aprobado cuando Bancard redirige con estado=aprobado', async ({ page }) => {
    await page.goto('/portal/carga-saldo?estado=aprobado&monto=100000')
    await expect(page.getByText('¡Pago aprobado!')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(/100\.000/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Realizar otra carga' })).toBeVisible()
  })

  test('muestra resultado cancelado cuando Bancard redirige con estado=cancelado', async ({ page }) => {
    await page.goto('/portal/carga-saldo?estado=cancelado')
    await expect(page.getByText('Pago cancelado')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('No se realizó ningún cargo.')).toBeVisible()
  })

  test('muestra resultado rechazado cuando Bancard redirige con estado=rechazado', async ({ page }) => {
    await page.goto('/portal/carga-saldo?estado=rechazado')
    await expect(page.getByText('Pago rechazado')).toBeVisible({ timeout: 5000 })
  })

  test('flujo completo — Ir a pagar abre el checkout embebido de Bancard', async ({ page }) => {
    // El beforeEach ya cargó /mi-hijo/ con un hijo (Lucas García, tarjeta 12345678, saldo 85000).
    // Al ser el único hijo se auto-selecciona. El pago ocasional ya no redirige de página
    // completa — inicia un checkout embebido (iframe vía SDK de Bancard, process_id + script_url).
    await page.route(/\/api\/v1\/core\/bancard\/iniciar\//, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ process_id: 'test-process-id', script_url: 'https://bancard.test/checkout.js' }),
      })
    )
    // El componente inyecta <script src={script_url}> y llama a window.Bancard.Checkout.createForm()
    // en el onload — devolvemos un script inocuo para no depender del SDK real de Bancard.
    await page.route('https://bancard.test/checkout.js', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/javascript',
        body: 'window.Bancard = { Checkout: { createForm: () => {} } };',
      })
    )

    await page.getByRole('button', { name: 'Gs. 100.000', exact: true }).click()
    await expect(page.getByRole('button', { name: /Ir a pagar/ })).toBeEnabled({ timeout: 3000 })
    await page.getByRole('button', { name: /Ir a pagar/ }).click()

    await expect(page.getByText('Ingresá los datos de tu tarjeta')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('#bancard-checkout-container')).toBeVisible()
  })
})

// ── Portal Historial (tab dentro de la ficha del hijo en el Dashboard) ────────

test.describe('Portal — Historial', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsPortal(page)

    await page.route(/\/api\/v1\/usuarios\/portal\/historial-consumos/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(HISTORIAL_MOCK) })
    )
    await page.route(/\/api\/v1\/usuarios\/portal\/historial-cantina/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(CANTINA_MOCK) })
    )

    // "Historial" ya no es una ruta propia — se consolidó como tab de la ficha del hijo en /portal
    await expect(page).toHaveURL('/portal')
    await page.getByRole('tab', { name: /Historial/ }).click()
  })

  test('carga sin errores', async ({ page }) => {
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
  })

  test('muestra las tabs y el navegador de meses', async ({ page }) => {
    await expect(page.getByRole('tab', { name: 'Resumen' })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Cantina/ })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Almuerzo/i })).toBeVisible()
    // Navegador de mes con chevrons prev/next
    await expect(page.getByLabel('Mes anterior')).toBeVisible()
    await expect(page.getByLabel('Mes siguiente')).toBeVisible()
  })

  test('muestra las estadísticas del mes', async ({ page }) => {
    await expect(page.getByText('Cobrados')).toBeVisible()
    await expect(page.getByText('Total almuerzos')).toBeVisible()
  })

  test('muestra la lista de consumos con badges', async ({ page }) => {
    // Badge "Cobrado" para consumo cobrado
    await expect(page.getByText('Cobrado').first()).toBeVisible({ timeout: 5000 })
    // Badge "Sin cargo" para consumo no cobrado
    await expect(page.getByText('Sin cargo')).toBeVisible()
  })

  test('tab Cantina muestra las compras en cantina', async ({ page }) => {
    await page.getByRole('tab', { name: /Cantina/ }).click()
    await expect(page.getByText('Sin compras en cantina')).not.toBeVisible()
    await expect(page.getByText('Gs. 12.500')).toBeVisible()
  })
})

// ── Control de acceso ─────────────────────────────────────────────────────────

test.describe('Portal — Control de acceso', () => {
  test('ADMIN no puede acceder a /portal — redirige a /login', async ({ page }) => {
    await setupPortalAuth(page, ADMIN)
    await page.route(/\/api\/v1\//, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
    )
    // Simular que el store ya tiene al ADMIN autenticado
    await page.goto('/portal/login')
    await page.getByPlaceholder('Ej: 3331234-2').fill(ADMIN.email)
    await page.getByPlaceholder('••••••••').fill('password123')
    await page.getByRole('button', { name: 'Ingresar' }).click()
    // El ADMIN no tiene rol CLIENTE_WEB → PrivateRoute redirige a /dashboard
    await expect(page).toHaveURL('/dashboard')
  })

  test('usuario sin autenticar en /portal redirige a /portal/login', async ({ page }) => {
    await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) =>
      route.fulfill({ status: 401, contentType: 'application/json', body: '{}' })
    )
    await page.goto('/portal')
    await expect(page).toHaveURL('/portal/login')
  })

  test('usuario sin autenticar en /portal/carga-saldo redirige a /portal/login', async ({ page }) => {
    await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) =>
      route.fulfill({ status: 401, contentType: 'application/json', body: '{}' })
    )
    await page.goto('/portal/carga-saldo')
    await expect(page).toHaveURL('/portal/login')
  })
})

// ── Portal Notificaciones ─────────────────────────────────────────────────────

const NOTIFICACIONES_MOCK = {
  results: [
    {
      id: 1, titulo: 'Saldo bajo', mensaje: 'El saldo de Lucas es menor a ₲5,000',
      leida: false, fecha: '2026-06-15T09:00:00Z', tipo: 'SALDO_BAJO',
    },
    {
      id: 2, titulo: 'Almuerzo consumido', mensaje: 'Lucas consumió almuerzo hoy',
      leida: true, fecha: '2026-06-14T12:30:00Z', tipo: 'CONSUMO',
    },
  ],
  count: 2, next: null, previous: null,
}

test.describe('Portal — Notificaciones', () => {
  test('muestra la lista de notificaciones', async ({ page }) => {
    await loginAsPortal(page)
    await page.route(/\/api\/v1\/notificaciones\/notificaciones/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(NOTIFICACIONES_MOCK) })
    )
    await page.goto('/portal/notificaciones')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText('Saldo bajo')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('Almuerzo consumido')).toBeVisible({ timeout: 5000 })
  })

  test('sin sesión redirige a /portal/login', async ({ page }) => {
    await page.goto('/portal/notificaciones')
    await expect(page).toHaveURL('/portal/login')
  })
})

// ── Portal Facturas ───────────────────────────────────────────────────────────

const FACTURAS_MOCK = [
  {
    id: 1, nro_factura: '001-001-0000001',
    monto_total: '75000', iva_10: '6818',
    fecha_emision: '2026-06-01T00:00:00Z',
    estado: 'EMITIDA',
  },
]

test.describe('Portal — Facturas', () => {
  test('muestra la lista de facturas del cliente', async ({ page }) => {
    await loginAsPortal(page)
    // El componente llama a /usuarios/portal/mis-facturas/ (no /contabilidad/facturas)
    // y espera un array directo, no una respuesta paginada
    await page.route(/\/api\/v1\/usuarios\/portal\/mis-facturas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(FACTURAS_MOCK) })
    )
    await page.goto('/portal/facturas')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText('001-001-0000001')).toBeVisible({ timeout: 5000 })
  })

  test('sin sesión redirige a /portal/login', async ({ page }) => {
    await page.goto('/portal/facturas')
    await expect(page).toHaveURL('/portal/login')
  })
})

// ── Portal Pagar Almuerzo ─────────────────────────────────────────────────────

test.describe('Portal — Pagar Almuerzo', () => {
  test('carga la página sin errores', async ({ page }) => {
    await loginAsPortal(page)
    await page.route(/\/api\/v1\/almuerzos\/portal\/cuentas/, (route) =>
      route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ results: [], count: 0 }) })
    )
    await page.goto('/portal/pagar-almuerzo')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    await expect(page.getByText(/almuerzo|pago|cuenta/i).first()).toBeVisible({ timeout: 5000 })
  })

  test('sin sesión redirige a /portal/login', async ({ page }) => {
    await page.goto('/portal/pagar-almuerzo')
    await expect(page).toHaveURL('/portal/login')
  })
})

// ── Portal Cambiar Contraseña ─────────────────────────────────────────────────

test.describe('Portal — Cambiar Contraseña', () => {
  test('muestra el formulario de cambio de contraseña', async ({ page }) => {
    await loginAsPortal(page)
    await page.goto('/portal/cambiar-contrasena')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText('Algo salió mal')).not.toBeVisible()
    // El h1 del componente dice exactamente "Cambiar contraseña"
    await expect(page.getByRole('heading', { name: 'Cambiar contraseña' })).toBeVisible({ timeout: 5000 })
  })

  test('sin sesión redirige a /portal/login', async ({ page }) => {
    await page.goto('/portal/cambiar-contrasena')
    await expect(page).toHaveURL('/portal/login')
  })
})
