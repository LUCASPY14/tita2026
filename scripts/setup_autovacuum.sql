-- setup_autovacuum.sql
-- Ajusta autovacuum para tablas de alto volumen transaccional.
-- Por defecto PostgreSQL usa scale_factor=0.2 (20%), lo que retrasa el vacuum
-- hasta que el 20% de la tabla sea dead tuples — inaceptable en tablas grandes.
--
-- Ejecutar:
--   1. Una vez en producción después del primer despliegue.
--   2. Automáticamente tras cada restauración desde backup (restore_cantina.ps1 lo llama).
--   3. Manualmente si se agrega una tabla nueva al listado.
--
-- Verificar efecto:
--   SELECT relname, reloptions FROM pg_class
--   WHERE relname IN ('ventas_venta','core_cargasaldo','core_movimientotarjeta',
--                     'almuerzos_registroconsumoalmuerzo','contabilidad_movimientocaja',
--                     'core_historicalcargasaldo','core_historicaltarjeta',
--                     'ventas_historicalventa','clientes_historicalcliente',
--                     'contabilidad_historicalcierrecaja','contabilidad_historicalfactura');

BEGIN;

-- Ventas: tabla más activa, una fila por transacción de caja
ALTER TABLE ventas_venta SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Cargas de saldo: múltiples estados, actualizaciones frecuentes (PENDIENTE→CONFIRMADA)
ALTER TABLE core_cargasaldo SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Movimientos de tarjeta: append-only en producción, pero con índices que se reescriben
ALTER TABLE core_movimientotarjeta SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Consumos de almuerzo: alta frecuencia en horario de comedor
ALTER TABLE almuerzos_registroconsumoalmuerzo SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Movimientos de caja: cierres diarios generan dead tuples por actualizaciones
ALTER TABLE contabilidad_movimientocaja SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

-- Tablas historical* (simple_history): son append-only por diseño, pero el planificador
-- necesita estadísticas frescas a medida que crecen. analyze_scale_factor bajo es clave.
ALTER TABLE core_historicalcargasaldo SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE core_historicaltarjeta SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE ventas_historicalventa SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE clientes_historicalcliente SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE contabilidad_historicalcierrecaja SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

ALTER TABLE contabilidad_historicalfactura SET (
    autovacuum_vacuum_scale_factor  = 0.05,
    autovacuum_analyze_scale_factor = 0.02
);

COMMIT;

-- Forzar un analyze inmediato para que el planificador tenga estadísticas frescas
ANALYZE ventas_venta;
ANALYZE core_cargasaldo;
ANALYZE core_movimientotarjeta;
ANALYZE almuerzos_registroconsumoalmuerzo;
ANALYZE contabilidad_movimientocaja;
ANALYZE core_historicalcargasaldo;
ANALYZE core_historicaltarjeta;
ANALYZE ventas_historicalventa;
ANALYZE clientes_historicalcliente;
ANALYZE contabilidad_historicalcierrecaja;
ANALYZE contabilidad_historicalfactura;
