# ========================================
# SCRIPT DE INICIO RÁPIDO - CANTINA TITA
# ========================================
# Este script automatiza el inicio del sistema con Docker

Write-Host "🚀 Iniciando Sistema Cantina TITA con Docker..." -ForegroundColor Cyan
Write-Host ""

# Verificar que Docker esté corriendo
$dockerRunning = docker info 2>&1 | Select-String "Server Version"
if (-not $dockerRunning) {
    Write-Host "❌ Docker Desktop no está corriendo. Por favor, inícialo primero." -ForegroundColor Red
    Write-Host "   Abre Docker Desktop y espera a que aparezca el icono verde." -ForegroundColor Yellow
    pause
    exit
}

Write-Host "✅ Docker Desktop está corriendo" -ForegroundColor Green

# Navegar al directorio del proyecto
$scriptPath = $PSScriptRoot
Set-Location $scriptPath
Write-Host "📁 Directorio: $scriptPath" -ForegroundColor Green

# Verificar archivo .env.docker
if (-not (Test-Path ".env.docker")) {
    Write-Host "⚠️  Archivo .env.docker no encontrado. Creando desde ejemplo..." -ForegroundColor Yellow
    if (Test-Path ".env.docker.example") {
        Copy-Item ".env.docker.example" ".env.docker"
        Write-Host "✅ Archivo .env.docker creado" -ForegroundColor Green
    } else {
        Write-Host "❌ Error: No se encontró .env.docker.example" -ForegroundColor Red
        pause
        exit
    }
}

# Obtener IP local
Write-Host ""
Write-Host "🔍 Detectando tu IP local..." -ForegroundColor Cyan
$ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -like "192.168.*"} | Select-Object -First 1).IPAddress

if ($ipAddress) {
    Write-Host "✅ Tu IP local es: $ipAddress" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Para acceder desde otras PCs, usa:" -ForegroundColor Yellow
    Write-Host "   http://$ipAddress" -ForegroundColor White
    Write-Host "   http://$ipAddress/admin" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "⚠️  No se pudo detectar tu IP automáticamente" -ForegroundColor Yellow
    Write-Host "   Ejecuta: ipconfig | findstr IPv4" -ForegroundColor White
    Write-Host ""
}

# Preguntar si es primera vez
Write-Host "¿Es la primera vez que ejecutas el sistema? (y/n): " -ForegroundColor Cyan -NoNewline
$primeraVez = Read-Host

if ($primeraVez -eq "y" -or $primeraVez -eq "Y" -or $primeraVez -eq "s" -or $primeraVez -eq "S") {
    Write-Host ""
    Write-Host "🏗️  Construyendo contenedores (puede tardar 5-10 minutos)..." -ForegroundColor Cyan
    docker-compose up --build -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "⏳ Esperando a que los servicios estén listos (30 segundos)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        
        Write-Host ""
        Write-Host "🗄️  Aplicando migraciones de base de datos..." -ForegroundColor Cyan
        docker-compose exec -T backend python manage.py migrate --noinput
        
        Write-Host ""
        Write-Host "📦 Recolectando archivos estáticos..." -ForegroundColor Cyan
        docker-compose exec -T backend python manage.py collectstatic --noinput
        
        Write-Host ""
        Write-Host "👤 Creando superusuario de Django..." -ForegroundColor Cyan
        Write-Host "   Sigue las instrucciones a continuación:" -ForegroundColor Yellow
        docker-compose exec backend python manage.py createsuperuser
    }
} else {
    Write-Host ""
    Write-Host "🚀 Levantando contenedores..." -ForegroundColor Cyan
    docker-compose up -d
}

# Verificar estado
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ ¡Sistema iniciado correctamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Estado de los contenedores:" -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "🌐 URLs de acceso:" -ForegroundColor Cyan
    Write-Host "   Local:           http://localhost" -ForegroundColor White
    if ($ipAddress) {
        Write-Host "   Red local:       http://$ipAddress" -ForegroundColor White
    }
    Write-Host "   Admin:           http://localhost/admin" -ForegroundColor White
    Write-Host "   API Swagger:     http://localhost:8000/swagger" -ForegroundColor White
    Write-Host "   API Redoc:       http://localhost:8000/redoc" -ForegroundColor White
    
    Write-Host ""
    Write-Host "📝 Comandos útiles:" -ForegroundColor Cyan
    Write-Host "   Ver logs:        docker-compose logs -f" -ForegroundColor White
    Write-Host "   Detener:         docker-compose stop" -ForegroundColor White
    Write-Host "   Reiniciar:       docker-compose restart" -ForegroundColor White
    Write-Host "   Apagar todo:     docker-compose down" -ForegroundColor White
    
    Write-Host ""
    Write-Host "📖 Para más información, lee: DOCKER_SETUP.md" -ForegroundColor Yellow
    
    # Preguntar si quiere ver los logs
    Write-Host ""
    Write-Host "¿Quieres ver los logs en tiempo real? (y/n): " -ForegroundColor Cyan -NoNewline
    $verLogs = Read-Host
    
    if ($verLogs -eq "y" -or $verLogs -eq "Y" -or $verLogs -eq "s" -or $verLogs -eq "S") {
        Write-Host ""
        Write-Host "📋 Mostrando logs (Ctrl+C para salir)..." -ForegroundColor Cyan
        docker-compose logs -f
    }
} else {
    Write-Host ""
    Write-Host "❌ Ocurrió un error al iniciar el sistema" -ForegroundColor Red
    Write-Host "   Verifica los logs con: docker-compose logs" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Presiona cualquier tecla para salir..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
