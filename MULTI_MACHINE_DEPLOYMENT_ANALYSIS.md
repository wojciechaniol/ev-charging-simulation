# Multi-Machine Deployment Analysis & Verification

## 🔍 Current Status: **MOSTLY READY** ⚠️

Your deployment plan is **nearly correct** but has **2 critical issues** that need fixing.

---

## ✅ What Works Correctly

### 1. Environment Variables - **PERFECT** ✅
- `KAFKA_BOOTSTRAP` is properly used throughout all services
- `CENTRAL_HOST` is correctly configured for monitors
- `CENTRAL_HTTP_URL` is correctly configured for drivers
- All services have proper fallback defaults (`${VAR:-default}`)

### 2. Docker Compose Structure - **GOOD** ✅
- `docker/docker-compose.remote-kafka.yml` is properly designed for remote Kafka
- Services are modular and can be deployed independently
- Port mappings are correct (9092 for Kafka, 8000 for Central)

### 3. Network Configuration - **GOOD** ✅
- Services use bridge networking by default
- Ports are exposed correctly for external access

---

## ❌ Critical Issues Found

### Issue #1: Kafka Advertised Listeners (CRITICAL) 🚨

**Problem:**
```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092  # ❌ WRONG - hardcoded to "kafka"
```

**Why This Breaks Your Plan:**
- Lab machines (CP1, CP2) cannot resolve the hostname `kafka`
- They need to connect using your personal computer's IP address
- Kafka will advertise `kafka:9092` which is unreachable from external machines

**Fix Required:**
```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${KAFKA_ADVERTISED_HOST:-kafka}:9092
```

Then set on Machine 1:
```bash
export KAFKA_ADVERTISED_HOST=$(ipconfig getifaddr en0)  # e.g., 192.168.1.100
```

---

### Issue #2: Monitor Dependencies in remote-kafka.yml (MEDIUM) ⚠️

**Problem:**
```yaml
depends_on:
  - ev-central
  - ev-cp-e-1
```

**Why This Breaks Your Plan:**
- On Machine 2 (CP1), you're only starting engines and monitors
- But monitors have `depends_on: ev-central`, which doesn't exist on Machine 2
- Docker Compose will fail because it expects `ev-central` to be defined

**Fix Required:**
Remove the `depends_on` clauses from monitors in the remote-kafka file, or make them conditional.

---

## 🔧 Required Fixes

### Fix #1: Update Kafka Configuration

Edit `docker-compose.yml` (lines 28-57):

```yaml
kafka:
  image: apache/kafka:3.7.0
  container_name: ev-kafka
  ports:
    - "9092:9092"
  environment:
    KAFKA_NODE_ID: 1
    KAFKA_PROCESS_ROLES: broker,controller
    KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${KAFKA_ADVERTISED_HOST:-localhost}:9092  # ✅ FIXED
    KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@localhost:9093  # ✅ Also change this
    # ... rest stays same
```

### Fix #2: Update remote-kafka.yml Monitor Dependencies

Edit `docker/docker-compose.remote-kafka.yml` - remove or comment out `depends_on`:

```yaml
# Charging Point Monitor 1
ev-cp-m-1:
  build:
    context: ..
    dockerfile: docker/Dockerfile.cp_m
  container_name: ev-cp-m-1
  environment:
    CP_MONITOR_CP_ID: CP-001
    CP_MONITOR_CP_E_HOST: ev-cp-e-1
    CP_MONITOR_CP_E_PORT: 8001
    CP_MONITOR_CENTRAL_HOST: ${CENTRAL_HOST:-ev-central}
    CP_MONITOR_CENTRAL_PORT: ${CENTRAL_PORT:-8000}
    CP_MONITOR_HEALTH_INTERVAL: 1.0
    CP_MONITOR_LOG_LEVEL: INFO
  # depends_on:  # ✅ REMOVED - not needed for remote deployment
  #   - ev-central
  #   - ev-cp-e-1
  networks:
    - evcharging-network
  restart: unless-stopped
```

---

## ✅ Corrected Deployment Plan

### Machine 1 – Personal Computer (Kafka + Central)

