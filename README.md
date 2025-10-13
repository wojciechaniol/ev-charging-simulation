# ⚡ EV Charging Simulation

A distributed electric vehicle charging management system built with Python, Docker, Kafka, and TCP sockets.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🏗️ Architecture

This project simulates a distributed EV charging infrastructure with the following components:

```
┌─────────────────┐         ┌──────────────┐         ┌─────────────────┐
│   EV Driver     │────────▶│  EV Central  │◀────────│  EV CP Monitor  │
│   (Client)      │         │ (Controller) │         │  (Health Check) │
└─────────────────┘         └──────────────┘         └─────────────────┘
        │                           │                          │
        │                           │                          │
        │         Kafka Topics      │                          │
        └───────────────────────────┴──────────────────────────┘
                                    │
                                    ▼
                          ┌──────────────────┐
                          │  EV CP Engine    │
                          │  (Power Control) │
                          └──────────────────┘
```

### Components

- **EV Central** - Central controller with web dashboard for monitoring
- **EV CP Engine (CP_E)** - Charging point engine managing power delivery and state
- **EV CP Monitor (CP_M)** - Health monitoring and fault detection
- **EV Driver** - Client for requesting charging sessions
- **Apache Kafka** - Event streaming backbone for distributed messaging

### Charging Point States

