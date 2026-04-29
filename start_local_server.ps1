# Start local development server on port 7000 with all required environment variables

$env:DEV_SKIP_AUTH = "true"
$env:DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
$env:SECRET_KEY = "dev-local-secret-key-change-in-production"
$env:API_KEY = "dev-webhook-key"
$env:JWT_SECRET_KEY = "dev-jwt-secret-key-change-in-production"
$env:JWT_ALGORITHM = "HS256"
$env:JWT_EXPIRATION_MINUTES = "1440"
$env:FRONTEND_URL = "http://localhost:7000"
$env:GOOGLE_CLIENT_ID = "638402661079-pjfnm1g84il9uvj9vtgh4v5jqj6uk1gi.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "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"
$env:GOOGLE_REDIRECT_URI = "http://localhost:7000/api/auth/google/callback"

Write-Host "[START] Starting development server on port 7000" -ForegroundColor Cyan
Write-Host "[INFO] Environment variables set" -ForegroundColor Green
Write-Host "[INFO] Database: frankfurt-postgres.render.com" -ForegroundColor Green
Write-Host ""

.\venv\Scripts\python.exe -m uvicorn app:app --reload --host 0.0.0.0 --port 7000
