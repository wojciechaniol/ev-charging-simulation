#!/bin/bash
# ⚠️ DEPRECATED: This script is for Linux/macOS only
# For Windows lab deployment, use: deploy-lab-cp.ps1
#
# Quick deployment script for Lab Machine (CP Engines + Monitors)
# Run this on Machine 2 (CP1) - Linux/macOS only

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
echo "1️⃣  Starting 5 Charging Point Engines and 5 Monitors (10 services)..."
docker compose -f docker/docker-compose.remote-kafka.yml up -d \
  ev-cp-e-1 ev-cp-e-2 ev-cp-e-3 ev-cp-e-4 ev-cp-e-5 \
  ev-cp-m-1 ev-cp-m-2 ev-cp-m-3 ev-cp-m-4 ev-cp-m-5

echo "   ⏳ Waiting for services to start (15 seconds)..."
sleep 15
echo ""

# Check services
echo "2️⃣  Checking service status..."
docker compose -f docker/docker-compose.remote-kafka.yml ps --filter "name=ev-cp"
echo ""
echo "   Total CP services running:"
docker ps --filter "name=ev-cp" --format "{{.Names}}" | wc -l | xargs echo "   Count:"
echo ""

# Verify logs
echo "3️⃣  Verifying connections (sample from CP-001 and CP-003)..."
echo ""
echo "   📋 CP-001 Engine logs:"
docker logs ev-cp-e-1 2>&1 | grep -E "Kafka|ACTIVATED|started successfully" | tail -3
echo ""
echo "   📋 CP-001 Monitor logs:"
docker logs ev-cp-m-1 2>&1 | grep -E "Monitoring|heartbeat|Health check" | tail -3
echo ""
echo "   📋 CP-003 Engine logs:"
docker logs ev-cp-e-3 2>&1 | grep -E "Kafka|ACTIVATED|started successfully" | tail -3
echo ""

echo "=========================================="
echo "✅ Lab CP Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Running Services (10 total):"
echo "   Engines: ev-cp-e-1, ev-cp-e-2, ev-cp-e-3, ev-cp-e-4, ev-cp-e-5"
echo "   Monitors: ev-cp-m-1, ev-cp-m-2, ev-cp-m-3, ev-cp-m-4, ev-cp-m-5"
echo ""
echo "⚡ Power Ratings:"
echo "   CP-001: 22.0 kW  (€0.30/kWh)"
echo "   CP-002: 50.0 kW  (€0.35/kWh)"
echo "   CP-003: 43.0 kW  (€0.32/kWh)"
echo "   CP-004: 150.0 kW (€0.40/kWh)"
echo "   CP-005: 7.2 kW   (€0.28/kWh)"
echo ""
echo "🔍 Monitor logs:"
echo "   docker logs -f ev-cp-e-1"
echo "   docker logs -f ev-cp-m-1"
echo ""
echo "🛑 To stop all services:"
echo "   docker compose -f docker/docker-compose.remote-kafka.yml down"
echo ""
