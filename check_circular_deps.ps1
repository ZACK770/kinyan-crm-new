# Script to detect circular dependencies in useCallback hooks
# This helps prevent "Cannot access X before initialization" errors

$frontendSrc = "frontend\src"
$pattern = "useCallback"

Write-Host "[START] Scanning for useCallback patterns..." -ForegroundColor Cyan

# Find all .tsx and .ts files
$files = Get-ChildItem -Path $frontendSrc -Include "*.tsx", "*.ts" -Recurse

$results = @()

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    
    # Find all useCallback declarations
    $useCallbackMatches = [regex]::Matches($content, 'const\s+(\w+)\s*=\s*useCallback\s*\(')
    
    if ($useCallbackMatches.Count -gt 0) {
        $fileResults = @{
            File = $file.FullName
            Functions = @()
        }
        
        foreach ($match in $useCallbackMatches) {
            $funcName = $match.Groups[1].Value
            
            # Find the dependency array for this useCallback
            # Look for the closing bracket of useCallback and the dependency array
            $startIndex = $match.Index
            $bracketCount = 0
            $inParentheses = $false
            $depArrayStart = -1
            $depArrayEnd = -1
            
            for ($i = $startIndex; $i -lt $content.Length; $i++) {
                $char = $content[$i]
                
                if ($char -eq '(') {
                    $bracketCount++
                    $inParentheses = $true
                } elseif ($char -eq ')') {
                    $bracketCount--
                    if ($bracketCount -eq 0 -and $inParentheses) {
                        # Found the end of useCallback function body
                        # Now look for dependency array
                        $remaining = $content.Substring($i + 1)
                        $depMatch = [regex]::Match($remaining, '\s*,\s*\[\s*([^\]]*)\s*\]')
                        
                        if ($depMatch.Success) {
                            $depsString = $depMatch.Groups[1].Value
                            $deps = $depsString -split '\s*,\s*' | Where-Object { $_ -ne '' }
                            
                            $fileResults.Functions += @{
                                Name = $funcName
                                Position = $match.Index
                                Dependencies = $deps
                            }
                        }
                        break
                    }
                }
            }
        }
        
        if ($fileResults.Functions.Count -gt 0) {
            $results += $fileResults
        }
    }
}

# Check for circular dependencies
Write-Host "`n[CHECK] Analyzing dependency order..." -ForegroundColor Yellow

$circularDeps = @()

foreach ($fileResult in $results) {
    $functions = $fileResult.Functions | Sort-Object { $_.Position }
    
    for ($i = 0; $i -lt $functions.Count; $i++) {
        $currentFunc = $functions[$i]
        
        foreach ($dep in $currentFunc.Dependencies) {
            # Check if this dependency is a function defined later
            $depFunc = $functions | Where-Object { $_.Name -eq $dep -and $_.Position -gt $currentFunc.Position }
            
            if ($depFunc) {
                $circularDeps += @{
                    File = $fileResult.File
                    Function = $currentFunc.Name
                    DependsOn = $dep
                    Issue = "Function '$($currentFunc.Name)' depends on '$dep' which is defined later"
                }
            }
        }
    }
}

# Report results
if ($circularDeps.Count -eq 0) {
    Write-Host "[SUCCESS] No circular dependencies found!" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Found $($circularDeps.Count) potential circular dependencies:" -ForegroundColor Red
    Write-Host ""
    
    foreach ($dep in $circularDeps) {
        Write-Host "  File: $($dep.File)" -ForegroundColor Red
        Write-Host "  Issue: $($dep.Issue)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "[DONE] Scan complete." -ForegroundColor Cyan
