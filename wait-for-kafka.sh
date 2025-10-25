#!/bin/sh
# Wait for Kafka to be ready before starting application services
# This eliminates KafkaConnectionError during initial startup

set -e

host_arg="${1:-}"
[ -n "$host_arg" ] && shift || true

# Resolve bootstrap host/port from available environment variables.
# Preference order allows per-service overrides while keeping backwards compatibility
# with the original hard-coded host.
bootstrap_target="${KAFKA_BOOTSTRAP:-${CENTRAL_KAFKA_BOOTSTRAP:-${CP_ENGINE_KAFKA_BOOTSTRAP:-${CP_MONITOR_KAFKA_BOOTSTRAP:-${DRIVER_KAFKA_BOOTSTRAP:-${host_arg:-kafka:9092}}}}}}"

# Some services (e.g., CP monitors) may only specify a Central host/port. Fall back to that
# when no Kafka bootstrap is configured.
if [ "$bootstrap_target" = "kafka:9092" ] && [ -n "$CP_MONITOR_CENTRAL_HOST" ]; then
  bootstrap_target="${CP_MONITOR_CENTRAL_HOST}:${CP_MONITOR_CENTRAL_PORT:-8000}"
fi

# Split host/port for nc checks
wait_host="${bootstrap_target%%:*}"
wait_port="${bootstrap_target##*:}"

max_attempts="${KAFKA_WAIT_MAX_ATTEMPTS:-30}"
wait_seconds="${KAFKA_WAIT_SECONDS:-2}"

echo "⏳ Waiting for service at ${wait_host}:${wait_port} to be ready..."
echo "   Max attempts: $max_attempts, Wait interval: ${wait_seconds}s"

attempt=0
until nc -z "$wait_host" "$wait_port" 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ $attempt -ge $max_attempts ]; then
    echo "❌ Service at ${wait_host}:${wait_port} did not become available after $max_attempts attempts"
    exit 1
  fi
  
  if [ $((attempt % 5)) -eq 0 ]; then
    echo "   Still waiting... (attempt $attempt/$max_attempts)"
  fi
  
  sleep $wait_seconds
done

echo "✅ Service at ${wait_host}:${wait_port} is ready!"
echo "🚀 Starting application: $@"

exec "$@"
