# ⚡ Fault Tolerance Quick Reference

> 🎯 **For a visual quick reference card**, see [CP_STATUS_QUICKREF_CARD.md](CP_STATUS_QUICKREF_CARD.md)  
> 📘 **For complete status logic details**, see [CP_STATUS_LOGIC.md](CP_STATUS_LOGIC.md)

## System Behavior on Component Failures

| Component Fails | What Continues | What Stops | Recovery Method |
|----------------|----------------|------------|-----------------|
| **CP Monitor** | • CP Engine<br>• Active sessions<br>• Other CPs<br>• Drivers | • Health checks<br>• New sessions to that CP | `docker start ev-cp-m-X` |
| **CP Engine** | • Monitor<br>• Other CPs<br>• Drivers<br>• Central | • Active session (that CP)<br>• New sessions to that CP | `docker start ev-cp-e-X` |
| **Driver** | • All CPs<br>• Other drivers<br>• Central<br>• Active session | • Driver requests<br>• Driver updates | `docker start ev-driver-X`<br>(receives missed messages) |
| **Central** | • Active sessions<br>• CP Engines<br>• Drivers | • New session requests<br>• Session coordination | `docker start ev-central`<br>(processes queued msgs) |
| **Kafka** | Nothing | Everything | `docker start ev-kafka`<br>(auto-recovers) |

---

## CP Status Display Logic

**The Monitor is responsible for informing the Central Unit of the CP's status.**

| Monitor Status | Engine Status | Central Display | Description |
|----------------|---------------|-----------------|-------------|
| **Monitor_OK** | **Engine_OK** | 🟢 **On** (Green) | CP is healthy and operational |
| **Monitor_OK** | **Engine_KO** | 🔴 **Broken** (Red) | Engine failed, Monitor detected and reported fault |
| **Monitor_KO** | **Engine_OK** | ⚫ **Disconnected** | No health messages from Monitor |
| **Monitor_KO** | **Engine_KO** | ⚫ **Disconnected** | No health messages from Monitor |

**Key Points:**
- **Disconnected** state occurs when Central does NOT receive any life messages from Monitor
- Monitor is the sole reporter of CP health status to Central
- Even if Engine is running, without Monitor, Central cannot determine CP availability
- Central relies on Monitor's health checks to differentiate between "Broken" and "Disconnected"

---

## Quick Tests

```bash
# Test Monitor Failure
docker stop ev-cp-m-1
docker logs ev-central | grep "CP-001"  # See fault detection
docker start ev-cp-m-1                  # Recovery

# Test Engine Failure  
docker stop ev-cp-e-2
sleep 20  # Wait for monitor to detect
docker logs ev-cp-m-2 | grep "FAULT"   # See detection
docker start ev-cp-e-2                  # Recovery

# Test Driver Disconnect
docker stop ev-driver-alice
sleep 30  # Let session complete
docker start ev-driver-alice
docker logs -f ev-driver-alice          # See missed messages

# Test Central Failure
docker stop ev-central
docker logs ev-cp-e-1 | tail -20        # Sessions continue
docker start ev-central                 # Recovery

# Automated Test Suite
./test-fault-tolerance.sh all
```

---

## Key Observations

### When Monitor Stops:
```
✓ CP Engine continues operation
✓ Active sessions complete normally
✓ Other CPs unaffected
✗ No new sessions accepted for that CP
```

### When Engine Stops:
```
✓ Monitor detects failure (15-20 seconds)
✓ Monitor notifies Central
✓ Other CPs continue normal operation
✗ Active session terminates
✗ No new sessions accepted
```

### When Driver Disconnects:
```
✓ Charging session continues
✓ Session completes normally
✓ Result message queued in Kafka
✓ On reconnect, driver receives all missed messages
```

### When Central Stops:
```
✓ Active charging sessions continue
✓ CP Engines complete sessions
✓ Results queued in Kafka
✗ Cannot coordinate new sessions
✓ On restart, Central processes queue
```

---

## Expected Log Patterns

### Monitor Failure Detection:
```
CP_M:CP-001 | Health check failed (1)
CP_M:CP-001 | Health check failed (2)
CP_M:CP-001 | Health check failed (3)
CP_M:CP-001 | FAULT DETECTED
CP_M:CP-001 | Fault notification sent to Central
```

### Central Fault Handling:
```
Central | CP CP-001 marked as FAULTY
Central | CP CP-001 has active session with driver-alice
```

### Automatic Recovery:
```
CP_M:CP-001 | Health restored
CP_M:CP-001 | Health restoration notification sent to Central
Central | CP CP-001 fault cleared, now available
```

---

## Status Verification

```bash
# Check all services
docker compose ps

# Check health status
docker inspect ev-kafka --format='{{.State.Health.Status}}'

# Check fault events
docker logs ev-central 2>&1 | grep -i "fault"

# Check active sessions
docker logs ev-central 2>&1 | grep "START_SUPPLY" | tail -10

# Check session completions
docker logs ev-cp-e-1 2>&1 | grep "Session.*completed"
```

---

## Recovery & Scalability

### ✅ Automatic Recovery
**The system recovers correctly when service is restored to any failed component.**

**Key Principle**: Only restart the failed component - all others auto-detect recovery.

```bash
# Restart ONLY the failed component:
docker start ev-cp-e-X      # Engine recovery
docker start ev-cp-m-X      # Monitor recovery
docker start ev-driver-X    # Driver recovery
docker start ev-central     # Central recovery
docker start ev-kafka       # Kafka recovery

# ✅ NO other restarts needed
# ✅ Components auto-reconnect
# ✅ State synchronizes automatically
# ✅ Recovery time: < 30 seconds
```

### ✅ Horizontal Scaling
**Adding new instances does not cause any errors.**

```bash
# Add new CP (no configuration changes needed)
docker run -d --name ev-cp-e-5 -e CP_ID=CP-005 ...
docker run -d --name ev-cp-m-5 -e CP_ID=CP-005 ...
# ✅ Auto-registers with Central
# ✅ Immediately available

# Add new Driver (no configuration changes needed)
docker run -d --name ev-driver-charlie -e DRIVER_ID=driver-charlie ...
# ✅ Auto-connects to Kafka
# ✅ Can request immediately

# Add multiple CPs simultaneously
for i in {6..10}; do
  docker run -d --name ev-cp-e-$i -e CP_ID=CP-00$i ...
done
# ✅ No conflicts or errors
# ✅ Scales linearly
```

**Guarantees**:
- ✅ No naming conflicts (unique IDs)
- ✅ No resource contention
- ✅ No configuration updates needed
- ✅ No service disruption
- ✅ Zero downtime scaling

---

## Critical Points

1. **Monitor ≠ Engine**: Monitor can fail while engine continues
2. **Kafka Durability**: Messages preserved across component failures
3. **Consumer Groups**: Drivers receive all messages on reconnect
4. **Independent Sessions**: CP Engines run sessions autonomously
5. **Graceful Degradation**: System capacity reduces, doesn't crash
6. **Minimal Restarts**: Only failed component needs restart
7. **Dynamic Scaling**: Add instances anytime without errors

---

## Files to Reference

- **`FAULT_TOLERANCE_GUIDE.md`** - Complete implementation details
- **`FAULT_TOLERANCE.md`** - Technical architecture (with Recovery & Scalability section)
- **`test-fault-tolerance.sh`** - Automated test suite

---

**Remember**: The system is designed so that **any single component failure only affects that component's service**. The rest continues operating normally. Recovery requires **minimum restarts** and scaling is **error-free**.

✅ Fault Tolerant | 🛡️ Resilient | 🔄 Auto-Recovery
