"""
Tests for the driver dashboard FastAPI application.
"""

from datetime import datetime, timezone
from fastapi.testclient import TestClient

from evcharging.apps.ev_driver.dashboard import (
    BroadcastAlert,
    ChargingPointDetail,
    Location,
    Notification,
    SessionHistoryEntry,
    SessionSummary,
    create_driver_dashboard_app,
)


class FakeDriver:
    driver_id = "driver-test"

    def __init__(self):
        self._cp = ChargingPointDetail(
            cp_id="CP-001",
            name="Test Point",
            status="FREE",
            power_kw=22.0,
            connector_type="Type 2",
            location=Location(
                address="123 Test St",
                city="Metropolis",
                latitude=1.0,
                longitude=2.0,
                distance_km=1.2,
            ),
            queue_length=0,
            estimated_wait_minutes=0,
            favorite=False,
            amenities=["WiFi"],
            price_eur_per_kwh=0.30,
            last_updated=datetime.now(timezone.utc),
        )
        self._session = SessionSummary(
            session_id="sess-1",
            request_id="req-1",
            cp_id="CP-001",
            status="PENDING",
            queue_position=1,
        )
        self._history = [
            SessionHistoryEntry(
                session_id="sess-0",
                request_id="req-0",
                cp_id="CP-001",
                status="COMPLETED",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                energy_kwh=10.0,
                cost_eur=3.5,
                receipt_url=None,
            )
        ]

    async def dashboard_charging_points(self, **_filters):
        return [self._cp]

    async def dashboard_charging_point(self, cp_id: str):
        if cp_id != self._cp.cp_id:
            raise KeyError(cp_id)
        return self._cp

    async def send_request(self, cp_id: str):
        return type("Req", (), {"request_id": "req-1"})

    async def dashboard_request_summary(self, request_id: str):
        if request_id != "req-1":
            raise KeyError(request_id)
        return self._session

    async def dashboard_cancel_request(self, request_id: str):
        return request_id == "req-1"

    async def dashboard_current_session(self):
        return self._session

    async def dashboard_stop_session(self, session_id: str):
        if session_id != "sess-1":
            return None
        return self._session.model_copy(update={"status": "STOPPED"})

    async def dashboard_session_history(self):
        return self._history

    async def dashboard_favorites(self):
        return []

    async def dashboard_add_favorite(self, cp_id: str):
        return None

    async def dashboard_remove_favorite(self, cp_id: str):
        return None

    async def dashboard_notifications(self):
        return [
            Notification(
                notification_id="note-1",
                created_at=datetime.now(timezone.utc),
                message="Test notification",
                type="SESSION",
                read=False,
            )
        ]

    async def dashboard_alerts(self):
        return [
            BroadcastAlert(
                alert_id="alert-1",
                title="Maintenance",
                message="CP-001 maintenance",
                severity="INFO",
                effective_at=datetime.now(timezone.utc),
                expires_at=None,
            )
        ]


def test_driver_dashboard_endpoints():
    driver = FakeDriver()
    app = create_driver_dashboard_app(driver)
    client = TestClient(app)

    resp = client.get("/charging-points")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) == 1
    assert points[0]["cp_id"] == "CP-001"

    resp = client.get("/charging-points/CP-001")
    assert resp.status_code == 200

    resp = client.post("/drivers/driver-test/requests", json={"cp_id": "CP-001", "vehicle_id": "veh-1"})
    assert resp.status_code == 202
    assert resp.json()["status"] == "PENDING"

    resp = client.delete("/drivers/driver-test/requests/req-1")
    assert resp.status_code == 204

    resp = client.get("/drivers/driver-test/sessions/current")
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "sess-1"

    resp = client.post("/drivers/driver-test/sessions/sess-1/stop")
    assert resp.status_code == 200
    assert resp.json()["status"] == "STOPPED"

    resp = client.get("/drivers/driver-test/sessions/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/drivers/driver-test/notifications")
    assert resp.status_code == 200
    assert resp.json()[0]["message"] == "Test notification"

    resp = client.get("/drivers/driver-test/alerts")
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Maintenance"
