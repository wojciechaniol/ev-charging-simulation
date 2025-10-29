# Quick deployment script for Lab Machine (CP Engines + Monitors)
# Run this on Machine 2 (CP1) - Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 EV Charging - Lab CP Setup" -ForegroundColor Green
Write-Host "   (Charging Point Engines + Monitors)" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if environment variables are set
if (-not $env:KAFKA_BOOTSTRAP) {
    Write-Host "❌ ERROR: KAFKA_BOOTSTRAP is not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Yellow
    Write-Host '  $env:KAFKA_BOOTSTRAP = "<personal-machine-ip>:9092"'
    Write-Host '  $env:CENTRAL_HOST = "<personal-machine-ip>"'
    Write-Host '  $env:CENTRAL_PORT = "8000"'
    Write-Host ""
    Write-Host "Example:" -ForegroundColor Cyan
    Write-Host '  $env:KAFKA_BOOTSTRAP = "192.168.1.100:9092"'
    Write-Host '  $env:CENTRAL_HOST = "192.168.1.100"'
    Write-Host '  $env:CENTRAL_PORT = "8000"'
    exit 1
}

if (-not $env:CENTRAL_HOST) {
    Write-Host "❌ ERROR: CENTRAL_HOST is not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run:" -ForegroundColor Yellow
    Write-Host '  $env:CENTRAL_HOST = "<personal-machine-ip>"'
    exit 1
}

Write-Host "🔧 Environment configured:" -ForegroundColor Green
Write-Host "   KAFKA_BOOTSTRAP=$env:KAFKA_BOOTSTRAP"
Write-Host "   CENTRAL_HOST=$env:CENTRAL_HOST"
Write-Host "   CENTRAL_PORT=$($env:CENTRAL_PORT ?? '8000')"
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
    Write-Host "   Please check:" -ForegroundColor Yellow
    Write-Host "     1. Personal computer is on and running Kafka"
    Write-Host "     2. Firewall allows port 9092"
    Write-Host "     3. Both machines are on same network"
    exit 1
}

# Test Central
Write-Host "   Testing Central connection..."
$centralPort = if ($env:CENTRAL_PORT) { $env:CENTRAL_PORT } else { "8000" }
$centralTest = Test-NetConnection -ComputerName $env:CENTRAL_HOST -Port $centralPort -WarningAction SilentlyContinue

if ($centralTest.TcpTestSucceeded) {
    Write-Host "   ✅ Central is reachable" -ForegroundColor Green
} else {
    Write-Host "   ❌ Cannot reach Central at http://$($env:CENTRAL_HOST):$centralPort" -ForegroundColor Red
    Write-Host "   Please check:" -ForegroundColor Yellow
    Write-Host "     1. Central is running on personal computer"
    Write-Host "     2. Firewall allows port $centralPort"
    exit 1
}
Write-Host ""

# Create network if not exists
Write-Host "🌐 Checking Docker network..." -ForegroundColor Cyan
$networkExists = docker network ls | Select-String "ev-charging-simulation-1_evcharging-network"
if (-not $networkExists) {
    Write-Host "   Network doesn't exist, creating..." -ForegroundColor Yellow
    docker network create ev-charging-simulation-1_evcharging-network
    Write-Host "   ✅ Network created" -ForegroundColor Green
} else {
    Write-Host "   ✅ Network already exists" -ForegroundColor Green
}
Write-Host ""

# Start CP services
Write-Host "1️⃣  Starting 5 Charging Point Engines and 5 Monitors (10 services)..." -ForegroundColor Cyan
docker compose -f docker/docker-compose.remote-kafka.yml up -d `
  ev-cp-e-001 ev-cp-e-002 ev-cp-e-003 ev-cp-e-004 ev-cp-e-005 `
  ev-cp-m-001 ev-cp-m-002 ev-cp-m-003 ev-cp-m-004 ev-cp-m-005

Write-Host "   ⏳ Waiting for services to start (15 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
Write-Host ""

# Check services
Write-Host "2️⃣  Checking service status..." -ForegroundColor Cyan
docker compose -f docker/docker-compose.remote-kafka.yml ps --filter "name=ev-cp"
Write-Host ""
$cpCount = (docker ps --filter "name=ev-cp" --format "{{.Names}}").Count
Write-Host "   Total CP services running: $cpCount" -ForegroundColor Green
Write-Host ""

# Verify logs
Write-Host "3️⃣  Checking CP Monitor Registration..." -ForegroundColor Cyan
Write-Host "   Inspecting logs for registration status..." -ForegroundColor Gray
Write-Host ""

