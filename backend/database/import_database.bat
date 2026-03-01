@echo off
REM Script para importar la base de datos dbcantinatita
REM Versión simplificada - CMD

echo.
echo ========================================
echo   Importador de Base de Datos
echo   dbcantinatita - Cantina Tita
echo ========================================
echo.

REM Verificar si el archivo SQL existe
if not exist "%~dp0dbcantinatita_schema.sql" (
    echo ERROR: No se encontro el archivo dbcantinatita_schema.sql
    echo.
    pause
    exit /b 1
)

echo [OK] Archivo SQL encontrado
echo.

REM Verificar si MySQL está instalado
where mysql >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: MySQL no esta instalado o no esta en el PATH
    echo.
    echo Soluciones:
    echo   1. Instalar MySQL desde: https://dev.mysql.com/downloads/mysql/
    echo   2. Agregar MySQL al PATH del sistema
    echo   3. Usar el script PowerShell: import_database.ps1
    echo.
    pause
    exit /b 1
)

echo [OK] MySQL encontrado
echo.

REM Solicitar credenciales
set /p MYSQL_USER=Usuario MySQL (predeterminado: root): 
if "%MYSQL_USER%"=="" set MYSQL_USER=root

set /p MYSQL_HOST=Host MySQL (predeterminado: localhost): 
if "%MYSQL_HOST%"=="" set MYSQL_HOST=localhost

echo.
echo Conectando a MySQL...
echo.

REM Ejecutar el script SQL
echo Ejecutando script SQL (esto puede tomar unos momentos)...
echo.

mysql -u %MYSQL_USER% -p -h %MYSQL_HOST% < "%~dp0dbcantitatita_schema.sql"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo   BASE DE DATOS CREADA EXITOSAMENTE
    echo ========================================
    echo.
    echo Proximos pasos:
    echo   1. Verificar configuracion en backend/settings/development.py
    echo   2. Ejecutar: python manage.py inspectdb
    echo.
) else (
    echo.
    echo ERROR al ejecutar el script SQL
    echo Verifique sus credenciales y que MySQL este ejecutandose
    echo.
)

pause
