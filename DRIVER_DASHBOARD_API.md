# 🚗 EV Driver Dashboard API Specification

## Overview

The Driver Dashboard provides a comprehensive self-service interface for EV drivers to discover charging points, manage charging sessions, and receive real-time notifications.

**Base URL**: `http://localhost:<DRIVER_DASHBOARD_PORT>`
**Default Port**: 8100 (configurable per driver)

---

## 🎯 Features

### ✅ Implemented Features

1. **Charging Point Discovery**
   - ✅ View all available charging points
   - ✅ Real-time status (FREE / OCCUPIED / OFFLINE)
   - ✅ Filter by city, connector type, power rating, availability
   - ✅ View detailed CP information (power, price, location, amenities)
   - ✅ Distance calculation (if GPS available)

2. **Session Management**
   - ✅ Request charging session from selected CP
   - ✅ View live status (PENDING / APPROVED / CHARGING / COMPLETED)
   - ✅ Real-time energy and cost tracking
   - ✅ Stop active charging session
   - ✅ Cancel pending request before approval
   - ✅ View session history and receipts

3. **Favorites & Personalization**
   - ✅ Mark favorite charging points
   - ✅ Quick access to favorites
   - ✅ Filter favorite CPs

4. **Notifications & Alerts**
   - ✅ Session approval/denial notifications
   - ✅ CP offline warnings during request
   - ✅ Broadcast alerts from central (maintenance/outages)
   - ✅ Real-time updates via polling

5. **Queue Management**
   - ✅ View queue length at occupied CPs
   - ✅ Estimated wait times

---

## 📡 API Endpoints

### Health Check

#### `GET /health`
Health check endpoint for the driver dashboard.

**Response:**
```json
{
  "status": "healthy",
  "service": "driver-dashboard"
}
```

---

### Charging Points

#### `GET /charging-points`
Get all charging points with optional filters.

**Query Parameters:**
- `city` (string, optional): Filter by city name
- `connector_type` (string, optional): Filter by connector (Type 2, CCS, CHAdeMO)
- `min_power_kw` (float, optional): Minimum power rating
- `only_available` (boolean, optional): Return only FREE points

**Response:**
```json
[
  {
    "cp_id": "CP-001",
    "name": "Downtown Fast Charger",
    "status": "FREE",
    "power_kw": 50.0,
    "connector_type": "CCS",
    "location": {
      "address": "123 Main St",
      "city": "Springfield",
      "latitude": 42.1234,
      "longitude": -71.5678,
      "distance_km": 2.5
    },
    "queue_length": 0,
    "estimated_wait_minutes": 0,
    "favorite": false
  }
]
```

#### `GET /charging-points/{cp_id}`
Get detailed information about a specific charging point.

**Response:**
```json
{
  "cp_id": "CP-001",
  "name": "Downtown Fast Charger",
  "status": "FREE",
  "power_kw": 50.0,
  "connector_type": "CCS",
  "location": { ... },
  "queue_length": 0,
  "estimated_wait_minutes": 0,
  "favorite": false,
  "amenities": ["WiFi", "Restroom", "Coffee Shop"],
  "price_eur_per_kwh": 0.42,
  "last_updated": "2025-10-25T12:00:00Z"
}
```

---

### Session Management

#### `POST /drivers/{driver_id}/requests`
Request a new charging session.

**Request Body:**
```json
{
  "cp_id": "CP-001",
  "vehicle_id": "vehicle-1",
  "preferred_start": "2025-10-25T14:00:00Z"  // optional
}
```

**Response (202 Accepted):**
```json
{
  "session_id": "pending-req-abc123",
  "request_id": "req-abc123",
  "cp_id": "CP-001",
  "status": "PENDING",
  "queue_position": null,
  "started_at": null,
  "completed_at": null,
  "energy_kwh": null,
  "cost_eur": null
}
```

#### `GET /drivers/{driver_id}/sessions/current`
Get the currently active session (if any).

**Response:**
```json
{
  "session_id": "session-xyz789",
  "request_id": "req-abc123",
  "cp_id": "CP-001",
  "status": "CHARGING",
  "queue_position": null,
  "started_at": "2025-10-25T12:00:00Z",
  "completed_at": null,
  "energy_kwh": 15.5,
  "cost_eur": 6.51
}
```

**Possible Statuses:**
- `PENDING` - Waiting for approval from central
- `APPROVED` - Approved, waiting to start
- `CHARGING` - Active charging session
- `COMPLETED` - Session finished successfully
- `DENIED` - Request denied by central
- `FAILED` - Session failed due to error
- `STOPPED` - Manually stopped by driver
- `CANCELLED` - Request cancelled before approval

