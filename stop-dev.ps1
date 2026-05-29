# Stop all TICDSS dev services.
#
# - Sends Ctrl+C-style close to the three dev windows by window title.
# - Stops the docker compose stack.
#
# Run from repo root:  .\stop-dev.ps1

$ErrorActionPreference = "Continue"
$root = $PSScriptRoot

Write-Host "─── Closing dev windows ───" -ForegroundColor Cyan
foreach ($title in @("TICDSS API :8001", "TICDSS ASR :8002", "TICDSS Web :3000")) {
    Get-Process powershell -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.MainWindowTitle -eq $title) {
            try {
                Stop-Process -Id $_.Id -Force
                Write-Host "✓ closed $title" -ForegroundColor Green
            } catch {
                Write-Host "✗ could not close $title — close it manually" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""
Write-Host "─── Stopping docker compose ───" -ForegroundColor Cyan
docker compose -f "$root\docker-compose.yml" down
Write-Host "✓ Done." -ForegroundColor Green