$registrationSuccess = 0
$registrationFailed = 0

for ($i = 1; $i -le 5; $i++) {
    $cpNum = "{0:D3}" -f $i
    $containerName = "ev-cp-m-$cpNum"
    
    Write-Host "   📊 CP-$cpNum Monitor:" -ForegroundColor White
    $logs = docker logs --tail 10 $containerName 2>&1
    
    if ($logs -match "registered with Central successfully") {
        Write-Host "      ✅ Registration SUCCESSFUL" -ForegroundColor Green
        $registrationSuccess++
    } elseif ($logs -match "Failed to register") {
        Write-Host "      ❌ Registration FAILED" -ForegroundColor Red
        Write-Host "      Last 5 log lines:" -ForegroundColor Yellow
        docker logs --tail 5 $containerName 2>&1 | ForEach-Object { Write-Host "         $_" -ForegroundColor Gray }
        $registrationFailed++
    } else {
        Write-Host "      ⚠️  Registration status unclear" -ForegroundColor Yellow
        Write-Host "      Last 3 log lines:" -ForegroundColor Gray
        docker logs --tail 3 $containerName 2>&1 | ForEach-Object { Write-Host "         $_" -ForegroundColor Gray }
    }
}

Write-Host ""
Write-Host "   📈 Registration Summary: $registrationSuccess successful, $registrationFailed failed" -ForegroundColor $(if ($registrationSuccess -eq 5) { "Green" } elseif ($registrationSuccess -gt 0) { "Yellow" } else { "Red" })
Write-Host ""

if ($registrationFailed -gt 0 -or $registrationSuccess -lt 5) {
    Write-Host "⚠️  REGISTRATION ISSUES DETECTED!" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Diagnostic commands to run:" -ForegroundColor Yellow
    Write-Host "   1. Check environment variables:" -ForegroundColor White
    Write-Host "      docker inspect ev-cp-m-001 | Select-String CENTRAL" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Test Central HTTP from container:" -ForegroundColor White
    Write-Host "      docker exec ev-cp-m-001 wget -O- http://${CENTRAL_HOST}:${CENTRAL_PORT}/health" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. Check firewall on Machine 1 ($CENTRAL_HOST):" -ForegroundColor White
    Write-Host "      Port 8000 must allow inbound connections" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   4. Verify Central is accessible from this machine:" -ForegroundColor White
    Write-Host "      Invoke-WebRequest -Uri http://${CENTRAL_HOST}:${CENTRAL_PORT}/health -UseBasicParsing" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   5. Check Central's /cp endpoint for registered CPs:" -ForegroundColor White
    Write-Host "      Invoke-WebRequest -Uri http://${CENTRAL_HOST}:${CENTRAL_PORT}/cp -UseBasicParsing" -ForegroundColor Gray
    Write-Host ""
}
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Lab CP Setup Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Running Services (10 total):" -ForegroundColor Yellow
Write-Host "   Engines: ev-cp-e-001, ev-cp-e-002, ev-cp-e-003, ev-cp-e-004, ev-cp-e-005"
Write-Host "   Monitors: ev-cp-m-001, ev-cp-m-002, ev-cp-m-003, ev-cp-m-004, ev-cp-m-005"
Write-Host ""
Write-Host "⚡ Power Ratings:" -ForegroundColor Yellow
Write-Host "   CP-001: 22.0 kW  (€0.30/kWh)"
Write-Host "   CP-002: 50.0 kW  (€0.35/kWh)"
Write-Host "   CP-003: 43.0 kW  (€0.32/kWh)"
Write-Host "   CP-004: 150.0 kW (€0.40/kWh)"
Write-Host "   CP-005: 7.2 kW   (€0.28/kWh)"
Write-Host ""
Write-Host "🔍 Monitor logs:" -ForegroundColor Cyan
Write-Host "   docker logs -f ev-cp-e-001"
Write-Host "   docker logs -f ev-cp-m-001"
Write-Host ""
Write-Host "✅ Verify CPs in Central Dashboard:" -ForegroundColor Green
Write-Host "   http://${CENTRAL_HOST}:${CENTRAL_PORT}"
Write-Host "   Or use API: Invoke-WebRequest -Uri http://${CENTRAL_HOST}:${CENTRAL_PORT}/cp -UseBasicParsing"
Write-Host ""
Write-Host "🛑 To stop all services:" -ForegroundColor Red
Write-Host "   docker compose -f docker/docker-compose.remote-kafka.yml down"
Write-Host ""
