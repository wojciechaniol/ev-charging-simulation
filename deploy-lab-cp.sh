#!/bin/bash
# Quick deployment script for Lab Machine (CP Engines + Monitors)
# Run this on Machine 2 (CP1)

set -e

echo "=========================================="
echo "🚀 EV Charging - Lab CP Setup"
echo "   (Charging Point Engines + Monitors)"
echo "=========================================="
echo ""

# Check if environment variables are set
if [ -z "$KAFKA_BOOTSTRAP" ]; then
    echo "❌ ERROR: KAFKA_BOOTSTRAP is not set"
    echo ""
    echo "Please run:"
    echo "  export KAFKA_BOOTSTRAP=<personal-machine-ip>:9092"
    echo "  export CENTRAL_HOST=<personal-machine-ip>"
    echo "  export CENTRAL_PORT=8000"
    echo ""
    echo "Example:"
    echo "  export KAFKA_BOOTSTRAP=192.168.1.100:9092"
    echo "  export CENTRAL_HOST=192.168.1.100"
    echo "  export CENTRAL_PORT=8000"
    exit 1
fi

if [ -z "$CENTRAL_HOST" ]; then
    echo "❌ ERROR: CENTRAL_HOST is not set"
    echo ""
    echo "Please run:"
    echo "  export CENTRAL_HOST=<personal-machine-ip>"
    exit 1
fi

echo "🔧 Environment configured:"
echo "   KAFKA_BOOTSTRAP=$KAFKA_BOOTSTRAP"
echo "   CENTRAL_HOST=$CENTRAL_HOST"
echo "   CENTRAL_PORT=${CENTRAL_PORT:-8000}"
echo ""

# Test connectivity
echo "🔍 Testing connectivity..."

# Test Kafka
echo "   Testing Kafka connection..."
if nc -zv $(echo $KAFKA_BOOTSTRAP | cut -d: -f1) $(echo $KAFKA_BOOTSTRAP | cut -d: -f2) 2>&1 | grep -q "succeeded"; then
    echo "   ✅ Kafka is reachable"
else
    echo "   ❌ Cannot reach Kafka at $KAFKA_BOOTSTRAP"
    echo "   Please check:"
    echo "     1. Personal computer is on and running Kafka"
    echo "     2. Firewall allows port 9092"
    echo "     3. Both machines are on same network"
    exit 1
fi

# Test Central
echo "   Testing Central connection..."
CENTRAL_PORT=${CENTRAL_PORT:-8000}
if curl -s -m 5 http://$CENTRAL_HOST:$CENTRAL_PORT/health > /dev/null 2>&1; then
    echo "   ✅ Central is reachable"
else
    echo "   ❌ Cannot reach Central at http://$CENTRAL_HOST:$CENTRAL_PORT"
    echo "   Please check:"
    echo "     1. Central is running on personal computer"
    echo "     2. Firewall allows port $CENTRAL_PORT"
    exit 1
fi
echo ""

# Start CP services
echo "1️⃣  Starting Charging Point Engines and Monitors..."
docker compose -f docker/docker-compose.remote-kafka.yml up -d \
  ev-cp-e-1 ev-cp-e-2 ev-cp-m-1 ev-cp-m-2

echo "   ⏳ Waiting for services to start (10 seconds)..."
sleep 10
echo ""

# Check services
echo "2️⃣  Checking service status..."
docker compose ps --filter "name=ev-cp"
echo ""

# Verify logs
echo "3️⃣  Verifying connections..."
echo ""
echo "   📋 CP-001 Engine logs:"
docker logs ev-cp-e-1 2>&1 | grep -E "Kafka|ACTIVATED|started successfully" | tail -5
echo ""
echo "   📋 CP-001 Monitor logs:"
docker logs ev-cp-m-1 2>&1 | grep -E "Monitoring|heartbeat|Health check" | tail -5
echo ""

echo "=========================================="
echo "✅ Lab CP Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Running Services:"
echo "   - ev-cp-e-1 (CP-001 Engine)"
echo "   - ev-cp-e-2 (CP-002 Engine)"
echo "   - ev-cp-m-1 (CP-001 Monitor)"
echo "   - ev-cp-m-2 (CP-002 Monitor)"
echo ""
echo "🔍 Monitor logs:"
echo "   docker logs -f ev-cp-e-1"
echo "   docker logs -f ev-cp-m-1"
echo ""
echo "🛑 To stop services:"
echo "   docker compose -f docker/docker-compose.remote-kafka.yml down"
echo ""
