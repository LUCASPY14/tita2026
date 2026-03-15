-- Inicialización de la base de datos Cantina Tita (MySQL 8.0)
-- Este script se ejecuta una sola vez cuando el contenedor se crea por primera vez.

-- Usar la base de datos de la aplicación
USE cantina_tita_db;

-- Configurar charset por defecto (ya heredado del contenedor, pero lo explicitamos)
ALTER DATABASE cantina_tita_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grants para el usuario de la aplicación
GRANT ALL PRIVILEGES ON cantina_tita_db.* TO 'cantina_user'@'%';
FLUSH PRIVILEGES;

-- Verificación
SELECT 'Cantina Tita DB initialized successfully' AS message;
