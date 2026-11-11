<#
.SYNOPSIS
    One-click detached launcher for CINEFLOW AI (FastAPI + Next.js Studio + Public Cloudflare HTTPS Tunnel).
#>
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogsDir = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Path $LogsDir -Force | Out-Null

# Clean up any previously tracked detached processes before launching
& (Join-Path $PSScriptRoot "stop_public_studio.ps1") | Out-Null
Start-Sleep -Milliseconds 500

$PythonBin = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonBin)) {
    throw "Backend virtual environment not found at $PythonBin"
}

$NextBin = Join-Path $RepoRoot "apps\web\node_modules\next\dist\bin\next"
if (-not (Test-Path $NextBin)) {
    throw "Next.js CLI not found at $NextBin. Run 'npm --prefix apps/web install' first."
}

if (-not (Test-Path (Join-Path $RepoRoot "apps\web\.next\BUILD_ID"))) {
    Write-Output "Building Next.js production bundle..."
    & npm --prefix (Join-Path $RepoRoot "apps\web") run build
    if ($LASTEXITCODE -ne 0) {
        throw "Next.js build failed."
    }
}

$NodeBin = (Get-Command node -ErrorAction Stop).Source
$CloudflaredBin = @(
    (Get-Command cloudflared -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
    "C:\Program Files (x86)\cloudflared\cloudflared.exe",
    "C:\Program Files\cloudflared\cloudflared.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1

if (-not $CloudflaredBin) {
    throw "cloudflared.exe not found. Install via: winget install Cloudflare.cloudflared"
}

foreach ($port in @(8000, 3000)) {
    $busy = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($busy) {
        throw "Port $port is already listening (PID $($busy.OwningProcess -join ',')). Free it or stop existing server first."
    }
}

# Remove stale tunnel log before launch so we only parse the newly issued URL
Remove-Item (Join-Path $LogsDir "cloudflared.err.log"), (Join-Path $LogsDir "cloudflared.out.log") -Force -ErrorAction SilentlyContinue

Write-Output "Starting FastAPI backend (127.0.0.1:8000)..."
$BackendProc = Start-Process -FilePath $PythonBin `
    -ArgumentList @("-m", "uvicorn", "backend.api.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $RepoRoot `
    -RedirectStandardOutput (Join-Path $LogsDir "backend.out.log") `
    -RedirectStandardError (Join-Path $LogsDir "backend.err.log") `
    -WindowStyle Hidden `
    -PassThru
Set-Content -Path (Join-Path $LogsDir "backend.pid") -Value $BackendProc.Id

Write-Output "Starting Next.js production server (127.0.0.1:3000)..."
$FrontendProc = Start-Process -FilePath $NodeBin `
    -ArgumentList @($NextBin, "start", "-p", "3000") `
    -WorkingDirectory (Join-Path $RepoRoot "apps\web") `
    -RedirectStandardOutput (Join-Path $LogsDir "frontend.out.log") `
    -RedirectStandardError (Join-Path $LogsDir "frontend.err.log") `
    -WindowStyle Hidden `
    -PassThru
Set-Content -Path (Join-Path $LogsDir "frontend.pid") -Value $FrontendProc.Id

# Wait for both local services
$deadline = (Get-Date).AddSeconds(45)
$backendReady = $false
$frontendReady = $false
while ((Get-Date) -lt $deadline -and (-not $backendReady -or -not $frontendReady)) {
    if (-not $backendReady) {
        try {
            $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 3
            if ($h.status -eq "ok") { $backendReady = $true }
        } catch {}
    }
    if (-not $frontendReady) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:3000/" -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -eq 200) { $frontendReady = $true }
        } catch {}
    }
    if (-not $backendReady -or -not $frontendReady) {
        Start-Sleep -Milliseconds 600
    }
}
if (-not $backendReady -or -not $frontendReady) {
    throw "Local services did not become ready within 45s (backend=$backendReady, frontend=$frontendReady)."
}

Write-Output "Starting Cloudflare HTTPS tunnel..."
$TunnelProc = Start-Process -FilePath $CloudflaredBin `
    -ArgumentList @("tunnel", "--url", "http://127.0.0.1:3000") `
    -WorkingDirectory $RepoRoot `
    -RedirectStandardOutput (Join-Path $LogsDir "cloudflared.out.log") `
    -RedirectStandardError (Join-Path $LogsDir "cloudflared.err.log") `
    -WindowStyle Hidden `
    -PassThru
Set-Content -Path (Join-Path $LogsDir "cloudflared.pid") -Value $TunnelProc.Id

# Parse public HTTPS URL from cloudflared stderr log
$PublicUrl = $null
$urlDeadline = (Get-Date).AddSeconds(35)
while ((Get-Date) -lt $urlDeadline -and -not $PublicUrl) {
    $errLog = Join-Path $LogsDir "cloudflared.err.log"
    if (Test-Path $errLog) {
        $raw = Get-Content $errLog -Raw -ErrorAction SilentlyContinue
        if ($raw -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
            $PublicUrl = $Matches[0]
            break
        }
    }
    Start-Sleep -Milliseconds 500
}

if (-not $PublicUrl) {
    throw "Cloudflare tunnel started (PID $($TunnelProc.Id)) but public URL did not appear in logs within 35s."
}

# Verify public HTTPS routing works end-to-end
$publicOk = $false
for ($i = 0; $i -lt 12; $i++) {
    try {
        $pubHealth = Invoke-RestMethod -Uri "$PublicUrl/api/v1/health" -TimeoutSec 10
        if ($pubHealth.status -eq "ok") {
            $publicOk = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Set-Content -Path (Join-Path $LogsDir "public_url.txt") -Value $PublicUrl

Write-Output ""
Write-Output "============================================================"
Write-Output "CINEFLOW AI IS LIVE (Detached Windows Background Processes)"
Write-Output "Public URL     : $PublicUrl"
Write-Output "Showcase Hub   : $PublicUrl/showcase"
Write-Output "Live HD Studio : $PublicUrl/editor?projectId=proj_bmsit_showcase_2026"
Write-Output "Local URL      : http://127.0.0.1:3000"
Write-Output "Public Verified: $publicOk"
Write-Output "PIDs           : backend=$($BackendProc.Id), frontend=$($FrontendProc.Id), cloudflared=$($TunnelProc.Id)"
Write-Output "Stop Script    : powershell -ExecutionPolicy Bypass -File scripts\stop_public_studio.ps1"
Write-Output "============================================================"
