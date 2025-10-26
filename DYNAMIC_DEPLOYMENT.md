# Dynamic Deployment and Fault Injection Guide

This guide explains how to dynamically add/remove charging points and drivers, and simulate crashes during system operation - perfect for instructor-led demonstrations and testing.

## 🎯 Overview

The system is designed to support:
- ✅ **Dynamic scaling**: Add new CPs or drivers at runtime
- ✅ **Fault injection**: Simulate crashes of any component
- ✅ **Multi-machine deployment**: Deploy components on different hosts
- ✅ **Hot reconfiguration**: No system restart required

## 📦 Prerequisites

1. The main system must be running:
   ```bash
   docker compose up -d
   ```

2. Images should be built (done automatically on first `docker compose up`)

## 🔌 Adding a New Charging Point

Use the `add-cp.sh` script to dynamically add a new charging point:

```bash
./add-cp.sh <cp_number> [kw_rate] [euro_rate]
```

### Examples:

```bash
# Add CP-011 with default values (22kW, €0.30/kWh)
./add-cp.sh 11

# Add CP-012 with 75kW charging at €0.38/kWh
./add-cp.sh 12 75.0 0.38

# Add CP-020 with 350kW ultra-fast charging at €0.50/kWh
./add-cp.sh 20 350.0 0.50
```

### What Happens:

1. ✅ Creates a docker-compose override file (`docker-compose.cp-XX.yml`)
2. ✅ Starts both CP engine and monitor containers
3. ✅ CP automatically connects to Kafka and registers with central controller
4. ✅ Monitor begins health checking the CP
5. ✅ CP becomes available for charging requests immediately

### Verify:

```bash
# Check CP engine logs
docker logs ev-cp-e-11

# Check monitor logs
docker logs ev-cp-m-11

# Verify in central dashboard
curl http://localhost:8000/cp | jq '.charging_points[] | select(.cp_id=="CP-011")'
```

### Stop a Dynamically Added CP:

```bash
docker compose -f docker-compose.cp-11.yml down
```

## 🚗 Adding a New Driver

Use the `add-driver.sh` script to dynamically add a new driver:

```bash
./add-driver.sh <driver_name> [dashboard_port]
```

### Examples:

```bash
# Add driver-frank with dashboard on port 8105
./add-driver.sh frank 8105

# Add driver-grace with dashboard on port 8106
./add-driver.sh grace 8106
```

### What Happens:

1. ✅ Creates a docker-compose override file (`docker-compose.driver-XX.yml`)
2. ✅ Starts driver container with unique ID
3. ✅ Driver dashboard becomes available on specified port
4. ✅ Driver automatically connects to Kafka and can make charging requests

### Access Dashboard:

```bash
# Open in browser
open http://localhost:8105

# Or check via API
curl http://localhost:8105/charging-points | jq '.[0:3]'
```

### Stop a Dynamically Added Driver:

```bash
docker compose -f docker-compose.driver-frank.yml down
```

## 💥 Simulating Crashes

Use the `simulate-crash.sh` script to simulate component failures:

```bash
./simulate-crash.sh [service_name]
```

### Examples:

```bash
# Crash a specific CP engine
./simulate-crash.sh ev-cp-e-5

# Crash a specific driver
./simulate-crash.sh ev-driver-alice

# Crash a random service (for unpredictable testing)
./simulate-crash.sh
```

### What Happens:

1. ✅ Service is immediately stopped (simulating a crash)
2. ✅ Monitor detects health check failures within 2-6 seconds
3. ✅ Central controller marks CP as faulty
4. ✅ Active charging sessions may fail or be interrupted
5. ✅ Fault tolerance mechanisms activate

### Recovery:

```bash
# Restart the crashed service
docker start ev-cp-e-5

# Or restart multiple services
docker start ev-cp-e-5 ev-cp-m-5
```

### Monitor the Recovery:

```bash
# Watch central controller logs
docker logs -f ev-central

# Check CP status after recovery
curl http://localhost:8000/cp | jq '.charging_points[] | select(.cp_id=="CP-005")'
```

## 🌐 Multi-Machine Deployment

To deploy components across different machines:

### Option 1: Use Remote Kafka

1. **Machine 1** (Kafka + Central):
   ```bash
   # Start Kafka and central controller
   docker compose up -d ev-kafka ev-central
   ```

2. **Machine 2** (Charging Points):
   ```bash
   # Export Kafka location
   export KAFKA_BOOTSTRAP=<machine1-ip>:9092
   
   # Start CPs
   ./add-cp.sh 1 22.0 0.30
   ./add-cp.sh 2 50.0 0.35
   ```

3. **Machine 3** (Drivers):
   ```bash
   # Export Kafka location
   export KAFKA_BOOTSTRAP=<machine1-ip>:9092
   
   # Start drivers
   ./add-driver.sh alice 8100
   ./add-driver.sh bob 8101
   ```

### Option 2: Use Existing Kafka Cluster

Edit `docker/docker-compose.remote-kafka.yml`:

```yaml
environment:
  CENTRAL_KAFKA_BOOTSTRAP: your-kafka-cluster:9092
```

