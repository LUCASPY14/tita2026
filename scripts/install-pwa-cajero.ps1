<#
.SYNOPSIS
    Instala y valida la PWA de ModoRecreo en un PC cajero.
.DESCRIPTION
    Verifica prerrequisitos (Chrome 90+, conectividad al servidor),
    valida que el Service Worker y el manifest sean accesibles,
    y guía la instalación de la PWA de forma interactiva.
.PARAMETER ServidorUrl
    URL base del servidor Cantina Tita. Por defecto http://localhost
.PARAMETER SoloValidar
    Solo verifica el estado; no abre Chrome ni guía la instalación.
.PARAMETER ConfigurarInicio
    Copia el acceso directo de Chrome App a la carpeta de Inicio de Windows
    para que la PWA arranque automáticamente con el sistema.
.EXAMPLE
    .\scripts\install-pwa-cajero.ps1
.EXAMPLE
    .\scripts\install-pwa-cajero.ps1 -ServidorUrl http://192.168.1.100
.EXAMPLE
    .\scripts\install-pwa-cajero.ps1 -SoloValidar
.EXAMPLE
    .\scripts\install-pwa-cajero.ps1 -ConfigurarInicio
#>
param(
    [string]$ServidorUrl     = "http://localhost",
    [switch]$SoloValidar,
    [switch]$ConfigurarInicio
)

$ErrorActionPreference = "Continue"
$allOk = $true

