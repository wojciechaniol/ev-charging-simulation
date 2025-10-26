#!/bin/bash
# Script to dynamically add a new Charging Point to the system
# Usage: ./add-cp.sh <cp_number> [kw_rate] [euro_rate]
#
# Example: ./add-cp.sh 11 75.0 0.38
# This will create CP-011 with 75kW charging at €0.38/kWh

set -e

# Check arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <cp_number> [kw_rate] [euro_rate]"
    echo "Example: $0 11 75.0 0.38"
    exit 1
fi

CP_NUM=$1
CP_ID=$(printf "CP-%03d" $CP_NUM)
KW_RATE=${2:-22.0}  # Default 22kW
EURO_RATE=${3:-0.30}  # Default €0.30/kWh

# Use remote kafka compose file if KAFKA_BOOTSTRAP is set, otherwise use main
COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}

echo "🔌 Adding Charging Point: $CP_ID"
echo "   Power: ${KW_RATE} kW"
echo "   Rate: €${EURO_RATE}/kWh"
echo ""

# Create temporary docker-compose override for this CP
OVERRIDE_FILE="docker-compose.cp-${CP_NUM}.yml"

cat > "$OVERRIDE_FILE" << EOF
services:
  ev-cp-e-${CP_NUM}:
    image: ev-charging-simulation-ev-cp-e-1
    container_name: ev-cp-e-${CP_NUM}
    environment:
      CP_ENGINE_KAFKA_BOOTSTRAP: \${KAFKA_BOOTSTRAP:-kafka:9092}
      CP_ENGINE_CP_ID: ${CP_ID}
      CP_ENGINE_HEALTH_PORT: 8001
      CP_ENGINE_LOG_LEVEL: INFO
      CP_ENGINE_KW_RATE: ${KW_RATE}
      CP_ENGINE_EURO_RATE: ${EURO_RATE}
    networks:
      - ev-charging-simulation_evcharging-network
    restart: unless-stopped

  ev-cp-m-${CP_NUM}:
    image: ev-charging-simulation-ev-cp-m-1
    container_name: ev-cp-m-${CP_NUM}
    environment:
      CP_MONITOR_CP_ID: ${CP_ID}
      CP_MONITOR_CP_E_HOST: ev-cp-e-${CP_NUM}
      CP_MONITOR_CP_E_PORT: 8001
      CP_MONITOR_CENTRAL_HOST: ev-central
      CP_MONITOR_CENTRAL_PORT: 8000
      CP_MONITOR_HEALTH_INTERVAL: 2.0
      CP_MONITOR_LOG_LEVEL: INFO
    depends_on:
      - ev-cp-e-${CP_NUM}
    networks:
      - ev-charging-simulation_evcharging-network
    restart: unless-stopped

networks:
  ev-charging-simulation_evcharging-network:
    external: true
EOF

echo "📝 Generated configuration: $OVERRIDE_FILE"
echo ""

# Start the services
echo "🚀 Starting $CP_ID services..."
docker compose -f "$OVERRIDE_FILE" up -d

echo ""
echo "✅ $CP_ID is now running!"
echo ""
echo "📊 Check status:"
echo "   docker logs ev-cp-e-${CP_NUM}"
echo "   docker logs ev-cp-m-${CP_NUM}"
echo ""
echo "🛑 To stop this CP:"
echo "   docker compose -f $OVERRIDE_FILE down"
echo ""
echo "💡 The override file has been saved as: $OVERRIDE_FILE"
echo "   You can reuse it later with: docker compose -f $OVERRIDE_FILE up -d"
