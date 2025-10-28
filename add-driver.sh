#!/bin/bash
# Script to dynamically add a new Driver at runtime
# Usage: ./add-driver.sh <driver_name> [dashboard_port]
#
# Example: ./add-driver.sh frank 8105

set -e

if [ -z "$1" ]; then
    echo "❌ Usage: $0 <driver_name> [dashboard_port]"
    echo "   Example: $0 frank 8105"
    exit 1
fi

DRIVER_NAME=$1
DRIVER_ID="driver-${DRIVER_NAME}"
DASHBOARD_PORT=${2:-8105}
REQUEST_INTERVAL=${3:-5.0}

KAFKA_BOOTSTRAP=${KAFKA_BOOTSTRAP:-kafka:9092}
CENTRAL_HTTP_URL=${CENTRAL_HTTP_URL:-http://ev-central:8000}

echo "🚗 Adding New Driver"
echo "===================="
echo "Driver Name:      $DRIVER_NAME"
echo "Driver ID:        $DRIVER_ID"
echo "Dashboard Port:   $DASHBOARD_PORT"
echo "Request Interval: $REQUEST_INTERVAL seconds"
echo "Kafka:            $KAFKA_BOOTSTRAP"
echo ""

# Create docker-compose override file
OVERRIDE_FILE="docker-compose.driver-${DRIVER_NAME}.yml"

cat > "$OVERRIDE_FILE" <<EOF
# Dynamically added driver-${DRIVER_NAME}
# Created: $(date)
# Can be stopped with: docker compose -f $OVERRIDE_FILE down

services:
  ev-driver-${DRIVER_NAME}:
    build:
      context: .
      dockerfile: docker/Dockerfile.driver
    container_name: ev-driver-${DRIVER_NAME}
    environment:
      DRIVER_DRIVER_ID: ${DRIVER_ID}
      DRIVER_KAFKA_BOOTSTRAP: ${KAFKA_BOOTSTRAP}
      DRIVER_REQUEST_INTERVAL: ${REQUEST_INTERVAL}
      DRIVER_LOG_LEVEL: INFO
      DRIVER_DASHBOARD_PORT: ${DASHBOARD_PORT}
      DRIVER_CENTRAL_HTTP_URL: ${CENTRAL_HTTP_URL}
    volumes:
      - ./requests.txt:/app/requests.txt:ro
    ports:
      - "${DASHBOARD_PORT}:${DASHBOARD_PORT}"
    networks:
      - evcharging-network
    restart: unless-stopped

networks:
  evcharging-network:
    external: true
    name: ev-charging-simulation-1_evcharging-network
EOF

echo "✅ Created override file: $OVERRIDE_FILE"
echo ""

# Start the service
echo "🚀 Starting Driver service..."
docker compose -f "$OVERRIDE_FILE" up -d

echo ""
echo "⏳ Waiting for service to start (5 seconds)..."
sleep 5

# Verify
echo ""
echo "📊 Verification:"
if docker ps | grep -q "ev-driver-${DRIVER_NAME}"; then
    echo "   ✅ Driver (ev-driver-${DRIVER_NAME}) is running"
else
    echo "   ❌ Driver failed to start"
fi

echo ""
echo "🌐 Access Driver Dashboard:"
echo "   http://localhost:${DASHBOARD_PORT}"
echo ""
echo "🔍 Check available CPs:"
echo "   curl http://localhost:${DASHBOARD_PORT}/charging-points | jq '.[0:3]'"
echo ""
echo "📝 View logs:"
echo "   docker logs ev-driver-${DRIVER_NAME}"
echo ""
echo "🛑 To remove this driver:"
echo "   docker compose -f $OVERRIDE_FILE down"
echo "   rm $OVERRIDE_FILE"
echo ""
echo "✅ Driver ${DRIVER_ID} deployment complete!"
