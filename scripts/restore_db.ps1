# ============================================
# Kinyan CRM - Database Restore Script
# ============================================
# Usage:
#   .\scripts\restore_db.ps1                          # shows list of backups to choose from
#   .\scripts\restore_db.ps1 -BackupFile "backups\kinyan_crm_2025-02-12_0300.dump"
# ============================================

param(
    [string]$BackupFile = ""
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BACKUP_DIR = Join-Path $PROJECT_ROOT "backups"

# --- If no file specified, show available backups ---
if (-not $BackupFile) {
    $backups = Get-ChildItem -Path $BACKUP_DIR -Filter "kinyan_crm_*.dump" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending

    if ($backups.Count -eq 0) {
        Write-Host "No backups found in $BACKUP_DIR" -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "Available backups:" -ForegroundColor Cyan
    Write-Host "-------------------"
    for ($i = 0; $i -lt $backups.Count; $i++) {
        $sizeMB = [math]::Round($backups[$i].Length / 1MB, 2)
        Write-Host "  [$($i+1)] $($backups[$i].Name)  (${sizeMB}MB, $($backups[$i].LastWriteTime.ToString('dd/MM/yyyy HH:mm')))"
    }
    Write-Host ""

    $choice = Read-Host "Enter backup number to restore (or 'q' to quit)"
    if ($choice -eq 'q') { exit 0 }

    $idx = [int]$choice - 1
    if ($idx -lt 0 -or $idx -ge $backups.Count) {
        Write-Host "Invalid choice." -ForegroundColor Red
        exit 1
    }

    $BackupFile = $backups[$idx].FullName
}

if (-not (Test-Path $BackupFile)) {
    Write-Error "Backup file not found: $BackupFile"
    exit 1
}

# --- Load DB URL ---
$envFile = Join-Path $PROJECT_ROOT ".env"
$DB_URL = ""
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^DATABASE_URL=(.+)$") {
        $DB_URL = $Matches[1].Trim()
    }
}
$PG_URL = $DB_URL -replace "postgresql\+asyncpg://", "postgresql://"

# --- Confirm ---
Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host "  WARNING: DATABASE RESTORE" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host "  File: $(Split-Path -Leaf $BackupFile)"
Write-Host "  This will OVERWRITE the current database!"
Write-Host ""

$confirm = Read-Host "Type 'RESTORE' to confirm"
if ($confirm -ne "RESTORE") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

# --- Find pg_restore ---
$pgRestore = Get-Command pg_restore -ErrorAction SilentlyContinue
if (-not $pgRestore) {
    $pgPaths = @(
        "C:\Program Files\PostgreSQL\16\bin\pg_restore.exe",
        "C:\Program Files\PostgreSQL\15\bin\pg_restore.exe",
        "C:\Program Files\PostgreSQL\14\bin\pg_restore.exe",
        "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe"
    )
    foreach ($p in $pgPaths) {
        if (Test-Path $p) { $pgRestore = $p; break }
    }
    if (-not $pgRestore) {
        Write-Error "pg_restore not found! Install PostgreSQL client tools."
        exit 1
    }
}

# --- Restore ---
Write-Host "[*] Restoring database..." -ForegroundColor Yellow

try {
    if ($pgRestore -is [string]) {
        & $pgRestore --clean --if-exists --no-owner --no-privileges -d $PG_URL $BackupFile 2>&1
    } else {
        & $pgRestore.Source --clean --if-exists --no-owner --no-privileges -d $PG_URL $BackupFile 2>&1
    }

    Write-Host "[+] Database restored successfully!" -ForegroundColor Green
} catch {
    Write-Host "[!] Restore failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
