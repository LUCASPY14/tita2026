import { test, expect, type Page } from '@playwright/test'

const usuario = { id_usuario: 1, email: 'admin@cantina.com', nombre: 'ADMIN', apellido: 'Test', rol: 'ADMIN' }
const ANIO = new Date().getFullYear()

const GRADOS = [
  { id_grado: 1, nombre: '3° Grado A', nivel: 2, orden: 3, es_ultimo: false, activo: true, siguiente: 2, siguiente_nombre: '4° Grado A' },
  { id_grado: 2, nombre: '4° Grado A', nivel: 2, orden: 4, es_ultimo: false, activo: true, siguiente: null, siguiente_nombre: null },
  { id_grado: 3, nombre: '9° Grado A', nivel: 3, orden: 9, es_ultimo: false, activo: true, siguiente: null, siguiente_nombre: null },
  { id_grado: 4, nombre: '1° AÑO Contabilidad', nivel: 4, orden: 10, es_ultimo: false, activo: true, siguiente: null, siguiente_nombre: null },
  { id_grado: 5, nombre: '3° AÑO Contabilidad', nivel: 4, orden: 12, es_ultimo: true, activo: true, siguiente: null, siguiente_nombre: null },
]

const linea = (id: number, nombre: string, origen: number, origenNombre: string, extra: Record<string, unknown> = {}) => ({
  id_promocion_alumno: id, hijo: id, hijo_nombre: nombre, hijo_activo: true,
  grado_origen: origen, grado_origen_nombre: origenNombre, origen_es_ultimo: false, origen_siguiente: null,
  decision: 'PROMUEVE', grado_destino: null, grado_destino_nombre: null, motivo: '', problema: '', ...extra,
})

const ANA = linea(1, 'Ana Promo', 1, '3° Grado A', { origen_siguiente: 2, grado_destino: 2, grado_destino_nombre: '4° Grado A' })
const BETO = linea(2, 'Beto Promo', 3, '9° Grado A', { problema: 'Falta el grado de destino.' })
const CARO = linea(3, 'Caro Promo', 5, '3° AÑO Contabilidad', { origen_es_ultimo: true, decision: 'EGRESA' })

const detalle = (lineas: unknown[], requisitos: Record<string, unknown>, extra: Record<string, unknown> = {}) => ({
  id_promocion: 1, anio: ANIO, estado: 'BORRADOR', creada_por_nombre: 'admin@cantina.com', fecha_creacion: `${ANIO}-12-01T10:00:00Z`,
  aplicada_por_nombre: null, fecha_aplicacion: null, total_alumnos: lineas.length, lineas,
  requisitos: {
    errores: [], avisos: [], habilitada_desde: `${ANIO + 1}-01-01`, puede_aplicar: false,
    resumen: { PROMUEVE: 2, REPITE: 0, CAMBIA: 0, EGRESA: 1, NO_CONTINUA: 0 }, ...requisitos,
  },
  ...extra,
})

const CON_ERROR = detalle([ANA, BETO, CARO], { errores: ['1 alumno(s) sin grado de destino: Beto Promo.'] })
const BETO_OK = linea(2, 'Beto Promo', 3, '9° Grado A', { grado_destino: 4, grado_destino_nombre: '1° AÑO Contabilidad' })
const LISTO = detalle([ANA, BETO_OK, CARO], { puede_aplicar: true })

const json = (body: unknown, status = 200) => ({ status, contentType: 'application/json', body: JSON.stringify(body) })

