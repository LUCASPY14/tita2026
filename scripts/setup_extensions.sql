-- setup_extensions.sql
-- Instala extensiones de PostgreSQL requeridas para monitoreo y diagnóstico.
-- Ejecutar UNA VEZ por base de datos, como superusuario.
--
-- PREREQUISITO para pg_stat_statements (requiere reinicio de PostgreSQL):
--   Editar postgresql.conf y agregar/descomentar:
--     shared_preload_libraries = 'pg_stat_statements'
--     pg_stat_statements.track = all
--     pg_stat_statements.max = 10000
--   Luego reiniciar el servicio:
--     Windows: Restart-Service postgresql-x64-16
--     Linux:   systemctl restart postgresql
--   Verificar que el reinicio fue exitoso antes de continuar.
--
-- Ejecutar:
--   psql -U postgres -d cantina_tita -f scripts/setup_extensions.sql

-- Recolecta estadísticas de ejecución por query (necesario para db_health_check.sql sección 6)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Funciones de administración adicionales (opcional pero útil)
CREATE EXTENSION IF NOT EXISTS pg_buffercache;

-- Verificar que quedaron instaladas
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('pg_stat_statements', 'pg_buffercache')
ORDER BY extname;
