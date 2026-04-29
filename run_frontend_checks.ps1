# Comprehensive frontend testing script
# Runs build, type checking, and circular dependency detection

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FRONTEND COMPREHENSIVE TEST SUITE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$frontendDir = "frontend"
$hasError = $false

# Check if frontend directory exists
if (-not (Test-Path $frontendDir)) {
    Write-Host "[ERROR] Frontend directory not found: $frontendDir" -ForegroundColor Red
    exit 1
}

# Change to frontend directory
Push-Location $frontendDir

# Test 1: npm install (if needed)
Write-Host "[TEST 1] Checking dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "  Installing dependencies..."
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed" -ForegroundColor Red
        $hasError = $true
    } else {
        Write-Host "[OK] Dependencies installed" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] Dependencies already installed" -ForegroundColor Green
}
Write-Host ""

# Test 2: TypeScript type checking
Write-Host "[TEST 2] TypeScript type checking..." -ForegroundColor Yellow
if (Test-Path "tsconfig.json") {
    npx tsc --noEmit
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] No TypeScript errors" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] TypeScript errors found" -ForegroundColor Red
        $hasError = $true
    }
} else {
    Write-Host "[SKIP] No tsconfig.json found" -ForegroundColor Gray
}
Write-Host ""

# Test 3: Build
Write-Host "[TEST 3] Production build..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Build successful" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    $hasError = $true
}
Write-Host ""

# Return to parent directory
Pop-Location

# Test 4: Circular dependency check
Write-Host "[TEST 4] Circular dependency detection..." -ForegroundColor Yellow
if (Test-Path "check_circular_deps.ps1") {
    powershell -ExecutionPolicy Bypass -File check_circular_deps.ps1
    # The script itself reports errors
} else {
    Write-Host "[SKIP] check_circular_deps.ps1 not found" -ForegroundColor Gray
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($hasError) {
    Write-Host "[FAIL] Some tests failed. Please review the errors above." -ForegroundColor Red
    exit 1
} else {
    Write-Host "[SUCCESS] All tests passed!" -ForegroundColor Green
    exit 0
}
