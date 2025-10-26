#!/bin/bash
# Script to dynamically add a new Driver to the system
# Usage: ./add-driver.sh <driver_name> [dashboard_port]
#
# Example: ./add-driver.sh frank 8105
# This will create driver-frank with dashboard on port 8105

set -e

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <driver_name> [dashboard_port]"
    echo "Example: $0 frank 8105"
    exit 1
fi

DRIVER_NAME=$1
DRIVER_ID="driver-${DRIVER_NAME}"
DASHBOARD_PORT=${2:-8100}  # Default port 8100

echo "🚗 Adding Driver: $DRIVER_ID"
echo "   Dashboard: http://localhost:${DASHBOARD_PORT}"
echo ""

# Create temporary docker-compose override for this driver
OVERRIDE_FILE="docker-compose.driver-${DRIVER_NAME}.yml"

cat > "$OVERRIDE_FILE" << EOF
services:
  ev-driver-${DRIVER_NAME}:
    image: ev-charging-simulation-ev-driver-alice
    container_name: ev-driver-${DRIVER_NAME}
    environment:
      DRIVER_DRIVER_ID: ${DRIVER_ID}
      DRIVER_KAFKA_BOOTSTRAP: \${KAFKA_BOOTSTRAP:-kafka:9092}
      DRIVER_REQUEST_INTERVAL: 5.0
      DRIVER_LOG_LEVEL: INFO
      DRIVER_DASHBOARD_PORT: ${DASHBOARD_PORT}
      DRIVER_CENTRAL_HTTP_URL: http://ev-central:8000
    volumes:
      - ./requests.txt:/app/requests.txt:ro
    ports:
      - "${DASHBOARD_PORT}:${DASHBOARD_PORT}"
    networks:
      - ev-charging-simulation_evcharging-network
    restart: unless-stopped

networks:
  ev-charging-simulation_evcharging-network:
    external: true
EOF

echo "📝 Generated configuration: $OVERRIDE_FILE"
echo ""

# Start the service
echo "🚀 Starting $DRIVER_ID service..."
docker compose -f "$OVERRIDE_FILE" up -d

echo ""
echo "✅ $DRIVER_ID is now running!"
echo ""
echo "🌐 Dashboard: http://localhost:${DASHBOARD_PORT}"
echo ""
echo "📊 Check logs:"
echo "   docker logs ev-driver-${DRIVER_NAME}"
echo ""
echo "🛑 To stop this driver:"
echo "   docker compose -f $OVERRIDE_FILE down"
echo ""
echo "💡 The override file has been saved as: $OVERRIDE_FILE"
echo "   You can reuse it later with: docker compose -f $OVERRIDE_FILE up -d"
