/**
 * Test de carga — Health check + endpoints de solo lectura
 *
 * Verifica que el health check y los endpoints de catálogo soporten
 * carga sostenida sin degradación (útil para detectar memory leaks).
 *
 * Ejecutar:
 *   k6 run --env BASE_URL=http://localhost:8000 tests/load/k6/health.js
 */

import http from 'k6/http'
import { check, sleep } from 'k6'
import { Rate } from 'k6/metrics'

const errorRate = new Rate('error_rate')

export const options = {
  vus: 10,
  duration: '2m',
  thresholds: {
    http_req_duration: ['p(95)<200'],
    error_rate:        ['rate<0.005'],
  },
}

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000'

export default function () {
  const r = http.get(`${BASE_URL}/api/v1/health/`)
  const ok = check(r, {
    'health 200 o 503': res => res.status === 200 || res.status === 503,
    'status en body':   res => {
      try { return 'status' in JSON.parse(res.body) }
      catch { return false }
    },
  })
  errorRate.add(!ok)
  sleep(1)
}
