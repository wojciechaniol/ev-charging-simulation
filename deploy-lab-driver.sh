#!/bin/bash
# Quick deployment script for Lab Machine (Driver)
# Run this on Machine 3 (CP2)

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

# Start Driver service
echo "1️⃣  Starting Driver Service..."
docker compose -f docker/docker-compose.remote-kafka.yml up -d ev-driver

echo "   ⏳ Waiting for driver to start (10 seconds)..."
sleep 10
echo ""

# Check service
echo "2️⃣  Checking service status..."
docker compose ps --filter "name=ev-driver"
echo ""

# Verify logs
echo "3️⃣  Verifying connection..."
echo ""
echo "   📋 Driver logs:"
docker logs ev-driver 2>&1 | grep -E "Starting|Kafka|started successfully|requested charging" | tail -10
echo ""

echo "=========================================="
echo "✅ Lab Driver Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Running Service:"
echo "   - ev-driver (driver-alice)"
echo ""
echo "🔍 Monitor logs:"
echo "   docker logs -f ev-driver"
echo ""
echo "📡 Check available charging points:"
echo "   curl $CENTRAL_HTTP_URL/cp | jq '.charging_points[] | {cp_id, state, engine_state}'"
echo ""
echo "🛑 To stop service:"
echo "   docker compose -f docker/docker-compose.remote-kafka.yml down"
echo ""
