#!/bin/bash
# Script to simulate a crash by stopping a random or specific service
# Usage: ./simulate-crash.sh [service_name]
#
# Example: ./simulate-crash.sh ev-cp-e-5  # Stop specific CP engine
# Example: ./simulate-crash.sh            # Stop random service

set -e

if [ -n "$1" ]; then
    # Stop specific service
    SERVICE=$1
    echo "💥 Simulating crash of: $SERVICE"
    docker stop "$SERVICE"
    echo "✅ $SERVICE has been stopped (crashed)"
    echo ""
    echo "🔄 To restart: docker start $SERVICE"
else
    # Stop random service (CP engine or driver)
    SERVICES=($(docker ps --filter "name=ev-cp-e" --filter "name=ev-driver" --format "{{.Names}}"))
    
    if [ ${#SERVICES[@]} -eq 0 ]; then
        echo "❌ No running CP engines or drivers found"
        exit 1
    fi
    
    RANDOM_INDEX=$((RANDOM % ${#SERVICES[@]}))
    SERVICE=${SERVICES[$RANDOM_INDEX]}
    
    echo "🎲 Randomly selected: $SERVICE"
    echo "💥 Simulating crash..."
    docker stop "$SERVICE"
    echo "✅ $SERVICE has been stopped (crashed)"
    echo ""
    echo "🔄 To restart: docker start $SERVICE"
fi

echo ""
echo "📊 Current system status:"
docker ps --filter "name=ev-" --format "table {{.Names}}\t{{.Status}}"
