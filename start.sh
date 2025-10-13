#!/bin/bash
# Quick start script for EV Charging Simulation
# Run this after installing dependencies

set -e

echo "🚀 EV Charging Simulation - Quick Start"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Option selection
echo "Choose deployment option:"
echo "1) Docker Compose (recommended)"
echo "2) Local development (requires local Kafka)"
echo ""
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "🐳 Starting services with Docker Compose..."
        cd docker
        docker-compose up -d
        echo ""
        echo "✅ Services started!"
        echo ""
        echo "📊 Dashboard: http://localhost:8000"
        echo "📝 View logs: docker-compose logs -f"
        echo "🛑 Stop services: docker-compose down"
        ;;
    2)
        echo ""
        echo "🔧 Starting local development mode..."
        echo ""
        echo "Starting Kafka..."
        docker run -d --name ev-kafka -p 9092:9092 \
            -e KAFKA_NODE_ID=1 \
            -e KAFKA_PROCESS_ROLES=broker,controller \
            -e KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093 \
            -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
            -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
            -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
            -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
            -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
            -e CLUSTER_ID=MkU3OEVBNTcwNTJENDM2Qk \
            apache/kafka:3.7.0
        
        echo "⏳ Waiting for Kafka to start..."
        sleep 10
        
        echo ""
        echo "✅ Kafka started!"
        echo ""
        echo "Now run these commands in separate terminals:"
        echo ""
        echo "Terminal 1 (Central):"
        echo "  export PYTHONPATH=."
        echo "  python -m evcharging.apps.ev_central.main"
        echo ""
        echo "Terminal 2 (CP Engine 1):"
        echo "  export PYTHONPATH=."
        echo "  python -m evcharging.apps.ev_cp_e.main --cp-id CP-001 --health-port 8001"
        echo ""
        echo "Terminal 3 (CP Engine 2):"
        echo "  export PYTHONPATH=."
        echo "  python -m evcharging.apps.ev_cp_e.main --cp-id CP-002 --health-port 8002"
        echo ""
        echo "Terminal 4 (CP Monitor 1):"
        echo "  export PYTHONPATH=."
        echo "  python -m evcharging.apps.ev_cp_m.main --cp-id CP-001 --cp-e-port 8001"
        echo ""
        echo "Terminal 5 (CP Monitor 2):"
        echo "  export PYTHONPATH=."
        echo "  python -m evcharging.apps.ev_cp_m.main --cp-id CP-002 --cp-e-port 8002"
        echo ""
        echo "Terminal 6 (Driver):"
        echo "  export PYTHONPATH=."
        echo "  python -m evcharging.apps.ev_driver.main --driver-id driver-alice --requests-file requests.txt"
        echo ""
        echo "📊 Dashboard will be at: http://localhost:8000"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
