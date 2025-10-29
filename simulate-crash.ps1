# PowerShell script to simulate a crash by stopping a random or specific service
# Usage: .\simulate-crash.ps1 [service_name]
#
# Example: .\simulate-crash.ps1 ev-cp-e-5  # Stop specific CP engine
# Example: .\simulate-crash.ps1            # Stop random service

param(
    [Parameter(Mandatory=$false)]
    [string]$ServiceName
)

$ErrorActionPreference = "Stop"

if ($ServiceName) {
    # Stop specific service
    Write-Host ""
    Write-Host "💥 Simulating crash of: $ServiceName" -ForegroundColor Red
    
    # Check if service exists
    $serviceExists = docker ps --filter "name=$ServiceName" --format "{{.Names}}"
    if (-not $serviceExists) {
        Write-Host "❌ Service '$ServiceName' not found or not running" -ForegroundColor Red
        Write-Host ""
        Write-Host "Available services:"
        docker ps --filter "name=ev-" --format "{{.Names}}"
        exit 1
    }
    
    docker stop $ServiceName | Out-Null
    Write-Host "✅ $ServiceName has been stopped (crashed)" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔄 To restart: docker start $ServiceName" -ForegroundColor Yellow
} else {
    # Stop random service (CP engine or driver)
    $services = @(docker ps --filter "name=ev-cp-e" --filter "name=ev-driver" --format "{{.Names}}")
    
    if ($services.Count -eq 0) {
        Write-Host "❌ No running CP engines or drivers found" -ForegroundColor Red
        exit 1
    }
    
    # Select random service
    $randomIndex = Get-Random -Minimum 0 -Maximum $services.Count
    $selectedService = $services[$randomIndex]
    
    Write-Host ""
    Write-Host "🎲 Randomly selected: $selectedService" -ForegroundColor Yellow
    Write-Host "💥 Simulating crash..." -ForegroundColor Red
    
    docker stop $selectedService | Out-Null
    
    Write-Host "✅ $selectedService has been stopped (crashed)" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔄 To restart: docker start $selectedService" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Current system status:" -ForegroundColor Cyan
docker ps --filter "name=ev-" --format "table {{.Names}}`t{{.Status}}"
