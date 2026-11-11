<#
.SYNOPSIS
    Stop detached CINEFLOW AI public studio processes (Backend, Frontend, Cloudflare Tunnel).
#>
$ErrorActionPreference = "SilentlyContinue"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LogsDir = Join-Path $RepoRoot "logs"

foreach ($name in @("cloudflared", "frontend", "backend")) {
    $pidFile = Join-Path $LogsDir "$name.pid"
    if (Test-Path $pidFile) {
        $procId = (Get-Content $pidFile -Raw).Trim()
        if ($procId -match '^\d+$') {
            $proc = Get-Process -Id ([int]$procId) -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id ([int]$procId) -Force
                Write-Output "Stopped $name (PID $procId)."
            }
        }
        Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
    }
}

Remove-Item (Join-Path $LogsDir "public_url.txt") -Force -ErrorAction SilentlyContinue
Write-Output "CINEFLOW AI background processes stopped."
