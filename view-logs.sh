#!/bin/bash
# View logs from all EV Charging Simulation services
# Usage: ./view-logs.sh [service-type]
# 
# service-type options:
#   all       - Show all service logs (default)
#   central   - Show only Central controller logs
#   cp        - Show all Charging Point Engine logs
#   monitor   - Show all CP Monitor logs
#   driver    - Show all Driver client logs
#   kafka     - Show Kafka broker logs

set -e

SERVICE_TYPE="${1:-all}"

case $SERVICE_TYPE in
    all)
        echo "📊 Showing logs from ALL services..."
        echo "   Press Ctrl+C to stop"
        echo ""
        docker compose logs -f
        ;;
    central)
        echo "🏢 Showing Central Controller logs..."
        echo "   Press Ctrl+C to stop"
        echo ""
        docker compose logs -f ev-central
        ;;
    cp)
        echo "⚡ Showing Charging Point Engine logs..."
        echo "   Press Ctrl+C to stop"
        echo ""
        docker compose logs -f ev-cp-e-1 ev-cp-e-2 ev-cp-e-3 ev-cp-e-4 ev-cp-e-5 \
                                      ev-cp-e-6 ev-cp-e-7 ev-cp-e-8 ev-cp-e-9 ev-cp-e-10
        ;;
    monitor)
        echo "💚 Showing CP Monitor logs..."
        echo "   Press Ctrl+C to stop"
        echo ""
        docker compose logs -f ev-cp-m-1 ev-cp-m-2 ev-cp-m-3 ev-cp-m-4 ev-cp-m-5 \
                                      ev-cp-m-6 ev-cp-m-7 ev-cp-m-8 ev-cp-m-9 ev-cp-m-10
        ;;
    driver)
        echo "🚗 Showing Driver Client logs..."
        echo "   Press Ctrl+C to stop"
        echo ""
        docker compose logs -f ev-driver-alice ev-driver-bob ev-driver-charlie \
                                      ev-driver-david ev-driver-eve
        ;;
    kafka)
        echo "📡 Showing Kafka broker logs..."
        echo "   Press Ctrl+C to stop"
        echo ""
        docker compose logs -f kafka
        ;;
    *)
        echo "❌ Unknown service type: $SERVICE_TYPE"
        echo ""
        echo "Usage: $0 [service-type]"
        echo ""
        echo "Available service types:"
        echo "  all       - Show all service logs (default)"
        echo "  central   - Show only Central controller logs"
        echo "  cp        - Show all Charging Point Engine logs"
        echo "  monitor   - Show all CP Monitor logs"
        echo "  driver    - Show all Driver client logs"
        echo "  kafka     - Show Kafka broker logs"
        exit 1
        ;;
esac
