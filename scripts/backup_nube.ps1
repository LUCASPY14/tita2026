# backup_nube.ps1
# Copia el último backup local de Cantina Tita a Google Drive (o cualquier
# destino compatible con rclone: OneDrive, Dropbox, S3, etc.)
#
# ────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN INICIAL (una sola vez)
# ────────────────────────────────────────────────────────────────────────────
#
# 1. Descargar rclone para Windows: https://rclone.org/downloads/
#    Extraer rclone.exe y copiar a C:\tools\rclone\ (o cualquier carpeta en PATH)
#
# 2. Configurar destino:
#    rclone config
#    → Elegir "n" (new remote)
#    → Name: "gdrive" (o el nombre que prefieras)
#    → Storage type: "drive" (Google Drive) o "onedrive", etc.
#    → Seguir el wizard OAuth (abre el navegador para autorizar)
#
# 3. Crear carpeta destino en Google Drive:
#    rclone mkdir gdrive:backups/cantina_tita
#
# 4. Registrar esta tarea después del backup local:
#    schtasks /Create /TN "Backup Cantina Nube" `
#      /TR "powershell -File C:\tita2026\scripts\backup_nube.ps1" `
#      /SC DAILY /ST 02:30 /RU SYSTEM
#
# ────────────────────────────────────────────────────────────────────────────

param(
    [string]$LocalDir    = "C:\backups\cantina",
    [string]$RemoteName  = "gdrive",                     # nombre configurado en rclone
    [string]$RemotePath  = "backups/cantina_tita",       # carpeta dentro de Google Drive
    [string]$RcloneBin   = "rclone",                     # rclone en PATH o ruta completa
    [int]   $KeepRemote  = 7,                            # semanas a conservar en la nube
    [switch]$SoloUltimo  = $false                        # solo subir el último .dump
)

$LOG_DIR = "$LocalDir\logs"
$FECHA   = Get-Date -Format "yyyyMMdd_HHmm"
$LOG     = "$LOG_DIR\backup_nube_$FECHA.log"

function Write-Log {
    param([string]$Msg, [string]$Level = "INFO")
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$Level] $Msg"
    Write-Host $line
    $line | Out-File -FilePath $LOG -Append -Encoding utf8
}

# Crear directorio de logs
if (-not (Test-Path $LOG_DIR)) { New-Item -ItemType Directory -Path $LOG_DIR | Out-Null }

Write-Log "=== Inicio backup a la nube ==="

# ── Verificar rclone ──────────────────────────────────────────────────────────
try {
    $rcloneVer = & $RcloneBin version 2>&1 | Select-Object -First 1
    Write-Log "rclone encontrado: $rcloneVer"
} catch {
    Write-Log "ERROR: rclone no encontrado en '$RcloneBin'. Instalar desde https://rclone.org" "ERROR"
    Write-Log "Saltando backup a la nube." "WARN"
    exit 0  # exit 0 para no interrumpir la tarea programada
}

# ── Determinar qué archivos subir ─────────────────────────────────────────────
$dumps = Get-ChildItem "$LocalDir\cantina_*.dump" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

if ($dumps.Count -eq 0) {
    Write-Log "No hay archivos .dump en $LocalDir. Ejecutar backup_cantina.ps1 primero." "WARN"
    exit 0
}

if ($SoloUltimo) {
    $archivos = @($dumps[0])
    Write-Log "Modo SoloUltimo: subiendo $($archivos[0].Name)"
} else {
    # Subir todos los dumps de los últimos 7 días
    $cutoff = (Get-Date).AddDays(-7)
    $archivos = $dumps | Where-Object { $_.LastWriteTime -ge $cutoff }
    Write-Log "Archivos a subir (últimos 7 días): $($archivos.Count)"
}

# ── Subir archivos ────────────────────────────────────────────────────────────
$subidos = 0
$errores = 0

foreach ($archivo in $archivos) {
    $destino = "${RemoteName}:${RemotePath}/$($archivo.Name)"
    Write-Log "Subiendo: $($archivo.Name) ($([math]::Round($archivo.Length / 1MB, 2)) MB) → $destino"
    try {
        & $RcloneBin copyto $archivo.FullName $destino --progress 2>&1 |
            ForEach-Object { Write-Log "  rclone: $_" }
        if ($LASTEXITCODE -eq 0) {
            Write-Log "  ✓ Subido correctamente"
            $subidos++
        } else {
            Write-Log "  ✗ rclone salió con código $LASTEXITCODE" "ERROR"
            $errores++
        }
    } catch {
        Write-Log "  ✗ Excepción: $_" "ERROR"
        $errores++
    }
}

# ── Verificar que el archivo existe en la nube ────────────────────────────────
if ($subidos -gt 0) {
    Write-Log "Verificando contenido remoto..."
    $listado = & $RcloneBin ls "${RemoteName}:${RemotePath}" 2>&1
    Write-Log "Archivos en la nube: $($listado.Split("`n").Count - 1)"
}

# ── Rotación de archivos remotos viejos ───────────────────────────────────────
$cutoffRemote = (Get-Date).AddDays(-$KeepRemote * 7)
Write-Log "Eliminando backups remotos anteriores a $($cutoffRemote.ToString('yyyy-MM-dd'))..."

& $RcloneBin delete "${RemoteName}:${RemotePath}" `
    --min-age "${KeepRemote}w" `
    --include "cantina_*.dump" 2>&1 |
    ForEach-Object { Write-Log "  rclone: $_" }

# ── Resumen ───────────────────────────────────────────────────────────────────
Write-Log "=== Fin backup a la nube | Subidos: $subidos | Errores: $errores ==="

if ($errores -gt 0) {
    Write-Log "ADVERTENCIA: $errores archivo(s) no se pudieron subir. Revisar $LOG" "WARN"
    exit 1
}

exit 0
