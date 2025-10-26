# 🎯 CP Status Quick Reference Card

```
╔═══════════════════════════════════════════════════════════════════╗
║                   CP STATUS DETERMINATION                         ║
║                    (Monitor + Engine)                             ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  Monitor sends health checks → Engine → Monitor reports Central  ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  🟢 ON (Green)                                                    ║
║  ├─ Monitor: ✅ Operational                                       ║
║  ├─ Engine:  ✅ Responding to health checks                       ║
║  ├─ Status:  Available for charging                              ║
║  └─ Action:  None - system healthy                               ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  🔴 BROKEN (Red)                                                  ║
║  ├─ Monitor: ✅ Operational & reporting                           ║
║  ├─ Engine:  ❌ NOT responding (timeout/crashed)                  ║
║  ├─ Status:  Unavailable - fault detected                        ║
║  └─ Action:  docker start ev-cp-e-X                              ║
║              (Monitor will auto-report recovery)                  ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  ⚫ DISCONNECTED                                                   ║
║  ├─ Monitor: ❌ NOT sending messages                              ║
║  ├─ Engine:  ❓ Unknown (could be up or down)                     ║
║  ├─ Status:  Unavailable - no visibility                         ║
║  └─ Action:  docker start ev-cp-m-X                              ║
║              (will re-register & check Engine)                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## Decision Flow

```
Central receives message from Monitor?
         │
    ┌────┴────┐
   YES       NO
    │         │
    │         └──→ DISCONNECTED ⚫
    │
    ▼
Engine healthy (per Monitor)?
    │
┌───┴───┐
│       │
YES     NO
│       │
│       └──→ BROKEN 🔴
│
└──→ ON 🟢
```

## Status Transitions

```
        ┌──────────────┐
        │ DISCONNECTED │ ⚫ (Initial/Monitor Down)
        └──────┬───────┘
               │ Monitor starts + Engine OK
               ▼
        ┌─────────┐
    ┌──▶│   ON    │ 🟢
    │   └─┬───┬───┘
    │     │   │
    │     │   └─────────────────┐
    │     │                     │
    │     │ Engine fails        │ Monitor stops
    │     │                     │
    │     ▼                     ▼
    │   ┌───────┐         ┌──────────────┐
    │   │BROKEN │ 🔴      │ DISCONNECTED │ ⚫
    │   └───┬───┘         └──────────────┘
    │       │
    └───────┘ Engine recovers
```

## Troubleshooting

| You See | Most Likely Cause | First Action |
|---------|-------------------|--------------|
| 🟢 → 🔴 | Engine crashed | Check Engine logs: `docker logs ev-cp-e-X` |
| 🟢 → ⚫ | Monitor stopped | Check Monitor logs: `docker logs ev-cp-m-X` |
| ⚫ → ⚫ (persistent) | Monitor won't start | Check container status: `docker ps -a` |
| 🔴 → 🔴 (persistent) | Engine won't start | Check Engine logs for errors |

## Recovery Commands

```bash
# Recover from BROKEN (🔴)
docker start ev-cp-e-X
# Wait 10-20 seconds for Monitor to detect recovery

# Recover from DISCONNECTED (⚫)
docker start ev-cp-m-X
# Monitor will re-register and report status

# Check status
docker logs ev-central | grep "CP-00X"

# Verify health checks
docker logs ev-cp-m-X | grep "Health check"
```

## Key Principles

1. **Monitor = Observer**
   - Reports what it sees
   - Single source of truth for CP health
   - Detects Engine failures via TCP health checks

2. **Central = Decision Maker**
   - Trusts Monitor's reports
   - Falls back to DISCONNECTED if no Monitor messages
   - Uses status to determine CP availability

3. **Engine = Worker**
   - Doesn't report its own status directly
   - Responds to Monitor's health checks
   - Continues operations even if Monitor fails

## Health Check Flow

```
Every 5 seconds:
    Monitor → TCP PING → Engine
                            │
                  ┌─────────┴─────────┐
                  │                   │
                  OK                  TIMEOUT
                  │                   │
                  ▼                   ▼
            consecutive=0      consecutive++
                  │                   │
                  │           (if consecutive >= 3)
                  │                   │
                  ▼                   ▼
            Monitor:          Monitor: FAULT
            "HEALTHY"         Report to Central
                  │                   │
                  ▼                   ▼
            Central: ON      Central: BROKEN
```

## For More Info

- **Full Guide**: [CP_STATUS_LOGIC.md](CP_STATUS_LOGIC.md)
- **Quick Ref**: [FAULT_TOLERANCE_QUICKREF.md](FAULT_TOLERANCE_QUICKREF.md)
- **Complete**: [FAULT_TOLERANCE.md](FAULT_TOLERANCE.md)
