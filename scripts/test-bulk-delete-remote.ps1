# Remote Bulk Delete Test Script
# Tests the bulk delete functionality on the remote Kinyan CRM server

param(
    [Parameter(Mandatory=$true)]
    [string]$Email,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [string]$ServerUrl = "https://kinyan-crm-new-1.onrender.com"
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting remote bulk delete test..." -ForegroundColor Green
Write-Host "🌐 Target server: $ServerUrl" -ForegroundColor Cyan

# Step 1: Login and get token
Write-Host "`n🔐 Logging in..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $Email
        password = $Password
    }
    
    $loginResponse = Invoke-RestMethod -Uri "$ServerUrl/api/auth/login" -Method Post -Body $loginBody -ContentType "application/x-www-form-urlencoded"
    $token = $loginResponse.access_token
    
    if (-not $token) {
        throw "No access token received"
    }
    
    Write-Host "✅ Login successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Headers for authenticated requests
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Step 2: Test endpoint availability
Write-Host "`n📡 Testing endpoint availability..." -ForegroundColor Yellow
try {
    $testBody = @{ ids = @() } | ConvertTo-Json
    $testResponse = Invoke-WebRequest -Uri "$ServerUrl/api/leads/bulk-delete" -Method Post -Headers $headers -Body $testBody -ErrorAction SilentlyContinue
    
    if ($testResponse.StatusCode -eq 405) {
        Write-Host "❌ Endpoint returns 405 Method Not Allowed - endpoint missing!" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "✅ Endpoint exists and responds (Status: $($testResponse.StatusCode))" -ForegroundColor Green
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 405) {
        Write-Host "❌ Endpoint returns 405 Method Not Allowed - endpoint missing!" -ForegroundColor Red
        exit 1
    } else {
        Write-Host "✅ Endpoint exists (got expected error: $($_.Exception.Response.StatusCode))" -ForegroundColor Green
    }
}

# Step 3: Create test leads
Write-Host "`n🏗️ Creating test leads..." -ForegroundColor Yellow
$testLeadIds = @()

for ($i = 1; $i -le 3; $i++) {
    try {
        $leadData = @{
            full_name = "Test Lead $i - DELETE ME"
            phone = "050000000$i"
            email = "test$i@delete.me"
            source_type = "test"
            source_name = "bulk_delete_test"
            notes = "Created by remote debugging script - safe to delete"
        } | ConvertTo-Json
        
        $createResponse = Invoke-RestMethod -Uri "$ServerUrl/api/leads/" -Method Post -Headers $headers -Body $leadData
        
        if ($createResponse.lead_id) {
            $testLeadIds += $createResponse.lead_id
            Write-Host "✅ Created test lead #$($createResponse.lead_id): Test Lead $i" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Lead created but no ID returned: $($createResponse | ConvertTo-Json)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ Failed to create test lead $i`: $($_.Exception.Message)" -ForegroundColor Red
    }
}

if ($testLeadIds.Count -eq 0) {
    Write-Host "❌ No test leads created. Cannot proceed with bulk delete test." -ForegroundColor Red
    exit 1
}

Write-Host "📋 Created $($testLeadIds.Count) test leads: $($testLeadIds -join ', ')" -ForegroundColor Cyan

# Step 4: Test bulk delete
Write-Host "`n🗑️ Testing bulk delete..." -ForegroundColor Yellow
try {
    $deleteData = @{ ids = $testLeadIds } | ConvertTo-Json
    
    Write-Host "📤 Sending bulk delete request with IDs: $($testLeadIds -join ', ')" -ForegroundColor Cyan
    
    $deleteResponse = Invoke-RestMethod -Uri "$ServerUrl/api/leads/bulk-delete" -Method Post -Headers $headers -Body $deleteData
    
    Write-Host "✅ Bulk delete API call successful" -ForegroundColor Green
    Write-Host "📊 Delete result: $($deleteResponse | ConvertTo-Json -Depth 3)" -ForegroundColor Cyan
    
    if ($deleteResponse.success) {
        Write-Host "✅ Server reports successful deletion of $($deleteResponse.deleted_count) leads" -ForegroundColor Green
    } else {
        Write-Host "❌ Server reports deletion failed: $($deleteResponse.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Bulk delete failed: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "📡 HTTP Status: $statusCode" -ForegroundColor Red
        
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "📡 Error body: $errorBody" -ForegroundColor Red
        } catch {
            Write-Host "📡 Could not read error response body" -ForegroundColor Red
        }
    }
    
    # Still try to verify if leads were deleted
}

# Step 5: Verify deletion
Write-Host "`n🔍 Verifying deletion..." -ForegroundColor Yellow
$verificationResults = @{}
$allDeleted = $true

foreach ($leadId in $testLeadIds) {
    try {
        $verifyResponse = Invoke-WebRequest -Uri "$ServerUrl/api/leads/$leadId" -Method Get -Headers $headers -ErrorAction SilentlyContinue
        
        if ($verifyResponse.StatusCode -eq 200) {
            $verificationResults[$leadId] = "still_exists"
            $allDeleted = $false
            Write-Host "❌ Lead #$leadId still exists!" -ForegroundColor Red
        } else {
            $verificationResults[$leadId] = "unknown_status_$($verifyResponse.StatusCode)"
            Write-Host "⚠️ Lead #$leadId verification returned $($verifyResponse.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            $verificationResults[$leadId] = "deleted"
            Write-Host "✅ Lead #$leadId confirmed deleted (404)" -ForegroundColor Green
        } else {
            $verificationResults[$leadId] = "error_$($_.Exception.Response.StatusCode.value__)"
            Write-Host "❌ Error verifying lead #$leadId`: $($_.Exception.Message)" -ForegroundColor Red
            $allDeleted = $false
        }
    }
}

# Summary
Write-Host "`n📊 Test Summary:" -ForegroundColor Cyan
Write-Host "   Test Lead IDs: $($testLeadIds -join ', ')" -ForegroundColor White
Write-Host "   All Leads Deleted: $allDeleted" -ForegroundColor $(if ($allDeleted) { "Green" } else { "Red" })

if ($allDeleted) {
    Write-Host "`n🎉 All tests passed! Bulk delete is working correctly." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n💥 Tests failed! Some leads were not deleted properly." -ForegroundColor Red
    Write-Host "Verification results:" -ForegroundColor Yellow
    foreach ($kvp in $verificationResults.GetEnumerator()) {
        Write-Host "   Lead #$($kvp.Key): $($kvp.Value)" -ForegroundColor White
    }
    exit 1
}
