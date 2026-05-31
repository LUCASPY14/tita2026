-- db_health_check.sql
-- Ejecutar semanalmente: psql -U postgres -d cantina_tita_dev -f db_health_check.sql
-- =========================================================================

\echo ''
\echo '=== 1. Dead tuples (tablas que necesitan VACUUM) ==='
SELECT
    schemaname,
    relname AS tabla,
    n_live_tup AS vivas,
    n_dead_tup AS muertas,
    CASE WHEN n_live_tup > 0
        THEN round(n_dead_tup::numeric / n_live_tup * 100, 1)
        ELSE 0 END AS pct_dead,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE n_dead_tup > 100
ORDER BY n_dead_tup DESC;

\echo ''
\echo '=== 2. Conexiones activas e inactivas ==='
SELECT
    state,
    count(*) AS conexiones,
    max(now() - state_change) AS tiempo_max
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state
ORDER BY conexiones DESC;

\echo ''
\echo '=== 3. Transacciones inactivas peligrosas (idle in transaction > 5 min) ==='
SELECT
    pid,
    usename,
    state,
    now() - state_change AS tiempo_inactivo,
    left(query, 80) AS ultima_query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
  AND now() - state_change > interval '5 minutes'
ORDER BY tiempo_inactivo DESC;

\echo ''
\echo '=== 4. Indices nunca usados (candidatos a eliminar) ==='
SELECT
    indexrelname AS indice,
    relname AS tabla,
    idx_scan AS veces_usado,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS tamanio
FROM pg_stat_user_indexes i
JOIN pg_index ix ON i.indexrelid = ix.indexrelid
WHERE idx_scan = 0
  AND NOT ix.indisprimary
  AND NOT ix.indisunique
  AND pg_relation_size(i.indexrelid) > 16384
ORDER BY pg_relation_size(i.indexrelid) DESC
LIMIT 20;

\echo ''
\echo '=== 5. Tablas con mayor crecimiento (top 10 por tamaño total) ==='
SELECT
    relname AS tabla,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) AS total,
    pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) AS datos,
    n_live_tup AS filas
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC
LIMIT 10;

\echo ''
\echo '=== 6. Consultas lentas recientes (requiere pg_stat_statements) ==='
SELECT
    calls,
    round(mean_exec_time::numeric, 0) AS ms_promedio,
    round(total_exec_time::numeric / 1000, 1) AS seg_total,
    left(query, 100) AS query
FROM pg_stat_statements
WHERE mean_exec_time > 500
ORDER BY mean_exec_time DESC
LIMIT 10;
