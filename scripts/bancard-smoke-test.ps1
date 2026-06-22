# scripts/bancard-smoke-test.ps1 — Cantina Tita
#
# Verifica la integración Bancard vPOS antes de ir a producción.
# Requiere credenciales de un usuario CLIENTE_WEB con tarjeta activa.
#
# Uso:
#   .\scripts\bancard-smoke-test.ps1
#   .\scripts\bancard-smoke-test.ps1 -ApiUrl http://192.168.1.100:8000 `
#       -Email padre@ejemplo.com -Password "mi_clave" -NroTarjeta "1234567890"
#
# Requisitos previos:
#   1. Backend corriendo con BANCARD_SANDBOX=True en .env
#   2. BANCARD_PUBLIC_KEY y BANCARD_PRIVATE_KEY configurados (sandbox)
#   3. BANCARD_RETURN_URL apuntando al backend accesible
#   4. Usuario CLIENTE_WEB con tarjeta ACTIVA existente

param(
    [string]$ApiUrl      = "http://localhost:8000",
    [string]$Email       = "",
    [string]$Password    = "",
    [string]$NroTarjeta  = "",
    [int]   $MontoTest   = 15000,
    [int]   $TimeoutSec  = 15
)

$ErrorActionPreference = "Continue"
$Passed  = 0
$Failed  = 0
$Skipped = 0
$AccessToken = ""

function Write-Section { param([string]$Title)
    Write-Host ""
    Write-Host "  $Title" -ForegroundColor Yellow
}

function Pass  { param([string]$Label)
    Write-Host ("    [OK]   {0}" -f $Label) -ForegroundColor Green
    $script:Passed++
}

function Fail  { param([string]$Label, [string]$Detail = "")
    $msg = if ($Detail) { "  ← $Detail" } else { "" }
    Write-Host ("   [ERR]  {0}{1}" -f $Label, $msg) -ForegroundColor Red
    $script:Failed++
}

function Skip  { param([string]$Label, [string]$Reason = "")
    Write-Host ("  [SKIP]  {0}  ({1})" -f $Label, $Reason) -ForegroundColor DarkGray
    $script:Skipped++
}

function Invoke-Api {
    param([string]$Method, [string]$Path, [hashtable]$Body = @{}, [bool]$Auth = $true)
    $headers = @{ "Content-Type" = "application/json" }
    if ($Auth -and $script:AccessToken) {
        $headers["Authorization"] = "Bearer $($script:AccessToken)"
    }
    $uri = "$ApiUrl$Path"
    try {
        $bodyJson = if ($Body.Count -gt 0) { $Body | ConvertTo-Json } else { $null }
        if ($bodyJson) {
            $resp = Invoke-WebRequest -Uri $uri -Method $Method -Headers $headers `
                -Body $bodyJson -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        } else {
            $resp = Invoke-WebRequest -Uri $uri -Method $Method -Headers $headers `
                -TimeoutSec $TimeoutSec -UseBasicParsing -ErrorAction Stop
        }
        return @{ ok = $true; code = [int]$resp.StatusCode; body = ($resp.Content | ConvertFrom-Json) }
    } catch {
        $webResp = $_.Exception.Response
        if ($null -ne $webResp) {
            $code = [int]$webResp.StatusCode
            try {
                $stream  = $webResp.GetResponseStream()
                $reader  = [System.IO.StreamReader]::new($stream)
                $content = $reader.ReadToEnd()
                $parsed  = $content | ConvertFrom-Json
                return @{ ok = $false; code = $code; body = $parsed; raw = $content }
            } catch {
                return @{ ok = $false; code = $code; body = $null; raw = "" }
            }
        }
        return @{ ok = $false; code = 0; body = $null; error = $_.Exception.Message }
    }
}

# ── Encabezado ────────────────────────────────────────────────────
$line = "─" * 62
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  Bancard Smoke Test — Cantina Tita" -ForegroundColor Cyan
Write-Host "  API: $ApiUrl" -ForegroundColor DarkGray
Write-Host $line -ForegroundColor DarkGray

# ── 1. Variables de entorno ───────────────────────────────────────
Write-Section "1. Verificación de variables de entorno"

