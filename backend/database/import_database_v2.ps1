# Script para importar el esquema de la base de datos dbcantinatita
# Version: 2.0
# Fecha: Febrero 2026

param(
    [string]$MySQLUser = "root",
    [string]$MySQLHost = "localhost",
    [int]$MySQLPort = 3306
)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Importador de Base de Datos" -ForegroundColor Cyan
Write-Host "  dbcantinatita - Cantina Tita" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si el archivo SQL existe
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$sqlFile = Join-Path $scriptPath "dbcantinatita_schema.sql"

if (-not (Test-Path $sqlFile)) {
    Write-Host "[ERROR] No se encontro el archivo SQL:" -ForegroundColor Red
    Write-Host "   $sqlFile" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Archivo SQL encontrado" -ForegroundColor Green
Write-Host "  Ubicacion: $sqlFile" -ForegroundColor Gray
Write-Host ""

# Verificar si MySQL esta instalado
$mysqlCommand = Get-Command mysql -ErrorAction SilentlyContinue

if (-not $mysqlCommand) {
    Write-Host "[ERROR] MySQL no esta instalado o no esta en el PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Soluciones:" -ForegroundColor Yellow
    Write-Host "  1. Instalar MySQL desde: https://dev.mysql.com/downloads/mysql/" -ForegroundColor Gray
    Write-Host "  2. Agregar MySQL al PATH del sistema" -ForegroundColor Gray
    Write-Host "  3. Usar MySQL Workbench para ejecutar el script manualmente" -ForegroundColor Gray
    exit 1
}

Write-Host "[OK] MySQL encontrado" -ForegroundColor Green
Write-Host ""

# Solicitar contrasena de MySQL
Write-Host "Ingrese la contrasena de MySQL para el usuario '$MySQLUser':" -ForegroundColor Cyan
$MySQLPassword = Read-Host -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($MySQLPassword)
$MySQLPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# Crear archivo temporal de configuracion MySQL
$tempConfigFile = [System.IO.Path]::GetTempFileName()
$configContent = @"
[client]
user=$MySQLUser
password=$MySQLPasswordPlain
host=$MySQLHost
port=$MySQLPort
"@
Set-Content -Path $tempConfigFile -Value $configContent -Force

Write-Host ""
Write-Host "Conectando a MySQL..." -ForegroundColor Yellow

# Verificar conexion
$testQuery = "SELECT 1"
$testResult = Invoke-Expression "echo `"$testQuery`" | mysql --defaults-extra-file=`"$tempConfigFile`" 2>&1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] No se pudo conectar a MySQL" -ForegroundColor Red
    Write-Host "   Verifique sus credenciales" -ForegroundColor Yellow
    Remove-Item $tempConfigFile -Force
    exit 1
}

Write-Host "[OK] Conexion exitosa a MySQL" -ForegroundColor Green
Write-Host ""

# Verificar si la base de datos ya existe
Write-Host "Verificando si la base de datos 'dbcantinatita' existe..." -ForegroundColor Yellow
$checkDbQuery = "SHOW DATABASES LIKE 'dbcantinatita'"
$dbExists = Invoke-Expression "echo `"$checkDbQuery`" | mysql --defaults-extra-file=`"$tempConfigFile`" -N 2>&1"

if ($dbExists -match "dbcantinatita") {
    Write-Host ""
    Write-Host "[ADVERTENCIA] La base de datos 'dbcantinatita' ya existe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Desea eliminarla y crearla nuevamente? (Se perderan todos los datos)" -ForegroundColor Cyan
    Write-Host "  [S] Si, eliminar y recrear" -ForegroundColor Gray
    Write-Host "  [N] No, cancelar operacion (predeterminado)" -ForegroundColor Gray
    Write-Host ""
    $confirm = Read-Host "Opcion [S/N]"
    
    if ($confirm -ne "S" -and $confirm -ne "s") {
        Write-Host ""
        Write-Host "[CANCELADO] Operacion cancelada por el usuario" -ForegroundColor Yellow
        Remove-Item $tempConfigFile -Force
        exit 0
    }
    
    Write-Host ""
    Write-Host "Eliminando base de datos existente..." -ForegroundColor Yellow
    $dropDbQuery = "DROP DATABASE dbcantinatita"
    Invoke-Expression "echo `"$dropDbQuery`" | mysql --defaults-extra-file=`"$tempConfigFile`" 2>&1" | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Base de datos eliminada" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Error al eliminar la base de datos" -ForegroundColor Red
        Remove-Item $tempConfigFile -Force
        exit 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ejecutando script SQL..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Esto puede tomar unos momentos..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar el script SQL
$importResult = Invoke-Expression "mysql --defaults-extra-file=`"$tempConfigFile`" < `"$sqlFile`" 2>&1"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  [OK] BASE DE DATOS CREADA EXITOSAMENTE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Obtener estadisticas
    $tableCountQuery = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'dbcantinatita' AND table_type = 'BASE TABLE'"
    $tableCount = Invoke-Expression "echo `"$tableCountQuery`" | mysql --defaults-extra-file=`"$tempConfigFile`" -N 2>&1"
    
    $viewCountQuery = "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'dbcantinatita'"
    $viewCount = Invoke-Expression "echo `"$viewCountQuery`" | mysql --defaults-extra-file=`"$tempConfigFile`" -N 2>&1"
    
    Write-Host "[RESUMEN]" -ForegroundColor Cyan
    Write-Host "   Base de datos: dbcantinatita" -ForegroundColor Gray
    Write-Host "   Tablas creadas: $tableCount" -ForegroundColor Gray
    Write-Host "   Vistas creadas: $viewCount" -ForegroundColor Gray
    Write-Host "   Servidor: $MySQLHost`:$MySQLPort" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "[PROXIMOS PASOS]" -ForegroundColor Cyan
    Write-Host "   1. Verificar la configuracion en backend/settings/development.py" -ForegroundColor Gray
    Write-Host "   2. Ejecutar: python manage.py inspectdb > database/generated_models.py" -ForegroundColor Gray
    Write-Host "   3. Separar modelos por app segun corresponda" -ForegroundColor Gray
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "[ERROR] Error al ejecutar el script SQL" -ForegroundColor Red
    Write-Host ""
    Write-Host "Detalles del error:" -ForegroundColor Yellow
    Write-Host $importResult -ForegroundColor Red
    Write-Host ""
}

# Limpiar archivo temporal
Remove-Item $tempConfigFile -Force -ErrorAction SilentlyContinue

Write-Host "Presione cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