#### `DELETE /drivers/{driver_id}/requests/{request_id}`
Cancel a pending charging request (before session starts).

**Response:** `204 No Content`

#### `POST /drivers/{driver_id}/sessions/{session_id}/stop`
Stop an active charging session.

**Response:**
```json
{
  "session_id": "session-xyz789",
  "request_id": "req-abc123",
  "cp_id": "CP-001",
  "status": "STOPPED",
  "started_at": "2025-10-25T12:00:00Z",
  "completed_at": "2025-10-25T12:30:00Z",
  "energy_kwh": 25.5,
  "cost_eur": 10.71
}
```

#### `GET /drivers/{driver_id}/sessions/history`
Get historical charging sessions.

**Response:**
```json
[
  {
    "session_id": "session-xyz789",
    "request_id": "req-abc123",
    "cp_id": "CP-001",
    "status": "COMPLETED",
    "started_at": "2025-10-25T12:00:00Z",
    "completed_at": "2025-10-25T12:30:00Z",
    "energy_kwh": 25.5,
    "cost_eur": 10.71,
    "receipt_url": "/receipts/session-xyz789.pdf"
  }
]
```

---

### Favorites

#### `GET /drivers/{driver_id}/favorites`
Get all favorite charging points.

**Response:**
```json
[
  {
    "cp_id": "CP-001",
    "name": "Downtown Fast Charger",
    "status": "FREE",
    ...
  }
]
```

#### `POST /drivers/{driver_id}/favorites`
Add a charging point to favorites.

**Request Body:**
```json
{
  "cp_id": "CP-001"
}
```

**Response:** `204 No Content`

#### `DELETE /drivers/{driver_id}/favorites/{cp_id}`
Remove a charging point from favorites.

**Response:** `204 No Content`

---

### Notifications

#### `GET /drivers/{driver_id}/notifications`
Get all notifications for the driver.

**Response:**
```json
[
  {
    "notification_id": "note-abc123",
    "created_at": "2025-10-25T12:00:00Z",
    "message": "Session approved for CP-001",
    "type": "SESSION",
    "read": false
  },
  {
    "notification_id": "note-xyz789",
    "created_at": "2025-10-25T11:55:00Z",
    "message": "Charging point CP-003 is currently offline.",
    "type": "ALERT",
    "read": false
  }
]
```

**Notification Types:**
- `SESSION` - Session-related updates
- `QUEUE` - Queue position changes
- `ALERT` - Warnings and alerts

#### `GET /drivers/{driver_id}/alerts`
Get broadcast alerts from central controller.

**Response:**
```json
[
  {
    "alert_id": "alert-123",
    "title": "Scheduled Maintenance",
    "message": "CP-001 and CP-002 will be offline from 2am-4am",
    "severity": "INFO",
    "effective_at": "2025-10-26T02:00:00Z",
    "expires_at": "2025-10-26T04:00:00Z"
  }
]
```

**Severity Levels:**
- `INFO` - General information
- `WARN` - Warning about service issues
- `CRITICAL` - Critical system alert

---

## 🌐 Web Dashboard

### `GET /`
Interactive HTML dashboard for drivers.

**Features:**
- Real-time charging point status
- Active session monitoring with live cost updates
- Filtering and search capabilities
- Favorite charging points management
- One-click session requests
- Session control (cancel/stop)
- Visual notifications
- Auto-refresh every 2 seconds

**Access:**
```
http://localhost:8100/  (alice)
http://localhost:8101/  (bob)
http://localhost:8102/  (charlie)
http://localhost:8103/  (david)
http://localhost:8104/  (eve)
```

---

## 🔄 Real-time Updates

The dashboard automatically polls the central controller every 1.5 seconds to:
- Update charging point statuses
- Refresh active session telemetry (energy, cost)
- Detect offline charging points
- Update queue lengths and wait times

**Update Mechanism:**
- Central polling loop in driver application
- Session state synchronized with central controller
- Automatic UI refresh every 2 seconds
- Notifications displayed for 5 seconds

---

## 📊 Status Flow Diagram

```
Driver Request Flow:
┌─────────┐
│ Driver  │
│ Selects │
│   CP    │
└────┬────┘
     │
     ▼
┌─────────────┐     ┌──────────┐
│   PENDING   │────▶│ APPROVED │
│  (Request   │     │(Waiting) │
│   Sent)     │     └────┬─────┘
└─────┬───────┘          │
      │                  ▼
      │            ┌──────────┐
      │            │ CHARGING │◀─── Real-time updates
      │            │ (Active) │     (energy, cost)
      │            └────┬─────┘
      │                 │
      ▼                 ▼
┌──────────┐      ┌───────────┐
│  DENIED  │      │ COMPLETED │
│ (Rejected│      │ (Finished)│
└──────────┘      └───────────┘
      │                 │
      └────────┬────────┘
               ▼
      ┌────────────────┐
      │Session History │
      │  with Receipt  │
      └────────────────┘
```

