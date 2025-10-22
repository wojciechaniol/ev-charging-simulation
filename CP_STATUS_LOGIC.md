# 🔌 Charging Point Status Logic

## Overview

This document explains how the Central Unit determines the operational status of each Charging Point (CP) based on health information reported by the Monitor component.

---

## Status Determination Matrix

### Visual Status Table

| Monitor | Engine | Central Display | Symbol | Available for Charging? |
|---------|--------|----------------|--------|------------------------|
| ✅ OK | ✅ OK | **On** | 🟢 | ✅ YES |
| ✅ OK | ❌ KO | **Broken** | 🔴 | ❌ NO |
| ❌ KO | ✅ OK | **Disconnected** | ⚫ | ❌ NO |
| ❌ KO | ❌ KO | **Disconnected** | ⚫ | ❌ NO |

---

## Status Descriptions

### 🟢 On (Green)
**Conditions:**
- Monitor is operational and sending health checks
- Engine is responding to health checks successfully
- All systems nominal

**What You Can Do:**
- Request new charging sessions
- Monitor telemetry in real-time
- Full CP functionality available

**Example Scenario:**
```
Monitor → [Health Check] → Engine: OK
Monitor → [Report: HEALTHY] → Central
Central: "CP-001 is On (Green)"
```

---

### 🔴 Broken (Red)
**Conditions:**
- Monitor is operational and sending health checks
- Engine is NOT responding to health checks (down, crashed, or unreachable)
- Monitor has detected the failure and notified Central

**What You Can Do:**
- View fault reason and timestamp
- Wait for Engine recovery
- Manually restart Engine container

**Example Scenario:**
```
Monitor → [Health Check] → Engine: TIMEOUT (3 consecutive failures)
Monitor → [Report: FAULT] → Central
Central: "CP-001 is Broken (Red)"
Reason: "Health check failures exceeded threshold"
```

**Recovery:**
```bash
docker start ev-cp-e-1
# Monitor will detect recovery and notify Central
# Status changes: Broken → On
```

---

