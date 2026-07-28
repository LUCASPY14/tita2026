# scripts/smoke-test.ps1 — Cantina Tita
#
# Verifica que los servicios críticos responden correctamente tras un deploy.
# Uso independiente:
#   .\scripts\smoke-test.ps1
#   .\scripts\smoke-test.ps1 -BaseUrl http://192.168.1.100 -ApiUrl http://192.168.1.100:8000
#
# También es llamado automáticamente por deploy.ps1 al final del paso 7.

param(
    [string]$BaseUrl        = "http://localhost",
    [string]$ApiUrl         = "http://localhost:8000",
    [int]   $TimeoutSec     = 10,
    [string]$DemoEmail      = "admin@tita.local",
    [securestring]$DemoPassword = $null
)

# Contraseña por defecto del usuario demo (solo para smoke test local)
if ($null -eq $DemoPassword) {
    $DemoPassword = ConvertTo-SecureString "demo1234" -AsPlainText -Force
}

function ConvertFrom-SecureStringPlain([securestring]$ss) {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($ss)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

$ErrorActionPreference = "Continue"
$Passed = 0
$Failed = 0

function Test-Endpoint {
    param(
        [string]$Label,
        [string]$Url,
        [int[]] $Expected = @(200),
        [string]$MustContain = "",
        [switch]$NoFollow
    )

    $code = 0
    $ok   = $false
    $msg  = ""

    try {
        $maxRedir = if ($NoFollow) { 0 } else { 5 }
        $resp = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec -UseBasicParsing -MaximumRedirection $maxRedir -ErrorAction Stop
        $code = [int]$resp.StatusCode
        if ($Expected -contains $code) {
            if ($MustContain -and ($resp.Content -notmatch [regex]::Escape($MustContain))) {
                $msg = "body no contiene '$MustContain'"
            } else {
                $ok = $true
            }
        } else {
            $msg = "esperado $($Expected -join ' o '), recibido $code"
        }
    } catch {
        $webResp = $_.Exception.Response
        if ($null -ne $webResp) {
            $code = [int]$webResp.StatusCode
            if ($Expected -contains $code) {
                $ok = $true
            } else {
                $msg = "HTTP $code — esperado $($Expected -join ' o ')"
            }
        } elseif ($NoFollow -and ($_.Exception.Message -match "302|redirect|Moved|Found|redireccionamiento|no válida|invalid")) {
            # PS5.1 MaximumRedirection=0 may throw without a readable Response for redirects
            $code = 302
            $ok   = $Expected -contains 302
            if (-not $ok) { $msg = "HTTP 302 — esperado $($Expected -join ' o ')" }
        } else {
            $code = 0
            $msg  = "sin respuesta: $($_.Exception.Message.Split([char]10)[0])"
        }
    }

    if ($ok) {
        Write-Host ("    [OK] {0,-46} {1}" -f $Label, $code) -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host ("   [ERR] {0,-46} {1}  {2}" -f $Label, $code, $msg) -ForegroundColor Red
        $script:Failed++
    }
}

# ── Encabezado ────────────────────────────────────────────────────
$line = "─" * 60
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
Write-Host "  Smoke Test — Cantina Tita" -ForegroundColor Cyan
Write-Host "  Backend : $ApiUrl" -ForegroundColor DarkGray
Write-Host "  Frontend: $BaseUrl" -ForegroundColor DarkGray
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

# ── 1. Health ────────────────────────────────────────────────────
Write-Host "  Health checks" -ForegroundColor Yellow
Test-Endpoint "Backend /api/health/"        "$ApiUrl/api/health/"   @(200) '"status"'
Test-Endpoint "Frontend (Nginx) /"          "$BaseUrl/"             @(200)
Test-Endpoint "Nginx → backend /api/health/" "$BaseUrl/api/health/" @(200) '"status"'

# ── 2. API — debe responder 401 sin token (no 500) ────────────────
Write-Host ""
Write-Host "  API endpoints — requieren auth (401 esperado)" -ForegroundColor Yellow
Test-Endpoint "JWT token endpoint"           "$ApiUrl/api/token/"                           @(400, 401, 405)
Test-Endpoint "Productos catálogo"           "$ApiUrl/api/v1/productos/productos/"           @(401, 403)
Test-Endpoint "Core tarjetas"               "$ApiUrl/api/v1/core/tarjetas/"                @(401, 403)
Test-Endpoint "Contabilidad cajas"          "$ApiUrl/api/v1/contabilidad/cajas/"            @(401, 403)
Test-Endpoint "Clientes"                    "$ApiUrl/api/v1/clientes/clientes/"             @(401, 403)
Test-Endpoint "Almuerzos menú diario"       "$ApiUrl/api/v1/almuerzos/menu/"               @(401, 403)
Test-Endpoint "Ventas"                      "$ApiUrl/api/v1/ventas/ventas/"                 @(401, 403)
Test-Endpoint "Facturas"                    "$ApiUrl/api/v1/contabilidad/facturas/"         @(401, 403)
Test-Endpoint "Notificaciones"              "$ApiUrl/api/v1/notificaciones/notificaciones/" @(401, 403)

# ── 3. Inventario — alertas (endpoint nuevo) ─────────────────────
Write-Host ""
Write-Host "  Inventario — alertas" -ForegroundColor Yellow
Test-Endpoint "Alertas de stock"            "$ApiUrl/api/v1/inventario/alertas-stock/"       @(401, 403)
Test-Endpoint "Alertas de vencimiento"      "$ApiUrl/api/v1/inventario/alertas-vencimiento/" @(401, 403)

# ── 4. Bancard — requieren auth (401 sin token) ───────────────────
Write-Host ""
Write-Host "  Bancard vPOS (requieren auth)" -ForegroundColor Yellow
Test-Endpoint "Bancard iniciar"             "$ApiUrl/api/v1/core/bancard/iniciar/"            @(401, 403, 405)
Test-Endpoint "Bancard retorno (público)"   "$ApiUrl/api/v1/core/bancard/retorno/"            @(302, 400, 404, 200) -NoFollow
Test-Endpoint "Bancard estado (sin ID)"     "$ApiUrl/api/v1/core/bancard/estado/no-existe/"   @(401, 403, 404)

# ── 5. Endpoints públicos / portal ───────────────────────────────
Write-Host ""
Write-Host "  Endpoints públicos" -ForegroundColor Yellow
Test-Endpoint "Portal frontend"             "$BaseUrl/portal/"      @(200)
Test-Endpoint "Admin Django"                "$ApiUrl/admin/"        @(200, 301, 302)
Test-Endpoint "API docs (Swagger)"          "$ApiUrl/api/v1/docs/"  @(200, 404)

# ── 6. Autenticación JWT + endpoint autenticado ───────────────────
Write-Host ""
Write-Host "  Autenticación JWT" -ForegroundColor Yellow

$accessToken = $null
try {
    $tokenBody = @{ email = $DemoEmail; password = (ConvertFrom-SecureStringPlain $DemoPassword) } | ConvertTo-Json
    $tokenResp = Invoke-WebRequest -Uri "$ApiUrl/api/token/" -Method POST `
        -Body $tokenBody -ContentType "application/json" `
        -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
    $parsed = $tokenResp.Content | ConvertFrom-Json
    $accessToken = $parsed.access
    if ($null -ne $accessToken -and $accessToken.Length -gt 20) {
        Write-Host ("    [OK] {0,-46} {1}" -f "POST /api/token/ con usuario demo", "200") -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host ("   [ERR] {0,-46} {1}" -f "POST /api/token/ — respuesta sin access", "") -ForegroundColor Red
        $script:Failed++
    }
} catch {
    $code = if ($null -ne $_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
    if ($code -eq 401 -or $code -eq 400) {
        # Credenciales de demo no válidas en este entorno (producción sin usuario demo) — no es fallo de infra
        Write-Host ("  [SKIP] {0,-46} {1}" -f "POST /api/token/ — usuario demo no existe en este entorno", "") -ForegroundColor DarkYellow
    } else {
        $hint = $_.Exception.Message.Split([char]10)[0]
        Write-Host ("   [ERR] {0,-46} {1}" -f "POST /api/token/", $hint) -ForegroundColor Red
        $script:Failed++
    }
}

if ($null -ne $accessToken) {
    $authHeaders = @{ Authorization = "Bearer $accessToken" }
    $authOk = $false
    try {
        $r = Invoke-WebRequest -Uri "$ApiUrl/api/v1/ventas/ventas/" -Headers $authHeaders `
            -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        $authOk = ([int]$r.StatusCode -eq 200)
    } catch { }
    if ($authOk) {
        Write-Host ("    [OK] {0,-46} {1}" -f "GET /api/v1/ventas/ventas/ con JWT", "200") -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host ("   [ERR] {0,-46}" -f "GET /api/v1/ventas/ventas/ con JWT") -ForegroundColor Red
        $script:Failed++
    }
} else {
    Write-Host ("  [SKIP] GET /api/v1/ventas/ventas/ — sin token") -ForegroundColor DarkYellow
}

# ── 7. WebSocket ──────────────────────────────────────────────────
Write-Host ""
Write-Host "  WebSocket — notificaciones en tiempo real" -ForegroundColor Yellow

if ($null -ne $accessToken) {
    $wsBase = $ApiUrl -replace "^http", "ws"
    $wsUrl  = "$wsBase/ws/notificaciones/?token=$accessToken"
    $wsOk   = $false
    try {
        $ws  = [System.Net.WebSockets.ClientWebSocket]::new()
        $ws.Options.SetRequestHeader("Origin", $BaseUrl)
        $cts = [System.Threading.CancellationTokenSource]::new(6000)
        $connectTask = $ws.ConnectAsync([Uri]$wsUrl, $cts.Token)
        $connectTask.Wait(5000) | Out-Null
        $wsOk = ($ws.State -eq [System.Net.WebSockets.WebSocketState]::Open)
        if ($wsOk) {
            $closeTask = $ws.CloseAsync(
                [System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure,
                "smoke-test", [System.Threading.CancellationToken]::None
            )
            $closeTask.Wait(3000) | Out-Null
        }
        $ws.Dispose()
    } catch { }

    if ($wsOk) {
        Write-Host ("    [OK] {0,-46}" -f "WS /ws/notificaciones/ → conexión abierta") -ForegroundColor Green
        $script:Passed++
    } else {
        Write-Host ("   [ERR] {0,-46}" -f "WS /ws/notificaciones/ — no conectó") -ForegroundColor Red
        $script:Failed++
    }
} else {
    Write-Host ("  [SKIP] WS /ws/notificaciones/ — sin token") -ForegroundColor DarkYellow
}

# ── Resumen ───────────────────────────────────────────────────────
$Total = $Passed + $Failed
Write-Host ""
Write-Host $line -ForegroundColor DarkGray
if ($Failed -eq 0) {
    Write-Host ("  RESULTADO: {0}/{1} checks pasaron" -f $Passed, $Total) -ForegroundColor Green
} else {
    Write-Host ("  RESULTADO: {0}/{1} checks fallaron" -f $Failed, $Total) -ForegroundColor Red
}
Write-Host $line -ForegroundColor DarkGray
Write-Host ""

if ($Failed -gt 0) { exit 1 }
exit 0
