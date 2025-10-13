"""
Charging Point state machine definition.
Defines valid states, transitions, and guard conditions.
"""

from enum import Enum
from typing import Optional, Set
from loguru import logger


class CPState(str, Enum):
    """Charging Point operational states."""
    DISCONNECTED = "DISCONNECTED"
    ACTIVATED = "ACTIVATED"
    STOPPED = "STOPPED"
    SUPPLYING = "SUPPLYING"
    FAULT = "FAULT"


class CPEvent(str, Enum):
    """Events that trigger state transitions."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    START_SUPPLY = "start_supply"
    STOP_SUPPLY = "stop_supply"
    FAULT_DETECTED = "fault_detected"
    FAULT_CLEARED = "fault_cleared"
    STOP_CP = "stop_cp"
    RESUME_CP = "resume_cp"


# Define valid state transitions
TRANSITIONS: dict[CPState, dict[CPEvent, CPState]] = {
    CPState.DISCONNECTED: {
        CPEvent.CONNECT: CPState.ACTIVATED,
    },
    CPState.ACTIVATED: {
        CPEvent.START_SUPPLY: CPState.SUPPLYING,
        CPEvent.STOP_CP: CPState.STOPPED,
        CPEvent.DISCONNECT: CPState.DISCONNECTED,
        CPEvent.FAULT_DETECTED: CPState.FAULT,
    },
    CPState.SUPPLYING: {
        CPEvent.STOP_SUPPLY: CPState.ACTIVATED,
        CPEvent.STOP_CP: CPState.STOPPED,
        CPEvent.DISCONNECT: CPState.DISCONNECTED,
        CPEvent.FAULT_DETECTED: CPState.FAULT,
    },
    CPState.STOPPED: {
        CPEvent.RESUME_CP: CPState.ACTIVATED,
        CPEvent.DISCONNECT: CPState.DISCONNECTED,
        CPEvent.FAULT_DETECTED: CPState.FAULT,
    },
    CPState.FAULT: {
        CPEvent.FAULT_CLEARED: CPState.ACTIVATED,
        CPEvent.DISCONNECT: CPState.DISCONNECTED,
    },
}


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


def transition(
    current_state: CPState,
    event: CPEvent,
    context: Optional[dict] = None
) -> CPState:
    """
    Attempt a state transition based on current state and event.
    
    Args:
        current_state: Current CP state
        event: Event triggering the transition
        context: Optional context for guard conditions (e.g., vehicle_plugged, authorized)
    
    Returns:
        New state after successful transition
    
    Raises:
        StateTransitionError: If transition is invalid
    """
    context = context or {}
    
    # Check if transition is defined
    if current_state not in TRANSITIONS:
        raise StateTransitionError(f"No transitions defined for state {current_state}")
    
    valid_events = TRANSITIONS[current_state]
    if event not in valid_events:
        raise StateTransitionError(
            f"Invalid transition: {current_state} + {event}. "
            f"Valid events: {list(valid_events.keys())}"
        )
    
    new_state = valid_events[event]
    
    # Apply guard conditions
    if event == CPEvent.START_SUPPLY:
        if not context.get("authorized", False):
            raise StateTransitionError("START_SUPPLY requires authorization from Central")
        if not context.get("vehicle_plugged", True):  # Default to True for simulation
            raise StateTransitionError("START_SUPPLY requires vehicle to be plugged in")
    
    logger.debug(f"State transition: {current_state} + {event} -> {new_state}")
    return new_state


def get_valid_events(state: CPState) -> Set[CPEvent]:
    """Get all valid events for a given state."""
    return set(TRANSITIONS.get(state, {}).keys())


def can_supply(state: CPState) -> bool:
    """Check if CP can start supplying power in current state."""
    return state == CPState.ACTIVATED


def is_operational(state: CPState) -> bool:
    """Check if CP is operational (not FAULT or DISCONNECTED)."""
    return state not in {CPState.FAULT, CPState.DISCONNECTED}
