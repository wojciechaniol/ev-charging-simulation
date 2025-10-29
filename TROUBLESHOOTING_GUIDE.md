# 🔧 EV Charging System - Troubleshooting Guide

This guide helps diagnose and fix common issues in multi-machine lab deployments.

## Table of Contents
1. [Charging Points Not Visible in Central Dashboard](#cps-not-visible)
2. [Drivers Not Requesting Charging](#drivers-not-requesting)
3. [Network Connectivity Issues](#network-issues)
4. [Kafka Connection Problems](#kafka-issues)
5. [Container Health Problems](#container-health)
6. [Firewall Configuration](#firewall-config)

---

## <a name="cps-not-visible"></a>1. Charging Points Not Visible in Central Dashboard

### Symptoms
- CP containers are running on Machine 2 (`docker ps` shows them)
- Central dashboard (Machine 1) is empty - no CPs visible
- No errors in `deploy-lab-cp.ps1` script output

### Root Causes & Solutions

#### ✅ Cause 1: Docker Network Not Created

**Problem:** CPs running in default bridge network, isolated from Central

**Diagnosis:**
```powershell
# Check if network exists
docker network ls | Select-String "ev-charging-simulation-1_evcharging-network"
```

**Solution:**
```powershell
# Create network manually
docker network create ev-charging-simulation-1_evcharging-network

# Restart containers
docker compose -f docker/docker-compose.remote-kafka.yml restart
```

**Prevention:** Updated `deploy-lab-cp.ps1` now auto-creates network

---

#### ✅ Cause 2: CP Monitor Registration Failed

**Problem:** CP Monitor cannot reach Central HTTP endpoint (port 8000)

**Diagnosis:**
```powershell
# Check CP Monitor logs for registration
docker logs ev-cp-m-001 | Select-String "register"

# Expected success message:
# "CP CP-001 registered with Central successfully"

# Expected failure message:
# "Failed to register CP CP-001 with Central"
```

**Solution - Firewall:**
```powershell
# On Machine 1 (Central), allow port 8000 inbound
New-NetFirewallRule -DisplayName "EV Central HTTP" `
  -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Verify rule
Get-NetFirewallRule -DisplayName "EV Central HTTP"
```

**Solution - Test from Machine 2:**
```powershell
# Test HTTP connectivity from CP machine
$CENTRAL_HOST = $env:CENTRAL_HOST
$CENTRAL_PORT = $env:CENTRAL_PORT

Invoke-WebRequest -Uri "http://${CENTRAL_HOST}:${CENTRAL_PORT}/health" -UseBasicParsing
# Should return: StatusCode 200

# Check registered CPs
Invoke-WebRequest -Uri "http://${CENTRAL_HOST}:${CENTRAL_PORT}/cp" -UseBasicParsing
# Should return JSON with CP list
```

**Solution - Test from Container:**
```powershell
# Test from inside container
docker exec ev-cp-m-001 wget -O- http://${CENTRAL_HOST}:${CENTRAL_PORT}/health
# Should print health status

# If fails: Environment variable issue
docker inspect ev-cp-m-001 | Select-String "CENTRAL_HOST"
docker inspect ev-cp-m-001 | Select-String "CENTRAL_PORT"
```

---

#### ✅ Cause 3: Incorrect Environment Variables

**Problem:** CP Monitors pointing to wrong Central address

**Diagnosis:**
```powershell
# Check environment variables in container
docker inspect ev-cp-m-001 --format='{{range .Config.Env}}{{println .}}{{end}}' | Select-String "CENTRAL"

# Should show:
# CENTRAL_HOST=192.168.1.100  (Machine 1 IP)
# CENTRAL_PORT=8000
```

**Solution:**
```powershell
# Set correct environment variables before deployment
$env:CENTRAL_HOST = "192.168.1.100"  # Machine 1 actual IP
$env:CENTRAL_PORT = "8000"

# Recreate containers
docker compose -f docker/docker-compose.remote-kafka.yml down
.\deploy-lab-cp.ps1
```

---

#### ✅ Cause 4: Kafka Connectivity Issues

**Problem:** CP Engine cannot send events to Kafka, Monitor gets no state updates

**Diagnosis:**
```powershell
# Check CP Engine logs for Kafka connection
docker logs ev-cp-e-001 | Select-String "Kafka"

# Should see: "Connected to Kafka" or "Kafka producer created"
# If errors: "Failed to connect to Kafka" or timeout messages
```

**Solution:**
```powershell
# On Machine 1 (Kafka), allow port 9092 inbound
New-NetFirewallRule -DisplayName "Kafka Broker" `
  -Direction Inbound -Protocol TCP -LocalPort 9092 -Action Allow

# Test from Machine 2
Test-NetConnection -ComputerName 192.168.1.100 -Port 9092

# If successful, restart CP containers
docker compose -f docker/docker-compose.remote-kafka.yml restart
```

---

### Quick Verification Checklist

Run these commands on **Machine 2** after deployment:

```powershell
# 1. Check containers running
docker ps --filter "name=ev-cp" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Check network membership
docker network inspect ev-charging-simulation-1_evcharging-network | Select-String "ev-cp"

# 3. Check CP Monitor registration logs
foreach ($i in 1..5) {
    $cpNum = "{0:D3}" -f $i
    Write-Host "CP-$cpNum:" -ForegroundColor Cyan
    docker logs ev-cp-m-$cpNum 2>&1 | Select-String "registered" | Select-Object -Last 1
}

# 4. Verify on Central (from Machine 2)
Invoke-WebRequest -Uri "http://$env:CENTRAL_HOST:$env:CENTRAL_PORT/cp" -UseBasicParsing | 
  ConvertFrom-Json | Format-Table

# Should list CP-001 through CP-005
```

---

## <a name="drivers-not-requesting"></a>2. Drivers Not Requesting Charging

### Symptoms
- Driver containers running on Machine 3
- No charging sessions visible in Central
- Driver dashboards accessible but empty

### Root Causes & Solutions

#### ✅ Cause 1: No CPs Available

**Problem:** Drivers waiting for available CPs

**Diagnosis:**
```powershell
# Check if Central knows about CPs
Invoke-WebRequest -Uri "$env:CENTRAL_HTTP_URL/cp" -UseBasicParsing | ConvertFrom-Json

# Should return 5 CPs (CP-001 through CP-005)
# If empty: CPs not registered (see Section 1)
```

**Solution:** Fix CP registration first (Section 1)

---

#### ✅ Cause 2: Kafka Connection Failed

**Problem:** Driver cannot send charge requests to Kafka

**Diagnosis:**
```powershell
# Check driver logs
docker logs ev-driver-alice | Select-String "Kafka"

# Should see: "Connected to Kafka" or "Producer created"
# If errors: "Cannot connect to Kafka" or timeout
```

**Solution:**
```powershell
# Test Kafka connectivity from Machine 3
$KAFKA_BOOTSTRAP = $env:KAFKA_BOOTSTRAP
$kafkaHost = $KAFKA_BOOTSTRAP -split ':' | Select-Object -First 1
$kafkaPort = $KAFKA_BOOTSTRAP -split ':' | Select-Object -Last 1

Test-NetConnection -ComputerName $kafkaHost -Port $kafkaPort

# If fails: Firewall on Machine 1 (see Firewall section)
```

---

#### ✅ Cause 3: Circuit Breaker Open

**Problem:** Driver experienced many failures, circuit breaker protecting

**Diagnosis:**
```powershell
# Check driver logs for circuit breaker
docker logs ev-driver-alice | Select-String "circuit"

# Messages like: "Circuit breaker OPEN" or "Too many failures"
```

**Solution:**
```powershell
# Wait 30 seconds for circuit breaker reset
Start-Sleep -Seconds 30

# Or restart driver
docker restart ev-driver-alice

# Check logs again
docker logs -f ev-driver-alice
```

---

## <a name="network-issues"></a>3. Network Connectivity Issues

### Complete Network Verification

Run from **each machine** to verify full connectivity:

```powershell
# ==========================================
# Machine 2 (CP) → Machine 1 (Central/Kafka)
# ==========================================

Write-Host "Testing connectivity to Machine 1..." -ForegroundColor Cyan

# Test Kafka (9092)
Test-NetConnection -ComputerName 192.168.1.100 -Port 9092

# Test Central HTTP (8000)
Test-NetConnection -ComputerName 192.168.1.100 -Port 8000

# Test Central TCP (9999)
Test-NetConnection -ComputerName 192.168.1.100 -Port 9999

# HTTP endpoint test
Invoke-WebRequest -Uri "http://192.168.1.100:8000/health" -UseBasicParsing
```

```powershell
# ==========================================
# Machine 3 (Driver) → Machine 1 (Central/Kafka)
# ==========================================

Write-Host "Testing connectivity to Machine 1..." -ForegroundColor Cyan

# Test Kafka (9092)
Test-NetConnection -ComputerName 192.168.1.100 -Port 9092

# Test Central HTTP (8000)
Test-NetConnection -ComputerName 192.168.1.100 -Port 8000

# HTTP endpoint test
Invoke-WebRequest -Uri "http://192.168.1.100:8000/cp" -UseBasicParsing
```

### Common Network Issues

#### Issue: TcpTestSucceeded = False

**Causes:**
1. Firewall blocking port
2. Service not listening on correct interface
3. Wrong IP address
4. Network isolation (different subnets)

**Solutions:**

```powershell
# 1. Check Windows Firewall rules on target machine
Get-NetFirewallRule -Enabled True | Where-Object {$_.LocalPort -eq 8000}

# 2. Check service is listening on 0.0.0.0 (all interfaces)
# On Machine 1, check Kafka
docker logs kafka | Select-String "advertised.listeners"
# Should contain: PLAINTEXT://192.168.1.100:9092 (not localhost)

# 3. Verify IP address
ipconfig
# Find correct adapter IP (usually Ethernet or Wi-Fi)

# 4. Check machines on same subnet
# All should be 192.168.1.x or 10.0.0.x etc.
```

---

## <a name="kafka-issues"></a>4. Kafka Connection Problems

### Kafka Not Reachable from Other Machines

**Problem:** Kafka listening on localhost only

**Diagnosis:**
```powershell
# On Machine 1, check Kafka advertised listeners
docker logs kafka | Select-String "advertised"

# Should see: PLAINTEXT://192.168.1.100:9092
# NOT: PLAINTEXT://localhost:9092
```

**Solution:**
```powershell
# Edit docker-compose.yml on Machine 1
# Find KAFKA_ADVERTISED_LISTENERS:
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://192.168.1.100:9092

# Replace 192.168.1.100 with your Machine 1 actual IP

# Restart Kafka
docker compose restart kafka
```

### Kafka Topic Not Created

**Problem:** Services cannot produce/consume messages

**Diagnosis:**
```powershell
# On Machine 1, list Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Should see:
# ev_events
# cp_events
# driver_events
```

**Solution:**
```powershell
# Auto-created on first message, but can create manually:
docker exec kafka kafka-topics --create --topic ev_events --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

---

## <a name="container-health"></a>5. Container Health Problems

### Container Exiting/Restarting

**Diagnosis:**
```powershell
# Check container status
docker ps -a --filter "name=ev-cp" --format "table {{.Names}}\t{{.Status}}"

# If "Exited" or "Restarting", check logs
docker logs ev-cp-e-001

# Common errors:
# - "Cannot connect to Kafka" → Kafka unreachable
# - "Address already in use" → Port conflict
# - "Module not found" → Image build issue
```

**Solution - Kafka Unreachable:**
```powershell
# Check environment variable
docker inspect ev-cp-e-001 | Select-String "KAFKA_BOOTSTRAP"

# Should match: 192.168.1.100:9092

# Fix and restart
$env:KAFKA_BOOTSTRAP = "192.168.1.100:9092"
docker compose -f docker/docker-compose.remote-kafka.yml up -d ev-cp-e-001
```

**Solution - Port Conflict:**
```powershell
# Find what's using the port
Get-NetTCPConnection -LocalPort 8001 -State Listen

# Stop conflicting service or change port in docker-compose
```

### Container Running but Unhealthy

**Diagnosis:**
```powershell
# Check health endpoint
Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing

# Should return 200 OK
# If timeout/error: Process crashed inside container
```

**Solution:**
```powershell
# Check Python process running
docker exec ev-cp-e-001 ps aux

# Should see: python -m evcharging.apps.ev_cp_e.main

# If not running: restart container
docker restart ev-cp-e-001
```

---

## <a name="firewall-config"></a>6. Firewall Configuration

### Required Firewall Rules

Run on **Machine 1 (Central + Kafka)** with Administrator PowerShell:

```powershell
# Allow Kafka (9092)
New-NetFirewallRule -DisplayName "Kafka Broker" `
  -Direction Inbound -Protocol TCP -LocalPort 9092 -Action Allow

# Allow Central HTTP (8000)
New-NetFirewallRule -DisplayName "EV Central HTTP" `
  -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow

# Allow Central TCP (9999)
New-NetFirewallRule -DisplayName "EV Central TCP" `
  -Direction Inbound -Protocol TCP -LocalPort 9999 -Action Allow

# Verify rules created
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*EV*" -or $_.DisplayName -like "*Kafka*"}
```

### Test Firewall Rules

From **Machine 2 or 3**:

```powershell
# Test each port
Test-NetConnection -ComputerName 192.168.1.100 -Port 9092  # Kafka
Test-NetConnection -ComputerName 192.168.1.100 -Port 8000  # Central HTTP
Test-NetConnection -ComputerName 192.168.1.100 -Port 9999  # Central TCP

# All should show: TcpTestSucceeded : True
```

### Disable Firewall Temporarily (Testing Only)

**⚠️ WARNING: Only for troubleshooting, not for production**

```powershell
# On Machine 1
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False

# Test connectivity again

# Re-enable after testing
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
```

---

## Quick Diagnostic Script

Run this comprehensive diagnostic on any machine:

```powershell
# Save as diagnose.ps1

Write-Host "=== EV Charging System Diagnostics ===" -ForegroundColor Cyan
Write-Host ""

# Environment
Write-Host "1. Environment Variables:" -ForegroundColor Yellow
Write-Host "   KAFKA_BOOTSTRAP = $env:KAFKA_BOOTSTRAP"
Write-Host "   CENTRAL_HOST = $env:CENTRAL_HOST"
Write-Host "   CENTRAL_PORT = $env:CENTRAL_PORT"
Write-Host "   CENTRAL_HTTP_URL = $env:CENTRAL_HTTP_URL"
Write-Host ""

# Docker
Write-Host "2. Docker Status:" -ForegroundColor Yellow
docker version
docker compose version
Write-Host ""

# Network
Write-Host "3. Docker Network:" -ForegroundColor Yellow
docker network ls | Select-String "ev-charging"
Write-Host ""

# Containers
Write-Host "4. Running Containers:" -ForegroundColor Yellow
docker ps --filter "name=ev-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""

# Connectivity
if ($env:CENTRAL_HOST) {
    Write-Host "5. Connectivity Tests:" -ForegroundColor Yellow
    
    Write-Host "   Kafka (9092):"
    Test-NetConnection -ComputerName $env:CENTRAL_HOST -Port 9092 -WarningAction SilentlyContinue | 
      Select-Object ComputerName, RemoteAddress, TcpTestSucceeded
    
    Write-Host "   Central HTTP (8000):"
    Test-NetConnection -ComputerName $env:CENTRAL_HOST -Port 8000 -WarningAction SilentlyContinue | 
      Select-Object ComputerName, RemoteAddress, TcpTestSucceeded
    
    Write-Host ""
}

# Logs
Write-Host "6. Recent Container Logs (errors):" -ForegroundColor Yellow
docker ps --filter "name=ev-" --format "{{.Names}}" | ForEach-Object {
    $containerName = $_
    $errors = docker logs --tail 20 $containerName 2>&1 | Select-String -Pattern "error|failed|exception" -CaseSensitive:$false
    if ($errors) {
        Write-Host "   $containerName :" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
    }
}

Write-Host ""
Write-Host "=== Diagnostics Complete ===" -ForegroundColor Green
```

---

## Getting Help

If issues persist after trying these solutions:

1. **Collect full logs:**
   ```powershell
   # Create logs directory
   New-Item -ItemType Directory -Path logs -Force
   
   # Export all container logs
   docker ps --filter "name=ev-" --format "{{.Names}}" | ForEach-Object {
       docker logs $_ > "logs/$_.log" 2>&1
   }
   
   # Zip logs
   Compress-Archive -Path logs -DestinationPath ev-logs.zip
   ```

2. **Document environment:**
   ```powershell
   # Save system info
   @"
   Machine IP: $(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"} | Select-Object -ExpandProperty IPAddress -First 1)
   Docker Version: $(docker version --format '{{.Server.Version}}')
   OS: $(Get-ComputerInfo | Select-Object -ExpandProperty OsName)
   Environment:
   - KAFKA_BOOTSTRAP=$env:KAFKA_BOOTSTRAP
   - CENTRAL_HOST=$env:CENTRAL_HOST
   - CENTRAL_PORT=$env:CENTRAL_PORT
   "@ | Out-File -FilePath system-info.txt
   ```

3. **Share with instructor/support:**
   - `ev-logs.zip`
   - `system-info.txt`
   - Exact error messages
   - What you tried from this guide

---

## Summary - Most Common Issues

| Symptom | Most Likely Cause | Quick Fix |
|---------|------------------|-----------|
| CPs not in dashboard | Firewall blocking port 8000 | `New-NetFirewallRule` on Machine 1 |
| CPs not in dashboard | Wrong CENTRAL_HOST IP | Set correct IP, redeploy |
| CPs not in dashboard | Network not created | Run `docker network create` |
| Containers exiting | Cannot reach Kafka | Firewall port 9092, check IP |
| Drivers not charging | No CPs available | Fix CP registration first |
| Test-NetConnection fails | Firewall blocking | Add firewall rules |
| "localhost" in logs | Kafka advertised listener wrong | Edit docker-compose.yml |

**Remember:** The improved `deploy-lab-cp.ps1` and `deploy-lab-driver.ps1` scripts now include automatic diagnostics and show registration status!

---

**Last Updated:** 2024 (matches Windows lab deployment scripts v2)
