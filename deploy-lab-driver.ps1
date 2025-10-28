# Quick deployment script for Lab Machine (Driver)
# Run this on Machine 3 (CP2) - Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 EV Charging - Lab Driver Setup" -ForegroundColor Green
Write-Host "   (Driver Service)" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if environment variables are set
if (-not $env:KAFKA_BOOTSTRAP) {
    Write-Host "❌ ERROR: KAFKA_BOOTSTRAP is not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Yellow
    Write-Host '  $env:KAFKA_BOOTSTRAP = "<personal-machine-ip>:9092"'
    Write-Host '  $env:CENTRAL_HTTP_URL = "http://<personal-machine-ip>:8000"'
    Write-Host ""
    Write-Host "Example:" -ForegroundColor Cyan
    Write-Host '  $env:KAFKA_BOOTSTRAP = "192.168.1.100:9092"'
    Write-Host '  $env:CENTRAL_HTTP_URL = "http://192.168.1.100:8000"'
    exit 1
}

if (-not $env:CENTRAL_HTTP_URL) {
    Write-Host "❌ ERROR: CENTRAL_HTTP_URL is not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Yellow
    Write-Host '  $env:CENTRAL_HTTP_URL = "http://<personal-machine-ip>:8000"'
    exit 1
}

Write-Host "🔧 Environment configured:" -ForegroundColor Green
Write-Host "   KAFKA_BOOTSTRAP=$env:KAFKA_BOOTSTRAP"
Write-Host "   CENTRAL_HTTP_URL=$env:CENTRAL_HTTP_URL"
Write-Host ""

# Test connectivity
Write-Host "🔍 Testing connectivity..." -ForegroundColor Cyan

# Test Kafka
Write-Host "   Testing Kafka connection..."
$kafkaHost = $env:KAFKA_BOOTSTRAP -split ':' | Select-Object -First 1
$kafkaPort = $env:KAFKA_BOOTSTRAP -split ':' | Select-Object -Last 1

$kafkaTest = Test-NetConnection -ComputerName $kafkaHost -Port $kafkaPort -WarningAction SilentlyContinue
if ($kafkaTest.TcpTestSucceeded) {
    Write-Host "   ✅ Kafka is reachable" -ForegroundColor Green
} else {
    Write-Host "   ❌ Cannot reach Kafka at $env:KAFKA_BOOTSTRAP" -ForegroundColor Red
    Write-Host "   Please check firewall and network connectivity" -ForegroundColor Yellow
    exit 1
}

# Test Central HTTP
Write-Host "   Testing Central HTTP connection..."
try {
    $response = Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ Central is reachable" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Cannot reach Central at $env:CENTRAL_HTTP_URL" -ForegroundColor Red
    Write-Host "   Please check firewall and network connectivity" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Start Driver services
Write-Host "1️⃣  Starting 5 Driver Services (Alice, Bob, Charlie, David, Eve)..." -ForegroundColor Cyan
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-driver-alice ev-driver-bob ev-driver-charlie ev-driver-david ev-driver-eve

Write-Host "   ⏳ Waiting for drivers to start (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
Write-Host ""

# Check services
Write-Host "2️⃣  Checking service status..." -ForegroundColor Cyan
docker compose -f docker/docker-compose.remote-kafka.yml ps --filter "name=ev-driver"
Write-Host ""
$driverCount = (docker ps --filter "name=ev-driver" --format "{{.Names}}").Count
Write-Host "   Total Driver services running: $driverCount" -ForegroundColor Green
Write-Host ""

# Verify logs
Write-Host "3️⃣  Verifying connections (sample from Alice and Bob)..." -ForegroundColor Cyan
Write-Host ""
Write-Host "   📋 Driver Alice logs:" -ForegroundColor Yellow
docker logs ev-driver-alice 2>&1 | Select-String "Starting|Kafka|started successfully|requested charging" | Select-Object -Last 5
Write-Host ""
Write-Host "   📋 Driver Bob logs:" -ForegroundColor Yellow
docker logs ev-driver-bob 2>&1 | Select-String "Starting|Kafka|started successfully|requested charging" | Select-Object -Last 5
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Lab Driver Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Running Services (5 total):" -ForegroundColor Yellow
Write-Host "   - ev-driver-alice  (Port 8100, 5.0s interval)"
Write-Host "   - ev-driver-bob    (Port 8101, 6.0s interval)"
Write-Host "   - ev-driver-charlie(Port 8102, 7.0s interval)"
Write-Host "   - ev-driver-david  (Port 8103, 8.0s interval)"
Write-Host "   - ev-driver-eve    (Port 8104, 4.5s interval)"
Write-Host ""
Write-Host "🔍 Monitor logs:" -ForegroundColor Cyan
Write-Host "   docker logs -f ev-driver-alice"
Write-Host "   docker logs -f ev-driver-bob"
Write-Host ""
Write-Host "🌐 Access Dashboards:" -ForegroundColor Cyan
Write-Host "   Alice:   http://localhost:8100"
Write-Host "   Bob:     http://localhost:8101"
Write-Host "   Charlie: http://localhost:8102"
Write-Host "   David:   http://localhost:8103"
Write-Host "   Eve:     http://localhost:8104"
Write-Host ""
Write-Host "📡 Check available charging points:" -ForegroundColor Cyan
Write-Host "   Invoke-WebRequest -Uri `"$env:CENTRAL_HTTP_URL/cp`" | ConvertFrom-Json"
Write-Host ""
Write-Host "🛑 To stop all services:" -ForegroundColor Red
Write-Host "   docker compose -f docker/docker-compose.remote-kafka.yml down"
Write-Host ""
