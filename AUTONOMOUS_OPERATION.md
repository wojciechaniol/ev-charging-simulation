# 🚀 Autonomous Operation Guide

## Overview

This EV Charging Simulation System is designed for **fully autonomous operation** without any user interaction. The entire system starts up, runs continuously, and demonstrates all functionality through observable terminal outputs.

## System Configuration

### **26 Services Total**

#### Infrastructure (1)
- **Kafka** - Message broker for event-driven communication

#### Central Controller (1)
- **ev-central** - Orchestrates all charging operations, provides web dashboard

#### Charging Points (10)
- **CP-001** to **CP-010** - Ten charging points with diverse power ratings:
  - CP-001: 22.0 kW @ €0.30/kWh (Standard AC)
  - CP-002: 50.0 kW @ €0.35/kWh (Fast DC)
  - CP-003: 43.0 kW @ €0.32/kWh (Fast DC)
  - CP-004: 150.0 kW @ €0.40/kWh (Ultra-Fast DC)
  - CP-005: 7.2 kW @ €0.28/kWh (Slow AC)
  - CP-006: 11.0 kW @ €0.29/kWh (Standard AC)
  - CP-007: 100.0 kW @ €0.38/kWh (Fast DC)
  - CP-008: 22.0 kW @ €0.31/kWh (Standard AC)
  - CP-009: 75.0 kW @ €0.36/kWh (Fast DC)
  - CP-010: 350.0 kW @ €0.45/kWh (Hyper-Fast DC)

#### Health Monitors (10)
- **ev-cp-m-1** to **ev-cp-m-10** - Monitor health of each charging point

#### Driver Clients (5)
- **driver-alice** - Request interval: 5.0s
- **driver-bob** - Request interval: 6.0s
- **driver-charlie** - Request interval: 7.0s
- **driver-david** - Request interval: 8.0s
- **driver-eve** - Request interval: 4.5s

## Starting the System

### Quick Start

```bash
# Start all 26 services
docker compose up -d

# Wait 30 seconds for initialization
sleep 30

# Verify all services are running
docker compose ps
```

### Expected Output

All services should show status: `Up` or `Up (healthy)`

```
NAME                IMAGE                        STATUS
ev-central          ...                          Up
ev-cp-e-1           ...                          Up
ev-cp-e-2           ...                          Up
...
ev-driver-alice     ...                          Up
ev-driver-bob       ...                          Up
...
```

## Observing the System

### Method 1: Dashboard (Visual)

**Access the web dashboard:**
```
http://localhost:8000
```

**What you'll see:**
- Real-time charging point states (color-coded badges)
- Active charging sessions with driver info
- Live telemetry: kW delivered and cost in €
- Auto-refresh every 2 seconds

### Method 2: Terminal Logs (Detailed)

Use the provided `view-logs.sh` script for organized log viewing:

```bash
# View all service logs together
./view-logs.sh all

# View only Central controller logs
./view-logs.sh central

# View only Charging Point engine logs
./view-logs.sh cp

# View only Monitor logs
./view-logs.sh monitor

# View only Driver logs
./view-logs.sh driver
```

