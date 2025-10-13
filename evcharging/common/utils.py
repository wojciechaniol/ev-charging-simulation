"""
Utility functions for EV Charging simulation.
Includes ID generation, timestamps, and LRC calculation stub.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional


def generate_id(prefix: str = "") -> str:
    """Generate a unique identifier with optional prefix."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}-{unique_id}" if prefix else unique_id


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def calculate_lrc(data: bytes) -> int:
    """
    Calculate Longitudinal Redundancy Check using XOR.
    
    TODO: Implement full <STX><DATA><ETX><LRC> framing for TCP protocol.
    
    Args:
        data: Byte data to calculate LRC for
    
    Returns:
        LRC value (XOR of all bytes)
    """
    lrc = 0
    for byte in data:
        lrc ^= byte
    return lrc


def frame_message(data: str) -> bytes:
    """
    Frame a message with STX, ETX, and LRC.
    
    TODO: Complete implementation for production use.
    
    Format: <STX><DATA><ETX><LRC>
    STX = 0x02, ETX = 0x03
    """
    STX = 0x02
    ETX = 0x03
    
    data_bytes = data.encode('utf-8')
    lrc = calculate_lrc(data_bytes)
    
    return bytes([STX]) + data_bytes + bytes([ETX, lrc])


def unframe_message(framed: bytes) -> Optional[str]:
    """
    Extract and validate a framed message.
    
    TODO: Complete implementation with proper error handling.
    
    Returns:
        Extracted message string or None if invalid
    """
    if len(framed) < 3:
        return None
    
    if framed[0] != 0x02 or framed[-2] != 0x03:
        return None
    
    data_bytes = framed[1:-2]
    received_lrc = framed[-1]
    calculated_lrc = calculate_lrc(data_bytes)
    
    if received_lrc != calculated_lrc:
        return None
    
    return data_bytes.decode('utf-8')


def format_currency(amount: float) -> str:
    """Format currency amount in euros."""
    return f"€{amount:.2f}"


def format_power(kw: float) -> str:
    """Format power in kilowatts."""
    return f"{kw:.2f} kW"
