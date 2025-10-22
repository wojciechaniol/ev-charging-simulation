#!/bin/sh
# Wait for Kafka to be ready before starting application services
# This eliminates KafkaConnectionError during initial startup

set -e

host="$1"
shift
max_attempts="${KAFKA_WAIT_MAX_ATTEMPTS:-30}"
wait_seconds="${KAFKA_WAIT_SECONDS:-2}"

echo "⏳ Waiting for Kafka at $host to be ready..."
echo "   Max attempts: $max_attempts, Wait interval: ${wait_seconds}s"

attempt=0
until nc -z ${host%%:*} ${host##*:} 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    echo "❌ Kafka at $host did not become available after $max_attempts attempts"
    exit 1
  fi
  
  if [ $((attempt % 5)) -eq 0 ]; then
    echo "   Still waiting... (attempt $attempt/$max_attempts)"
  fi
  
  sleep $wait_seconds
done

echo "✅ Kafka at $host is ready!"
echo "🚀 Starting application: $@"

exec "$@"
