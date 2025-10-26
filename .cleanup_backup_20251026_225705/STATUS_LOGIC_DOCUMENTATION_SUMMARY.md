# 📋 CP Status Logic Documentation - Summary

## What Was Added

This update clarifies the **Monitor and Engine status determination logic** that Central uses to display Charging Point (CP) operational status.

---

## New Documentation Files

### 1. **CP_STATUS_LOGIC.md** ✨ NEW
A comprehensive guide explaining how Central determines CP status based on Monitor and Engine health.

**Contents:**
- ✅ Status determination matrix (Monitor OK/KO × Engine OK/KO)
- ✅ Visual status table with symbols (🟢 On, 🔴 Broken, ⚫ Disconnected)
- ✅ Detailed descriptions of each status state
- ✅ Architecture flow diagrams
- ✅ State transition diagrams
- ✅ Implementation code references
- ✅ Testing procedures for each status transition
- ✅ FAQ section addressing common questions

**Key Concept:**
```
Monitor is the SOLE reporter of CP health to Central
- Monitor_OK + Engine_OK    = On (Green)
- Monitor_OK + Engine_KO    = Broken (Red)
- Monitor_KO + Engine_OK/KO = Disconnected
```

---

## Updated Documentation Files

### 2. **FAULT_TOLERANCE_QUICKREF.md** - Updated
Added a new section: **"CP Status Display Logic"**

**What's New:**
- Status matrix table showing all Monitor/Engine combinations
- Visual symbols for each state (🟢 🔴 ⚫)
- Key points explaining:
  - Disconnected = no messages from Monitor
  - Monitor is sole reporter to Central
  - Even if Engine runs, no Monitor = Disconnected

**Location in file:** After "System Behavior on Component Failures" section

---

### 3. **FAULT_TOLERANCE.md** - Updated
Added a new section: **"CP Status Reporting Architecture"**

**What's New:**
- Complete status matrix with availability column
- Key architectural points explaining the design
- Why Monitor is the sole reporter (separation of concerns)
- Timeout-based detection explanation
- Recovery scenario flows
- Design rationale (why not have Central check Engine directly?)

**Location in file:** After "Overview" section, before "Current Implementation Status"

---

### 4. **README.md** - Updated
Added new documentation section: **"📚 Fault Tolerance Documentation"**

**What's New:**
- Links to all fault tolerance documents
- Specific callout for CP_STATUS_LOGIC.md
- Organized documentation references

**Location in file:** After "📚 Deployment Documentation" section

---

## Status Matrix Summary

| Monitor | Engine | Display | Symbol | Available? |
|---------|--------|---------|--------|-----------|
| ✅ OK | ✅ OK | **On** | 🟢 | ✅ YES |
| ✅ OK | ❌ KO | **Broken** | 🔴 | ❌ NO |
| ❌ KO | ✅ OK | **Disconnected** | ⚫ | ❌ NO |
| ❌ KO | ❌ KO | **Disconnected** | ⚫ | ❌ NO |

---

## Key Takeaways

### 1. Monitor's Role
- **Single source of truth** for CP health reporting
- Performs TCP health checks to Engine every 5 seconds
- Notifies Central of FAULT or HEALTHY status changes
- Must be operational for Central to know CP status

### 2. Status States

**🟢 On (Green)**
- Everything working normally
- Monitor alive and Engine responding
- CP available for new charging sessions

**🔴 Broken (Red)**
- Monitor detected Engine failure
- Monitor still reporting to Central
- Central knows about the problem
- CP unavailable for new sessions

**⚫ Disconnected**
- Central not receiving Monitor messages
- Could be Monitor failure OR network issue
- Central cannot determine Engine state
- CP unavailable for new sessions

### 3. Why This Design?

**Separation of Concerns:**
- Monitor = Observability/Health
- Engine = Charging Operations
- Central = Coordination

**Benefits:**
- Clear responsibility boundaries
- Prevents false positives from network glitches
- Scales better (Central doesn't need to track all Engine endpoints)
- Consistent fault detection methodology

---

## Testing Quick Reference

```bash
# Test Engine Failure → Broken
docker stop ev-cp-e-1
docker logs -f ev-cp-m-1  # See fault detection
docker logs ev-central | grep "BROKEN"

# Test Monitor Failure → Disconnected
docker stop ev-cp-m-1
docker logs ev-central | grep "DISCONNECTED"

# Test Recovery from Broken
docker start ev-cp-e-1
docker logs -f ev-cp-m-1  # See recovery
docker logs ev-central | grep "ON"

# Test Recovery from Disconnected
docker start ev-cp-m-1
docker logs -f ev-cp-m-1  # See re-registration
docker logs ev-central | grep "CP-001"
```

---

## Files Modified

1. ✅ **CP_STATUS_LOGIC.md** - Created (new file)
2. ✅ **FAULT_TOLERANCE_QUICKREF.md** - Updated
3. ✅ **FAULT_TOLERANCE.md** - Updated
4. ✅ **README.md** - Updated

---

## Next Steps

### For Developers
1. Read **CP_STATUS_LOGIC.md** to understand status determination
2. Review state transition diagrams
3. Run the test procedures to see status changes in action

### For Operations
1. Use **FAULT_TOLERANCE_QUICKREF.md** for quick troubleshooting
2. Reference status matrix when investigating CP issues
3. Follow recovery procedures based on status type

### For Documentation
- All documentation is now consistent with Monitor/Engine/Central status logic
- Visual diagrams illustrate the architecture
- Test procedures validate the documented behavior

---

## Related Documentation

- **[CP_STATUS_LOGIC.md](CP_STATUS_LOGIC.md)** - Complete status logic reference
- **[FAULT_TOLERANCE.md](FAULT_TOLERANCE.md)** - Full fault tolerance guide
- **[FAULT_TOLERANCE_QUICKREF.md](FAULT_TOLERANCE_QUICKREF.md)** - Quick reference
- **[README.md](README.md)** - Main project documentation
