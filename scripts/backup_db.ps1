# ============================================
# Kinyan CRM - Database Backup Script
# ============================================
# Usage:
#   .\scripts\backup_db.ps1              # גיבוי רגיל
#   .\scripts\backup_db.ps1 -KeepDays 30 # שמור 30 ימים (ברירת מחדל: 14)
#
# To schedule automatic daily backup:
#   1. Open Task Scheduler (taskschd.msc)
#   2. Create Basic Task > "Kinyan DB Backup"
#   3. Trigger: Daily at 03:00
#   4. Action: Start a program
#      Program: powershell.exe
#      Arguments: -ExecutionPolicy Bypass -File "C:\Users\משתמש\Documents\Downloads\kinyan-crm-new-main\kinyan-crm-new-main\scripts\backup_db.ps1"
#      Start in: C:\Users\משתמש\Documents\Downloads\kinyan-crm-new-main\kinyan-crm-new-main
# ============================================

param(
    [int]$KeepDays = 14
)

$ErrorActionPreference = "Stop"

# --- Config ---
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BACKUP_DIR = Join-Path $PROJECT_ROOT "backups"
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd_HHmm"
$BACKUP_FILE = Join-Path $BACKUP_DIR "kinyan_crm_$TIMESTAMP.dump"
$LOG_FILE = Join-Path $BACKUP_DIR "backup.log"

# Load DB URL from .env
$envFile = Join-Path $PROJECT_ROOT ".env"
if (-not (Test-Path $envFile)) {
    Write-Error "ERROR: .env file not found at $envFile"
    exit 1
}

$DB_URL = ""
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^DATABASE_URL=(.+)$") {
        $DB_URL = $Matches[1].Trim()
    }
}

if (-not $DB_URL) {
    Write-Error "ERROR: DATABASE_URL not found in .env"
    exit 1
}

# Convert asyncpg URL to regular psycopg format for pg_dump
$PG_URL = $DB_URL -replace "postgresql\+asyncpg://", "postgresql://"

# --- Create backup dir ---
if (-not (Test-Path $BACKUP_DIR)) {
    New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
    Write-Host "[+] Created backup directory: $BACKUP_DIR"
}

# --- Check pg_dump exists ---
$pgDump = Get-Command pg_dump -ErrorAction SilentlyContinue
if (-not $pgDump) {
    # Try common PostgreSQL install paths
    $pgPaths = @(
        "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
        "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
    )
    foreach ($p in $pgPaths) {
        if (Test-Path $p) {
            $pgDump = $p
            break
        }
    }
    if (-not $pgDump) {
        Write-Error @"
ERROR: pg_dump not found!
Install PostgreSQL client tools:
  https://www.postgresql.org/download/windows/
  (choose 'Command Line Tools' only during install)
"@
        exit 1
    }
}

# --- Run backup ---
$startTime = Get-Date
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Kinyan CRM - Database Backup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[*] Time: $TIMESTAMP"
Write-Host "[*] Target: $BACKUP_FILE"
Write-Host "[*] Running pg_dump..." -ForegroundColor Yellow

try {
    if ($pgDump -is [string]) {
        & $pgDump $PG_URL --format=custom --file="$BACKUP_FILE" --no-owner --no-privileges 2>&1
    } else {
        & $pgDump.Source $PG_URL --format=custom --file="$BACKUP_FILE" --no-owner --no-privileges 2>&1
    }

    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed with exit code $LASTEXITCODE"
    }

    $fileSize = (Get-Item $BACKUP_FILE).Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
    $duration = (Get-Date) - $startTime

    $logEntry = "$TIMESTAMP | SUCCESS | ${fileSizeMB}MB | $([math]::Round($duration.TotalSeconds, 1))s"
    Add-Content -Path $LOG_FILE -Value $logEntry

    Write-Host "[+] Backup completed successfully!" -ForegroundColor Green
    Write-Host "    Size: ${fileSizeMB}MB"
    Write-Host "    Duration: $([math]::Round($duration.TotalSeconds, 1))s"

} catch {
    $logEntry = "$TIMESTAMP | FAILED | $($_.Exception.Message)"
    Add-Content -Path $LOG_FILE -Value $logEntry
    Write-Host "[!] Backup FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# --- Cleanup old backups ---
$cutoff = (Get-Date).AddDays(-$KeepDays)
$oldFiles = Get-ChildItem -Path $BACKUP_DIR -Filter "kinyan_crm_*.dump" | Where-Object { $_.LastWriteTime -lt $cutoff }

if ($oldFiles.Count -gt 0) {
    Write-Host "[*] Cleaning up $($oldFiles.Count) backups older than $KeepDays days..." -ForegroundColor Yellow
    $oldFiles | Remove-Item -Force
    Write-Host "[+] Cleanup done." -ForegroundColor Green
}

# --- Summary ---
$allBackups = Get-ChildItem -Path $BACKUP_DIR -Filter "kinyan_crm_*.dump" | Sort-Object LastWriteTime -Descending
$totalSizeMB = [math]::Round(($allBackups | Measure-Object -Property Length -Sum).Sum / 1MB, 2)

Write-Host ""
Write-Host "--- Backup Summary ---" -ForegroundColor Cyan
Write-Host "  Total backups: $($allBackups.Count)"
Write-Host "  Total size: ${totalSizeMB}MB"
Write-Host "  Retention: $KeepDays days"
Write-Host "  Latest: $($allBackups[0].Name)"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