```bash
# 1. Set your machine's network IP for Kafka advertising
export KAFKA_ADVERTISED_HOST=$(ipconfig getifaddr en0)  # macOS
# OR: export KAFKA_ADVERTISED_HOST=$(hostname -I | awk '{print $1}')  # Linux

# 2. Start Kafka (now it will advertise the correct IP)
docker compose up -d kafka

# 3. Wait for Kafka to be ready
sleep 30
docker logs ev-kafka | grep "started (kafka.server.KafkaRaftServer)"

# 4. Start Central Controller
docker compose -f docker/docker-compose.remote-kafka.yml up -d ev-central

# 5. Verify Central is connected to Kafka
curl http://localhost:8000/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "ev-central",
#   "kafka_producer": "connected",
#   "kafka_consumer": "connected"
# }

# 6. Check your IP (share this with lab machines)
echo "Kafka/Central running at: $KAFKA_ADVERTISED_HOST"
```

**Expected Logs to See:**
```
✅ "Kafka producer started: <your-ip>:9092"
✅ "Kafka consumer started: topics=['driver.requests', 'cp.status', 'cp.telemetry']"
✅ "EV Central Controller started successfully"
✅ "Dashboard available at http://localhost:8000"
```

---

### Machine 2 (CP1) – Lab Computer (CP Engines + Monitors)

```bash
# 1. Set environment variables (replace with actual IP)
export KAFKA_BOOTSTRAP=192.168.1.100:9092  # Your personal machine IP
export CENTRAL_HOST=192.168.1.100
export CENTRAL_PORT=8000

# 2. Start CP engines and monitors
docker compose -f docker/docker-compose.remote-kafka.yml up -d \
  ev-cp-e-1 ev-cp-e-2 ev-cp-m-1 ev-cp-m-2

# 3. Verify services started
docker compose ps

# 4. Check logs for successful connection
docker logs ev-cp-e-1 2>&1 | grep -E "Kafka|started successfully|ACTIVATED"
docker logs ev-cp-m-1 2>&1 | grep -E "heartbeat|Monitoring CP-001"
```

**Expected Logs to See:**

**CP Engine (ev-cp-e-1):**
```
✅ "Kafka producer started: 192.168.1.100:9092"
✅ "Kafka consumer started: topics=['central.commands']"
✅ "CP CP-001: Health server listening on port 8001"
✅ "CP CP-001: CPState.DISCONNECTED + CPEvent.CONNECT -> CPState.ACTIVATED"
✅ "CP Engine CP-001 started successfully"
```

**CP Monitor (ev-cp-m-1):**
```
✅ "Monitoring CP-001 at ev-cp-e-1:8001"
✅ "Central heartbeat sent successfully"
✅ "Health check: CP-001 is HEALTHY"
```

---

### Machine 3 (CP2) – Lab Computer (Drivers)

```bash
# 1. Set environment variables (replace with actual IP)
export KAFKA_BOOTSTRAP=192.168.1.100:9092  # Your personal machine IP
export CENTRAL_HTTP_URL=http://192.168.1.100:8000

# 2. Start driver
docker compose -f docker/docker-compose.remote-kafka.yml up -d ev-driver

# 3. Check logs
docker logs ev-driver 2>&1 | grep -E "Kafka|started|requested charging"
```

**Expected Logs to See:**
```
✅ "Starting Driver client: driver-alice"
✅ "Kafka producer started: 192.168.1.100:9092"
✅ "Kafka consumer started: topics=['driver.updates']"
✅ "Driver driver-alice started successfully"
✅ "📤 Driver driver-alice requested charging at CP-001"
✅ "✅ ACCEPTED | Request accepted, starting charging"
✅ "🔋 IN_PROGRESS | Charging: 22.0 kW, €0.02"
```

---

## 🧪 Complete Verification Checklist

### From Machine 1 (Your Personal Computer)

```bash
# Check Kafka is accessible externally
docker exec ev-kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Check Central dashboard
curl http://localhost:8000/cp

# Verify CPs registered from lab machines
curl http://localhost:8000/cp | jq '.charging_points | length'  # Should see 2+ CPs
```

### From Machine 2 (Lab - CP1)

