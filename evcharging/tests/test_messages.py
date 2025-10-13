"""
Unit tests for Pydantic message models.
Validates JSON schema, serialization, and validation.
"""

import pytest
from datetime import datetime
from evcharging.common.messages import (
    DriverRequest, DriverUpdate, CentralCommand, CPStatus, CPTelemetry,
    MessageStatus, CommandType, get_json_schemas
)


def test_driver_request_validation():
    """Test DriverRequest model validation."""
    request = DriverRequest(
        request_id="req-001",
        driver_id="driver-123",
        cp_id="CP-001"
    )
    
    assert request.request_id == "req-001"
    assert request.driver_id == "driver-123"
    assert request.cp_id == "CP-001"
    assert isinstance(request.ts, datetime)


def test_driver_request_json_serialization():
    """Test DriverRequest JSON serialization."""
    request = DriverRequest(
        request_id="req-001",
        driver_id="driver-123",
        cp_id="CP-001"
    )
    
    json_str = request.model_dump_json()
    assert "req-001" in json_str
    assert "driver-123" in json_str
    
    # Deserialize
    request2 = DriverRequest.model_validate_json(json_str)
    assert request2.request_id == request.request_id


def test_driver_update_statuses():
    """Test all DriverUpdate status values."""
    for status in MessageStatus:
        update = DriverUpdate(
            request_id="req-001",
            driver_id="driver-123",
            cp_id="CP-001",
            status=status,
            reason="Test reason"
        )
        assert update.status == status


def test_central_command_types():
    """Test all CentralCommand types."""
    for cmd_type in CommandType:
        command = CentralCommand(
            cmd=cmd_type,
            cp_id="CP-001",
            payload={"test": "data"}
        )
        assert command.cmd == cmd_type


def test_cp_status_creation():
    """Test CPStatus model."""
    status = CPStatus(
        cp_id="CP-001",
        state="ACTIVATED",
        reason="System startup"
    )
    
    assert status.cp_id == "CP-001"
    assert status.state == "ACTIVATED"
    assert status.reason == "System startup"


def test_cp_telemetry_fields():
    """Test CPTelemetry model with all fields."""
    telemetry = CPTelemetry(
        cp_id="CP-001",
        kw=22.5,
        euros=3.75,
        driver_id="driver-123",
        session_id="session-001"
    )
    
    assert telemetry.cp_id == "CP-001"
    assert telemetry.kw == 22.5
    assert telemetry.euros == 3.75
    assert telemetry.driver_id == "driver-123"
    assert telemetry.session_id == "session-001"


def test_json_schemas_export():
    """Test JSON schema export for all models."""
    schemas = get_json_schemas()
    
    assert "DriverRequest" in schemas
    assert "DriverUpdate" in schemas
    assert "CentralCommand" in schemas
    assert "CPStatus" in schemas
    assert "CPTelemetry" in schemas
    
    # Check schema structure
    driver_request_schema = schemas["DriverRequest"]
    assert "properties" in driver_request_schema
    assert "request_id" in driver_request_schema["properties"]


def test_message_validation_errors():
    """Test that validation errors are raised for invalid data."""
    with pytest.raises(Exception):
        # Missing required field
        DriverRequest(request_id="req-001", driver_id="driver-123")
    
    with pytest.raises(Exception):
        # Invalid status
        DriverUpdate(
            request_id="req-001",
            driver_id="driver-123",
            cp_id="CP-001",
            status="INVALID_STATUS"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