```
DISCONNECTED → ACTIVATED → SUPPLYING → ACTIVATED
      ↓            ↓             ↓
    FAULT ← ← ← ← FAULT ← ← ← FAULT
      ↓
  ACTIVATED

ACTIVATED ↔ STOPPED (administrative control)
```

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended) - [Install Docker](https://docs.docker.com/get-docker/)
- **Python 3.11+** (for local development) - [Download Python](https://www.python.org/downloads/)
- **Make** (optional, for convenience commands)

### Running with Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd ev-charging-simulation
   ```

2. **Start all services:**
   ```bash
   make up
   # or
   cd docker && docker-compose up
   ```

3. **Access the dashboard:**
   
   Open http://localhost:8000 in your browser

4. **View logs:**
   ```bash
   make logs
   # or
   cd docker && docker-compose logs -f
   ```

5. **Stop services:**
   ```bash
   make down
   ```

### Running Locally (Without Docker)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Kafka** (using Docker):
   ```bash
   docker run -d --name kafka \
     -p 9092:9092 \
     -e KAFKA_NODE_ID=1 \
     -e KAFKA_PROCESS_ROLES=broker,controller \
     -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093 \
     -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
     -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
     -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
     -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
     -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
     -e CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk \
     apache/kafka:3.7.0
   ```

3. **Start services in separate terminals:**

   **Terminal 1 - EV Central:**
   ```bash
   export PYTHONPATH=.
   python -m evcharging.apps.ev_central.main \
     --kafka-bootstrap localhost:9092 \
     --http-port 8000 \
     --listen-port 9999
   ```

   **Terminal 2 - CP Engine 1:**
   ```bash
   export PYTHONPATH=.
   python -m evcharging.apps.ev_cp_e.main \
     --kafka-bootstrap localhost:9092 \
     --cp-id CP-001 \
     --health-port 8001
   ```

   **Terminal 3 - CP Engine 2:**
   ```bash
   export PYTHONPATH=.
   python -m evcharging.apps.ev_cp_e.main \
     --kafka-bootstrap localhost:9092 \
     --cp-id CP-002 \
     --health-port 8002
   ```

   **Terminal 4 - CP Monitor 1:**
   ```bash
   export PYTHONPATH=.
   python -m evcharging.apps.ev_cp_m.main \
     --cp-id CP-001 \
     --cp-e-host localhost \
     --cp-e-port 8001 \
     --central-host localhost \
     --central-port 8000
   ```

   **Terminal 5 - CP Monitor 2:**
   ```bash
   export PYTHONPATH=.
   python -m evcharging.apps.ev_cp_m.main \
     --cp-id CP-002 \
     --cp-e-host localhost \
     --cp-e-port 8002 \
     --central-host localhost \
     --central-port 8000
   ```

   **Terminal 6 - EV Driver:**
   ```bash
   export PYTHONPATH=.
   python -m evcharging.apps.ev_driver.main \
     --driver-id driver-alice \
     --kafka-bootstrap localhost:9092 \
     --requests-file requests.txt
   ```

## 📊 Dashboard

The web dashboard at http://localhost:8000 displays:

- **Real-time charging point states** with color-coded badges
- **Active charging sessions** with driver information
- **Live telemetry:** Power delivery (kW) and cost (€)
- **Auto-refresh** every 2 seconds for real-time updates

### Dashboard Preview

![Dashboard](docs/dashboard-preview.png)

*The dashboard shows all charging points with their current states, active sessions, and real-time power/cost metrics.*

## 🧪 Testing

Run unit tests:

```bash
make test
# or
pytest evcharging/tests/ -v
```

**Test coverage includes:**
- Message validation and JSON schemas
- State machine transitions
- Guard conditions
- Error handling

Expected output:
```
evcharging/tests/test_messages.py ........ [50%]
evcharging/tests/test_states.py .......... [100%]

======================== 25 passed in 0.5s ========================
```

## 📁 Project Structure

```
ev-charging-simulation/
├── evcharging/
│   ├── apps/
│   │   ├── ev_central/         # Central controller & dashboard
│   │   │   ├── main.py         # Controller logic
│   │   │   ├── dashboard.py    # FastAPI web interface
│   │   │   └── tcp_server.py   # TCP control plane
│   │   ├── ev_cp_e/            # Charging Point Engine
│   │   │   └── main.py         # State machine & telemetry
│   │   ├── ev_cp_m/            # Charging Point Monitor
│   │   │   └── main.py         # Health checks & registration
│   │   └── ev_driver/          # Driver client
│   │       └── main.py         # Request handler
│   ├── common/
│   │   ├── config.py           # Pydantic settings
│   │   ├── kafka.py            # Kafka helpers
│   │   ├── messages.py         # Message schemas
│   │   ├── states.py           # State machine
│   │   └── utils.py            # Utility functions
│   └── tests/
│       ├── test_messages.py    # Message validation tests
│       └── test_states.py      # State machine tests
├── docker/
│   ├── docker-compose.yml      # Service orchestration
│   └── Dockerfile.*            # Service images
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── requests.txt                # Sample CP IDs for driver
├── Makefile                    # Convenience commands
└── README.md                   # This file
```

## 🔧 Configuration

Copy `.env.example` to `.env` and adjust settings:

```bash
cp .env.example .env
```

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `CENTRAL_KAFKA_BOOTSTRAP` | Kafka broker address | `localhost:9092` |
| `CENTRAL_HTTP_PORT` | Dashboard HTTP port | `8000` |
| `CP_ENGINE_KW_RATE` | Power delivery rate (kW) | `22.0` |
| `CP_ENGINE_EURO_RATE` | Cost per kWh (€) | `0.30` |
| `DRIVER_REQUEST_INTERVAL` | Time between requests (s) | `4.0` |

See `.env.example` for all available options.

## 📡 Kafka Topics

The system uses the following Kafka topics:

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `central.commands` | Central → CP_E | Commands (start/stop charging) |
| `cp.status` | CP_E → Central | State updates |
| `cp.telemetry` | CP_E → Central | Real-time charging data |
| `driver.requests` | Driver → Central | Charging requests |
| `driver.updates` | Central → Driver | Status updates |

### Message Formats

All messages use JSON format with Pydantic validation. Example:

```json
// Driver Request
{
  "request_id": "req-abc123",
  "driver_id": "driver-alice",
  "cp_id": "CP-001",
  "ts": "2025-10-13T12:00:00Z"
}

// CP Telemetry
{
  "cp_id": "CP-001",
  "kw": 22.5,
  "euros": 3.75,
  "driver_id": "driver-alice",
  "session_id": "session-xyz",
  "ts": "2025-10-13T12:00:05Z"
}
```

## 🎯 Usage Example

### Happy Path Flow

1. **Driver sends request** for CP-001
2. **Central validates** CP availability → Sends ACCEPTED
3. **Central commands** CP_E to start supply
4. **CP_E transitions** ACTIVATED → SUPPLYING
5. **Telemetry flows** every 1 second (kW, €)
6. **Driver receives** IN_PROGRESS updates
7. **Session completes** after 10 seconds
8. **CP_E transitions** SUPPLYING → ACTIVATED
9. **Driver receives** COMPLETED status

### Sample Log Output

```
2025-10-13 12:00:05 | INFO | Driver:driver-alice | 📤 Requested charging at CP-001
2025-10-13 12:00:06 | INFO | Driver:driver-alice | ✅ CP-001 | ACCEPTED
2025-10-13 12:00:07 | INFO | CP_E:CP-001 | Charging session started for driver-alice
2025-10-13 12:00:08 | INFO | Driver:driver-alice | 🔋 CP-001 | IN_PROGRESS | 22.0 kW, €0.01
2025-10-13 12:00:09 | INFO | Driver:driver-alice | 🔋 CP-001 | IN_PROGRESS | 22.0 kW, €0.02
...
2025-10-13 12:00:16 | INFO | CP_E:CP-001 | Session completed. Total: 0.06 kWh, €0.02
2025-10-13 12:00:16 | INFO | Driver:driver-alice | ✔️ CP-001 | COMPLETED
```

## 🛠️ Development

### Adding More Charging Points

Edit `docker/docker-compose.yml` and add new services:

```yaml
ev-cp-e-3:
  build:
    context: ..
    dockerfile: docker/Dockerfile.cp_e
  environment:
    CP_ENGINE_CP_ID: CP-003
    CP_ENGINE_HEALTH_PORT: 8001
    # ... other config

ev-cp-m-3:
  build:
    context: ..
    dockerfile: docker/Dockerfile.cp_m
  environment:
    CP_MONITOR_CP_ID: CP-003
    CP_MONITOR_CP_E_HOST: ev-cp-e-3
    # ... other config
```

### Running Tests

```bash
# All tests
make test

# Specific test file
pytest evcharging/tests/test_states.py -v

# With coverage
pytest --cov=evcharging evcharging/tests/
```

### Code Quality

```bash
# Type checking (optional)
mypy evcharging/

# Linting (optional)
ruff check evcharging/
```

## 🐛 Troubleshooting

### Services won't start

```bash
# Check Docker status
docker ps

# Check Kafka logs
docker logs ev-kafka

# Restart everything
make clean && make up
```

### Port conflicts

```bash
# Check what's using the port
lsof -i :8000
lsof -i :9092

# Kill the process or change port in .env
```

### Connection errors

```bash
# Verify network
docker network ls
docker network inspect docker_evcharging-network

# Check Kafka topics
docker exec -it ev-kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

## 📚 API Reference

### Central HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard HTML |
| `/health` | GET | Health check |
| `/cp` | GET | List all charging points |
| `/cp/{cp_id}` | GET | Get specific CP details |
| `/cp/register` | POST | Register/update CP |
| `/telemetry` | GET | Get all telemetry |

### Example API Calls

```bash
# Health check
curl http://localhost:8000/health

# List all charging points
curl http://localhost:8000/cp | jq

# Get specific CP
curl http://localhost:8000/cp/CP-001 | jq

# Get telemetry
curl http://localhost:8000/telemetry | jq
```

## 🔮 Future Enhancements

- [ ] **Database persistence** - SQLite/PostgreSQL for CP & driver data
- [ ] **TCP framing protocol** - Implement `<STX><DATA><ETX><LRC>`
- [ ] **Advanced dashboard** - Charts with Chart.js/Plotly
- [ ] **Authentication** - JWT-based auth for drivers
- [ ] **Reservation system** - Book charging slots in advance
- [ ] **Payment processing** - Simulate payment flows
- [ ] **Load balancing** - Distribute load across CPs
- [ ] **Metrics & monitoring** - Prometheus + Grafana
- [ ] **Mobile app** - React Native client
- [ ] **WebSocket support** - Real-time dashboard updates

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Apache Kafka for event streaming
- FastAPI for the web framework
- Pydantic for data validation
- Docker for containerization

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check the [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for common operations
- Review test files for usage examples

---

**Happy Charging! ⚡🚗**