---

## 🚀 Usage Examples

### Starting a Driver Dashboard

```bash
# Alice's dashboard on port 8100
DRIVER_DASHBOARD_PORT=8100 DRIVER_DRIVER_ID=driver-alice python -m evcharging.apps.ev_driver.main

# Bob's dashboard on port 8101
DRIVER_DASHBOARD_PORT=8101 DRIVER_DRIVER_ID=driver-bob python -m evcharging.apps.ev_driver.main
```

### Requesting a Charging Session (API)

```bash
# Request charging at CP-001
curl -X POST http://localhost:8100/drivers/driver-alice/requests \
  -H "Content-Type: application/json" \
  -d '{"cp_id": "CP-001", "vehicle_id": "vehicle-1"}'
```

### Checking Active Session

```bash
# Get current session status
curl http://localhost:8100/drivers/driver-alice/sessions/current | jq
```

### Filtering Charging Points

```bash
# Find all DC fast chargers with >40kW in Springfield
curl "http://localhost:8100/charging-points?city=Springfield&connector_type=CCS&min_power_kw=40" | jq
```

### Managing Favorites

```bash
# Add CP-001 to favorites
curl -X POST http://localhost:8100/drivers/driver-alice/favorites \
  -H "Content-Type: application/json" \
  -d '{"cp_id": "CP-001"}'

# Get all favorites
curl http://localhost:8100/drivers/driver-alice/favorites | jq
```

---

## 🎨 Dashboard Features

### Visual Indicators
- 🟢 **GREEN** (FREE) - Available for charging
- 🟠 **ORANGE** (OCCUPIED) - Currently in use
- 🔴 **RED** (OFFLINE) - Not operational
- ⭐ **GOLD STAR** - Favorite charging point
- 🔋 **PULSING** - Active charging session

### Session Information Display
- Real-time energy delivery (kWh)
- Live cost accumulation (€)
- Session duration
- Status updates
- Action buttons (Cancel/Stop)

### Filtering Options
- 📍 City/Location
- 🔌 Connector type
- ⚡ Power rating
- 📊 Availability status

---

## 🔐 Security Considerations

1. **Driver Authentication**: Each driver has a unique `driver_id`
2. **Endpoint Validation**: All endpoints validate driver_id matches
3. **Session Ownership**: Drivers can only control their own sessions
4. **CORS Enabled**: For web dashboard access

---

## 📈 Performance

- **Polling Interval**: 1.5 seconds (configurable)
- **UI Refresh**: 2 seconds (configurable)
- **Notification Duration**: 5 seconds
- **Request Timeout**: 30 seconds per charging request
- **Session History**: Unlimited (in-memory, production should use DB)

---

## 🐛 Error Handling

### Common Error Responses

**404 Not Found:**
```json
{
  "detail": "Driver not found"
}
```

**404 Not Found (CP):**
```json
{
  "detail": "Charging point not found"
}
```

**400 Bad Request:**
```json
{
  "detail": "Invalid request payload"
}
```

---

## 📝 Notes

1. **Real-time Cost Updates**: The dashboard displays cost with 4 decimal precision (€0.0123) updating every second during charging
2. **Distance Calculation**: Currently returns static values; integrate GPS for accurate distances
3. **Queue Management**: Queue length and wait time are estimates based on current occupancy
4. **Session History**: Stored in memory; use persistent storage for production
5. **Receipt Generation**: Receipt URLs are placeholders; implement PDF generation for production

---

## 🔄 Future Enhancements

### Potential Features (Not Yet Implemented)
- [ ] WebSocket support for true real-time push notifications
- [ ] Payment integration
- [ ] Route planning to charging points
- [ ] Reservation system (book ahead)
- [ ] Push notifications to mobile devices
- [ ] Rating/review system for charging points
- [ ] Social features (share favorite spots)
- [ ] Carbon footprint tracking
- [ ] Integration with vehicle API for battery status
- [ ] Multi-vehicle support per driver

---

## 📚 Related Documentation

- [Project README](README.md)
- [Central Dashboard API](evcharging/apps/ev_central/dashboard.py)
- [Driver Configuration](evcharging/common/config.py)
- [Charging Point Metadata](evcharging/common/charging_points.py)

---

## 🤝 Support

For issues or questions about the Driver Dashboard:
1. Check the logs for detailed error messages
2. Verify charging point metadata is configured
3. Ensure central controller is running
4. Confirm Kafka connectivity

**Log Location**: Console output with structured logging via `loguru`
