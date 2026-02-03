"""
Integration tests for ControlService.

Tests the control service's ability to:
- Enable/disable gamepad and keyboard/mouse control
- Process movement commands
- Manage settings and presets
- Send robot actions
- Send camera control commands
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.services import StateService, ControlService, ConnectionService


@pytest.fixture
def state_service():
    """Create a StateService instance for testing."""
    return StateService()


@pytest.fixture
def connection_service(state_service):
    """Create a ConnectionService instance for testing."""
    return ConnectionService(state_service)


@pytest.fixture
def control_service(state_service):
    """Create a ControlService instance for testing."""
    return ControlService(state_service)


class TestControlServiceInitialization:
    """Test ControlService initialization."""
    
    def test_service_initialization(self, control_service, state_service):
        """Test that ControlService initializes correctly."""
        assert control_service.state == state_service
        assert control_service.logger is not None
        assert 'beginner' in control_service.presets
        assert 'normal' in control_service.presets
        assert 'advanced' in control_service.presets
        assert 'sport' in control_service.presets


class TestGamepadEnable:
    """Test gamepad enable/disable functionality."""
    
    def test_enable_gamepad_when_not_connected(self, control_service, connection_service):
        """Test enabling gamepad when robot is not connected."""
        result = control_service.enable_gamepad(True, connection_service)
        
        assert result['status'] == 'error'
        assert 'not connected' in result['message'].lower()
    
    def test_enable_gamepad_when_connected(self, control_service, state_service, connection_service):
        """Test enabling gamepad when robot is connected."""
        # Mock connection
        state_service.is_connected = True
        
        with patch.object(connection_service, 'initialize_robot_sync'):
            result = control_service.enable_gamepad(True, connection_service)
        
        assert result['status'] == 'success'
        assert result['enabled'] is True
        assert state_service.gamepad_enabled is True
        assert state_service.emergency_stop_active is False
    
    def test_disable_gamepad(self, control_service, state_service, connection_service):
        """Test disabling gamepad."""
        state_service.is_connected = True
        state_service.gamepad_enabled = True
        
        result = control_service.enable_gamepad(False, connection_service)
        
        assert result['status'] == 'success'
        assert result['enabled'] is False
        assert state_service.gamepad_enabled is False


class TestKeyboardMouseEnable:
    """Test keyboard/mouse enable/disable functionality."""
    
    def test_enable_keyboard_mouse_when_not_connected(self, control_service, connection_service):
        """Test enabling keyboard/mouse when robot is not connected."""
        result = control_service.enable_keyboard_mouse(True, connection_service)
        
        assert result['status'] == 'error'
        assert 'not connected' in result['message'].lower()
    
    def test_enable_keyboard_mouse_when_connected(self, control_service, state_service, connection_service):
        """Test enabling keyboard/mouse when robot is connected."""
        state_service.is_connected = True
        
        with patch.object(connection_service, 'initialize_robot_sync'):
            result = control_service.enable_keyboard_mouse(True, connection_service)
        
        assert result['status'] == 'success'
        assert result['enabled'] is True
        assert state_service.keyboard_mouse_enabled is True
        assert state_service.emergency_stop_active is False


class TestSettingsManagement:
    """Test settings management functionality."""
    
    def test_get_settings(self, control_service, state_service):
        """Test getting current settings."""
        result = control_service.get_settings()
        
        assert result['status'] == 'success'
        assert 'settings' in result
        assert result['settings'] == state_service.gamepad_settings
    
    def test_update_settings(self, control_service, state_service):
        """Test updating settings with validation."""
        data = {
            'deadzone_left_stick': 0.2,
            'sensitivity_linear': 1.5,
            'max_linear_velocity': 0.8
        }
        
        result = control_service.update_settings(data)
        
        assert result['status'] == 'success'
        assert state_service.gamepad_settings['deadzone_left_stick'] == 0.2
        assert state_service.gamepad_settings['sensitivity_linear'] == 1.5
        assert state_service.gamepad_settings['max_linear_velocity'] == 0.8
    
    def test_update_settings_with_clamping(self, control_service, state_service):
        """Test that settings are clamped to valid ranges."""
        data = {
            'deadzone_left_stick': 2.0,  # Should be clamped to 1.0
            'sensitivity_linear': 0.05,  # Should be clamped to 0.1
            'max_linear_velocity': 5.0   # Should be clamped to 1.0
        }
        
        result = control_service.update_settings(data)
        
        assert result['status'] == 'success'
        assert state_service.gamepad_settings['deadzone_left_stick'] == 1.0
        assert state_service.gamepad_settings['sensitivity_linear'] == 0.1
        assert state_service.gamepad_settings['max_linear_velocity'] == 1.0

    def test_apply_preset_beginner(self, control_service, state_service):
        """Test applying beginner preset."""
        result = control_service.apply_preset('beginner')

        assert result['status'] == 'success'
        assert result['preset'] == 'beginner'
        assert state_service.gamepad_settings['deadzone_left_stick'] == 0.15
        assert state_service.gamepad_settings['speed_multiplier'] == 0.7

    def test_apply_preset_sport(self, control_service, state_service):
        """Test applying sport preset."""
        result = control_service.apply_preset('sport')

        assert result['status'] == 'success'
        assert result['preset'] == 'sport'
        assert state_service.gamepad_settings['sensitivity_linear'] == 1.5
        assert state_service.gamepad_settings['speed_multiplier'] == 1.5

    def test_apply_invalid_preset(self, control_service):
        """Test applying invalid preset."""
        result = control_service.apply_preset('invalid_preset')

        assert result['status'] == 'error'
        assert 'invalid' in result['message'].lower()


class TestMovementCommandProcessing:
    """Test movement command processing."""

    def test_process_command_when_not_connected(self, control_service):
        """Test processing command when not connected."""
        data = {'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0}
        result = control_service.process_movement_command(data)

        assert result['status'] == 'error'
        assert 'not active' in result['message'].lower()

    def test_process_command_with_gamepad_enabled(self, control_service, state_service):
        """Test processing command with gamepad enabled."""
        state_service.is_connected = True
        state_service.gamepad_enabled = True

        data = {'lx': 0.5, 'ly': 0.5, 'rx': 0.2, 'ry': 0.0}
        result = control_service.process_movement_command(data)

        assert result['status'] == 'success'
        assert 'velocities' in result
        assert 'vx' in result['velocities']
        assert 'vy' in result['velocities']
        assert 'vyaw' in result['velocities']

    def test_process_command_applies_deadzone(self, control_service, state_service):
        """Test that deadzone is applied correctly."""
        state_service.is_connected = True
        state_service.gamepad_enabled = True
        state_service.gamepad_settings['deadzone_left_stick'] = 0.2

        # Input below deadzone should result in zero velocity
        data = {'lx': 0.1, 'ly': 0.1, 'rx': 0.0, 'ry': 0.0}
        result = control_service.process_movement_command(data)

        assert result['status'] == 'success'
        assert result['velocities']['vx'] == 0.0
        assert result['velocities']['vy'] == 0.0

    def test_process_command_applies_sensitivity(self, control_service, state_service):
        """Test that sensitivity multipliers are applied."""
        state_service.is_connected = True
        state_service.gamepad_enabled = True
        state_service.set_gamepad_setting('sensitivity_linear', 2.0)
        state_service.set_gamepad_setting('deadzone_left_stick', 0.0)
        state_service.set_gamepad_setting('speed_multiplier', 1.0)

        data = {'lx': 0.0, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0}
        result = control_service.process_movement_command(data)

        assert result['status'] == 'success'
        # With 2.0 sensitivity, 1.0 speed_multiplier and 0.5 input, should get 1.0 (clamped to max_linear_velocity=0.6)
        # 0.5 * 2.0 * 1.0 = 1.0, clamped to 0.6
        assert result['velocities']['vx'] == 0.6

    def test_process_zero_velocity_command(self, control_service, state_service):
        """Test processing zero velocity command."""
        state_service.is_connected = True
        state_service.gamepad_enabled = True

        data = {'lx': 0.0, 'ly': 0.0, 'rx': 0.0, 'ry': 0.0}
        result = control_service.process_movement_command(data)

        assert result['status'] == 'success'
        assert result['zero_velocity'] is True
        assert result['should_send'] is True  # First zero velocity should be sent

        # Second zero velocity should not be sent
        result2 = control_service.process_movement_command(data)
        assert result2['should_send'] is False


@pytest.mark.asyncio
class TestRobotActions:
    """Test robot action commands."""

    async def test_send_emergency_stop(self, control_service, state_service):
        """Test sending emergency stop action."""
        state_service.connection = Mock()
        state_service.connection.datachannel = Mock()
        state_service.connection.datachannel.pub_sub = Mock()
        state_service.connection.datachannel.pub_sub.publish_request_new = AsyncMock()

        result = await control_service.send_robot_action('emergency_stop')

        assert result['status'] == 'success'
        assert state_service.emergency_stop_active is True

    async def test_send_stand_up(self, control_service, state_service):
        """Test sending stand up action."""
        state_service.connection = Mock()
        state_service.connection.datachannel = Mock()
        state_service.connection.datachannel.pub_sub = Mock()
        state_service.connection.datachannel.pub_sub.publish_request_new = AsyncMock()

        result = await control_service.send_robot_action('stand_up')

        assert result['status'] == 'success'
        # Should call publish_request_new twice (StandUp + BalanceStand)
        assert state_service.connection.datachannel.pub_sub.publish_request_new.call_count == 2

    async def test_send_unknown_action(self, control_service, state_service):
        """Test sending unknown action."""
        state_service.connection = Mock()

        result = await control_service.send_robot_action('unknown_action')

        assert result['status'] == 'error'
        assert 'unknown' in result['message'].lower()


@pytest.mark.asyncio
class TestCameraControl:
    """Test camera control commands."""

    async def test_send_camera_control(self, control_service, state_service):
        """Test sending camera control command."""
        state_service.connection = Mock()
        state_service.connection.datachannel = Mock()
        state_service.connection.datachannel.pub_sub = Mock()
        state_service.connection.datachannel.pub_sub.publish_request_new = AsyncMock()

        await control_service.send_camera_control(0.5)

        # Verify publish_request_new was called with correct parameters
        state_service.connection.datachannel.pub_sub.publish_request_new.assert_called_once()
        call_args = state_service.connection.datachannel.pub_sub.publish_request_new.call_args
        assert call_args[0][1]['parameter']['yaw'] == 0.5

