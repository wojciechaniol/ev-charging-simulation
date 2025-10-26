#!/bin/bash
# Quick deployment script for Machine 1 (Kafka + Central)
# This script automates the setup process for the personal computer

set -e

echo "=========================================="
echo "🚀 EV Charging - Machine 1 Setup"
echo "   (Kafka + Central Controller)"
echo "=========================================="
echo ""

# Detect IP address
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    MACHINE_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "localhost")
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    MACHINE_IP=$(hostname -I | awk '{print $1}')
else
    echo "⚠️  Unknown OS, defaulting to localhost"
    MACHINE_IP="localhost"
fi

echo "📍 Detected IP: $MACHINE_IP"
echo ""

# Export environment variable
export KAFKA_ADVERTISED_HOST=$MACHINE_IP

echo "🔧 Environment configured:"
echo "   KAFKA_ADVERTISED_HOST=$KAFKA_ADVERTISED_HOST"
echo ""

# Start Kafka
echo "1️⃣  Starting Kafka..."
docker compose up -d kafka

echo "   ⏳ Waiting for Kafka to be ready (30 seconds)..."
sleep 30

# Check Kafka health
echo "   🔍 Checking Kafka status..."
if docker logs ev-kafka 2>&1 | grep -q "started (kafka.server.KafkaRaftServer)"; then
    echo "   ✅ Kafka is running"
else
    echo "   ⚠️  Kafka might still be starting, checking logs..."
    docker logs ev-kafka --tail 20
fi
echo ""

# Start Central Controller
echo "2️⃣  Starting Central Controller..."
docker compose -f docker/docker-compose.remote-kafka.yml up -d ev-central

echo "   ⏳ Waiting for Central to start (10 seconds)..."
sleep 10

# Verify Central
echo "   🔍 Checking Central status..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null || echo '{"status":"error"}')
if echo "$HEALTH_CHECK" | grep -q '"status":"healthy"'; then
    echo "   ✅ Central Controller is healthy"
else
    echo "   ⚠️  Central might still be starting, checking logs..."
    docker logs ev-central --tail 20
fi
echo ""

# Display summary
echo "=========================================="
echo "✅ Machine 1 Setup Complete!"
echo "=========================================="
echo ""
echo "📊 Service URLs:"
echo "   Dashboard: http://localhost:8000"
echo "   Health:    http://localhost:8000/health"
echo ""
echo "📡 Connection Info (share with lab machines):"
echo "   KAFKA_BOOTSTRAP=$MACHINE_IP:9092"
echo "   CENTRAL_HOST=$MACHINE_IP"
echo "   CENTRAL_HTTP_URL=http://$MACHINE_IP:8000"
echo ""
echo "🔥 Firewall Reminder:"
echo "   Make sure ports 9092 and 8000 are accessible"
echo "   macOS: System Preferences > Security & Privacy > Firewall"
echo "   Linux: sudo ufw allow 9092,8000/tcp"
echo ""
echo "📋 Next Steps:"
echo "   1. Open dashboard: http://localhost:8000"
echo "   2. Share IP '$MACHINE_IP' with lab machines"
echo "   3. On lab machines, run deploy-lab-cp.sh or deploy-lab-driver.sh"
echo ""
echo "🛑 To stop services:"
echo "   docker compose down"
echo ""
