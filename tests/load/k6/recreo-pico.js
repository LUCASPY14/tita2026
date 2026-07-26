/**
 * Test de carga — Pico del recreo (test manual pre-deploy)
 *
 * Simula el escenario real del recreo escolar:
 *   - 5 cajeros en PCs ModoRecreo operando 20 minutos continuos
 *   - 1 admin y 1 operador de comedor concurrentes
 *   - Pico de 15 VUs durante el "toque de campana" (primeros 5 min)
 *
 * NO corre en CI (dura ~25 minutos). Correr manualmente antes de
 * un deploy a producción:
 *
 *   k6 run --env BASE_URL=http://localhost:8000 tests/load/k6/recreo-pico.js
 *
 * Requiere fixtures:
 *   cd backend && python manage.py seed_k6_fixtures
 *
 * SLOs objetivo (producción):
 *   - Lookup tarjeta   p(95) < 300 ms
 *   - POST venta       p(99) < 800 ms
 *   - Error rate       < 0.5%
 */

import http from 'k6/http'
import { check, group, sleep } from 'k6'
import { Counter, Rate, Trend } from 'k6/metrics'

// ─── Métricas ─────────────────────────────────────────────────────────────────
const ventasCreadas   = new Counter('ventas_creadas')
const errorRate       = new Rate('error_rate')
const tarjetaLatency  = new Trend('tarjeta_lookup_ms', true)
const ventaLatency    = new Trend('venta_post_ms', true)
const catalogoLatency = new Trend('catalogo_ms', true)

// ─── Opciones ─────────────────────────────────────────────────────────────────
export const options = {
  scenarios: {
    // Pico inicial — campana del recreo, todos los cajeros arrancan juntos
    pico_campana: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m',  target: 15 }, // ramp-up rápido (todos abren la caja)
        { duration: '4m',  target: 15 }, // pico sostenido (primeros 5 min del recreo)
        { duration: '2m',  target: 7  }, // decaimiento (cola se reduce)
      ],
      tags: { scenario: 'pico_campana' },
    },
    // Carga sostenida — 5 cajeros los 20 minutos del recreo
    cajeros_recreo: {
      executor: 'constant-vus',
      vus: 5,
      duration: '20m',
      startTime: '0s',
      tags: { scenario: 'cajeros' },
    },
    // Personal de fondo — admin + comedor durante todo el recreo
    personal_fondo: {
      executor: 'constant-vus',
      vus: 2,
      duration: '20m',
      startTime: '0s',
      tags: { scenario: 'admin_comedor' },
    },
  },
  thresholds: {
    // SLOs de producción (más estrictos que en CI)
    tarjeta_lookup_ms:              ['p(95)<300', 'p(99)<500'],
    venta_post_ms:                  ['p(99)<800'],
    catalogo_ms:                    ['p(95)<200'],
    error_rate:                     ['rate<0.005'],
    http_req_failed:                ['rate<0.005'],
    'http_req_duration{scenario:cajeros}': ['p(95)<400'],
  },
}

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000'
const API      = `${BASE_URL}/api/v1`

const CAJEROS = [
  { email: 'cajero1@cantina.test', password: 'Test1234!' },
  { email: 'cajero2@cantina.test', password: 'Test1234!' },
  { email: 'cajero3@cantina.test', password: 'Test1234!' },
  { email: 'cajero4@cantina.test', password: 'Test1234!' },
  { email: 'cajero5@cantina.test', password: 'Test1234!' },
  { email: 'admin@cantina.test',   password: 'Test1234!' },
  { email: 'cocina@cantina.test',  password: 'Test1234!' },
]

const TARJETAS_TEST = ['10000001', '10000002', '10000003', '10000004', '10000005']
const CLIENTE_ID    = parseInt(__ENV.K6_CLIENTE_ID || '1')
const PRODUCTO_ID   = parseInt(__ENV.K6_PRODUCTO_ID || '1')

// ─── Setup: autenticar todos los usuarios ────────────────────────────────────
export function setup() {
  const tokens = {}
  for (const cred of CAJEROS) {
    const res = http.post(
      `${BASE_URL}/api/token/`,
      JSON.stringify(cred),
      { headers: { 'Content-Type': 'application/json' } },
    )
    if (res.status === 200) {
      tokens[cred.email] = JSON.parse(res.body).access
    } else {
      console.warn(`Login fallido para ${cred.email}: ${res.status}`)
    }
  }
  const tokenCount = Object.keys(tokens).length
  console.log(`Setup completo — ${tokenCount}/${CAJEROS.length} usuarios autenticados`)
  if (tokenCount === 0) {
    throw new Error('Sin tokens — correr: python manage.py seed_k6_fixtures')
  }
  return { tokens }
}

// ─── Ciclo principal de un cajero ─────────────────────────────────────────────
export default function main(data) {
  const idx     = (__VU - 1) % CAJEROS.length
  const email   = CAJEROS[idx].email
  const token   = data.tokens[email]
  const tarjeta = TARJETAS_TEST[Math.floor(Math.random() * TARJETAS_TEST.length)]

  if (!token) {
    errorRate.add(1)
    return
  }

  const headers = {
    'Content-Type':  'application/json',
    'Authorization': `Bearer ${token}`,
  }

  // 1. Lookup de tarjeta (el cajero toca la tarjeta en el lector)
  group('lookup_tarjeta', () => {
    const t0  = Date.now()
    const res = http.get(`${API}/core/tarjetas/?search=${tarjeta}`, { headers })
    tarjetaLatency.add(Date.now() - t0)
    const ok = check(res, { 'tarjeta 200': r => r.status === 200 })
    errorRate.add(!ok)
  })

  sleep(0.2 + Math.random() * 0.3) // el cajero lee el saldo en pantalla

  // 2. POST venta
  group('post_venta', () => {
    const payload = JSON.stringify({
      cliente: CLIENTE_ID,
      tarjeta: tarjeta,
      items:   [{ producto: PRODUCTO_ID, cantidad: 1, precio_unitario: 5000 }],
    })
    const t0  = Date.now()
    const res = http.post(`${API}/ventas/ventas/`, payload, { headers })
    ventaLatency.add(Date.now() - t0)
    const created = res.status === 201
    check(res, { 'venta 201': () => created })
    if (created) ventasCreadas.add(1)
    // 400 = validación de negocio (saldo insuficiente) — no es error de infra
    errorRate.add(!created && res.status !== 400)
  })

  sleep(0.3 + Math.random() * 0.4) // tiempo de impresión del ticket

  // 3. Catálogo (cache hit esperado en Redis)
  group('catalogo_cache', () => {
    const t0  = Date.now()
    const res = http.get(`${API}/productos/productos/?activo=true`, { headers })
    catalogoLatency.add(Date.now() - t0)
    check(res, { 'catálogo 200': r => r.status === 200 })
  })

  // Pausa realista entre clientes (1–3 s según velocidad del cajero)
  sleep(1 + Math.random() * 2)
}

// ─── Teardown ─────────────────────────────────────────────────────────────────
export function teardown(data) {
  console.log('─'.repeat(50))
  console.log('RESUMEN DEL TEST RECREO-PICO')
  console.log(`Tokens activos al teardown: ${Object.keys(data.tokens).length}`)
  console.log('Revisar métricas en k6 Cloud o en el output de terminal.')
  console.log('─'.repeat(50))
}
