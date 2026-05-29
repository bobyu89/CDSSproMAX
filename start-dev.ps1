# TICDSS daily dev launcher.
#
# Starts:
#   - docker compose (postgres + minio + langfuse) in detached mode
#   - waits for Postgres to become healthy
#   - opens 3 new PowerShell windows: API (8001), ASR (8002), Web (3000)
#
# Run from repo root:  .\start-dev.ps1
# Or double-click start-dev.cmd.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

function Info($msg)  { Write-Host "  $msg" -ForegroundColor Gray }
function Step($msg)  { Write-Host ""; Write-Host "─── $msg ───" -ForegroundColor Cyan }
function Ok($msg)    { Write-Host "✓ $msg" -ForegroundColor Green }
function Fail($msg)  { Write-Host "✗ $msg" -ForegroundColor Red; exit 1 }

# ── 1. Sanity checks ─────────────────────────────────────────────────────
Step "Checking tools"
foreach ($t in @("docker", "uv", "pnpm")) {
    if (-not (Get-Command $t -ErrorAction SilentlyContinue)) {
        Fail "$t not found in PATH. Run .\scripts\setup.ps1 first."
    }
    Ok "$t found"
}

if (-not (Test-Path "$root\.env")) {
    Fail ".env missing. Run .\scripts\setup.ps1 first."
}

# ── 2. Start infrastructure ──────────────────────────────────────────────
Step "Starting infrastructure (postgres + minio + langfuse)"
docker compose -f "$root\docker-compose.yml" up -d
if ($LASTEXITCODE -ne 0) { Fail "docker compose up failed" }

Step "Waiting for Postgres health"
$tries = 0
while ($tries -lt 30) {
    $health = docker inspect --format='{{.State.Health.Status}}' ticdss-postgres 2>$null
    if ($health -eq "healthy") { Ok "Postgres healthy"; break }
    Start-Sleep -Seconds 1
    $tries++
}
if ($tries -ge 30) { Fail "Postgres did not become healthy in 30s — check: docker compose logs postgres" }

# ── 3. Spawn three dev windows ───────────────────────────────────────────
Step "Launching dev windows"

function Spawn($title, $cwd, $cmd) {
    $full = "Set-Location -LiteralPath '$cwd'; `$host.UI.RawUI.WindowTitle = '$title'; Write-Host '── $title ──' -ForegroundColor Cyan; $cmd"
    Start-Process -FilePath "powershell.exe" `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $full)
    Info "→ $title"
}

Spawn "TICDSS API :8001" "$root\apps\api" `
    "uv run uvicorn src.main:app --reload --port 8001 --host 0.0.0.0"

Spawn "TICDSS ASR :8002" "$root\apps\asr" `
    "`$env:ASR_STUB_MODE='true'; uv run uvicorn src.main:app --reload --port 8002 --host 0.0.0.0"

Spawn "TICDSS Web :3000" "$root" `
    "pnpm dev:web"

# ── 4. Summary ───────────────────────────────────────────────────────────
Start-Sleep -Seconds 2
Write-Host ""
Write-Host "✓ All services launching." -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Yellow
Write-Host "  Web      → http://localhost:3000"
Write-Host "  API      → http://localhost:8001/health"
Write-Host "  ASR      → http://localhost:8002/health"
Write-Host "  Langfuse → http://localhost:3001"
Write-Host "  MinIO    → http://localhost:9001  (login: ticdss / ticdss123)"
Write-Host ""
Write-Host "Demo login (seeded):" -ForegroundColor Yellow
Write-Host "  Student → P001 / demo1234"
Write-Host "  Teacher → T001 / demo1234"
Write-Host "  Admin   → ADMIN001 / demo1234"
Write-Host ""
Write-Host "Stop everything with:  .\stop-dev.ps1" -ForegroundColor Gray
