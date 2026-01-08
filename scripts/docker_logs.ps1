# Quick script to view Docker logs
# Usage: .\scripts\docker_logs.ps1 [lines]

param(
    [int]$Lines = 100
)

Write-Host "=== Cleo Docker Logs (last $Lines lines) ===" -ForegroundColor Cyan
Write-Host ""

docker logs cleo-api --tail $Lines --timestamps

Write-Host ""
Write-Host "For live stream: docker logs cleo-api --follow" -ForegroundColor Gray
Write-Host "For all logs: docker logs cleo-api" -ForegroundColor Gray
