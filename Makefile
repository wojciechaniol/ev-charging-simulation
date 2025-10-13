.PHONY: help install test up down logs clean

help:
	@echo "EV Charging Simulation - Makefile Commands"
	@echo ""
	@echo "  make install    - Install Python dependencies"
	@echo "  make test       - Run unit tests"
	@echo "  make up         - Start all services with Docker Compose"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - Show logs from all services"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make local-run  - Run services locally (requires Kafka)"
	@echo ""

install:
	pip install -r requirements.txt

test:
	pytest evcharging/tests/ -v

up:
	cd docker && docker-compose up -d

down:
	cd docker && docker-compose down

logs:
	cd docker && docker-compose logs -f

clean:
	cd docker && docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Local development (assumes Kafka running on localhost:9092)
local-run:
	@echo "Starting services locally..."
	@echo "Make sure Kafka is running on localhost:9092"
	@echo ""
	python -m evcharging.apps.ev_central.main &
	sleep 2
	python -m evcharging.apps.ev_cp_e.main --cp-id CP-001 --health-port 8001 &
	python -m evcharging.apps.ev_cp_e.main --cp-id CP-002 --health-port 8002 &
	sleep 2
	python -m evcharging.apps.ev_cp_m.main --cp-id CP-001 --cp-e-port 8001 &
	python -m evcharging.apps.ev_cp_m.main --cp-id CP-002 --cp-e-port 8002 &
	sleep 2
	python -m evcharging.apps.ev_driver.main --driver-id driver-alice --requests-file requests.txt
