-- setup_partitions.sql
-- Convierte las tablas históricas de alto crecimiento a tablas particionadas
-- por año (PostgreSQL declarative partitioning, RANGE sobre fecha).
--
-- APLICAR CUANDO: la tabla supere ~200.000 filas (revisar con db_health_check.sql).
-- PREREQUISITO: PostgreSQL 14+ (ya confirmado en el sistema).
--
-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  INSTRUCCIONES DE USO                                                    │
-- │                                                                          │
-- │  1. Hacer backup COMPLETO antes de ejecutar:                             │
-- │       .\backup_cantina.ps1                                               │
-- │                                                                          │
-- │  2. Ejecutar en psql (connectado como superusuario):                     │
-- │       \i C:/tita2026/scripts/setup_partitions.sql                        │
-- │                                                                          │
-- │  3. Verificar que Django sigue funcionando:                              │
-- │       python manage.py check                                             │
-- │       pytest                                                             │
-- │                                                                          │
-- │  4. Crear particiones futuras con el management command:                 │
-- │       python manage.py create_year_partition --year 2027                 │
-- └──────────────────────────────────────────────────────────────────────────┘

-- ============================================================================
-- TABLA: core_movimientotarjeta
-- Crece ~N_transacciones_día * 365 filas/año.
-- Columna de partición: fecha (timestamp with time zone)
-- ============================================================================

BEGIN;

-- 1. Renombrar la tabla original
ALTER TABLE core_movimientotarjeta RENAME TO core_movimientotarjeta_old;

-- 2. Crear nueva tabla particionada (misma estructura)
CREATE TABLE core_movimientotarjeta (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tarjeta_id  varchar(20) NOT NULL
                    REFERENCES core_tarjeta(nro_tarjeta) DEFERRABLE INITIALLY DEFERRED,
    fecha       timestamptz NOT NULL DEFAULT now(),
    tipo        varchar(10) NOT NULL,
    monto       numeric(12, 0) NOT NULL,
    saldo_anterior   numeric(12, 0) NOT NULL,
    saldo_resultante numeric(12, 0) NOT NULL,
    descripcion varchar(255),
    carga_id    bigint REFERENCES core_cargasaldo(id) ON DELETE SET NULL,
    consumo_id  bigint REFERENCES core_consumotarjeta(id) ON DELETE SET NULL,
    creado_por_id bigint NOT NULL REFERENCES usuarios_usuario(id),
    fecha_creacion timestamptz NOT NULL DEFAULT now()
) PARTITION BY RANGE (fecha);

-- 3. Crear índices en la tabla raíz (se heredan a las particiones)
CREATE INDEX idx_mov_tarj_fecha ON core_movimientotarjeta (tarjeta_id, fecha);
CREATE INDEX idx_mov_tarj_tipo  ON core_movimientotarjeta (tarjeta_id, tipo);

-- 4. Crear partición para datos históricos (antes de 2025)
CREATE TABLE core_movimientotarjeta_old_data
    PARTITION OF core_movimientotarjeta
    FOR VALUES FROM (MINVALUE) TO ('2025-01-01 00:00:00+00');

-- 5. Crear partición por año (2025, 2026, ...)
CREATE TABLE core_movimientotarjeta_2025
    PARTITION OF core_movimientotarjeta
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');

CREATE TABLE core_movimientotarjeta_2026
    PARTITION OF core_movimientotarjeta
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE TABLE core_movimientotarjeta_2027
    PARTITION OF core_movimientotarjeta
    FOR VALUES FROM ('2027-01-01 00:00:00+00') TO ('2028-01-01 00:00:00+00');

-- 6. Migrar datos de la tabla original
INSERT INTO core_movimientotarjeta
SELECT * FROM core_movimientotarjeta_old;

-- 7. Verificar que los conteos coincidan
DO $$
DECLARE
    cnt_old bigint;
    cnt_new bigint;
BEGIN
    SELECT COUNT(*) INTO cnt_old FROM core_movimientotarjeta_old;
    SELECT COUNT(*) INTO cnt_new FROM core_movimientotarjeta;
    IF cnt_old <> cnt_new THEN
        RAISE EXCEPTION 'Conteo no coincide: old=% new=%', cnt_old, cnt_new;
    END IF;
    RAISE NOTICE 'OK: % filas migradas correctamente', cnt_new;
END;
$$;

-- 8. Eliminar tabla original (hacer DESPUÉS de verificar)
-- DROP TABLE core_movimientotarjeta_old;

COMMIT;


-- ============================================================================
-- TABLA: usuarios_auditoriaoperacion
-- Crece con cada operación registrada (audit log).
-- Columna de partición: timestamp
-- ============================================================================

BEGIN;

ALTER TABLE usuarios_auditoriaoperacion RENAME TO usuarios_auditoriaoperacion_old;

CREATE TABLE usuarios_auditoriaoperacion (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id  bigint REFERENCES usuarios_usuario(id) ON DELETE SET NULL,
    timestamp   timestamptz NOT NULL DEFAULT now(),
    accion      varchar(100) NOT NULL,
    modelo      varchar(100),
    objeto_id   varchar(50),
    descripcion text,
    ip_address  inet,
    user_agent  text,
    datos_antes jsonb,
    datos_despues jsonb
) PARTITION BY RANGE (timestamp);

CREATE INDEX idx_auditoria_ts   ON usuarios_auditoriaoperacion (timestamp DESC);
CREATE INDEX idx_auditoria_user ON usuarios_auditoriaoperacion (usuario_id, timestamp DESC);

CREATE TABLE usuarios_auditoriaoperacion_old_data
    PARTITION OF usuarios_auditoriaoperacion
    FOR VALUES FROM (MINVALUE) TO ('2025-01-01 00:00:00+00');

CREATE TABLE usuarios_auditoriaoperacion_2025
    PARTITION OF usuarios_auditoriaoperacion
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');

CREATE TABLE usuarios_auditoriaoperacion_2026
    PARTITION OF usuarios_auditoriaoperacion
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

CREATE TABLE usuarios_auditoriaoperacion_2027
    PARTITION OF usuarios_auditoriaoperacion
    FOR VALUES FROM ('2027-01-01 00:00:00+00') TO ('2028-01-01 00:00:00+00');

INSERT INTO usuarios_auditoriaoperacion
SELECT * FROM usuarios_auditoriaoperacion_old;

DO $$
DECLARE
    cnt_old bigint;
    cnt_new bigint;
BEGIN
    SELECT COUNT(*) INTO cnt_old FROM usuarios_auditoriaoperacion_old;
    SELECT COUNT(*) INTO cnt_new FROM usuarios_auditoriaoperacion;
    IF cnt_old <> cnt_new THEN
        RAISE EXCEPTION 'Conteo no coincide: old=% new=%', cnt_old, cnt_new;
    END IF;
    RAISE NOTICE 'OK: % filas migradas correctamente', cnt_new;
END;
$$;

-- DROP TABLE usuarios_auditoriaoperacion_old;

COMMIT;


-- ============================================================================
-- Verificar estado de particionamiento
-- ============================================================================
SELECT
    parent.relname                          AS tabla_raiz,
    child.relname                           AS particion,
    pg_get_expr(child.relpartbound, child.oid) AS rango,
    pg_size_pretty(pg_relation_size(child.oid)) AS tamanio
FROM
    pg_inherits
    JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
    JOIN pg_class child  ON pg_inherits.inhrelid  = child.oid
WHERE
    parent.relname IN ('core_movimientotarjeta', 'usuarios_auditoriaoperacion')
ORDER BY
    parent.relname, child.relname;