$envFile = Join-Path (Split-Path $PSScriptRoot) "backend\.env.production"
if (-not (Test-Path $envFile)) {
    $envFile = Join-Path (Split-Path $PSScriptRoot) "backend\.env"
}

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    $checks = @{
        "BANCARD_PUBLIC_KEY"   = $envContent -match "BANCARD_PUBLIC_KEY\s*=\s*\S+"
        "BANCARD_PRIVATE_KEY"  = $envContent -match "BANCARD_PRIVATE_KEY\s*=\s*\S+"
        "BANCARD_RETURN_URL"   = $envContent -match "BANCARD_RETURN_URL\s*=\s*\S+"
        "PORTAL_FRONTEND_URL"  = $envContent -match "PORTAL_FRONTEND_URL\s*=\s*\S+"
        "BANCARD_SANDBOX"      = $envContent -match "BANCARD_SANDBOX\s*=\s*True"
    }
    foreach ($kv in $checks.GetEnumerator()) {
        if ($kv.Value) { Pass $kv.Key }
        else            { Fail $kv.Key "no configurado o vacío en $envFile" }
    }
} else {
    Skip "Archivo .env" "no encontrado en $envFile — omitiendo checks de env"
}

# ── 2. Health check ───────────────────────────────────────────────
Write-Section "2. Health check del backend"

$health = Invoke-Api "GET" "/api/health/ready/" -Auth $false
if ($health.ok -and $health.body.status -eq "ready") {
    Pass "Backend /api/health/ready/ → status=ready"
} elseif ($health.ok) {
    Fail "Backend responde pero status=$($health.body.status)"
} else {
    Fail "Backend no responde (código $($health.code))" $health.error
}

# ── 3. Autenticación ──────────────────────────────────────────────
Write-Section "3. Autenticación JWT"

if (-not $Email -or -not $Password) {
    Skip "Login" "Email/Password no provistos — usá -Email y -Password"
    Skip "Endpoints autenticados" "sin token no se puede continuar"
    $skipAuth = $true
} else {
    $loginResp = Invoke-Api "POST" "/api/token/" @{ email = $Email; password = $Password } -Auth $false
    if ($loginResp.ok -and $loginResp.body.access) {
        $script:AccessToken = $loginResp.body.access
        $rol = $loginResp.body.rol ?? "(desconocido)"
        Pass "Login exitoso — rol=$rol"
        if ($loginResp.body.requiere_2fa -eq $true) {
            Fail "Usuario tiene 2FA habilitado — este test no soporta 2FA. Usá un usuario sin 2FA."
            $skipAuth = $true
        } else {
            $skipAuth = $false
        }
    } else {
        $detail = $loginResp.body.detail ?? $loginResp.body ?? "sin respuesta"
        Fail "Login fallido (HTTP $($loginResp.code))" $detail
        $skipAuth = $true
    }
}

# ── 4. Endpoint /bancard/iniciar/ ─────────────────────────────────
Write-Section "4. POST /api/v1/core/bancard/iniciar/"

if ($skipAuth) {
    Skip "bancard/iniciar" "sin token de autenticación"
} elseif (-not $NroTarjeta) {
    Skip "bancard/iniciar" "NroTarjeta no provisto — usá -NroTarjeta"
} else {
    # 4a. Validación de monto mínimo
    $r = Invoke-Api "POST" "/api/v1/core/bancard/iniciar/" @{ nro_tarjeta = $NroTarjeta; monto = 500 }
    if (-not $r.ok -and $r.code -eq 400) {
        Pass "Monto < 10.000 rechazado (400)"
    } else {
        Fail "Validación monto mínimo" "esperado 400, recibido $($r.code)"
    }

    # 4b. Validación de monto máximo
    $r = Invoke-Api "POST" "/api/v1/core/bancard/iniciar/" @{ nro_tarjeta = $NroTarjeta; monto = 6000000 }
    if (-not $r.ok -and $r.code -eq 400) {
        Pass "Monto > 5.000.000 rechazado (400)"
    } else {
        Fail "Validación monto máximo" "esperado 400, recibido $($r.code)"
    }

    # 4c. Pago real en sandbox
    $r = Invoke-Api "POST" "/api/v1/core/bancard/iniciar/" @{ nro_tarjeta = $NroTarjeta; monto = $MontoTest }
    if ($r.ok -and $r.code -eq 201 -and $r.body.shop_process_id -and $r.body.redirect_url) {
        $script:ShopProcessId = $r.body.shop_process_id
        Pass "Pago iniciado — shop_process_id=$($script:ShopProcessId)"
        Pass "redirect_url presente → $($r.body.redirect_url.Substring(0, [Math]::Min(60, $r.body.redirect_url.Length)))..."
    } elseif ($r.code -eq 503) {
        Fail "Servicio Bancard no disponible (503)" ($r.body.detail ?? "circuit breaker abierto o claves no configuradas")
    } elseif ($r.code -eq 404) {
        Fail "Tarjeta no encontrada (404)" "verificá -NroTarjeta=$NroTarjeta"
    } elseif ($r.code -eq 400 -and $r.body.detail -match "inactiva|suspendida|bloqueada") {
        Fail "Tarjeta no activa" $r.body.detail
    } else {
        Fail "Respuesta inesperada (HTTP $($r.code))" ($r.body.detail ?? $r.raw)
    }
}

