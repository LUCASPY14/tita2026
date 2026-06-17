-- setup_db_user.sql
-- Crea el usuario de aplicación (app_cantina) con privilegios mínimos.
-- Ejecutar UNA VEZ como superusuario al aprovisionar una instancia nueva.
--
-- Uso:
--   psql -U postgres -d cantina_tita -f scripts/setup_db_user.sql
--
-- El usuario app_cantina ya existe en la instancia de desarrollo.
-- Este script es para entornos nuevos (producción, staging).

-- 1. Crear usuario sin superusuario ni capacidad de crear DBs/roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_cantina') THEN
        CREATE USER app_cantina
            WITH PASSWORD 'CAMBIAR_ESTA_CLAVE_EN_PRODUCCION'
            NOSUPERUSER NOCREATEDB NOCREATEROLE
            LOGIN;
        RAISE NOTICE 'Usuario app_cantina creado.';
    ELSE
        RAISE NOTICE 'Usuario app_cantina ya existe — sin cambios.';
    END IF;
END;
$$;

-- 2. Acceso a la base de datos
GRANT CONNECT ON DATABASE cantina_tita TO app_cantina;

-- 3. Uso del schema
GRANT USAGE ON SCHEMA public TO app_cantina;

-- 4. DML sobre todas las tablas existentes
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_cantina;

-- 5. Uso de todas las secuencias existentes (para INSERT con SERIAL/IDENTITY)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_cantina;

-- 6. Privilegios automáticos para tablas y secuencias futuras (migraciones Django)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_cantina;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_cantina;

-- 7. Usuario reporting (solo lectura para reportes externos / BI)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'reporting') THEN
        CREATE USER reporting
            WITH PASSWORD 'CAMBIAR_ESTA_CLAVE_EN_PRODUCCION'
            NOSUPERUSER NOCREATEDB NOCREATEROLE
            LOGIN;
        RAISE NOTICE 'Usuario reporting creado.';
    ELSE
        RAISE NOTICE 'Usuario reporting ya existe — sin cambios.';
    END IF;
END;
$$;

GRANT CONNECT ON DATABASE cantina_tita TO reporting;
GRANT USAGE ON SCHEMA public TO reporting;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO reporting;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO reporting;

-- 8. Verificación final
SELECT usename, usesuper, usecreatedb,
       (SELECT COUNT(*) FROM information_schema.role_table_grants
        WHERE grantee = pg_user.usename AND table_schema = 'public') AS tablas_con_acceso
FROM pg_user
WHERE usename IN ('app_cantina', 'reporting')
ORDER BY usename;
