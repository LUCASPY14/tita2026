# Script para importar el esquema de la base de datos dbcantinatita
# Versión: 1.0
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
    Write-Host "❌ ERROR: No se encontró el archivo SQL:" -ForegroundColor Red
    Write-Host "   $sqlFile" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Archivo SQL encontrado" -ForegroundColor Green
Write-Host "  Ubicación: $sqlFile" -ForegroundColor Gray
Write-Host ""

# Verificar si MySQL está instalado
$mysqlCommand = Get-Command mysql -ErrorAction SilentlyContinue

if (-not $mysqlCommand) {
    Write-Host "❌ ERROR: MySQL no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Soluciones:" -ForegroundColor Yellow
    Write-Host "  1. Instalar MySQL desde: https://dev.mysql.com/downloads/mysql/" -ForegroundColor Gray
    Write-Host "  2. Agregar MySQL al PATH del sistema" -ForegroundColor Gray
    Write-Host "  3. Usar MySQL Workbench para ejecutar el script manualmente" -ForegroundColor Gray
    exit 1
}

Write-Host "✓ MySQL encontrado" -ForegroundColor Green
Write-Host ""

# Solicitar contraseña de MySQL
Write-Host "Ingrese la contraseña de MySQL para el usuario '$MySQLUser':" -ForegroundColor Cyan
$MySQLPassword = Read-Host -AsSecureString
$MySQLPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($MySQLPassword))

Write-Host ""
Write-Host "Conectando a MySQL..." -ForegroundColor Yellow

# Verificar conexión
$testConnection = "SELECT 1;" | mysql -u $MySQLUser -p"$MySQLPasswordPlain" -h $MySQLHost -P $MySQLPort 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ ERROR: No se pudo conectar a MySQL" -ForegroundColor Red
    Write-Host "   Verifique sus credenciales" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Conexión exitosa a MySQL" -ForegroundColor Green
Write-Host ""

# Verificar si la base de datos ya existe
Write-Host "Verificando si la base de datos 'dbcantinatita' existe..." -ForegroundColor Yellow
$dbExists = "SHOW DATABASES LIKE 'dbcantinatita';" | mysql -u $MySQLUser -p"$MySQLPasswordPlain" -h $MySQLHost -P $MySQLPort -N 2>&1

if ($dbExists -like "*dbcantinatita*") {
    Write-Host ""
    Write-Host "⚠️  ADVERTENCIA: La base de datos 'dbcantinatita' ya existe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "¿Desea eliminarla y crearla nuevamente? (Se perderán todos los datos)" -ForegroundColor Cyan
    Write-Host "  [S] Sí, eliminar y recrear" -ForegroundColor Gray
    Write-Host "  [N] No, cancelar operación (predeterminado)" -ForegroundColor Gray
    Write-Host ""
    $confirm = Read-Host "Opción [S/N]"
    
    if ($confirm -ne "S" -and $confirm -ne "s") {
        Write-Host ""
        Write-Host "❌ Operación cancelada por el usuario" -ForegroundColor Yellow
        exit 0
    }
    
    Write-Host ""
    Write-Host "Eliminando base de datos existente..." -ForegroundColor Yellow
    "DROP DATABASE dbcantinatita;" | mysql -u $MySQLUser -p"$MySQLPasswordPlain" -h $MySQLHost -P $MySQLPort 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Base de datos eliminada" -ForegroundColor Green
    } else {
        Write-Host "❌ ERROR al eliminar la base de datos" -ForegroundColor Red
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
$result = Get-Content $sqlFile -Raw | mysql -u $MySQLUser -p"$MySQLPasswordPlain" -h $MySQLHost -P $MySQLPort 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  ✓ BASE DE DATOS CREADA EXITOSAMENTE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Obtener estadísticas
    $tableCount = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'dbcantinatita' AND table_type = 'BASE TABLE';" | mysql -u $MySQLUser -p"$MySQLPasswordPlain" -h $MySQLHost -P $MySQLPort -N 2>&1
    $viewCount = "SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'dbcantinatita';" | mysql -u $MySQLUser -p"$MySQLPasswordPlain" -h $MySQLHost -P $MySQLPort -N 2>&1
    
    Write-Host "📊 Resumen:" -ForegroundColor Cyan
    Write-Host "   Base de datos: dbcantinatita" -ForegroundColor Gray
    Write-Host "   Tablas creadas: $tableCount" -ForegroundColor Gray
    Write-Host "   Vistas creadas: $viewCount" -ForegroundColor Gray
    Write-Host "   Servidor: $MySQLHost:$MySQLPort" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
    Write-Host "   1. Verificar la configuración en backend/settings/development.py" -ForegroundColor Gray
    Write-Host "   2. Ejecutar: python manage.py inspectdb > apps/all_models.py" -ForegroundColor Gray
    Write-Host "   3. Separar modelos por app según corresponda" -ForegroundColor Gray
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "❌ ERROR al ejecutar el script SQL" -ForegroundColor Red
    Write-Host ""
    Write-Host "Detalles del error:" -ForegroundColor Yellow
    Write-Host $result -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "Presione cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
