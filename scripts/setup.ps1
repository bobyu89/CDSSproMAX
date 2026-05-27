# TICDSS one-shot setup for Windows PowerShell.
# Run from repo root:  .\scripts\setup.ps1

$ErrorActionPreference = "Stop"

function Step($msg) {
    Write-Host ""
    Write-Host "─── $msg ───" -ForegroundColor Cyan
}

function Ok($msg) {
    Write-Host "✓ $msg" -ForegroundColor Green
}

function CheckTool($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "✗ Required tool '$name' not found in PATH" -ForegroundColor Red
        return $false
    }
    Ok "$name found at $($cmd.Source)"
    return $true
}

Step "Checking required tools"
$allOk = $true
foreach ($t in @("docker", "node", "pnpm", "uv")) {
    if (-not (CheckTool $t)) { $allOk = $false }
}
if (-not $allOk) {
    Write-Host ""
    Write-Host "Install missing tools then re-run." -ForegroundColor Yellow
    Write-Host "  - docker:  https://www.docker.com/products/docker-desktop"
    Write-Host "  - node:    https://nodejs.org/  (v20+)"
    Write-Host "  - pnpm:    npm install -g pnpm  (v9+)"
    Write-Host "  - uv:      https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
}

Step "Installing dependencies"
Push-Location apps/api
uv sync
Pop-Location
Ok "apps/api deps synced"

Push-Location apps/asr
uv sync
Pop-Location
Ok "apps/asr deps synced"

pnpm install
Ok "Frontend deps installed"

Step "Setting up .env if missing"
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Ok ".env copied from .env.example — edit it to add ANTHROPIC_API_KEY / GOOGLE_API_KEY"
} else {
    Ok ".env already exists, leaving alone"
}

Step "Starting infrastructure (postgres + langfuse)"
docker compose up -d
Ok "Containers started"

Step "Waiting for Postgres to become healthy"
$tries = 0
while ($tries -lt 30) {
    $health = docker inspect --format='{{.State.Health.Status}}' ticdss-postgres 2>$null
    if ($health -eq "healthy") {
        Ok "Postgres healthy"
        break
    }
    Start-Sleep -Seconds 1
    $tries++
}
if ($tries -ge 30) {
    Write-Host "✗ Postgres did not become healthy in 30s. Check: docker compose logs postgres" -ForegroundColor Red
    exit 1
}

Step "Running database migration"
Push-Location apps/api
uv run alembic upgrade head
Pop-Location
Ok "Schema created"

Step "Seeding demo data"
Push-Location apps/api
uv run python ../../scripts/seed_users.py
uv run python ../../scripts/import_cases.py
try {
    uv run python scripts/seed_bibliotheke.py
} catch {
    Write-Host "(bibliotheke seed skipped — model download may take time on first run)" -ForegroundColor Yellow
}
Pop-Location
Ok "Demo users + 38 cases imported"

Write-Host ""
Write-Host "✓✓✓ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next: open three PowerShell windows and run:"
Write-Host "  Terminal A:  cd apps\api;  uv run uvicorn src.main:app --reload --port 8001"
Write-Host "  Terminal B:  pnpm dev:web"
Write-Host "  Terminal C:  cd apps\asr;  `$env:ASR_STUB_MODE='true'; uv run uvicorn src.main:app --reload --port 8002"
Write-Host ""
Write-Host "Then open http://localhost:3000 — log in as P001 / demo1234"