function Write-Check {
    param([bool]$ok, [string]$msg)
    if ($ok) { Write-Host "  [OK]    $msg" -ForegroundColor Green }
    else      { Write-Host "  [FALLO] $msg" -ForegroundColor Red }
    return $ok
}
function Write-Warn {
    param([string]$msg)
    Write-Host "  [AVISO] $msg" -ForegroundColor Yellow
}
function Write-Step {
    param([string]$n, [string]$msg)
    Write-Host ""
    Write-Host "[$n] $msg" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║   Cantina Tita — Instalación PWA Cajero (ModoRecreo)    ║" -ForegroundColor Blue
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host "  Servidor: $ServidorUrl"
Write-Host "  Fecha:    $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-Host ""

# ── 1. Google Chrome ───────────────────────────────────────────────────────────
Write-Step "1/5" "Google Chrome"

$chromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$chromePath = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($null -eq $chromePath) {
    $allOk = $false
    Write-Check $false "Google Chrome no encontrado. Instalarlo desde https://www.google.com/chrome/"
} else {
    $verInfo = (Get-Item $chromePath).VersionInfo
    $ver     = $verInfo.ProductVersion
    $major   = [int]($ver -split '\.')[0]
    if (-not (Write-Check ($major -ge 90) "Chrome $ver (mínimo requerido: 90)")) {
        $allOk = $false
        Write-Warn "Actualizar Chrome desde chrome://settings/help"
    }
}

# ── 2. Conectividad con el servidor ───────────────────────────────────────────
Write-Step "2/5" "Conectividad con el servidor"

try {
    $health = Invoke-RestMethod -Uri "$ServidorUrl/api/health/" -TimeoutSec 10
    if (-not (Write-Check ($health.status -eq "ok") "Health check: $($health.status)")) {
        $allOk = $false
    }
    # Checks adicionales si el health los incluye
    if ($health.checks) {
        $dbOk    = $health.checks.db    -eq "ok"
        $redisOk = $health.checks.redis -eq "ok"
        if (-not (Write-Check $dbOk    "Base de datos: $($health.checks.db)"))    { $allOk = $false }
        if (-not (Write-Check $redisOk "Redis: $($health.checks.redis)"))          { $allOk = $false }
    }
} catch {
    $allOk = $false
    Write-Check $false "No se pudo conectar a $ServidorUrl/api/health/"
    Write-Warn "Verificar que el servidor esté encendido y que esta PC esté en la red de la cantina"
}

# ── 3. Service Worker ─────────────────────────────────────────────────────────
Write-Step "3/5" "Service Worker"

try {
    $swResp  = Invoke-WebRequest -Uri "$ServidorUrl/sw.js" -TimeoutSec 10 -UseBasicParsing
    $swOk    = $swResp.StatusCode -eq 200
    if (-not (Write-Check $swOk "sw.js accesible (HTTP $($swResp.StatusCode))")) { $allOk = $false }

    $ct = [string]($swResp.Headers.'Content-Type')
    if ($ct -like "*html*") {
        $allOk = $false
        Write-Check $false "sw.js devuelve HTML en lugar de JavaScript — el nginx no está sirviendo el archivo correctamente"
    } else {
        Write-Check $true "Content-Type: $ct"
    }

    $cacheCtrl = [string]($swResp.Headers.'Cache-Control')
    if ($cacheCtrl -like "*immutable*" -or $cacheCtrl -like "*max-age=3153*") {
        Write-Warn "Cache-Control del SW incluye caché larga ($cacheCtrl). Regenerar la imagen Docker."
    } else {
        Write-Check $true "Cache-Control: $cacheCtrl"
    }
} catch {
    $allOk = $false
    Write-Check $false "sw.js no accesible: $_"
}

# ── 4. Manifest PWA ───────────────────────────────────────────────────────────
Write-Step "4/5" "Manifest PWA"

try {
    $mResp = Invoke-WebRequest -Uri "$ServidorUrl/manifest.webmanifest" -TimeoutSec 10 -UseBasicParsing
    if (-not (Write-Check ($mResp.StatusCode -eq 200) "manifest.webmanifest accesible (HTTP $($mResp.StatusCode))")) {
        $allOk = $false
    }

    $manifest = $mResp.Content | ConvertFrom-Json

    if (-not (Write-Check (-not [string]::IsNullOrEmpty($manifest.name)) "name: $($manifest.name)")) { $allOk = $false }
    if (-not (Write-Check ($manifest.start_url -eq "/modo-recreo") "start_url: $($manifest.start_url)")) { $allOk = $false }
    if (-not (Write-Check ($manifest.display -eq "standalone") "display: $($manifest.display)")) { $allOk = $false }
    if (-not (Write-Check ($manifest.icons.Count -gt 0) "icons: $($manifest.icons.Count) definidos")) { $allOk = $false }
} catch {
    $allOk = $false
    Write-Check $false "manifest.webmanifest no accesible: $_"
}

# ── 5. Icono ──────────────────────────────────────────────────────────────────
Write-Step "5/5" "Icono de la aplicación"

try {
    $iconResp = Invoke-WebRequest -Uri "$ServidorUrl/logo_tita.png" -TimeoutSec 10 -UseBasicParsing
    $sz = $iconResp.Content.Length
    if (-not (Write-Check ($iconResp.StatusCode -eq 200 -and $sz -gt 5000) `
              "logo_tita.png ($([math]::Round($sz/1024))KB)")) {
        $allOk = $false
    }
} catch {
    $allOk = $false
    Write-Check $false "Icono no accesible: $_"
}

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
if ($allOk) {
    Write-Host "RESULTADO: TODO OK — este PC puede instalar ModoRecreo como PWA." -ForegroundColor Green
} else {
    Write-Host "RESULTADO: HAY ERRORES — resolver los problemas antes de continuar." -ForegroundColor Red
    if ($SoloValidar) { exit 1 }
    Write-Host "Corregir los errores y volver a ejecutar este script." -ForegroundColor Yellow
    exit 1
}

if ($SoloValidar) { exit 0 }
if ($null -eq $chromePath) { exit 1 }

# ── Instrucciones de instalación ──────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║              INSTALACIÓN DE LA PWA                      ║" -ForegroundColor Yellow
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Yellow
Write-Host "║                                                          ║" -ForegroundColor Yellow
Write-Host "║  Se va a abrir Chrome en la página de ModoRecreo.       ║" -ForegroundColor Yellow
Write-Host "║                                                          ║" -ForegroundColor Yellow
Write-Host "║  Pasos para instalar:                                    ║" -ForegroundColor Yellow
Write-Host "║  1. Esperá que la página cargue completamente            ║" -ForegroundColor Yellow
Write-Host "║  2. Buscá el ícono (□↑) en la barra de direcciones      ║" -ForegroundColor Yellow
Write-Host "║     Si no aparece: F5 para recargar y esperá 5 seg.     ║" -ForegroundColor Yellow
Write-Host "║  3. Hacé clic en ese ícono → 'Instalar'                 ║" -ForegroundColor Yellow
Write-Host "║  4. La app se abre como ventana independiente            ║" -ForegroundColor Yellow
Write-Host "║  5. Anclá el ícono 'Cantina' a la Barra de tareas       ║" -ForegroundColor Yellow
Write-Host "║                                                          ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
Write-Host ""

Read-Host "Presioná ENTER para abrir Chrome en ModoRecreo..."

Start-Process $chromePath -ArgumentList `
    "--new-window",
    "--start-maximized",
    "--no-first-run",
    "$ServidorUrl/modo-recreo"

Write-Host ""
Write-Host "Chrome abierto. Seguí los pasos de la pantalla para instalar la PWA." -ForegroundColor Cyan
Write-Host ""

# ── Configurar inicio automático ──────────────────────────────────────────────
if ($ConfigurarInicio) {
    Write-Host "── Configurando inicio automático de la PWA ──" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "NOTA: Chrome instala un acceso directo al instalar la PWA."
    Write-Host "Una vez instalada, el acceso directo aparece en:"
    Write-Host "  %APPDATA%\Microsoft\Windows\Start Menu\Programs\Chrome Apps\"
    Write-Host ""

    $startupFolder = [Environment]::GetFolderPath("Startup")
    $chromeAppsDir = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Chrome Apps"

    if (Test-Path $chromeAppsDir) {
        $pwaShortcut = Get-ChildItem $chromeAppsDir -Filter "Cantina*.lnk" | Select-Object -First 1
        if ($null -ne $pwaShortcut) {
            $dest = Join-Path $startupFolder $pwaShortcut.Name
            Copy-Item $pwaShortcut.FullName -Destination $dest -Force
            Write-Check $true "Acceso directo copiado a la carpeta de Inicio: $dest"
            Write-Host "  La PWA iniciará automáticamente con Windows." -ForegroundColor Green
        } else {
            Write-Warn "No se encontró el acceso directo de la PWA en Chrome Apps."
            Write-Warn "Instalar la PWA primero (pasos anteriores) y luego re-ejecutar con -ConfigurarInicio"
        }
    } else {
        Write-Warn "Carpeta de Chrome Apps no encontrada. Instalar la PWA primero."
    }
}

Write-Host ""
Write-Host "Después de instalar, verificar con: .\scripts\install-pwa-cajero.ps1 -SoloValidar" -ForegroundColor DarkGray
Write-Host ""
