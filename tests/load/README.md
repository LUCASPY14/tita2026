# Tests de carga — Cantina Tita

Validan que el sistema aguante la carga real de la topología de producción:  
**5 cajeros simultáneos** en ModoRecreo comprando con tarjeta RFID.

---

## Requisitos

- [k6](https://k6.io/docs/get-started/installation/) instalado (`choco install k6` en Windows)
- Backend Django corriendo (dev o producción local)
- Base de datos con datos de prueba (ver Paso 1)

Verificar instalación:
```powershell
k6 version
```

---

## Paso 1 — Crear datos de prueba

El comando `seed_k6_fixtures` crea todo lo necesario de forma idempotente:

```powershell
cd backend
python manage.py seed_k6_fixtures
```

Crea:
- 5 cajeros (`cajero1@cantina.test` … `cajero5@cantina.test`, contraseña `Test1234!`)
- 5 tarjetas RFID (`10000001` … `10000005`, saldo Gs 1.000.000 c/u)
- 1 producto `pk=1` con precio Gs 5.000
- 5 cajas y sus CierreCaja abiertos

El comando imprime el `K6_CLIENTE_ID` necesario para el siguiente paso.

---

## Paso 2 — Ejecutar el test de caja (POS recreo)

```powershell
# Desde la raíz del proyecto
k6 run --env BASE_URL=http://localhost:8000 `
       --env K6_CLIENTE_ID=<id_impreso_por_seed> `
       tests/load/k6/caja.js
```

### Escenarios del test

| Escenario | VUs | Duración | Descripción |
|-----------|-----|----------|-------------|
| `carga_sostenida` | 5 | 1 min | Topología real: 5 cajeros simultáneos |
| `pico_recreo` | 0→15→0 | ~40 s | Pico de recreo largo (comienza al minuto 65) |

Duración total: ~2 minutos.

### Thresholds (umbrales para pasar el test)

| Métrica | Umbral | Qué mide |
|---------|--------|---------|
| `http_req_duration` p(95) | < 400 ms | Latencia general |
| `tarjeta_lookup_ms` p(95) | < 300 ms | GET tarjeta por número |
| `tarjeta_lookup_ms` p(99) | < 500 ms | Percentil 99 lookup |
| `venta_post_ms` p(99) | < 800 ms | POST /ventas/ventas/ |
| `error_rate` | < 1% | Errores de infraestructura |
| `http_req_failed` | < 1% | Cualquier error HTTP |

Si todos los thresholds pasan, k6 termina con **exit code 0**.

---

## Paso 3 — Health check (test simple)

```powershell
k6 run --env BASE_URL=http://localhost:8000 tests/load/k6/health.js
```

10 VUs durante 2 minutos golpeando `/api/health/`. Útil para verificar que  
la infraestructura base responde antes de correr el test completo.

---

## Interpretar resultados

Ejemplo de salida exitosa:

```
✓ tarjeta 200
✓ tarjeta tiene results
✓ venta 201

tarjeta_lookup_ms.....: avg=45ms  p(95)=120ms  p(99)=230ms
venta_post_ms.........: avg=180ms p(95)=310ms  p(99)=490ms
ventas_creadas........: 287
error_rate............: 0.00%

✓ http_req_duration.............: p(95)<400 ✓ ...
✓ tarjeta_lookup_ms p(95)<300  ✓ ...
✓ venta_post_ms    p(99)<800  ✓ ...
✓ error_rate               ✓ rate<0.01
```

### Si el test falla

**`venta_post_ms` alto (>800ms p99):**
- Revisar índices en DB: `EXPLAIN ANALYZE` sobre la query de ventas
- Verificar que Redis está corriendo (`.\scripts\start_redis.ps1`)
- Verificar memoria disponible del servidor

**`error_rate` alto (>1%):**
- Ver logs del backend: `docker compose logs --tail=50 backend`
- Si hay errores 429 (Too Many Requests): el throttle está activo — es esperado en  
  tests muy agresivos; ajustar `DEFAULT_THROTTLE_RATES['user']` para el entorno de test  
  o autenticar los VUs con roles que tengan mayor límite

**`tarjeta_lookup_ms` alto:**
- Verificar índice en `tarjetas.nro_tarjeta` (ya existe como PK CharField)
- Si la tabla de tarjetas tiene muchos registros, verificar el `search=` query

---

## Correr contra producción (LAN escolar)

Para validar en el servidor real antes del lanzamiento:

```powershell
# Reemplazar con la IP del servidor
k6 run --env BASE_URL=http://192.168.1.100:8000 `
       --env K6_CLIENTE_ID=<id> `
       tests/load/k6/caja.js
```

Los datos de prueba deben existir en la DB de producción (`seed_k6_fixtures` en el servidor).  
Eliminar los datos de prueba después con:

```sql
-- Ejecutar en psql contra cantina_tita
DELETE FROM tarjetas WHERE nro_tarjeta IN ('10000001','10000002','10000003','10000004','10000005');
DELETE FROM usuarios WHERE email LIKE '%@cantina.test';
```

---

## Topología objetivo (referencia)

```
Recreo real:
  5 PCs cajeros × 1 venta/30s = 10 req/min por PC
  Total: 50 req/min ≈ 0.83 req/s

Pico máximo (recreo doble):
  15 PCs × 1 venta/20s = 45 req/min por PC
  Total: 675 req/min ≈ 11 req/s
```

Los thresholds del test (`p(99) < 800ms`) están calibrados para este tráfico.
