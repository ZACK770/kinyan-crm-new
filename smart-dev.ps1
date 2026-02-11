# ============================================================
# Smart Dev Script - הרצה חכמה של סביבת פיתוח
# ============================================================
# סקריפט חכם שמטפל בכל מה שצריך:
#   1. בודק אם השרת כבר רץ
#   2. בונה את הפרונטאנד רק אם יש שינויים
#   3. מריץ את השרת אם צריך
#   4. מציג סטטוס ברור
# 
# שימוש: .\smart-dev.ps1
# ============================================================

param(
    [switch]$Force,        # אילוץ בנייה מחדש
    [switch]$SkipBuild,    # דילוג על בנייה
    [int]$Port = 8001      # פורט (ברירת מחדל 8001)
)

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   🚀 Smart Dev - Kinyan CRM" -ForegroundColor White
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# שלב 1: בדיקה אם השרת כבר רץ
# ============================================================
Write-Host "[1/4] בדיקת שרת קיים..." -ForegroundColor Cyan

$serverRunning = $false
$existingProcess = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

if ($existingProcess) {
    $pid = $existingProcess.OwningProcess
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    
    if ($process) {
        Write-Host "✅ שרת כבר רץ על פורט $Port (PID: $pid)" -ForegroundColor Green
        Write-Host "   תהליך: $($process.ProcessName)" -ForegroundColor Gray
        Write-Host ""
        
        $response = Read-Host "האם לעצור ולהפעיל מחדש? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Write-Host "   עוצר תהליך $pid..." -ForegroundColor Yellow
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
        } else {
            Write-Host ""
            Write-Host "🌐 השרת זמין ב:" -ForegroundColor Green
            Write-Host "   App:     http://localhost:$Port" -ForegroundColor White
            Write-Host "   API:     http://localhost:$Port/api/" -ForegroundColor White
            Write-Host "   Docs:    http://localhost:$Port/docs" -ForegroundColor White
            Write-Host ""
            exit 0
        }
    }
}

Write-Host "✅ פורט $Port פנוי" -ForegroundColor Green
Write-Host ""

# ============================================================
# שלב 2: בדיקת שינויים בפרונטאנד
# ============================================================
Write-Host "[2/4] בדיקת פרונטאנד..." -ForegroundColor Cyan

$frontendDir = Join-Path $PSScriptRoot "frontend"
$distDir = Join-Path $frontendDir "dist"
$srcDir = Join-Path $frontendDir "src"
$needsBuild = $false

if (-not (Test-Path $distDir)) {
    Write-Host "⚠️  תיקיית dist לא קיימת - נדרשת בנייה" -ForegroundColor Yellow
    $needsBuild = $true
} elseif ($Force) {
    Write-Host "🔨 אילוץ בנייה מחדש (--Force)" -ForegroundColor Yellow
    $needsBuild = $true
} elseif (-not $SkipBuild) {
    # בדיקת תאריך שינוי אחרון
    $distTime = (Get-ChildItem $distDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    $srcTime = (Get-ChildItem $srcDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    
    if ($srcTime -gt $distTime) {
        Write-Host "⚠️  נמצאו שינויים בקוד המקור - נדרשת בנייה" -ForegroundColor Yellow
        $needsBuild = $true
    } else {
        Write-Host "✅ הפרונטאנד עדכני (אין שינויים)" -ForegroundColor Green
    }
}

Write-Host ""

# ============================================================
# שלב 3: בניית פרונטאנד (אם נדרש)
# ============================================================
if ($needsBuild -and -not $SkipBuild) {
    Write-Host "[3/4] בונה פרונטאנד..." -ForegroundColor Cyan
    Write-Host ""
    
    Push-Location $frontendDir
    
    # בדיקת node_modules
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 מתקין תלויות..." -ForegroundColor Yellow
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ שגיאה בהתקנת תלויות" -ForegroundColor Red
            Pop-Location
            exit 1
        }
    }
    
    # בנייה
    Write-Host "🔨 בונה..." -ForegroundColor Yellow
    npm run build
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ בנייה הושלמה בהצלחה!" -ForegroundColor Green
    } else {
        Write-Host "❌ שגיאה בבנייה" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host ""
} else {
    Write-Host "[3/4] דילוג על בנייה" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================
# שלב 4: הפעלת שרת
# ============================================================
Write-Host "[4/4] מפעיל שרת..." -ForegroundColor Cyan
Write-Host ""

# הגדרת משתני סביבה
$env:DATABASE_URL = "postgresql+asyncpg://crm_new_user:45RsFRWnUuvPQFAttG37PxisVlC79HZv@dpg-d65jjr56ubrc7396u8r0-a.frankfurt-postgres.render.com/crm_new"
$env:SECRET_KEY = "dev-local-secret-key-change-in-production"
$env:API_KEY = "dev-webhook-key"
$env:JWT_SECRET_KEY = "dev-jwt-secret-key-change-in-production"
$env:JWT_ALGORITHM = "HS256"
$env:JWT_EXPIRATION_MINUTES = "1440"
$env:FRONTEND_URL = "http://localhost:$Port"
$env:DEV_SKIP_AUTH = "true"

# Google OAuth
$env:GOOGLE_CLIENT_ID = "638402661079-pjfnm1g84il9uvj9vtgh4v5jqj6uk1gi.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "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"
$env:GOOGLE_REDIRECT_URI = "http://localhost:$Port/api/auth/google/callback"

# הפעלת virtual environment אם קיים
if (Test-Path ".\.venv311\Scripts\Activate.ps1") {
    & .\.venv311\Scripts\Activate.ps1
} elseif (Test-Path ".\venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
}

# הרצת migrations
Write-Host "🗄️  מריץ migrations..." -ForegroundColor Cyan
alembic upgrade head 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations הושלמו" -ForegroundColor Green
} else {
    Write-Host "⚠️  Migrations warning (ייתכן שכבר עדכני)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   ✨ השרת מוכן!" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   🌐 App:     http://localhost:$Port" -ForegroundColor White
Write-Host "   📡 API:     http://localhost:$Port/api/" -ForegroundColor White
Write-Host "   📚 Docs:    http://localhost:$Port/docs" -ForegroundColor White
Write-Host "   💚 Health:  http://localhost:$Port/health" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "לחץ Ctrl+C לעצירה" -ForegroundColor Gray
Write-Host ""

# הפעלת השרת
uvicorn app:app --reload --host 0.0.0.0 --port $Port