**Or use docker compose directly:**

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f ev-central
docker compose logs -f ev-cp-e-1
docker compose logs -f ev-driver-alice
```

## What to Observe

### 1. Central Controller Terminal

**Key Events:**
```
✅ Driver request received: driver=driver-alice, cp=CP-001
✅ CP CP-001 registered successfully
✅ Assigned driver-alice to CP-001
✅ Session started for driver-alice at CP-001
✅ Session completed for driver-alice at CP-001
```

**What it shows:**
- Driver request reception
- Charging point registration
- Request validation (ACCEPTED/DENIED)
- CP assignment and session management
- State synchronization
- Fault notifications from monitors

### 2. Charging Point Engine Terminals

**Key Events:**
```
✅ CP CP-001: DISCONNECTED → ACTIVATED (Engine started)
✅ CP CP-001: ACTIVATED → SUPPLYING (Charging started)
🔋 Telemetry: 22.0 kW, €0.006 (session-xyz)
✅ CP CP-001: SUPPLYING → ACTIVATED (Charging completed)
```

**What it shows:**
- State machine transitions with guard conditions
- Command reception from Central
- Telemetry emission during charging (1Hz)
- Session start and completion
- Power delivery and cost calculation

### 3. Monitor Terminals

**Key Events:**
```
✅ CP CP-001 registered with Central
💚 Health check passed for CP-001
⚠️  Health check failed (1) for CP-001
❌ CP CP-001 marked as FAULTY
✅ CP CP-001 recovered from fault
```

**What it shows:**
- Registration with Central controller
- Periodic health checks (every 2 seconds)
- Fault detection (3 consecutive failures)
- Recovery detection
- Health status reporting

### 4. Driver Client Terminals

**Key Events:**
```
📤 driver-alice requested charging at CP-001
✅ driver-alice | CP-001 | ACCEPTED
🔋 driver-alice | CP-001 | IN_PROGRESS | 22.0 kW, €0.01
✔️  driver-alice | CP-001 | COMPLETED
❌ driver-alice | CP-002 | DENIED | CP not available
```

**What it shows:**
- Charging requests sent to Central
- Response status (ACCEPTED, DENIED, IN_PROGRESS, COMPLETED)
- Real-time charging progress with kW and cost
- Request intervals and retry logic
- Completion notifications

## Typical Autonomous Flow

### Happy Path (Successful Charging)

**Timeline:**
1. **T+0s** - System starts, all services initialize
2. **T+5s** - Kafka ready, services connect
3. **T+10s** - Monitors register CPs with Central
4. **T+15s** - All CPs in ACTIVATED state
5. **T+20s** - driver-alice sends request for CP-001
6. **T+21s** - Central validates and accepts request
7. **T+22s** - Central sends START_SUPPLY to CP-001
8. **T+23s** - CP-001 transitions to SUPPLYING state
9. **T+24-33s** - Telemetry flows every second
10. **T+34s** - Charging completes (10 seconds)
11. **T+35s** - CP-001 transitions back to ACTIVATED
12. **T+36s** - driver-alice receives COMPLETED status
13. **T+41s** - driver-alice requests next CP

**What you observe:**
```
[ev-driver-alice] 📤 Requested charging at CP-001
[ev-central] Driver request received: driver-alice, cp=CP-001
[ev-central] Assigned driver-alice to CP-001
[ev-cp-e-1] ACTIVATED → SUPPLYING
[ev-cp-e-1] Telemetry: 22.0 kW, €0.006
[ev-driver-alice] 🔋 IN_PROGRESS | 22.0 kW, €0.01
...
[ev-cp-e-1] Session completed. Total: 0.06 kWh, €0.02
[ev-cp-e-1] SUPPLYING → ACTIVATED
[ev-driver-alice] ✔️ COMPLETED
```

### Concurrent Charging (Multiple Drivers)

With 5 drivers and different request intervals, you'll see:

**Overlapping Sessions:**
```
[ev-central] Active sessions: 5
  - driver-alice at CP-001 (3s remaining)
  - driver-bob at CP-003 (7s remaining)
  - driver-charlie at CP-005 (9s remaining)
  - driver-david at CP-007 (2s remaining)
  - driver-eve at CP-002 (5s remaining)
```

**Dashboard view:**
- Multiple green "SUPPLYING" badges
- 5 active charging session cards
- Real-time telemetry for all active sessions

### Fault Scenario (Health Check Failure)

**If a CP becomes unresponsive:**

```
[ev-cp-m-1] ⚠️  Health check failed (1) for CP-001
[ev-cp-m-1] ⚠️  Health check failed (2) for CP-001
[ev-cp-m-1] ❌ Health check failed (3) for CP-001
[ev-cp-m-1] Notifying Central: CP-001 is FAULTY
[ev-central] Marked CP-001 as faulty
[ev-driver-alice] ❌ CP-001 | DENIED | CP not available
```

**When CP recovers:**

```
[ev-cp-m-1] ✅ Health check passed for CP-001
[ev-cp-m-1] Notifying Central: CP-001 recovered
[ev-central] Cleared fault for CP-001
[ev-driver-alice] ✅ CP-001 | ACCEPTED
```

### CP Not Available (Already in Use)

```
[ev-driver-bob] 📤 Requested charging at CP-001
[ev-central] CP-001 already assigned to driver-alice
[ev-driver-bob] ❌ CP-001 | DENIED | CP not available
[ev-driver-bob] Waiting 6.0s before next request...
```

## Continuous Operation

### Request Loop

Each driver continuously cycles through the `requests.txt` file:

**requests.txt (20 CPs):**
```
CP-001, CP-006, CP-002, CP-007, CP-003, CP-008, CP-004, CP-009, CP-005, CP-010
CP-001, CP-002, CP-003, CP-004, CP-005, CP-006, CP-007, CP-008, CP-009, CP-010
```

**Behavior:**
- After completing request 20, driver loops back to request 1
- Different request intervals create realistic concurrency
- System runs indefinitely until stopped

### Autonomous Testing Scenarios

The system automatically demonstrates:

✅ **Concurrent charging** - Multiple drivers charging simultaneously  
✅ **Request queuing** - Drivers wait when CPs are busy  
✅ **State transitions** - All state machine paths exercised  
✅ **Telemetry streaming** - Real-time power and cost updates  
✅ **Health monitoring** - Continuous CP health checks  
✅ **Fault detection** - Automatic fault detection and recovery  
✅ **Session lifecycle** - Complete charging session from start to finish  
✅ **Load distribution** - Requests spread across 10 CPs  
✅ **Circuit breaker** - Prevents requests to faulty CPs  

## Stopping the System

### Graceful Shutdown

```bash
# Stop all services gracefully
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v
```

### Restart

```bash
# Restart all services
docker compose restart

