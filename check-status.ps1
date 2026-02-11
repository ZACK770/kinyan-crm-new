# ============================================================
# Check Status - בדיקת סטטוס מהירה של המערכת
# ============================================================
# בודק מה רץ, מה עדכני, ומה צריך תשומת לב
# 
# שימוש: .\check-status.ps1
# ============================================================

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   📊 סטטוס מערכת - Kinyan CRM" -ForegroundColor White
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# בדיקת שרתים פעילים
# ============================================================
Write-Host "🖥️  שרתים פעילים:" -ForegroundColor Cyan
Write-Host ""

$ports = @(8000, 8001, 3000, 5173)
$foundServers = $false

foreach ($port in $ports) {
    $connection = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connection) {
        $pid = $connection.OwningProcess
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "  ✅ פורט $port - $($process.ProcessName) (PID: $pid)" -ForegroundColor Green
            $foundServers = $true
        }
    }
}

if (-not $foundServers) {
    Write-Host "  ⚠️  אין שרתים פעילים" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================
# בדיקת מצב פרונטאנד
# ============================================================
Write-Host "🎨 פרונטאנד:" -ForegroundColor Cyan
Write-Host ""

$frontendDir = Join-Path $PSScriptRoot "frontend"
$distDir = Join-Path $frontendDir "dist"
$srcDir = Join-Path $frontendDir "src"

if (Test-Path $distDir) {
    $distTime = (Get-ChildItem $distDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    $srcTime = (Get-ChildItem $srcDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    
    $age = (Get-Date) - $distTime
    $ageText = if ($age.TotalHours -lt 1) {
        "$([math]::Round($age.TotalMinutes)) דקות"
    } elseif ($age.TotalDays -lt 1) {
        "$([math]::Round($age.TotalHours)) שעות"
    } else {
        "$([math]::Round($age.TotalDays)) ימים"
    }
    
    if ($srcTime -gt $distTime) {
        Write-Host "  ⚠️  יש שינויים שלא נבנו!" -ForegroundColor Yellow
        Write-Host "     בנייה אחרונה: לפני $ageText" -ForegroundColor Gray
        Write-Host "     הרץ: .\smart-dev.ps1 --Force" -ForegroundColor Gray
    } else {
        Write-Host "  ✅ הפרונטאנד עדכני" -ForegroundColor Green
        Write-Host "     בנייה אחרונה: לפני $ageText" -ForegroundColor Gray
    }
} else {
    Write-Host "  ❌ הפרונטאנד לא נבנה" -ForegroundColor Red
    Write-Host "     הרץ: .\smart-dev.ps1" -ForegroundColor Gray
}

Write-Host ""

# ============================================================
# בדיקת virtual environment
# ============================================================
Write-Host "🐍 Python Environment:" -ForegroundColor Cyan
Write-Host ""

if (Test-Path ".\.venv311") {
    Write-Host "  ✅ Virtual environment קיים (.venv311)" -ForegroundColor Green
} elseif (Test-Path ".\venv") {
    Write-Host "  ✅ Virtual environment קיים (venv)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Virtual environment לא נמצא" -ForegroundColor Yellow
}

# בדיקת Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ❌ Python לא מותקן או לא בנתיב" -ForegroundColor Red
}

Write-Host ""

# ============================================================
# בדיקת תלויות
# ============================================================
Write-Host "📦 תלויות:" -ForegroundColor Cyan
Write-Host ""

# Node modules
if (Test-Path "$frontendDir\node_modules") {
    $nodeModulesSize = (Get-ChildItem "$frontendDir\node_modules" -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "  ✅ Node modules מותקנים ($([math]::Round($nodeModulesSize)) MB)" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Node modules לא מותקנים" -ForegroundColor Yellow
    Write-Host "     הרץ: cd frontend && npm install" -ForegroundColor Gray
}

Write-Host ""

# ============================================================
# בדיקת קבצי קונפיגורציה
# ============================================================
Write-Host "⚙️  קונפיגורציה:" -ForegroundColor Cyan
Write-Host ""

$configFiles = @(
    @{Path=".env"; Required=$false},
    @{Path="alembic.ini"; Required=$true},
    @{Path="requirements.txt"; Required=$true},
    @{Path="frontend\package.json"; Required=$true}
)

foreach ($file in $configFiles) {
    if (Test-Path $file.Path) {
        Write-Host "  ✅ $($file.Path)" -ForegroundColor Green
    } else {
        if ($file.Required) {
            Write-Host "  ❌ $($file.Path) חסר!" -ForegroundColor Red
        } else {
            Write-Host "  ⚠️  $($file.Path) לא קיים (אופציונלי)" -ForegroundColor Yellow
        }
    }
}

Write-Host ""

# ============================================================
# המלצות
# ============================================================
Write-Host "💡 המלצות:" -ForegroundColor Cyan
Write-Host ""

$recommendations = @()

if (-not $foundServers) {
    $recommendations += "להפעיל את השרת: .\smart-dev.ps1"
}

if ((Test-Path $distDir) -and (Test-Path $srcDir)) {
    $distTime = (Get-ChildItem $distDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    $srcTime = (Get-ChildItem $srcDir -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1).LastWriteTime
    if ($srcTime -gt $distTime) {
        $recommendations += "לבנות את הפרונטאנד: .\smart-dev.ps1 --Force"
    }
}

if (-not (Test-Path "$frontendDir\node_modules")) {
    $recommendations += "להתקין תלויות: cd frontend && npm install"
}

if ($recommendations.Count -eq 0) {
    Write-Host "  ✅ הכל נראה תקין!" -ForegroundColor Green
} else {
    foreach ($rec in $recommendations) {
        Write-Host "  • $rec" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""
