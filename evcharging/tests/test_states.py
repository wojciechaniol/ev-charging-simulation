"""
Unit tests for CP state machine.
Validates state transitions, guard conditions, and error handling.
"""

import pytest
from evcharging.common.states import (
    CPState, CPEvent, transition, StateTransitionError,
    get_valid_events, can_supply, is_operational
)


def test_initial_connection():
    """Test transition from DISCONNECTED to ACTIVATED."""
    state = transition(CPState.DISCONNECTED, CPEvent.CONNECT)
    assert state == CPState.ACTIVATED


def test_start_supply_from_activated():
    """Test starting supply from ACTIVATED state."""
    context = {"authorized": True, "vehicle_plugged": True}
    state = transition(CPState.ACTIVATED, CPEvent.START_SUPPLY, context)
    assert state == CPState.SUPPLYING


def test_start_supply_requires_authorization():
    """Test that START_SUPPLY requires authorization."""
    context = {"authorized": False}
    
    with pytest.raises(StateTransitionError, match="authorization"):
        transition(CPState.ACTIVATED, CPEvent.START_SUPPLY, context)


def test_stop_supply():
    """Test stopping supply returns to ACTIVATED."""
    state = transition(CPState.SUPPLYING, CPEvent.STOP_SUPPLY)
    assert state == CPState.ACTIVATED


def test_fault_from_any_state():
    """Test fault can occur from operational states."""
    # From ACTIVATED
    state = transition(CPState.ACTIVATED, CPEvent.FAULT_DETECTED)
    assert state == CPState.FAULT
    
    # From SUPPLYING
    state = transition(CPState.SUPPLYING, CPEvent.FAULT_DETECTED)
    assert state == CPState.FAULT
    
    # From STOPPED
    state = transition(CPState.STOPPED, CPEvent.FAULT_DETECTED)
    assert state == CPState.FAULT


def test_fault_recovery():
    """Test recovering from FAULT state."""
    state = transition(CPState.FAULT, CPEvent.FAULT_CLEARED)
    assert state == CPState.ACTIVATED


def test_stop_and_resume_cp():
    """Test CP stop and resume operations."""
    # Stop CP
    state = transition(CPState.ACTIVATED, CPEvent.STOP_CP)
    assert state == CPState.STOPPED
    
    # Resume CP
    state = transition(CPState.STOPPED, CPEvent.RESUME_CP)
    assert state == CPState.ACTIVATED


def test_invalid_transition():
    """Test that invalid transitions raise errors."""
    with pytest.raises(StateTransitionError):
        # Cannot start supply from STOPPED state
        transition(CPState.STOPPED, CPEvent.START_SUPPLY)
    
    with pytest.raises(StateTransitionError):
        # Cannot stop supply from ACTIVATED state
        transition(CPState.ACTIVATED, CPEvent.STOP_SUPPLY)


def test_disconnect_from_any_state():
    """Test disconnection is possible from any state."""
    states = [CPState.ACTIVATED, CPState.SUPPLYING, CPState.STOPPED, CPState.FAULT]
    
    for state in states:
        result = transition(state, CPEvent.DISCONNECT)
        assert result == CPState.DISCONNECTED


def test_get_valid_events():
    """Test getting valid events for each state."""
    activated_events = get_valid_events(CPState.ACTIVATED)
    assert CPEvent.START_SUPPLY in activated_events
    assert CPEvent.STOP_CP in activated_events
    assert CPEvent.DISCONNECT in activated_events
    
    supplying_events = get_valid_events(CPState.SUPPLYING)
    assert CPEvent.STOP_SUPPLY in supplying_events
    assert CPEvent.FAULT_DETECTED in supplying_events


def test_can_supply_predicate():
    """Test can_supply helper function."""
    assert can_supply(CPState.ACTIVATED) is True
    assert can_supply(CPState.SUPPLYING) is False
    assert can_supply(CPState.STOPPED) is False
    assert can_supply(CPState.FAULT) is False


def test_is_operational_predicate():
    """Test is_operational helper function."""
    assert is_operational(CPState.ACTIVATED) is True
    assert is_operational(CPState.SUPPLYING) is True
    assert is_operational(CPState.STOPPED) is True
    assert is_operational(CPState.FAULT) is False
    assert is_operational(CPState.DISCONNECTED) is False


def test_state_transition_sequence():
    """Test a complete charging session sequence."""
    # Start disconnected
    state = CPState.DISCONNECTED
    
    # Connect
    state = transition(state, CPEvent.CONNECT)
    assert state == CPState.ACTIVATED
    
    # Start supply
    context = {"authorized": True, "vehicle_plugged": True}
    state = transition(state, CPEvent.START_SUPPLY, context)
    assert state == CPState.SUPPLYING
    
    # Stop supply (normal completion)
    state = transition(state, CPEvent.STOP_SUPPLY)
    assert state == CPState.ACTIVATED
    
    # Disconnect
    state = transition(state, CPEvent.DISCONNECT)
    assert state == CPState.DISCONNECTED


def test_fault_during_supply():
    """Test fault detection during active supply."""
    state = CPState.SUPPLYING
    
    # Fault detected
    state = transition(state, CPEvent.FAULT_DETECTED)
    assert state == CPState.FAULT
    
    # Fault cleared
    state = transition(state, CPEvent.FAULT_CLEARED)
    assert state == CPState.ACTIVATED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