# Or stop and start fresh
docker compose down
docker compose up -d
```

## Verification

### Quick Health Check

```bash
# Check all services are running
docker compose ps

# Check Central is responding
curl http://localhost:8000/health

# Check CP list
curl http://localhost:8000/cp | jq

# Check telemetry
curl http://localhost:8000/telemetry | jq
```

### Automated Verification Script

```bash
./verify.sh
```

**Checks performed:**
- ✓ All containers running
- ✓ Kafka broker accessible
- ✓ Central controller responding
- ✓ Charging points registered
- ✓ No critical errors in logs

## Troubleshooting

### Services Not Starting

```bash
# Check logs for errors
docker compose logs

# Restart specific service
docker compose restart ev-central

# Full reset
docker compose down -v
docker compose up -d
```

### Kafka Connection Issues

```bash
# Check Kafka is running
docker compose ps kafka

# Check Kafka logs
docker compose logs kafka

# Restart Kafka
docker compose restart kafka
```

### CPs Not Registering

```bash
# Check monitor logs
docker compose logs ev-cp-m-1

# Verify Central is accessible
curl http://localhost:8000/health

# Check network connectivity
docker network inspect ev-charging-simulation_evcharging-network
```

## Performance Metrics

### Expected Behavior

| Metric | Value |
|--------|-------|
| **Startup time** | 30-45 seconds |
| **Request latency** | < 100ms |
| **Telemetry rate** | 1 Hz per active CP |
| **Health check interval** | 2 seconds |
| **Session duration** | ~10 seconds |
| **Concurrent sessions** | Up to 10 (one per CP) |
| **Fault detection** | < 6 seconds (3 failures × 2s) |

### System Load

With all 26 services running:

- **CPU**: ~10-15% on modern hardware
- **Memory**: ~2-3 GB total
- **Disk I/O**: Minimal (logs only)
- **Network**: ~1-2 MB/s (Kafka traffic)

## Educational Value

### What This Demonstrates

**Software Engineering:**
- ✅ Microservices architecture
- ✅ Event-driven design patterns
- ✅ State machine implementation
- ✅ Asynchronous programming
- ✅ Error handling and validation

**Distributed Systems:**
- ✅ Message-oriented middleware (Kafka)
- ✅ Service discovery and registration
- ✅ Fault tolerance and recovery
- ✅ Circuit breaker pattern
- ✅ Health monitoring

**DevOps:**
- ✅ Docker containerization
- ✅ Multi-service orchestration
- ✅ Configuration management
- ✅ Log aggregation
- ✅ Observable systems

**Testing:**
- ✅ Autonomous system testing
- ✅ Load generation
- ✅ Fault injection readiness
- ✅ End-to-end validation
- ✅ Observable behavior

## Summary

This system is designed for **zero-interaction autonomous operation**. Simply start it with `docker compose up -d` and observe the behavior through:

1. **Web Dashboard** - Visual real-time monitoring at http://localhost:8000
2. **Terminal Logs** - Detailed event streams via `docker compose logs -f`
3. **REST API** - Programmatic access to system state

The system will run continuously, demonstrating all functionality through observable events in the various service terminals. Perfect for validation, testing, and educational demonstrations.

---

**Ready to Run**: `docker compose up -d`  
**Dashboard**: http://localhost:8000  
**Logs**: `./view-logs.sh all`  
**Stop**: `docker compose down`

🚗⚡ **Happy Autonomous Charging!**
