# Run RAGIL payment test
$env:DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
$env:NEDARIM_API_URL = "https://matara.pro/api"
$env:NEDARIM_API_KEY = "ou946"
$env:NEDARIM_MOSAD_ID = "7009959"
$env:NEDARIM_API_PASSWORD = "ou946"

$pythonPath = Join-Path (Join-Path (Split-Path $PSScriptRoot) ".venv311\Scripts") "python.exe"
& $pythonPath scripts\test_payment_ragil.py