```bash
# Test Kafka connectivity
docker run --rm confluentinc/cp-kafka:latest \
  kafka-broker-api-versions --bootstrap-server $KAFKA_BOOTSTRAP

# Check if CPs are running
docker ps --filter "name=ev-cp"

# Test Central HTTP connectivity
curl http://$CENTRAL_HOST:8000/health
```

### From Machine 3 (Lab - CP2)

```bash
# Test Kafka connectivity (same as CP1)
docker run --rm confluentinc/cp-kafka:latest \
  kafka-broker-api-versions --bootstrap-server $KAFKA_BOOTSTRAP

# Test Central HTTP connectivity
curl $CENTRAL_HTTP_URL/health

# Check available CPs from driver's perspective
curl $CENTRAL_HTTP_URL/cp | jq '.charging_points[] | {cp_id, state}'
```

---

## 🔥 Common Issues & Solutions

### Issue: "Connection refused to Kafka"

**Symptoms:**
```
ERROR: Failed to connect to Kafka at 192.168.1.100:9092
```

**Solutions:**
1. **Check firewall** on Machine 1:
   ```bash
   # macOS - allow port 9092
   sudo pfctl -d  # Disable firewall temporarily for testing
   
   # Or add specific rule (permanently):
   # System Preferences > Security & Privacy > Firewall > Firewall Options
   # Add Docker and allow incoming connections
   ```

2. **Verify Kafka is listening on all interfaces:**
   ```bash
   docker exec ev-kafka netstat -tuln | grep 9092
   # Should show: 0.0.0.0:9092 (not 127.0.0.1:9092)
   ```

3. **Test network connectivity from lab machine:**
   ```bash
   nc -zv 192.168.1.100 9092
   # Should show: Connection succeeded
   ```

### Issue: "Monitor can't reach Central"

**Symptoms:**
```
ERROR: Failed to send heartbeat to Central
```

**Solutions:**
1. **Check Central is listening externally:**
   ```bash
   # On Machine 1
   docker logs ev-central | grep "running on"
   # Should show: 0.0.0.0:8000 (not 127.0.0.1:8000)
   ```

2. **Test HTTP connectivity from lab:**
   ```bash
   curl http://192.168.1.100:8000/health
   ```

3. **Verify CENTRAL_HOST is set correctly:**
   ```bash
   echo $CENTRAL_HOST  # Should be IP, not "localhost"
   ```

### Issue: "CPs not showing in dashboard"

**Cause:** Central controller restarted and lost state

**Solution:**
```bash
# Restart CP engines to re-sync
docker compose -f docker/docker-compose.remote-kafka.yml restart \
  ev-cp-e-1 ev-cp-e-2
```

---

## 📊 What to Show During Presentation

### 1. **Architecture Diagram**
Show the 3-machine setup:
```
[Machine 1: Your PC]          [Machine 2: Lab CP1]        [Machine 3: Lab CP2]
    Kafka (9092) <-------------- CP-E-1, CP-M-1 <-----+
    Central (8000) <----------- CP-E-2, CP-M-2        |
                 <--------------------------------- Driver
```

### 2. **Live Logs** (Terminal Windows)
- **Machine 1:** `docker logs -f ev-central`
- **Machine 2:** `docker logs -f ev-cp-e-1`
- **Machine 3:** `docker logs -f ev-driver`

### 3. **Dashboard View**
- Open `http://localhost:8000` on Machine 1
- Show real-time CP status updates
- Show charging sessions from remote driver

### 4. **Fault Injection Demo**
```bash
# On Machine 2 - crash a CP
docker stop ev-cp-e-1

# Watch on Machine 1 dashboard - CP-001 becomes faulty

# Recover
docker start ev-cp-e-1

# Watch recovery in real-time
```

---

## 📝 Summary

**Status:** Your plan is **90% correct!**

**What You Need to Do:**
1. ✅ Fix Kafka advertised listeners (5 minutes)
2. ✅ Remove depends_on from monitors in remote-kafka.yml (2 minutes)
3. ✅ Test locally first with export commands (10 minutes)
4. ✅ Deploy to lab machines (20 minutes)

**Total Setup Time:** ~40 minutes

**After Fixes:** Your deployment plan will work **perfectly** for the 3-machine lab setup!