# ── 5. Endpoint /bancard/estado/ ──────────────────────────────────
Write-Section "5. GET /api/v1/core/bancard/estado/<shop_process_id>/"

if ($skipAuth) {
    Skip "bancard/estado" "sin token"
} elseif (-not $script:ShopProcessId) {
    Skip "bancard/estado" "no se pudo crear el pago en el paso 4"
} else {
    $r = Invoke-Api "GET" "/api/v1/core/bancard/estado/$($script:ShopProcessId)/"
    if ($r.ok -and $r.body.estado) {
        Pass "Estado consultado — estado=$($r.body.estado), monto=$($r.body.monto)"
    } elseif ($r.code -eq 403) {
        Fail "Permiso denegado (403)" "el usuario no es dueño de la tarjeta o no es ADMIN"
    } else {
        Fail "Respuesta inesperada (HTTP $($r.code))" ($r.body.detail ?? "")
    }

    # Verificar que un ID inexistente devuelva 404
    $r2 = Invoke-Api "GET" "/api/v1/core/bancard/estado/id-que-no-existe-xyz123/"
    if ($r2.code -eq 404) {
        Pass "ID inexistente devuelve 404"
    } else {
        Fail "ID inexistente debería dar 404" "recibido $($r2.code)"
    }
}

# ── 6. Endpoint /bancard/retorno/ sin params ─────────────────────
Write-Section "6. GET /api/v1/core/bancard/retorno/ (sin shop_process_id)"

$r = Invoke-Api "GET" "/api/v1/core/bancard/retorno/" -Auth $false
# Debe redirigir (302) o dar 302 con Location al portal de error
if ($r.code -in @(200, 302, 301)) {
    Pass "Retorno sin params redirige/responde correctamente (HTTP $($r.code))"
} else {
    Fail "Retorno sin params" "esperado redirect o 200, recibido $($r.code)"
}

# ── 7. Acceso sin autenticación ───────────────────────────────────
Write-Section "7. Protección de endpoints (sin token)"

$cases = @(
    @{ path = "/api/v1/core/bancard/iniciar/"; method = "POST"; label = "iniciar sin auth" }
    @{ path = "/api/v1/core/bancard/estado/cualquiera/"; method = "GET"; label = "estado sin auth" }
)
foreach ($c in $cases) {
    $r = Invoke-Api $c.method $c.path -Auth $false
    if ($r.code -in @(401, 403)) {
        Pass "$($c.label) → $($r.code)"
    } else {
        Fail "$($c.label) debería requerir auth" "recibido $($r.code)"
    }
}

# ── Resumen ───────────────────────────────────────────────────────
$Total = $Passed + $Failed + $Skipped
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
if ($Failed -eq 0 -and $Skipped -eq 0) {
    Write-Host ("  RESULTADO: {0}/{1} pasaron ✓" -f $Passed, $Total) -ForegroundColor Green
} elseif ($Failed -eq 0) {
    Write-Host ("  RESULTADO: {0} OK, {1} skipped — verificar manualmente lo omitido" -f $Passed, $Skipped) -ForegroundColor Yellow
} else {
    Write-Host ("  RESULTADO: {0} fallos de {1} ({2} skipped)" -f $Failed, $Total, $Skipped) -ForegroundColor Red
    Write-Host ""
    Write-Host "  Próximos pasos:" -ForegroundColor DarkGray
    Write-Host "    1. Verificar BANCARD_PUBLIC_KEY y BANCARD_PRIVATE_KEY en .env" -ForegroundColor DarkGray
    Write-Host "    2. Confirmar BANCARD_SANDBOX=True" -ForegroundColor DarkGray
    Write-Host "    3. Verificar que la tarjeta exista y esté ACTIVA en DB" -ForegroundColor DarkGray
    Write-Host "    4. Confirmar que BANCARD_RETURN_URL sea alcanzable desde internet (sandbox)" -ForegroundColor DarkGray
}
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

if ($script:ShopProcessId) {
    Write-Host "  Pago creado en sandbox: shop_process_id = $($script:ShopProcessId)" -ForegroundColor DarkGray
    Write-Host "  Para completar el flujo visitar: $ApiUrl/api/v1/core/bancard/estado/$($script:ShopProcessId)/" -ForegroundColor DarkGray
    Write-Host ""
}

if ($Failed -gt 0) { exit 1 }
exit 0
