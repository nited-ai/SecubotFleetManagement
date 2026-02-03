"""
Unit tests for movement command flow.

Tests the complete flow from processing movement commands to sending them to the robot.
This ensures that refactoring doesn't break the critical path of command execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services import StateService, ControlService


class TestMovementCommandFlow:
    """Test the complete movement command flow."""

    @pytest.fixture
    def state(self):
        """Create a state service for testing."""
        state = StateService()
        state.is_connected = True
        state.gamepad_enabled = True
        return state

    @pytest.fixture
    def control_service(self, state):
        """Create a control service for testing."""
        return ControlService(state)

    def test_process_and_send_gamepad_command(self, control_service, state):
        """Test that gamepad commands are processed and sent correctly."""
        # Setup: Create event loop
        state.event_loop = Mock()
        state.event_loop.is_running.return_value = True
        
        # Process command
        data = {'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0}
        result = control_service.process_movement_command(data)
        
        # Verify processing succeeded
        assert result['status'] == 'success'
        assert result['should_send'] is True
        assert 'velocities' in result
        
        # Send command
        velocities = result['velocities']
        send_result = control_service.send_movement_command_sync(
            velocities['vx'],
            velocities['vy'],
            velocities['vyaw'],
            result['zero_velocity']
        )
        
        # Verify sending succeeded
        assert send_result['status'] == 'success'
        assert 'scheduled' in send_result['message'].lower()

    def test_process_and_send_keyboard_mouse_command(self, control_service, state):
        """Test that keyboard/mouse commands are processed and sent correctly."""
        # Setup: Create event loop and enable keyboard/mouse
        state.event_loop = Mock()
        state.event_loop.is_running.return_value = True
        state.gamepad_enabled = False
        state.keyboard_mouse_enabled = True
        
        # Process command with keyboard/mouse velocity limits
        data = {
            'lx': 0.3, 'ly': 0.5, 'rx': 0.2, 'ry': 0.0,
            'max_linear': 0.6,
            'max_strafe': 0.4,
            'max_rotation': 0.8,
            'source': 'keyboard_mouse'
        }
        result = control_service.process_movement_command(data)
        
        # Verify processing succeeded
        assert result['status'] == 'success'
        assert result['should_send'] is True
        
        # Send command
        velocities = result['velocities']
        send_result = control_service.send_movement_command_sync(
            velocities['vx'],
            velocities['vy'],
            velocities['vyaw'],
            result['zero_velocity']
        )
        
        # Verify sending succeeded
        assert send_result['status'] == 'success'

    def test_zero_velocity_command_not_sent_twice(self, control_service, state):
        """Test that zero velocity commands are only sent once."""
        # Setup
        state.event_loop = Mock()
        state.event_loop.is_running.return_value = True
        
        # First zero velocity command
        data = {'lx': 0.0, 'ly': 0.0, 'rx': 0.0, 'ry': 0.0}
        result1 = control_service.process_movement_command(data)
        
        assert result1['status'] == 'success'
        assert result1['zero_velocity'] is True
        assert result1['should_send'] is True  # First time should send
        
        # Second zero velocity command
        result2 = control_service.process_movement_command(data)
        
        assert result2['status'] == 'success'
        assert result2['zero_velocity'] is True
        assert result2['should_send'] is False  # Second time should NOT send

    def test_send_command_fails_when_event_loop_not_running(self, control_service, state):
        """Test that sending fails gracefully when event loop is not running."""
        # Setup: Event loop not running
        state.event_loop = Mock()
        state.event_loop.is_running.return_value = False
        
        # Try to send command
        send_result = control_service.send_movement_command_sync(0.5, 0.0, 0.0, False)
        
        # Verify it fails gracefully
        assert send_result['status'] == 'error'
        assert 'event loop' in send_result['message'].lower()

    def test_process_command_when_not_connected(self, control_service, state):
        """Test that processing fails when not connected."""
        # Setup: Not connected
        state.is_connected = False
        
        # Try to process command
        data = {'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0}
        result = control_service.process_movement_command(data)
        
        # Verify it fails
        assert result['status'] == 'error'
        assert 'not active' in result['message'].lower()

    def test_process_command_when_control_disabled(self, control_service, state):
        """Test that processing fails when control is disabled."""
        # Setup: Control disabled
        state.gamepad_enabled = False
        state.keyboard_mouse_enabled = False
        
        # Try to process command
        data = {'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0}
        result = control_service.process_movement_command(data)
        
        # Verify it fails
        assert result['status'] == 'error'
        assert 'not active' in result['message'].lower()