### ⚫ Disconnected
**Conditions:**
- Monitor has stopped sending health messages to Central
- Central cannot determine CP status
- Engine may be running or down (Central doesn't know)

**Why This Happens:**
- Monitor process crashed or was stopped (Ctrl+C)
- Monitor container stopped
- Network issues between Monitor and Central
- Monitor lost connection to Kafka

**What You Can Do:**
- Check Monitor logs
- Restart Monitor container
- Verify network connectivity

**Example Scenario:**
```
Monitor: [STOPPED]
Central: "No messages from CP-001 Monitor"
Central: "CP-001 is Disconnected"
```

**Recovery:**
```bash
docker start ev-cp-m-1
# Monitor will:
# 1. Re-register with Central
# 2. Resume health checks
# 3. Report current Engine status
# Status changes: Disconnected → On or Broken (based on Engine state)
```

---

## Architecture Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CENTRAL UNIT                          │
│                                                               │
│  Decision Logic:                                             │
│  • Receiving Monitor messages? → YES → Check Engine status  │
│                                → NO  → DISCONNECTED          │
│  • Engine healthy (per Monitor)? → YES → ON (Green)         │
│                                  → NO  → BROKEN (Red)        │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │ Health Reports
                           │ (via HTTP/Kafka)
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                      CP MONITOR                              │
│                                                               │
│  Responsibilities:                                           │
│  • Perform TCP health checks to Engine (every 5 seconds)    │
│  • Detect Engine failures (3 consecutive timeouts)          │
│  • Report FAULT to Central when Engine fails                │
│  • Report HEALTHY to Central when Engine recovers           │
│  • Send periodic heartbeats to prove Monitor is alive       │
└──────────────────────────┬──────────────────────────────────┘
                           │ Health Checks
                           │ (TCP ping/pong)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      CP ENGINE                               │
│                                                               │
│  Responsibilities:                                           │
│  • Respond to Monitor health checks                          │
│  • Execute charging sessions                                 │
│  • Manage session state                                      │
│  • Send telemetry updates                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## State Transitions

### Normal Operation
```
[Initial] → Monitor Registers → [Disconnected]
                               ↓
                   Monitor starts health checks
                               ↓
                   Engine responds OK
                               ↓
                   Monitor reports HEALTHY
                               ↓
                         [On - Green] ✅
```

### Engine Failure
```
[On - Green] → Engine stops responding
             ↓
        Monitor detects failure (15-20 seconds)
             ↓
        Monitor sends FAULT notification
             ↓
        [Broken - Red] 🔴
```

### Monitor Failure
```
[On - Green] → Monitor process stops
             ↓
        Central stops receiving messages
             ↓
        Central timeout (no heartbeat)
             ↓
        [Disconnected] ⚫
```

### Recovery from Broken
```
[Broken - Red] → Engine restarted
               ↓
          Monitor detects health restoration
               ↓
          Monitor sends HEALTHY notification
               ↓
          [On - Green] ✅
```

### Recovery from Disconnected
```
[Disconnected] → Monitor restarted
               ↓
          Monitor re-registers with Central
               ↓
          Monitor checks Engine status
               ├─→ Engine OK → [On - Green] ✅
               └─→ Engine KO → [Broken - Red] 🔴
```

---

## Implementation Details

### Monitor Health Check Code
**Location:** `evcharging/apps/ev_cp_m/main.py`

```python
async def health_check_loop(self):
    consecutive_failures = 0
    
    while self._running:
        try:
            # Attempt TCP connection to Engine
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.config.cp_e_host, 
                    self.config.cp_e_port
                ),
                timeout=2.0
            )
            
            # Success - reset counter
            consecutive_failures = 0
            
            # If we were unhealthy, notify recovery
            if not self.is_healthy:
                self.is_healthy = True
                await self.notify_central_healthy()
                
        except Exception:
            consecutive_failures += 1
            
            # Fault threshold: 3 consecutive failures
            if consecutive_failures >= 3 and self.is_healthy:
                self.is_healthy = False
                await self.notify_central_fault()
        
        await asyncio.sleep(5)  # Check every 5 seconds
```

### Central Fault Handling Code
**Location:** `evcharging/apps/ev_central/main.py`

```python
async def mark_cp_faulty(self, cp_id: str, reason: str):
    """Mark a charging point as broken."""
    if cp_id in self.charging_points:
        cp = self.charging_points[cp_id]
        cp.is_faulty = True
        cp.fault_reason = reason
        cp.fault_timestamp = utc_now()
        
        # Record in database
        self.db.record_fault_event(cp_id, "FAULT", reason)
        
        logger.warning(f"CP {cp_id} marked as BROKEN: {reason}")

def clear_cp_fault(self, cp_id: str):
    """Clear broken status - CP is back to On."""
    if cp_id in self.charging_points:
        cp = self.charging_points[cp_id]
        cp.is_faulty = False
        cp.fault_reason = None
        
        # Record recovery in database
        self.db.record_fault_event(cp_id, "RECOVERY", "Health restored")
        
        logger.info(f"CP {cp_id} is now ON (Green)")
```

---

## Testing Status Transitions

### Test 1: Engine Failure → Broken
```bash
# CP starts in On state
docker logs ev-cp-m-1 | tail -5
# CP_M:CP-001 | Health check OK

# Stop Engine
docker stop ev-cp-e-1

# Wait 15-20 seconds, then check Monitor logs
docker logs ev-cp-m-1 | grep "FAULT"
# CP_M:CP-001 | Health check failed (1)
# CP_M:CP-001 | Health check failed (2)
# CP_M:CP-001 | Health check failed (3)
# CP_M:CP-001 | FAULT DETECTED
# CP_M:CP-001 | Fault notification sent to Central

# Check Central
docker logs ev-central | grep "CP-001"
# Central | CP CP-001 marked as BROKEN: Health check failures exceeded threshold
```

### Test 2: Monitor Failure → Disconnected
```bash
# CP starts in On state
docker stop ev-cp-m-1

# Check Central (after timeout period)
docker logs ev-central | grep "CP-001"
# Central | No health messages from CP-001, marking as DISCONNECTED
```

### Test 3: Recovery from Broken
```bash
# CP is in Broken state
docker logs ev-central | grep "CP-001"
# Central | CP CP-001 marked as BROKEN

# Restart Engine
docker start ev-cp-e-1

# Monitor will detect recovery
docker logs ev-cp-m-1 | tail -10
# CP_M:CP-001 | Health check OK
# CP_M:CP-001 | Health restored
# CP_M:CP-001 | Health restoration notification sent to Central

# Check Central
docker logs ev-central | grep "CP-001"
# Central | CP CP-001 is now ON (Green)
```

### Test 4: Recovery from Disconnected
```bash
# CP is in Disconnected state
docker start ev-cp-m-1

# Monitor re-registers and checks Engine
docker logs ev-cp-m-1 | tail -10
# CP_M:CP-001 | Registered with Central
# CP_M:CP-001 | Starting health checks
# CP_M:CP-001 | Health check OK  (Engine was still running)
# CP_M:CP-001 | Health restoration notification sent

# Check Central
docker logs ev-central | grep "CP-001"
# Central | CP CP-001 is now ON (Green)
```

---

## FAQ

### Why not have Central check Engine directly?
**Separation of Concerns**: The Monitor is specifically designed to observe and report. Having Central reach out to each Engine would:
- Increase Central's complexity
- Create tight coupling
- Make fault detection inconsistent
- Complicate scaling (Central would need to track all Engine endpoints)

### What if Monitor is lying about Engine status?
The system trusts the Monitor as the authoritative health reporter. In production:
- Monitor runs in a separate container with its own resources
- Monitor failures are independent of Engine failures
- Central validates Monitor heartbeats (if Monitor stops, CP becomes Disconnected)

### Can a CP in Disconnected state complete active sessions?
**Yes!** The Engine continues operating even when Monitor is down:
- Active charging sessions complete normally
- Engine sends results to Kafka
- Driver receives completion notification
- However, Central won't accept NEW sessions to that CP

### How long before Disconnected is detected?
- Monitor sends health checks every 5 seconds
- Central expects periodic registration/health messages
- Typical Disconnected detection: 15-30 seconds after Monitor stops

### How does recovery work?
**The system recovers correctly when service is restored to any failed component.**

**Key Principle**: Only restart the failed component - no other restarts needed.

**Recovery Times**:
- Engine recovery: 5-10 seconds after restart
- Monitor recovery: 5-10 seconds (auto re-registers)
- Total system restoration: < 30 seconds

**Example**:
```bash
# CP is Broken (Engine down)
docker start ev-cp-e-1
# Monitor detects recovery automatically
# Central updated to On status
# ✅ No other components need restart
```

### Can I add new CPs without errors?
**Yes!** Adding new instances does not cause any errors.

**Scaling Guarantees**:
- ✅ Unique CP IDs prevent conflicts
- ✅ No configuration changes needed
- ✅ Auto-registration with Central
- ✅ Immediate availability for charging
- ✅ Can add multiple CPs simultaneously

**Example**:
```bash
# Add CP-005
docker run -d --name ev-cp-e-5 -e CP_ID=CP-005 ...
docker run -d --name ev-cp-m-5 -e CP_ID=CP-005 ...
# ✅ Registers automatically
# ✅ Shows as On (Green) when healthy
# ✅ No errors or conflicts
```

---

## Related Documentation

- **[FAULT_TOLERANCE.md](FAULT_TOLERANCE.md)** - Complete fault tolerance (includes Recovery & Scalability section)
- **[FAULT_TOLERANCE_QUICKREF.md](FAULT_TOLERANCE_QUICKREF.md)** - Quick reference guide
- **[AUTONOMOUS_OPERATION_VALIDATION.md](AUTONOMOUS_OPERATION_VALIDATION.md)** - Autonomous operation tests
