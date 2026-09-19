# Módulo de Almuerzos

Gestiona el almuerzo escolar: planes y suscripciones, ingreso al comedor con tarjeta, cobro mediante una **cuenta corriente por alumno** (saldo de almuerzo), recargas, menú diario y control de alérgenos.

## Idea central

El almuerzo funciona como una cuenta corriente, no como un prepago estricto ni como una factura mensual:

```
suscripción activa  →  ingreso en el comedor  →  se descuenta el precio del saldo del alumno
                                                  (puede quedar negativo, nunca bloquea)
recarga (caja / portal / cuenta corriente)  →  se suma al saldo
```

- La **única fuente de verdad** del dinero es `SaldoAlmuerzo` (+ su ledger `MovimientoSaldoAlmuerzo`).
- "Pagado" / "Pendiente" no es un estado por mes: refleja si **hoy** el saldo del alumno está al día (`>= 0`) o en negativo.
- El saldo negativo está permitido a propósito. No existe límite de crédito de almuerzo; nada bloquea el ingreso al comedor por deuda.
- Los reportes y el portal se calculan **en vivo** desde consumos, recargas y saldo. No hay tablas mensuales que generar ni triggers que sincronizar.

## Modelos (`models.py`)

| Modelo | Rol |
|--------|-----|
| `PrecioAlmuerzo` | Precio unitario vigente por rango de fechas. Es el precio que se cobra por almuerzo. |
| `TipoAlmuerzo` | Variante del almuerzo (plato/postre/bebida). Su `precio_unitario` es el respaldo si no hay `PrecioAlmuerzo` vigente. |
| `PlanAlmuerzo` | Plan al que se suscribe el alumno. Habilita el ingreso; no define el cobro. |
| `SuscripcionAlmuerzo` | Alumno ↔ plan. Estados: `ACTIVA`, `SUSPENDIDA`, `CANCELADA`. **Obligatoria para comer.** A lo sumo una `ACTIVA` por alumno (`unique_suscripcion_activa_por_hijo`). |
| `RegistroConsumoAlmuerzo` | Un ingreso al comedor. `ya_cobrado=True` en el primero del día, `False` en el segundo (sin costo). Estados: `REGISTRADO`, `RECHAZADO`, `ANULADO`. |
| `SaldoAlmuerzo` | Saldo corriente del alumno (`OneToOne` con `Hijo`). Puede ser negativo. |
| `MovimientoSaldoAlmuerzo` | Ledger de auditoría: `RECARGA`, `CONSUMO`, `AJUSTE` (con `saldo_resultante`). |
| `RecargaSaldoAlmuerzo` | Recarga de saldo. Estados: `PENDIENTE`, `CONFIRMADA`, `RECHAZADA`. Puede tener factura. |
| `MenuDiario` / `DetalleMenuDiario` | Menú publicado por fecha y sus ítems (con producto, curso y cantidad). |
| `Alergeno` / `ProductoAlergeno` | Catálogo de alérgenos y su relación con productos (`contiene` / trazas). |
| `CuentaAlmuerzoMensual` / `PagoCuentaAlmuerzo` | **Solo archivo histórico** del sistema anterior (cobro mensual). No se crean filas nuevas; ver [Legado](#legado). |

## Flujo de negocio

### 1. Registrar el ingreso (`AlmuerzoService.registrar_consumo`)

Reglas, en orden:

1. Se exige la tarjeta y que pertenezca al alumno y esté `ACTIVA`. La tarjeta solo identifica; **no descuenta saldo de cantina**.
2. No se permiten fechas futuras.
3. Debe existir una suscripción `ACTIVA` y vigente en esa fecha (`resolver_suscripcion_activa`). Se resuelve en el servidor; el cliente no la envía. Sin ella: error 400.
4. Límite diario (`validar_limite_registros_diarios`), con el alumno bloqueado por `select_for_update` para evitar carreras:
   - Máximo **2 registros por día**.
   - El segundo requiere al menos **240 s** desde el primero (anti doble escaneo).
   - El primero cobra; el segundo es solo control interno de cocina (`ya_cobrado=False`, costo 0) y **no se muestra a los padres**.
5. Costo del primero: `PrecioAlmuerzo` vigente; si no hay, `TipoAlmuerzo.precio_unitario`; si tampoco, error.
6. Se crea el registro y se descuenta el costo del saldo (`_debitar_saldo_almuerzo`) con su movimiento `CONSUMO`.
7. Al confirmarse la transacción se encola un WhatsApp al responsable ("almorzó hoy").

**Idempotencia (cola offline):** el navegador envía un `client_request_id` (UUID). Si el Service Worker reintenta un POST cuya respuesta se perdió, el servidor reconoce el id y devuelve el registro ya creado en vez de duplicarlo.

**Alérgenos:** las restricciones críticas con `requiere_autorizacion` bloquean el ingreso salvo que se envíe `forzar_restriccion: true` (autorización explícita); el resto son advertencias.

### 2. Anular un registro

`POST /registros-consumo/{id}/anular/` (solo desde `REGISTRADO`): pasa a `ANULADO` y, si estaba cobrado, devuelve el costo al saldo (movimiento `AJUSTE`). `estado` es de solo lectura en el serializer a propósito: esta es la única vía. Eliminar físicamente un registro `ANULADO` es solo para ADMIN.

### 3. Recargar saldo (`AlmuerzoService.recargar_saldo` / `confirmar_recarga`)

| Vía | Quién | Resultado |
|-----|-------|-----------|
| Efectivo / POS débito / POS crédito | Cajero, cobrador, admin | Se acredita al instante (mín. 5.000 Gs., máx. 5.000.000 Gs.). Crea el ingreso en la caja si el usuario tiene una abierta. Opcionalmente emite factura. |
| `CUENTA_CORRIENTE` | Staff | Se acredita al instante y se registra un **débito** en la cuenta corriente del responsable. Exige `permite_cuenta_corriente` y respeta su límite de crédito. |
| Bancard (tarjeta nueva o guardada) | Padre, desde el portal | Se acredita cuando Bancard confirma el pago (`acreditar_pago_almuerzo`). No toca caja. |
| Transferencia u otros | Staff | Queda `PENDIENTE`; se acredita al confirmarla (`POST /recargas-saldo/{id}/confirmar/`, opcionalmente con `nro_factura`). |

Si una recarga en efectivo/POS o una confirmación ocurre **sin caja abierta**, se acredita igual pero la respuesta incluye `advertencia` y la UI la muestra (el ingreso no quedó registrado en caja).

## API

Todas las rutas cuelgan de `/api/v1/almuerzos/`.

| Ruta | Descripción | Permiso |
|------|-------------|---------|
| `precios-almuerzo/` (+ `precio-actual/`) | CRUD de precios vigentes | Admin (lectura para el resto) |
| `tipos-almuerzo/`, `planes-almuerzo/` | Catálogos | Admin (lectura para el resto) |
| `suscripciones/` | Alta, edición, cancelar/suspender (`PATCH estado`). Devuelve 400 legible si el alumno ya tiene una activa. | Staff / portal (lectura propia) |
| `registros-consumo/` (+ `anular/`) | Ingreso al comedor | Alta y anulación: cajero/admin |
| `saldos/` | Saldo por alumno. Filtros: `hijo`, `con_deuda=true`, `search` (alumno o tarjeta), `ordering=saldo_actual` | Staff / portal (solo sus hijos) |
| `saldos/resumen/` | Deuda total, saldo a favor y cantidad de alumnos (sobre todos, no la página) | Staff / portal |
| `saldos/{id}/movimientos/` | Últimos 100 movimientos del saldo | Staff / portal |
| `recargas-saldo/` (+ `confirmar/`) | Alta y confirmación de recargas. Filtros `hijo`, `estado` | Cajero, cobrador, admin |
| `estado-cuenta/?anio=&mes=` | Consumo del mes + recargas del mes + estado actual del saldo, por alumno | Staff |
| `reportes/`, `reporte-consumo-grado/`, `reporte-cobranza/` | Reportes (JSON / CSV / Excel) | Staff |
| `menu/` (+ `hoy/`), `detalle-menu/` | Menú diario | Staff escribe, portal lee |
| `alergenos/`, `productos-alergenos/` | Alérgenos | Admin (lectura para el resto) |
| `cuentas-mensuales/`, `pagos-cuentas/` | **Solo lectura** (archivo histórico) | Staff / portal |

Pagos online del portal (en `core`): `POST /bancard/iniciar-almuerzo/` y `POST /bancard/pagar-almuerzo-con-tarjeta/`.

## Frontend

- **`/almuerzos`** (staff): tabs *Consumos*, *Cuentas Mensuales* (reporte de consumo, en vivo), *Saldos* (panel de cobranza: totales de deuda, listado, recargas pendientes de confirmar y "Cargar saldo"), *Suscripciones* y *Menú*.
- **`/comedor`**: registro de ingresos con tarjeta; muestra el saldo del alumno.
- **`/tarjetas`**: columna "Saldo almuerzo" (rojo si es negativo).
- **`/carga-saldo`**: recargas de cantina o de almuerzo (toggle).
- **Portal de padres**: consumo del mes, historial de recargas, almuerzos consumidos y recarga por Bancard.

## Tareas Celery (`tasks.py`)

| Tarea | Cuándo | Qué hace |
|-------|--------|----------|
| `cerrar_cuentas_mes_anterior` (beat: `resumen-mensual-almuerzos`) | Día 1, 05:00 | **Solo informativa**: calcula en vivo el consumo del mes anterior y envía un WhatsApp de resumen por alumno más un email a los admins. No escribe cuentas. Es crítica (alerta a `ADMINS` si falla). |
| `avisar_deuda_almuerzo` | Viernes 08:00 | Notificación in-app a los padres con saldo de almuerzo negativo. |
| `alertar_saldo_almuerzo_negativo` | Diario 09:45 | Avisa a los admins de alumnos cuya deuda alcanza 100.000 Gs. |

## Validadores (`validators.py`)

- `validar_restricciones_alergenicas(hijo)` → `(advertencias, bloqueantes)`.
- `verificar_alergenos_venta(hijo, productos)` → cruce de alérgenos del producto con las restricciones del alumno.
- `resolver_suscripcion_activa(hijo, fecha)` → la suscripción vigente o `None`.
- `validar_limite_registros_diarios(hijo, fecha)` → `True` si es el primer registro (cobra), `False` si es el segundo; lanza error en el tercero o si es demasiado pronto.

## Tests

```bash
pytest apps/almuerzos/ -q
```

Cubren: servicio de consumo y recargas, concurrencia del límite diario (`test_registro_consumo_concurrencia.py`), idempotencia, suscripción obligatoria y única, saldos/panel de cobranza, `estado-cuenta`, reportes, tareas y admin.

## Legado

Hasta septiembre de 2026 el cobro se hacía por mes: un trigger SQL (`trg_sync_cuenta_almuerzo`) mantenía `CuentaAlmuerzoMensual`, una tarea Celery generaba las cuentas y `RegistroConsumoAlmuerzo.marcado_en_cuenta` marcaba los consumos procesados. Todo eso se eliminó (migración `0026`): dos sistemas cobraban el mismo almuerzo en paralelo y se contradecían. `CuentaAlmuerzoMensual` y `PagoCuentaAlmuerzo` se conservan únicamente como historial consultable (los pagos históricos ya están facturados), y la facturación de pagos históricos sigue disponible en Contabilidad.
