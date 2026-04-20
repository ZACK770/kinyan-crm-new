# Quick test script for workspace fixes
# Usage: .\scripts\test-workspace-fixes.ps1 [--local]

param(
    [switch]$Local
)

$ErrorActionPreference = "Continue"

# Configuration
if ($Local) {
    $BaseUrl = "http://localhost:8000"
    Write-Host "🏠 Testing LOCAL server" -ForegroundColor Yellow
} else {
    $BaseUrl = "https://kinyan-crm-new-1.onrender.com"
    Write-Host "🌐 Testing PRODUCTION server" -ForegroundColor Yellow
}

Write-Host "🎯 Target: $BaseUrl" -ForegroundColor Cyan
Write-Host ""

# Get auth token
$AuthToken = $env:AUTH_TOKEN
if (-not $AuthToken) {
    $AuthToken = Read-Host "Enter auth token (or press Enter to skip)"
}

$Headers = @{
    "Content-Type" = "application/json"
}
if ($AuthToken) {
    $Headers["Authorization"] = "Bearer $AuthToken"
}

function Test-Endpoint {
    param($Method, $Url, $Body = $null, $Description)
    
    Write-Host "🔧 $Description..." -ForegroundColor Blue
    
    try {
        $params = @{
            Uri = "$BaseUrl$Url"
            Method = $Method
            Headers = $Headers
            TimeoutSec = 30
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "✅ SUCCESS: $Description" -ForegroundColor Green
        return $response
    }
    catch {
        Write-Host "❌ FAILED: $Description" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "   Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        }
        return $null
    }
}

# Test 1: Authentication
Write-Host "=" * 50
Write-Host "TEST 1: Authentication" -ForegroundColor Magenta
$user = Test-Endpoint "GET" "/api/auth/me" -Description "Auth check"
if (-not $user) {
    Write-Host "❌ Cannot continue without authentication" -ForegroundColor Red
    exit 1
}
Write-Host "👤 Logged in as: $($user.full_name) (level: $($user.permission_level))" -ForegroundColor Green

# Test 2: Get a test lead
Write-Host ""
Write-Host "=" * 50
Write-Host "TEST 2: Get Test Lead" -ForegroundColor Magenta
$leads = Test-Endpoint "GET" "/api/leads?limit=1" -Description "Get first lead"
if (-not $leads -or $leads.Count -eq 0) {
    Write-Host "❌ No leads found for testing" -ForegroundColor Red
    exit 1
}
$testLead = $leads[0]
$leadId = $testLead.id
Write-Host "🎯 Test lead: $($testLead.full_name) (ID: $leadId)" -ForegroundColor Green

# Test 3: Debug endpoint
Write-Host ""
Write-Host "=" * 50
Write-Host "TEST 3: Debug Endpoint" -ForegroundColor Magenta
$debugData = Test-Endpoint "GET" "/api/leads/$leadId/debug" -Description "Debug endpoint"
if ($debugData) {
    Write-Host "📊 Debug Summary:" -ForegroundColor Cyan
    Write-Host "   Status: $($debugData.debug_summary.status)" -ForegroundColor White
    Write-Host "   Salesperson: $($debugData.debug_summary.salesperson_name)" -ForegroundColor White
    Write-Host "   Course: $($debugData.debug_summary.course_name)" -ForegroundColor White
}

# Test 4: Field updates (the main fix)
Write-Host ""
Write-Host "=" * 50
Write-Host "TEST 4: Field Updates (500 Error Fix)" -ForegroundColor Magenta

$timestamp = Get-Date -Format "HH:mm:ss"

# Test the problematic id_number field that caused 500
$testFields = @(
    @{ field = "id_number"; value = "123456789"; desc = "ID Number (original 500 cause)" }
    @{ field = "notes"; value = "Test note $timestamp"; desc = "Notes field" }
    @{ field = "status"; value = "ליד בתהליך"; desc = "Status field (triggers last_edited_at)" }
    @{ field = "family_name"; value = "טסט-$timestamp"; desc = "Family name with Hebrew" }
)

$successCount = 0
foreach ($test in $testFields) {
    $body = @{ }
    $body[$test.field] = $test.value
    $result = Test-Endpoint "PATCH" "/api/leads/$leadId" $body -Description $test.desc
    
    if ($result) {
        $successCount++
        Write-Host "   ✓ Field '$($test.field)' updated to: $($result.($test.field))" -ForegroundColor Green
        
        # Check for timestamp fields (proof that db.refresh worked)
        if ($result.updated_at) {
            Write-Host "   ✓ updated_at present: $($result.updated_at)" -ForegroundColor Green
        }
        if ($result.last_edited_at) {
            Write-Host "   ✓ last_edited_at present: $($result.last_edited_at)" -ForegroundColor Green
        }
    }
    
    Start-Sleep -Milliseconds 500
}

# Test 5: Verify no 500 errors in rapid succession
Write-Host ""
Write-Host "=" * 50
Write-Host "TEST 5: Rapid Updates (No 500 Check)" -ForegroundColor Magenta

$rapidTests = 1..3 | ForEach-Object {
    $body = @{ notes = "Rapid test $_ at $timestamp" }
    Test-Endpoint "PATCH" "/api/leads/$leadId" $body -Description "Rapid update $_"
}
$rapidSuccessCount = ($rapidTests | Where-Object { $_ -ne $null }).Count

# Summary
Write-Host ""
Write-Host "=" * 80
Write-Host "📊 TEST SUMMARY" -ForegroundColor Magenta
Write-Host "=" * 80

Write-Host "✅ Authentication: PASSED" -ForegroundColor Green
Write-Host "✅ Test Lead Found: PASSED" -ForegroundColor Green

if ($debugData) {
    Write-Host "✅ Debug Endpoint: PASSED" -ForegroundColor Green
} else {
    Write-Host "❌ Debug Endpoint: FAILED" -ForegroundColor Red
}

Write-Host "🔧 Field Updates: $successCount/$($testFields.Count) PASSED" -ForegroundColor $(if ($successCount -eq $testFields.Count) { "Green" } else { "Yellow" })
Write-Host "⚡ Rapid Updates: $rapidSuccessCount/3 PASSED" -ForegroundColor $(if ($rapidSuccessCount -eq 3) { "Green" } else { "Yellow" })

$totalTests = 5
$passedTests = 2 + $(if ($debugData) { 1 } else { 0 }) + $(if ($successCount -eq $testFields.Count) { 1 } else { 0 }) + $(if ($rapidSuccessCount -eq 3) { 1 } else { 0 })

Write-Host ""
if ($passedTests -eq $totalTests) {
    Write-Host "🎉 ALL TESTS PASSED! Workspace fixes are working correctly." -ForegroundColor Green
    Write-Host "✅ The 500 error has been fixed" -ForegroundColor Green
    Write-Host "✅ Field updates work without refresh needed" -ForegroundColor Green
} else {
    Write-Host "⚠️ $($totalTests - $passedTests) test(s) failed. Check output above." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🔗 Useful URLs:" -ForegroundColor Cyan
Write-Host "   Swagger UI: $BaseUrl/docs" -ForegroundColor White
Write-Host "   Debug endpoint: $BaseUrl/api/leads/$leadId/debug" -ForegroundColor White
Write-Host "   Lead workspace: $BaseUrl/leads (click on lead $leadId)" -ForegroundColor White
