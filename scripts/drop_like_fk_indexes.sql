-- drop_like_fk_indexes.sql
-- Elimina los índices varchar_pattern_ops (_like) generados automáticamente por Django
-- sobre columnas FK que apuntan al PK texto de Tarjeta (nro_tarjeta VARCHAR).
--
-- RAÍZ DEL PROBLEMA:
--   Tarjeta usa nro_tarjeta (VARCHAR) como primary_key=True.
--   Django crea automáticamente un índice _like sobre toda columna VARCHAR indexada,
--   incluyendo las FK columns que apuntan a ese PK.
--   Nunca se hace LIKE sobre una columna FK, así que estos índices no sirven.
--
-- NOTA IMPORTANTE:
--   Django recrea estos índices al ejecutar 'migrate' sobre una base vacía.
--   Por eso este script debe ejecutarse DESPUÉS de cada 'migrate' en producción
--   y DESPUÉS de cada restauración desde backup (restore_cantina.ps1 lo llama).
--
-- Ejecutar:
--   psql -U cantina_user -d cantina_tita -f scripts/drop_like_fk_indexes.sql
--
-- Verificar antes de ejecutar (idx_scan debería ser 0 siempre):
--   SELECT indexrelname, idx_scan FROM pg_stat_user_indexes
--   WHERE indexrelname LIKE '%_like' AND idx_scan = 0;

DROP INDEX CONCURRENTLY IF EXISTS almuerzos_registroconsumoalmuerzo_nro_tarjeta_id_23931441_like;
DROP INDEX CONCURRENTLY IF EXISTS core_cargasaldo_tarjeta_id_4e2e79ff_like;
DROP INDEX CONCURRENTLY IF EXISTS core_consumotarjeta_tarjeta_id_131dc41a_like;
DROP INDEX CONCURRENTLY IF EXISTS core_historicalcargasaldo_tarjeta_id_b3df0f29_like;
DROP INDEX CONCURRENTLY IF EXISTS core_movimientotarjeta_tarjeta_id_1ac33c9b_like;
DROP INDEX CONCURRENTLY IF EXISTS ventas_historicalventa_tarjeta_id_da9d42dd_like;
DROP INDEX CONCURRENTLY IF EXISTS ventas_venta_tarjeta_id_006922fc_like;

-- Verificar resultado: deben haber desaparecido los 7 índices
SELECT indexrelname
FROM pg_stat_user_indexes
WHERE indexrelname IN (
    'almuerzos_registroconsumoalmuerzo_nro_tarjeta_id_23931441_like',
    'core_cargasaldo_tarjeta_id_4e2e79ff_like',
    'core_consumotarjeta_tarjeta_id_131dc41a_like',
    'core_historicalcargasaldo_tarjeta_id_b3df0f29_like',
    'core_movimientotarjeta_tarjeta_id_1ac33c9b_like',
    'ventas_historicalventa_tarjeta_id_da9d42dd_like',
    'ventas_venta_tarjeta_id_006922fc_like'
);
-- Resultado esperado: 0 filas (todos eliminados)
