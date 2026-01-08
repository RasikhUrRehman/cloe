# Analyze Logs Script
# Provides statistics and insights from the logs

param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd")
)

$ErrorActionPreference = "Stop"

Write-Host "=== Cleo Log Analyzer ===" -ForegroundColor Cyan
Write-Host "Analyzing logs for: $Date" -ForegroundColor Yellow
Write-Host ""

$logFile = "logs\cleo_$Date.log"

if (-not (Test-Path $logFile)) {
    Write-Host "Log file not found: $logFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available log files:" -ForegroundColor Yellow
    Get-ChildItem logs\cleo_*.log | ForEach-Object {
        Write-Host "  $($_.Name) - $($_.Length) bytes - $($_.LastWriteTime)" -ForegroundColor Gray
    }
    exit 1
}

$content = Get-Content $logFile

Write-Host "Total log entries: $($content.Count)" -ForegroundColor Green
Write-Host ""

# Count by log level
Write-Host "=== Log Level Distribution ===" -ForegroundColor Cyan
$levels = @{}
$content | ForEach-Object {
    if ($_ -match '\| (\w+)\s+\|') {
        $level = $matches[1].Trim()
        if (-not $levels.ContainsKey($level)) {
            $levels[$level] = 0
        }
        $levels[$level]++
    }
}

$levels.GetEnumerator() | Sort-Object Name | ForEach-Object {
    $color = switch ($_.Key) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "INFO" { "Green" }
        "DEBUG" { "Gray" }
        default { "White" }
    }
    Write-Host "  $($_.Key): $($_.Value)" -ForegroundColor $color
}

Write-Host ""

# Show recent errors
$errors = $content | Where-Object { $_ -match '\| ERROR\s+\|' }
if ($errors.Count -gt 0) {
    Write-Host "=== Recent Errors ($($errors.Count) total) ===" -ForegroundColor Red
    $errors | Select-Object -Last 10 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Red
    }
} else {
    Write-Host "=== No Errors Found! ✓ ===" -ForegroundColor Green
}

Write-Host ""

# Show API activity
$apiRequests = $content | Where-Object { $_ -match 'HTTP|GET|POST|PUT|DELETE' }
if ($apiRequests.Count -gt 0) {
    Write-Host "=== API Activity ($($apiRequests.Count) requests) ===" -ForegroundColor Cyan
    Write-Host "Last 5 requests:" -ForegroundColor Yellow
    $apiRequests | Select-Object -Last 5 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
}

Write-Host ""

# File size
$fileSize = (Get-Item $logFile).Length
$fileSizeMB = [math]::Round($fileSize / 1MB, 2)
Write-Host "Log file size: $fileSizeMB MB" -ForegroundColor Cyan

Write-Host ""
