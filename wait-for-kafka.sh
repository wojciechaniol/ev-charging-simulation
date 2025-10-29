#!/bin/bash
# Wait for Kafka to be ready before starting services
# This script ensures Kafka broker is fully initialized

set -e

# Get Kafka host from environment or use default
KAFKA_HOST="${KAFKA_BOOTSTRAP:-${CP_ENGINE_KAFKA_BOOTSTRAP:-${CP_MONITOR_KAFKA_BOOTSTRAP:-kafka:9092}}}"
MAX_ATTEMPTS=60
ATTEMPT=0

echo "⏳ Waiting for Kafka at $KAFKA_HOST to be ready..."

# Extract host and port
KAFKA_HOST_CLEAN="${KAFKA_HOST#*://}"
IFS=':' read -r HOST PORT <<< "$KAFKA_HOST_CLEAN"

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Try to connect to Kafka
    if nc -z -w 2 "$HOST" "$PORT" >/dev/null 2>&1; then
        echo "✅ Kafka is accepting connections at $KAFKA_HOST"
        echo "✅ Starting application..."
        
        # Start the actual application passed as arguments
        # If no arguments, start the service based on SERVICE_TYPE env var or container name
        if [ $# -eq 0 ]; then
            # First check SERVICE_TYPE environment variable
            if [ -n "$SERVICE_TYPE" ]; then
                case "$SERVICE_TYPE" in
                    "central")
                        exec python -m evcharging.apps.ev_central.main
                        ;;
                    "cp-engine"|"cp-e")
                        exec python -m evcharging.apps.ev_cp_e.main
                        ;;
                    "cp-monitor"|"cp-m")
                        exec python -m evcharging.apps.ev_cp_m.main
                        ;;
                    "driver")
                        exec python -m evcharging.apps.ev_driver.main
                        ;;
                    *)
                        echo "❌ ERROR: Unknown SERVICE_TYPE: $SERVICE_TYPE"
                        exit 1
                        ;;
                esac
            # Fallback: Auto-detect based on HOSTNAME or container name
            elif [[ "$HOSTNAME" == *"cp-m"* ]] || [[ "$CONTAINER_NAME" == *"cp-m"* ]]; then
                exec python -m evcharging.apps.ev_cp_m.main
            elif [[ "$HOSTNAME" == *"cp-e"* ]] || [[ "$CONTAINER_NAME" == *"cp-e"* ]]; then
                exec python -m evcharging.apps.ev_cp_e.main
            elif [[ "$HOSTNAME" == *"driver"* ]] || [[ "$CONTAINER_NAME" == *"driver"* ]]; then
                exec python -m evcharging.apps.ev_driver.main
            else
                # Default to central
                exec python -m evcharging.apps.ev_central.main
            fi
        else
            # Execute the command passed as arguments
            exec "$@"
        fi
    fi
    
    echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS: Kafka cannot reach $HOST:$PORT"
    sleep 2
done

echo "❌ ERROR: Kafka did not become ready after $MAX_ATTEMPTS attempts"
echo "   Please check:"
echo "   1. Kafka container is running: docker ps | grep kafka"
echo "   2. Kafka logs: docker logs <kafka-container-name>"
echo "   3. Network connectivity to $KAFKA_HOST"
exit 1