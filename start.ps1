# ============================================================
# Kinyan CRM - Single Server Startup Script
# ============================================================
# This script starts EVERYTHING on ONE server:
#   - Builds frontend (React)
#   - Runs database migrations
#   - Starts FastAPI (serves API + Frontend)
# 
# Usage: .\start.ps1
# ============================================================

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   Kinyan CRM - Single Server" -ForegroundColor White
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:DEV_SKIP_AUTH = "true"  # Skip authentication for testing
$env:DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
$env:SECRET_KEY = "dev-local-secret-key-change-in-production"
$env:API_KEY = "dev-webhook-key"
$env:JWT_SECRET_KEY = "dev-jwt-secret-key-change-in-production"
$env:JWT_ALGORITHM = "HS256"
$env:JWT_EXPIRATION_MINUTES = "1440"
$env:FRONTEND_URL = "http://localhost:8001"

# Google OAuth
$env:GOOGLE_CLIENT_ID = "638402661079-pjfnm1g84il9uvj9vtgh4v5jqj6uk1gi.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "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"
$env:GOOGLE_REDIRECT_URI = "http://localhost:8001/api/auth/google/callback"

Write-Host "[OK] Environment configured" -ForegroundColor Green
Write-Host "[DB] Render PostgreSQL (Frankfurt)" -ForegroundColor Yellow

# Check if virtual environment exists
if (Test-Path ".\.venv311\Scripts\Activate.ps1") {
    Write-Host "[OK] Activating virtual environment (.venv311)..." -ForegroundColor Cyan
    & .\.venv311\Scripts\Activate.ps1
} elseif (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "[OK] Activating virtual environment (venv)..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
}

# Build frontend if needed
if (-not (Test-Path ".\frontend\dist\index.html")) {
    Write-Host ""
    Write-Host "[BUILD] Building frontend..." -ForegroundColor Cyan
    Push-Location frontend
    npm install
    npm run build
    Pop-Location
    Write-Host "[OK] Frontend built!" -ForegroundColor Green
} else {
    Write-Host "[OK] Frontend already built (frontend/dist exists)" -ForegroundColor Green
}

# Run database migrations
Write-Host ""
Write-Host "[DB] Running migrations..." -ForegroundColor Cyan
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Migrations complete" -ForegroundColor Green
} else {
    Write-Host "[!] Migration warning (may already be up to date)" -ForegroundColor Yellow
}

# Start the server
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ONE SERVER - Everything included!" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   App:     http://localhost:8001" -ForegroundColor White
Write-Host "   API:     http://localhost:8001/api/" -ForegroundColor White
Write-Host "   Docs:    http://localhost:8001/docs" -ForegroundColor White
Write-Host "   Health:  http://localhost:8001/health" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

uvicorn app:app --reload --host 0.0.0.0 --port 8001