async function entrar(page: Page) {
  await page.route(/\/api\/v1\//, (route) => route.fulfill(json({ results: [], count: 0 })))
  await page.route(/\/api\/v1\/usuarios\/usuarios\/me/, (route) => route.fulfill(json(usuario)))
  await page.route(/\/api\/token/, (route) => route.fulfill(json({ access: 'tok', refresh: 'ref', user: usuario })))
  await page.goto('/login')
  await page.getByPlaceholder('Tu CI o RUC').fill('1234567')
  await page.getByPlaceholder('••••••••').fill('password123')
  await page.getByRole('button', { name: 'Iniciar Sesión' }).click()
  await page.waitForURL('/dashboard')
  await page.route(/\/api\/v1\/clientes\/grados\/(\?|$)/, (route) =>
    route.fulfill(json({ results: GRADOS, count: GRADOS.length })))
}

async function abrirPestana(page: Page) {
  await page.goto('/configuracion')
  await page.getByRole('button', { name: 'Promoción anual' }).click()
}

test.describe('Promoción anual', () => {
  test('sin borrador ofrece prepararlo y muestra lo que falta para aplicarlo', async ({ page }) => {
    await entrar(page)
    let creado = false
    await page.route(/\/api\/v1\/clientes\/promociones\/(\?|$)/, (route) => {
      if (route.request().method() === 'POST') {
        creado = true
        expect(route.request().postDataJSON()).toEqual({ anio: ANIO })
        return route.fulfill(json(CON_ERROR, 201))
      }
      return route.fulfill(json({ results: [], count: 0 }))
    })
    await abrirPestana(page)
    await expect(page.getByText(`No hay un borrador de promoción para ${ANIO}`)).toBeVisible({ timeout: 6000 })
    await page.getByRole('button', { name: `Preparar borrador ${ANIO}` }).click()

    await expect(page.getByText('1 alumno(s) sin grado de destino: Beto Promo.')).toBeVisible()
    expect(creado).toBe(true)
    await expect(page.getByRole('button', { name: 'Aplicar promoción' })).toBeDisabled()
    // El grado con problemas se abre solo; el que está bien queda plegado.
    await expect(page.getByLabel('Grado de destino de Beto Promo')).toBeVisible()
    await expect(page.getByText('Ana Promo')).toHaveCount(0)
  })

  test('el admin elige el bachillerato de un alumno de 9° y aplica la promoción', async ({ page }) => {
    await entrar(page)
    let parche: Record<string, unknown> | null = null
    let aplicado = false
    await page.route(/\/api\/v1\/clientes\/promociones\/1\/$/, (route) => route.fulfill(json(CON_ERROR)))
    await page.route(/\/api\/v1\/clientes\/promociones\/(\?|$)/, (route) =>
      route.fulfill(json({ results: [{ ...CON_ERROR, lineas: undefined }], count: 1 })))
    await page.route(/\/api\/v1\/clientes\/promociones\/1\/lineas\/2\/$/, (route) => {
      parche = route.request().postDataJSON()
      return route.fulfill(json(LISTO))
    })
    await page.route(/\/api\/v1\/clientes\/promociones\/1\/aplicar\/$/, (route) => {
      aplicado = true
      return route.fulfill(json({ ...LISTO, estado: 'APLICADA', resumen: { PROMUEVE: 2, EGRESA: 1 } }))
    })

    await abrirPestana(page)
    await expect(page.getByLabel('Grado de destino de Beto Promo')).toBeVisible({ timeout: 6000 })
    await page.getByLabel('Grado de destino de Beto Promo').selectOption({ label: '1° AÑO Contabilidad' })
    await expect.poll(() => parche).toEqual({ decision: 'PROMUEVE', grado_destino: 4 })

    const aplicar = page.getByRole('button', { name: 'Aplicar promoción' })
    await expect(aplicar).toBeEnabled()
    await aplicar.click()
    await expect(page.getByText('No se puede deshacer.')).toBeVisible()

    // Sin la casilla no se aplica.
    await page.getByRole('dialog').getByRole('button', { name: 'Aplicar promoción' }).click()
    expect(aplicado).toBe(false)

    await page.getByLabel('Revisé el borrador y quiero aplicarlo').check()
    await page.getByRole('dialog').getByRole('button', { name: 'Aplicar promoción' }).click()
    await expect.poll(() => aplicado).toBe(true)
  })

  test('marcar "Cambia de grado" pide el destino antes de guardar', async ({ page }) => {
    await entrar(page)
    const parches: Record<string, unknown>[] = []
    await page.route(/\/api\/v1\/clientes\/promociones\/1\/$/, (route) => route.fulfill(json(detalle([ANA, BETO_OK, CARO], {}))))
    await page.route(/\/api\/v1\/clientes\/promociones\/(\?|$)/, (route) =>
      route.fulfill(json({ results: [{ ...LISTO, lineas: undefined }], count: 1 })))
    await page.route(/\/api\/v1\/clientes\/promociones\/1\/lineas\/2\/$/, (route) => {
      parches.push(route.request().postDataJSON())
      return route.fulfill(json(LISTO))
    })
    await abrirPestana(page)
    await page.getByRole('button', { name: /9° Grado A/ }).click()
    await page.getByLabel('Decisión para Beto Promo').selectOption('CAMBIA')
    await expect(page.getByText('Falta el grado de destino')).toBeVisible()
    expect(parches).toHaveLength(0)

    await page.getByLabel('Grado de destino de Beto Promo').selectOption({ label: '4° Grado A' })
    await expect.poll(() => parches).toEqual([{ decision: 'CAMBIA', grado_destino: 2 }])
  })

  test('una promoción aplicada se muestra de solo lectura', async ({ page }) => {
    await entrar(page)
    const aplicada = detalle([ANA, BETO_OK, CARO], {}, {
      estado: 'APLICADA', aplicada_por_nombre: 'admin@cantina.com', fecha_aplicacion: `${ANIO + 1}-01-02T12:00:00Z`,
    })
    await page.route(/\/api\/v1\/clientes\/promociones\/1\/$/, (route) => route.fulfill(json(aplicada)))
    await page.route(/\/api\/v1\/clientes\/promociones\/(\?|$)/, (route) =>
      route.fulfill(json({ results: [{ ...aplicada, lineas: undefined }], count: 1 })))
    await abrirPestana(page)
    await expect(page.getByText('Aplicada', { exact: true })).toBeVisible({ timeout: 6000 })
    await expect(page.getByRole('button', { name: 'Aplicar promoción' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: /Descartar borrador/ })).toHaveCount(0)
  })
})

test.describe('Grado siguiente en Configuración', () => {
  test('"Sugerir siguientes" completa los grados y avisa los que faltan', async ({ page }) => {
    await entrar(page)
    let pedido: Record<string, unknown> | null = null
    await page.route(/\/api\/v1\/clientes\/grados\/sugerir-siguientes\/$/, (route) => {
      pedido = route.request().postDataJSON()
      return route.fulfill(json({
        asignados: [{ grado: '4° Grado A', siguiente: '5° Grado A' }],
        pendientes: [{ grado: '9° Grado A', motivo: 'Pasa a 1° AÑO' }], ya_configurados: 1, aplicado: true,
      }))
    })
    await page.goto('/configuracion')
    await page.getByRole('button', { name: 'Grados' }).click()
    await expect(page.getByText('4° Grado A').first()).toBeVisible({ timeout: 6000 })
    await expect(page.getByText('Sin definir').first()).toBeVisible()
    await page.getByRole('button', { name: /Sugerir siguientes/ }).click()
    await expect.poll(() => pedido).toEqual({ aplicar: true })
    await expect(page.getByText(/1 grado\(s\) completados/)).toBeVisible()
  })
})
