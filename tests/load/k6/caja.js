/**
 * Test de carga — Concurrencia en caja (ModoRecreo / POS escolar)
 *
 * Escenario: 5 cajeros simultáneos (topología real: 5 PCs Modo Recreo)
 * Cada iteración simula un ciclo completo de venta:
 *   1. Login  →  2. Lookup tarjeta  →  3. POST venta  →  4. Verificar saldo
 *
 * Ejecutar:
 *   k6 run --env BASE_URL=http://localhost:8000 tests/load/k6/caja.js
 *
 * Thresholds objetivo:
 *   - p(95) < 400 ms  para lookups de tarjeta
 *   - p(99) < 800 ms  para POST ventas
 *   - error rate < 1%
 */

import http from 'k6/http'
import { check, group, sleep } from 'k6'
import { Counter, Rate, Trend } from 'k6/metrics'

// ─── Métricas personalizadas ──────────────────────────────────────────────────
const ventasCreadas  = new Counter('ventas_creadas')
const errorRate      = new Rate('error_rate')
const tarjetaLatency = new Trend('tarjeta_lookup_ms', true)
const ventaLatency   = new Trend('venta_post_ms', true)

// ─── Opciones ─────────────────────────────────────────────────────────────────
export const options = {
  scenarios: {
    // Carga constante — 5 VUs durante 1 minuto (topología real)
    carga_sostenida: {
      executor: 'constant-vus',
      vus: 5,
      duration: '1m',
      tags: { scenario: 'carga_sostenida' },
    },
    // Pico breve — 15 VUs durante 20s (recreo largo)
    pico_recreo: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 15 },
        { duration: '20s', target: 15 },
        { duration: '10s', target: 0  },
      ],
      startTime: '65s',
      tags: { scenario: 'pico_recreo' },
    },
  },
  thresholds: {
    http_req_duration:   ['p(95)<400'],
    tarjeta_lookup_ms:   ['p(95)<300', 'p(99)<500'],
    venta_post_ms:       ['p(99)<800'],
    error_rate:          ['rate<0.01'],
    http_req_failed:     ['rate<0.01'],
  },
}

const BASE_URL  = __ENV.BASE_URL || 'http://localhost:8000'
const API       = `${BASE_URL}/api/v1`

// Credenciales de prueba — deben existir en la DB de test
const CAJEROS = [
  { email: 'cajero1@cantina.test', password: 'Test1234!' },
  { email: 'cajero2@cantina.test', password: 'Test1234!' },
  { email: 'cajero3@cantina.test', password: 'Test1234!' },
  { email: 'cajero4@cantina.test', password: 'Test1234!' },
  { email: 'cajero5@cantina.test', password: 'Test1234!' },
]

// Tarjetas de prueba — deben existir en la DB de test con saldo suficiente
// nro_tarjeta es PK CharField; se envía como valor del campo "tarjeta" en el payload de venta
const TARJETAS_TEST = ['10000001', '10000002', '10000003', '10000004', '10000005']

// ID del cliente k6 — impreso por `python manage.py seed_k6_fixtures`
// Override: k6 run --env K6_CLIENTE_ID=<id> ...
const CLIENTE_ID = parseInt(__ENV.K6_CLIENTE_ID || '1')

// ─── Setup: autenticar todos los VUs ─────────────────────────────────────────
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
    }
  }
  return { tokens }
}

// ─── Escenario principal ──────────────────────────────────────────────────────
export default function main(data) {
  // Cada VU actúa como un cajero diferente (round-robin por VU ID)
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

  group('1. Lookup tarjeta', () => {
    const start = Date.now()
    const res = http.get(`${API}/core/tarjetas/?search=${tarjeta}`, { headers })
    tarjetaLatency.add(Date.now() - start)

    const ok = check(res, {
      'tarjeta 200': r => r.status === 200,
      'tarjeta tiene results': r => {
        try { return Array.isArray(JSON.parse(r.body).results) }
        catch { return false }
      },
    })
    errorRate.add(!ok)
  })

  sleep(0.3) // tiempo de lectura del cajero

  group('2. POST venta', () => {
    const payload = JSON.stringify({
      cliente:  CLIENTE_ID,
      // "tarjeta" acepta el nro_tarjeta (PK CharField del modelo Tarjeta)
      tarjeta:  tarjeta,
      // precio_unitario requerido para que monto_total > 0 (validación del service)
      items:    [{ producto: 1, cantidad: 1, precio_unitario: 5000 }],
    })

    const start = Date.now()
    const res = http.post(`${API}/ventas/ventas/`, payload, { headers })
    ventaLatency.add(Date.now() - start)

    const created = res.status === 201
    const ok = check(res, {
      'venta 201': () => created,
    })
    if (created) ventasCreadas.add(1)
    errorRate.add(!ok && res.status !== 400) // 400 = validación negocio (no error infra)
  })

  sleep(0.5 + Math.random() * 0.5)

  group('3. Carga catálogo (cache-hit esperado)', () => {
    const res = http.get(`${API}/productos/productos/?activo=true`, { headers })
    check(res, { 'catálogo 200': r => r.status === 200 })
  })

  sleep(1 + Math.random())
}

// ─── Teardown: resumen ────────────────────────────────────────────────────────
export function teardown(data) {
  console.log(`Ventas creadas durante el test: ${ventasCreadas.name}`)
}
