#!/bin/bash
# Wait for Kafka to be ready before starting services
# This script ensures Kafka broker is fully initialized

set -e

KAFKA_HOST="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
MAX_ATTEMPTS=60
ATTEMPT=0

echo "⏳ Waiting for Kafka at $KAFKA_HOST to be ready..."

# Extract host and port
IFS=':' read -r HOST PORT <<< "$KAFKA_HOST"

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Try to connect to Kafka
    if nc -z "$HOST" "$PORT" 2>/dev/null; then
        echo "✅ Kafka is accepting connections at $KAFKA_HOST"
        
        # Additional check: Try to list topics (requires kafka-topics.sh in PATH)
        if command -v kafka-topics.sh &> /dev/null; then
            if kafka-topics.sh --bootstrap-server "$KAFKA_HOST" --list &> /dev/null; then
                echo "✅ Kafka broker is fully operational"
                exit 0
            fi
        else
            # If kafka-topics.sh not available, just rely on TCP connection
            echo "✅ Kafka TCP connection successful (broker validation skipped)"
            exit 0
        fi
    fi
    
    echo "   Attempt $ATTEMPT/$MAX_ATTEMPTS: Kafka not ready yet, waiting 2 seconds..."
    sleep 2
done

echo "❌ ERROR: Kafka did not become ready after $MAX_ATTEMPTS attempts"
echo "   Please check:"
echo "   1. Kafka container is running: docker ps | grep kafka"
echo "   2. Kafka logs: docker logs <kafka-container-name>"
echo "   3. Network connectivity to $KAFKA_HOST"
exit 1
