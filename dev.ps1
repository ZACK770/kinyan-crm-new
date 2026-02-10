# dev.ps1 - Quick dev server (kills port 8000, starts uvicorn)
# Usage: .\dev.ps1

Write-Host "Stopping processes on port 8000..." -ForegroundColor Yellow

# Kill any process listening on port 8000
$connections = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
foreach ($conn in $connections) {
    $pid = $conn.OwningProcess
    if ($pid -and $pid -ne 0) {
        Write-Host "  Killing process $pid" -ForegroundColor Red
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
}

# Also kill any Python processes (backup)
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Wait for processes to die
Start-Sleep -Seconds 2

# Verify port is free
$stillListening = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($stillListening) {
    Write-Host "ERROR: Port 8000 is still in use!" -ForegroundColor Red
    exit 1
}

Write-Host "Port 8000 is free" -ForegroundColor Green

# Set environment variables
$env:DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
$env:SECRET_KEY = "dev-secret"
$env:JWT_SECRET_KEY = "dev-jwt"
$env:DEV_SKIP_AUTH = "true"

Write-Host "Starting server on http://localhost:8000 ..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
Write-Host ""

# Start uvicorn
uvicorn app:app --reload --host 0.0.0.0 --port 8000
