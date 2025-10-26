"""
Pydantic models for all Kafka message types.
Provides JSON-schema export and validation for inter-service communication.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from evcharging.common.utils import utc_now


class MessageStatus(str, Enum):
    """Status codes for driver request updates."""
    ACCEPTED = "accepted"
    DENIED = "denied"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class CommandType(str, Enum):
    """Command types that Central can send to CP_E."""
    START_SUPPLY = "start_supply"
    STOP_SUPPLY = "stop_supply"
    STOP_CP = "stop_cp"
    RESUME_CP = "resume_cp"
    SHUTDOWN = "shutdown"


class DriverRequest(BaseModel):
    """Request from driver to charge at a specific CP."""
    request_id: str = Field(..., description="Unique request identifier")
    driver_id: str = Field(..., description="Driver identifier")
    cp_id: str = Field(..., description="Charging point identifier")
    ts: datetime = Field(default_factory=utc_now, description="Timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req-001",
                "driver_id": "driver-123",
                "cp_id": "CP-001",
                "ts": "2025-10-13T12:00:00Z"
            }
        }
    )


class DriverUpdate(BaseModel):
    """Status update sent back to driver."""
    request_id: str = Field(..., description="Original request identifier")
    driver_id: str = Field(..., description="Driver identifier")
    cp_id: str = Field(..., description="Charging point identifier")
    status: MessageStatus = Field(..., description="Current status")
    reason: Optional[str] = Field(None, description="Additional information or error reason")
    ts: datetime = Field(default_factory=utc_now, description="Timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "request_id": "req-001",
                "driver_id": "driver-123",
                "cp_id": "CP-001",
                "status": "in_progress",
                "reason": "Charging started",
                "ts": "2025-10-13T12:00:01Z"
            }
        }
    )


class CentralCommand(BaseModel):
    """Command from Central to CP_E."""
    cmd: CommandType = Field(..., description="Command type")
    cp_id: str = Field(..., description="Target charging point")
    payload: Optional[dict] = Field(None, description="Additional command data")
    ts: datetime = Field(default_factory=utc_now, description="Timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cmd": "start_supply",
                "cp_id": "CP-001",
                "payload": {"driver_id": "driver-123", "request_id": "req-001"},
                "ts": "2025-10-13T12:00:00Z"
            }
        }
    )


class CPStatus(BaseModel):
    """Status report from CP_E to Central."""
    cp_id: str = Field(..., description="Charging point identifier")
    state: str = Field(..., description="Current CP state")
    reason: Optional[str] = Field(None, description="State change reason")
    ts: datetime = Field(default_factory=utc_now, description="Timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cp_id": "CP-001",
                "state": "SUPPLYING",
                "reason": "Driver request accepted",
                "ts": "2025-10-13T12:00:01Z"
            }
        }
    )


class CPTelemetry(BaseModel):
    """Real-time telemetry from CP_E during charging session."""
    cp_id: str = Field(..., description="Charging point identifier")
    kw: float = Field(..., description="Current power delivery in kW")
    kwh: float = Field(..., description="Cumulative energy delivered in kWh")
    euros: float = Field(..., description="Cumulative cost in euros")
    driver_id: Optional[str] = Field(None, description="Current driver (non-personal demo ID)")
    session_id: Optional[str] = Field(None, description="Current charging session ID")
    ts: datetime = Field(default_factory=utc_now, description="Timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cp_id": "CP-001",
                "kw": 22.5,
                "kwh": 1.2,
                "euros": 3.75,
                "driver_id": "driver-123",
                "session_id": "session-001",
                "ts": "2025-10-13T12:00:05Z"
            }
        }
    )


class CPRegistration(BaseModel):
    """CP Monitor registration message to Central."""
    cp_id: str = Field(..., description="Charging point identifier")
    cp_e_host: str = Field(..., description="CP Engine host")
    cp_e_port: int = Field(..., description="CP Engine port")
    ts: datetime = Field(default_factory=utc_now, description="Timestamp")


def get_json_schemas() -> dict:
    """Export JSON schemas for all message types."""
    return {
        "DriverRequest": DriverRequest.model_json_schema(),
        "DriverUpdate": DriverUpdate.model_json_schema(),
        "CentralCommand": CentralCommand.model_json_schema(),
        "CPStatus": CPStatus.model_json_schema(),
        "CPTelemetry": CPTelemetry.model_json_schema(),
        "CPRegistration": CPRegistration.model_json_schema(),
    }
