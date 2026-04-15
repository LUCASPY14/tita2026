# Script para ejecutar el servidor de desarrollo Django
# Rama: desarrollo
# Uso: .\run-dev-server.ps1

Write-Host "🚀 Iniciando servidor Django (rama desarrollo)..." -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path ".\manage.py")) {
    Write-Host "❌ Error: manage.py no encontrado en el directorio actual" -ForegroundColor Red
    Write-Host "   Asegúrate de ejecutar este script desde: D:\tita2026\backend\" -ForegroundColor Yellow
    exit 1
}

# Activar entorno virtual de cantina_tita
$venvPath = "..\cantina_tita\venv"
if (-not (Test-Path "$venvPath\Scripts\Activate.ps1")) {
    Write-Host "❌ Error: Entorno virtual no encontrado en $venvPath" -ForegroundColor Red
    Write-Host "   Crea el entorno virtual ejecutando:" -ForegroundColor Yellow
    Write-Host "   python -m venv ..\cantina_tita\venv" -ForegroundColor White
    exit 1
}

Write-Host "📦 Activando entorno virtual..." -ForegroundColor Green
& "$venvPath\Scripts\Activate.ps1"

# Crear directorio logs si no existe
if (-not (Test-Path "logs")) {
    Write-Host "📁 Creando directorio de logs..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Verificar variables de entorno
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Advertencia: Archivo .env no encontrado" -ForegroundColor Yellow
    Write-Host "   Creando .env desde .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "   ✅ Archivo .env creado" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "🔧 Ejecutando migraciones..." -ForegroundColor Cyan
python manage.py migrate --noinput

Write-Host ""
Write-Host "🌐 Iniciando servidor en http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "   Presiona Ctrl+C para detener el servidor" -ForegroundColor Gray
Write-Host ""

# Ejecutar servidor
python manage.py runserver
