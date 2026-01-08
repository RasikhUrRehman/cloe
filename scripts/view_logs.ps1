# View Logs Script for Cleo Application
# This script provides easy access to view logs from Docker or local files

param(
    [Parameter(Position=0)]
    [ValidateSet("docker", "file", "errors", "tail", "follow")]
    [string]$Mode = "docker",
    
    [Parameter(Position=1)]
    [int]$Lines = 50
)

$ErrorActionPreference = "Stop"

Write-Host "=== Cleo Log Viewer ===" -ForegroundColor Cyan
Write-Host ""

switch ($Mode) {
    "docker" {
        Write-Host "Viewing Docker container logs (last $Lines lines)..." -ForegroundColor Yellow
        docker logs cleo-api --tail $Lines
    }
    
    "file" {
        $today = Get-Date -Format "yyyy-MM-dd"
        $logFile = "logs\cleo_$today.log"
        
        if (Test-Path $logFile) {
            Write-Host "Viewing log file: $logFile (last $Lines lines)" -ForegroundColor Yellow
            Get-Content $logFile -Tail $Lines
        } else {
            Write-Host "Log file not found: $logFile" -ForegroundColor Red
            Write-Host "Available log files:" -ForegroundColor Yellow
            Get-ChildItem logs\cleo_*.log | Select-Object Name, LastWriteTime, Length
        }
    }
    
    "errors" {
        $today = Get-Date -Format "yyyy-MM-dd"
        $errorFile = "logs\cleo_errors_$today.log"
        
        if (Test-Path $errorFile) {
            Write-Host "Viewing error log: $errorFile" -ForegroundColor Red
            Get-Content $errorFile
        } else {
            Write-Host "No errors logged today! ✓" -ForegroundColor Green
            Write-Host "Available error log files:" -ForegroundColor Yellow
            Get-ChildItem logs\cleo_errors_*.log -ErrorAction SilentlyContinue | Select-Object Name, LastWriteTime, Length
        }
    }
    
    "tail" {
        $today = Get-Date -Format "yyyy-MM-dd"
        $logFile = "logs\cleo_$today.log"
        
        if (Test-Path $logFile) {
            Write-Host "Tailing log file: $logFile (last $Lines lines, updating...)" -ForegroundColor Yellow
            Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
            Get-Content $logFile -Tail $Lines -Wait
        } else {
            Write-Host "Log file not found: $logFile" -ForegroundColor Red
        }
    }
    
    "follow" {
        Write-Host "Following Docker logs (live stream)..." -ForegroundColor Yellow
        Write-Host "Press Ctrl+C to stop" -ForegroundColor Gray
        docker logs cleo-api --follow
    }
}

Write-Host ""
Write-Host "=== Available Commands ===" -ForegroundColor Cyan
Write-Host "  .\scripts\view_logs.ps1 docker     - View Docker container logs" -ForegroundColor Gray
Write-Host "  .\scripts\view_logs.ps1 file       - View today's log file" -ForegroundColor Gray
Write-Host "  .\scripts\view_logs.ps1 errors     - View error logs" -ForegroundColor Gray
Write-Host "  .\scripts\view_logs.ps1 tail       - Live tail of log file" -ForegroundColor Gray
Write-Host "  .\scripts\view_logs.ps1 follow     - Live follow Docker logs" -ForegroundColor Gray
Write-Host ""