Then start services:

```bash
docker compose -f docker/docker-compose.remote-kafka.yml up -d
```

## 📊 Monitoring and Verification

### Check All Running Services:

```bash
docker ps --filter "name=ev-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Check System Status:

```bash
# Central dashboard
curl http://localhost:8000/cp | jq '.charging_points | length'

# Active sessions
curl http://localhost:8000/cp | jq '.active_requests'

# All CPs status
curl http://localhost:8000/cp | jq '.charging_points[] | {cp_id, state, engine_state, monitor_status}'
```

### Check Driver Activity:

```bash
# Driver alice logs
docker logs ev-driver-alice --tail 20

# All active charging sessions
docker ps --filter "name=ev-driver" --format "{{.Names}}" | xargs -I {} sh -c 'echo "=== {} ===" && docker logs {} 2>&1 | grep "IN_PROGRESS" | tail -1'
```

## 🧪 Testing Scenarios

### Scenario 1: Scale Up During Peak Load

```bash
# Start with 10 CPs
docker compose up -d

# Simulate peak demand - add more CPs
./add-cp.sh 11 150.0 0.40
./add-cp.sh 12 150.0 0.40
./add-cp.sh 13 350.0 0.50

# Add more drivers
./add-driver.sh frank 8105
./add-driver.sh grace 8106
```

### Scenario 2: Rolling Failure Recovery

```bash
# Crash CP-005
./simulate-crash.sh ev-cp-e-5

# Wait 10 seconds, observe fault detection
sleep 10

# Recover
docker start ev-cp-e-5

# Verify recovery
docker logs ev-cp-m-5 --tail 20
```

### Scenario 3: Cascading Failures

```bash
# Crash multiple CPs
./simulate-crash.sh ev-cp-e-3
./simulate-crash.sh ev-cp-e-7
./simulate-crash.sh ev-cp-e-9

# Monitor system behavior
docker logs -f ev-central

# Recover one at a time
docker start ev-cp-e-3
sleep 15
docker start ev-cp-e-7
sleep 15
docker start ev-cp-e-9
```

### Scenario 4: Driver Crash During Charging

```bash
# Start charging
curl -X POST http://localhost:8100/drivers/driver-alice/requests \
  -H "Content-Type: application/json" \
  -d '{"cp_id": "CP-002", "vehicle_id": "VEH-001"}'

# Crash driver during charging
./simulate-crash.sh ev-driver-alice

# Observe CP and session state
curl http://localhost:8000/cp | jq '.charging_points[] | select(.cp_id=="CP-002")'

# Restart driver
docker start ev-driver-alice
```

## 🔧 Troubleshooting

### CP Not Appearing in Dashboard

```bash
# Check if CP engine started
docker logs ev-cp-e-XX

# Check if connected to Kafka
docker logs ev-cp-e-XX | grep "Kafka consumer started"

# Check central controller received status
docker logs ev-central | grep "CP-0XX"
```

### Driver Can't Request Charging

```bash
# Verify CPs are ACTIVATED
curl http://localhost:8000/cp | jq '.charging_points[] | select(.engine_state!="ACTIVATED")'

# Check driver connection
docker logs ev-driver-XX | grep "started successfully"

# Test manually
curl -X POST http://localhost:8100/drivers/driver-alice/requests \
  -H "Content-Type: application/json" \
  -d '{"cp_id": "CP-001", "vehicle_id": "VEH-001"}'
```

### Clean Up All Dynamic Services

```bash
# Stop all dynamically created CPs
ls docker-compose.cp-*.yml | xargs -I {} docker compose -f {} down

# Stop all dynamically created drivers
ls docker-compose.driver-*.yml | xargs -I {} docker compose -f {} down

# Remove override files
rm docker-compose.cp-*.yml docker-compose.driver-*.yml
```

## 📝 Notes for Instructors

1. **Grading Scenarios**: You can deploy any number of CPs/drivers and crash them at will
2. **Performance Testing**: Add CPs incrementally to observe scaling behavior
3. **Fault Tolerance Testing**: Crash components during active sessions
4. **Recovery Testing**: Verify automatic recovery and state synchronization
5. **Network Partitions**: Use `docker network disconnect` to simulate network issues

## 🚀 Advanced Usage

### Custom CP Configuration

Edit the generated `docker-compose.cp-XX.yml` file to customize:
- Power ratings (kW)
- Pricing (€/kWh)
- Health check intervals
- Network settings

### Batch Operations

```bash
# Add 5 CPs at once
for i in {11..15}; do ./add-cp.sh $i 50.0 0.35; done

# Add 3 drivers at once
for driver in frank grace henry; do ./add-driver.sh $driver $((8100 + i)); i=$((i+1)); done
```

### Export/Import Configuration

```bash
# Save current state
docker ps --filter "name=ev-" --format "{{.Names}}" > deployed-services.txt

# Later, restart from saved state
cat deployed-services.txt | grep "ev-cp-e" | sed 's/ev-cp-e-//' | xargs -I {} ./add-cp.sh {}
```

---

**Need Help?** Check the logs: `docker logs <container-name>`
