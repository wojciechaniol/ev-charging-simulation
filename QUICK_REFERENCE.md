# EV Charging Simulation - Quick Reference

## 🚀 Start Commands

### Docker (Recommended)
```bash
make up              # Start all services
make logs            # View logs
make down            # Stop services
make clean           # Clean up everything
```

### Local Development
```bash
# Install dependencies first
pip install -r requirements.txt

# Then run the start script
chmod +x start.sh
./start.sh
```

## 📡 Service Endpoints

| Service | Port | Description |
|---------|------|-------------|
| EV Central Dashboard | 8000 | Web UI at http://localhost:8000 |
| EV Central TCP | 9999 | Control plane (future use) |
| CP Engine Health | 8001-800x | Health check endpoints |
| Kafka | 9092 | Message broker |

## 🧪 Test Commands

```bash
# Run all tests
make test
pytest evcharging/tests/ -v

# Run specific test file
pytest evcharging/tests/test_messages.py -v
pytest evcharging/tests/test_states.py -v

# Check types (optional)
mypy evcharging/
```

## 📊 Kafka Topics

| Topic | Purpose |
|-------|---------|
| `central.commands` | Central → CP_E commands |
| `cp.status` | CP_E → Central state updates |
| `cp.telemetry` | CP_E → Central real-time data |
| `driver.requests` | Driver → Central charging requests |
| `driver.updates` | Central → Driver status updates |

## 🔄 State Transitions

```
DISCONNECTED → ACTIVATED → SUPPLYING → ACTIVATED
      ↓            ↓             ↓
    FAULT ← ← ← ← FAULT ← ← ← FAULT
      ↓
  ACTIVATED

ACTIVATED ↔ STOPPED (admin control)
```

## 📝 Message Examples

### Driver Request
```json
{
  "request_id": "req-abc123",
  "driver_id": "driver-alice",
  "cp_id": "CP-001",
  "ts": "2025-10-13T12:00:00Z"
}
```

### CP Telemetry
```json
{
  "cp_id": "CP-001",
  "kw": 22.5,
  "euros": 3.75,
  "driver_id": "driver-alice",
  "session_id": "session-xyz",
  "ts": "2025-10-13T12:00:05Z"
}
```

## 🛠️ Troubleshooting

### Services won't start
```bash
# Check Docker
docker ps

# Check Kafka health
docker logs ev-kafka

# Restart everything
make clean && make up
```

### Connection errors
```bash
# Check network
docker network ls
docker network inspect docker_evcharging-network

# Check Kafka topics
docker exec -it ev-kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### Port conflicts
```bash
# Check what's using the port
lsof -i :8000
lsof -i :9092

# Kill process or change port in .env
```

## 🎯 Development Workflow

1. **Make changes** to code
2. **Run tests**: `make test`
3. **Rebuild Docker**: `cd docker && docker-compose build`
4. **Restart**: `make down && make up`
5. **View logs**: `make logs`

## 📚 Key Files to Modify

| File | Purpose |
|------|---------|
| `requests.txt` | CP IDs for driver to request |
| `.env` | Service configuration |
| `evcharging/common/config.py` | Settings schemas |
| `evcharging/common/states.py` | State machine logic |
| `evcharging/apps/*/main.py` | Service implementations |

## 🔍 Monitoring

### Check Service Health
```bash
# Central
curl http://localhost:8000/health

# CP list
curl http://localhost:8000/cp

# Specific CP
curl http://localhost:8000/cp/CP-001

# Telemetry
curl http://localhost:8000/telemetry
```

### Docker Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ev-central
docker-compose logs -f ev-cp-e-1
docker-compose logs -f ev-driver
```

## 🎨 Customization

### Add More CPs
1. Edit `docker/docker-compose.yml`
2. Add new `ev-cp-e-X` and `ev-cp-m-X` services
3. Update `CP_ENGINE_CP_ID` and `CP_MONITOR_CP_ID`

### Change Charging Parameters
```bash
# Edit .env or docker-compose.yml
CP_ENGINE_KW_RATE=50.0      # Power delivery
CP_ENGINE_EURO_RATE=0.40    # Price per kWh
```

### Modify Request Interval
```bash
DRIVER_REQUEST_INTERVAL=10.0  # Seconds between requests
```

## 🐛 Debug Mode

```bash
# Enable debug logging
export CENTRAL_LOG_LEVEL=DEBUG
export CP_ENGINE_LOG_LEVEL=DEBUG
export DRIVER_LOG_LEVEL=DEBUG

# Or in docker-compose.yml
environment:
  CENTRAL_LOG_LEVEL: DEBUG
```

## 📞 Support

For issues or questions:
1. Check `README.md` for full documentation
2. Review `PROJECT_SUMMARY.md` for architecture details
3. Run tests to verify installation: `make test`
