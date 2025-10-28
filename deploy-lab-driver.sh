#!/bin/bash
# ⚠️ DEPRECATED: This script is for Linux/macOS only
# For Windows lab deployment, use: deploy-lab-driver.ps1
#
# Quick deployment script for Lab Machine (Driver)
# Run this on Machine 3 (CP2) - Linux/macOS only

set -e

echo "=========================================="
echo "🚀 EV Charging - Lab Driver Setup"
echo "   (Driver Service)"
echo "=========================================="
echo ""

# Check if environment variables are set
if [ -z "$KAFKA_BOOTSTRAP" ]; then
    echo "❌ ERROR: KAFKA_BOOTSTRAP is not set"
    echo ""
    echo "Please run:"
    echo "  export KAFKA_BOOTSTRAP=<personal-machine-ip>:9092"
    echo "  export CENTRAL_HTTP_URL=http://<personal-machine-ip>:8000"
    echo ""
    echo "Example:"
    echo "  export KAFKA_BOOTSTRAP=192.168.1.100:9092"
    echo "  export CENTRAL_HTTP_URL=http://192.168.1.100:8000"
    exit 1
fi

if [ -z "$CENTRAL_HTTP_URL" ]; then
    echo "❌ ERROR: CENTRAL_HTTP_URL is not set"
    echo ""
    echo "Please run:"
    echo "  export CENTRAL_HTTP_URL=http://<personal-machine-ip>:8000"
    exit 1
fi

echo "🔧 Environment configured:"
echo "   KAFKA_BOOTSTRAP=$KAFKA_BOOTSTRAP"
echo "   CENTRAL_HTTP_URL=$CENTRAL_HTTP_URL"
echo ""

# Test connectivity
echo "🔍 Testing connectivity..."

# Test Kafka
echo "   Testing Kafka connection..."
if nc -zv $(echo $KAFKA_BOOTSTRAP | cut -d: -f1) $(echo $KAFKA_BOOTSTRAP | cut -d: -f2) 2>&1 | grep -q "succeeded"; then
    echo "   ✅ Kafka is reachable"
else
    echo "   ❌ Cannot reach Kafka at $KAFKA_BOOTSTRAP"
    echo "   Please check firewall and network connectivity"
    exit 1
fi

# Test Central HTTP
echo "   Testing Central HTTP connection..."
if curl -s -m 5 $CENTRAL_HTTP_URL/health > /dev/null 2>&1; then
    echo "   ✅ Central is reachable"
else
    echo "   ❌ Cannot reach Central at $CENTRAL_HTTP_URL"
    echo "   Please check firewall and network connectivity"
    exit 1
fi
echo ""

# Start Driver services
echo "1️⃣  Starting 5 Driver Services (Alice, Bob, Charlie, David, Eve)..."
docker compose -f docker/docker-compose.remote-kafka.yml up -d \
  ev-driver-alice ev-driver-bob ev-driver-charlie ev-driver-david ev-driver-eve

echo "   ⏳ Waiting for drivers to start (15 seconds)..."
sleep 15
echo ""

# Check services
echo "2️⃣  Checking service status..."
docker compose -f docker/docker-compose.remote-kafka.yml ps --filter "name=ev-driver"
echo ""
echo "   Total Driver services running:"
docker ps --filter "name=ev-driver" --format "{{.Names}}" | wc -l | xargs echo "   Count:"
echo ""

# Verify logs
echo "3️⃣  Verifying connections (sample from Alice and Bob)..."
echo ""
echo "   📋 Driver Alice logs:"
docker logs ev-driver-alice 2>&1 | grep -E "Starting|Kafka|started successfully|requested charging" | tail -5
echo ""
echo "   📋 Driver Bob logs:"
docker logs ev-driver-bob 2>&1 | grep -E "Starting|Kafka|started successfully|requested charging" | tail -5
echo ""

echo "=========================================="
echo "✅ Lab Driver Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Running Services (5 total):"
echo "   - ev-driver-alice  (Port 8100, 5.0s interval)"
echo "   - ev-driver-bob    (Port 8101, 6.0s interval)"
echo "   - ev-driver-charlie(Port 8102, 7.0s interval)"
echo "   - ev-driver-david  (Port 8103, 8.0s interval)"
echo "   - ev-driver-eve    (Port 8104, 4.5s interval)"
echo ""
echo "🔍 Monitor logs:"
echo "   docker logs -f ev-driver-alice"
echo "   docker logs -f ev-driver-bob"
echo ""
echo "🌐 Access Dashboards:"
echo "   Alice:   http://localhost:8100"
echo "   Bob:     http://localhost:8101"
echo "   Charlie: http://localhost:8102"
echo "   David:   http://localhost:8103"
echo "   Eve:     http://localhost:8104"
echo ""
echo "📡 Check available charging points:"
echo "   curl $CENTRAL_HTTP_URL/cp | jq '.charging_points[] | {cp_id, state, engine_state}'"
echo ""
echo "🛑 To stop all services:"
echo "   docker compose -f docker/docker-compose.remote-kafka.yml down"
echo ""
