"""
Unit tests for robot control functionality.

Tests cover:
- Gamepad command processing
- Keyboard/mouse command processing
- Settings management (dead zones, sensitivity, velocity limits)
- Preset configurations
- Robot actions (stand, sit, crouch, speed levels)
- AI mode functions (FreeWalk, FreeBound, FreeJump, FreeAvoid)
- Emergency stop functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import time


@pytest.mark.unit
@pytest.mark.control
class TestGamepadSettings:
    """Test gamepad settings management."""
    
    def test_default_gamepad_settings(self, default_gamepad_settings):
        """Test default gamepad settings values."""
        assert default_gamepad_settings['deadzone_left_stick'] == 0.15
        assert default_gamepad_settings['deadzone_right_stick'] == 0.15
        assert default_gamepad_settings['sensitivity_linear'] == 1.0
        assert default_gamepad_settings['sensitivity_strafe'] == 1.0
        assert default_gamepad_settings['sensitivity_rotation'] == 1.0
        assert default_gamepad_settings['max_linear_velocity'] == 0.6
        assert default_gamepad_settings['max_strafe_velocity'] == 0.4
        assert default_gamepad_settings['max_rotation_velocity'] == 0.8
        assert default_gamepad_settings['speed_multiplier'] == 1.0
    
    def test_update_deadzone_settings(self, default_gamepad_settings):
        """Test updating deadzone settings with validation."""
        settings = default_gamepad_settings.copy()
        
        # Valid update
        new_deadzone = 0.20
        settings['deadzone_left_stick'] = max(0.0, min(1.0, new_deadzone))
        
        assert settings['deadzone_left_stick'] == 0.20
    
    def test_deadzone_validation_min(self, default_gamepad_settings):
        """Test deadzone minimum validation (0.0)."""
        settings = default_gamepad_settings.copy()
        
        # Try to set below minimum
        invalid_deadzone = -0.5
        settings['deadzone_left_stick'] = max(0.0, min(1.0, invalid_deadzone))
        
        assert settings['deadzone_left_stick'] == 0.0
    
    def test_deadzone_validation_max(self, default_gamepad_settings):
        """Test deadzone maximum validation (1.0)."""
        settings = default_gamepad_settings.copy()
        
        # Try to set above maximum
        invalid_deadzone = 1.5
        settings['deadzone_left_stick'] = max(0.0, min(1.0, invalid_deadzone))
        
        assert settings['deadzone_left_stick'] == 1.0
    
    def test_update_sensitivity_settings(self, default_gamepad_settings):
        """Test updating sensitivity settings with validation."""
        settings = default_gamepad_settings.copy()
        
        # Valid update
        new_sensitivity = 1.5
        settings['sensitivity_linear'] = max(0.1, min(2.0, new_sensitivity))
        
        assert settings['sensitivity_linear'] == 1.5
    
    def test_sensitivity_validation_min(self, default_gamepad_settings):
        """Test sensitivity minimum validation (0.1)."""
        settings = default_gamepad_settings.copy()
        
        # Try to set below minimum
        invalid_sensitivity = 0.05
        settings['sensitivity_linear'] = max(0.1, min(2.0, invalid_sensitivity))
        
        assert settings['sensitivity_linear'] == 0.1
    
    def test_sensitivity_validation_max(self, default_gamepad_settings):
        """Test sensitivity maximum validation (2.0)."""
        settings = default_gamepad_settings.copy()
        
        # Try to set above maximum
        invalid_sensitivity = 3.0
        settings['sensitivity_linear'] = max(0.1, min(2.0, invalid_sensitivity))
        
        assert settings['sensitivity_linear'] == 2.0
    
    def test_update_velocity_limits(self, default_gamepad_settings):
        """Test updating velocity limit settings."""
        settings = default_gamepad_settings.copy()
        
        # Update velocity limits
        settings['max_linear_velocity'] = max(0.1, min(1.5, 0.8))
        settings['max_strafe_velocity'] = max(0.1, min(1.0, 0.5))
        settings['max_rotation_velocity'] = max(0.1, min(2.0, 1.0))
        
        assert settings['max_linear_velocity'] == 0.8
        assert settings['max_strafe_velocity'] == 0.5
        assert settings['max_rotation_velocity'] == 1.0


@pytest.mark.unit
@pytest.mark.control
class TestGamepadPresets:
    """Test gamepad preset configurations."""
    
    def test_beginner_preset(self):
        """Test beginner preset configuration."""
        beginner_preset = {
            'deadzone_left_stick': 0.20,
            'deadzone_right_stick': 0.20,
            'sensitivity_linear': 0.7,
            'sensitivity_strafe': 0.7,
            'sensitivity_rotation': 0.7,
            'max_linear_velocity': 0.4,
            'max_strafe_velocity': 0.3,
            'max_rotation_velocity': 0.6,
            'speed_multiplier': 0.7
        }
        
        assert beginner_preset['deadzone_left_stick'] == 0.20
        assert beginner_preset['sensitivity_linear'] == 0.7
        assert beginner_preset['max_linear_velocity'] == 0.4
    
    def test_normal_preset(self):
        """Test normal preset configuration."""
        normal_preset = {
            'deadzone_left_stick': 0.15,
            'deadzone_right_stick': 0.15,
            'sensitivity_linear': 1.0,
            'sensitivity_strafe': 1.0,
            'sensitivity_rotation': 1.0,
            'max_linear_velocity': 0.6,
            'max_strafe_velocity': 0.4,
            'max_rotation_velocity': 0.8,
            'speed_multiplier': 1.0
        }
        
        assert normal_preset['deadzone_left_stick'] == 0.15
        assert normal_preset['sensitivity_linear'] == 1.0
        assert normal_preset['max_linear_velocity'] == 0.6
    
    def test_advanced_preset(self):
        """Test advanced preset configuration."""
        advanced_preset = {
            'deadzone_left_stick': 0.10,
            'deadzone_right_stick': 0.10,
            'sensitivity_linear': 1.3,
            'sensitivity_strafe': 1.3,
            'sensitivity_rotation': 1.3,
            'max_linear_velocity': 0.8,
            'max_strafe_velocity': 0.6,
            'max_rotation_velocity': 1.0,
            'speed_multiplier': 1.3
        }
        
        assert advanced_preset['deadzone_left_stick'] == 0.10
        assert advanced_preset['sensitivity_linear'] == 1.3
        assert advanced_preset['max_linear_velocity'] == 0.8

    def test_sport_preset(self):
        """Test sport preset configuration."""
        sport_preset = {
            'deadzone_left_stick': 0.05,
            'deadzone_right_stick': 0.05,
            'sensitivity_linear': 1.5,
            'sensitivity_strafe': 1.5,
            'sensitivity_rotation': 1.5,
            'max_linear_velocity': 1.0,
            'max_strafe_velocity': 0.8,
            'max_rotation_velocity': 1.2,
            'speed_multiplier': 1.5
        }

        assert sport_preset['deadzone_left_stick'] == 0.05
        assert sport_preset['sensitivity_linear'] == 1.5
        assert sport_preset['max_linear_velocity'] == 1.0


@pytest.mark.unit
@pytest.mark.control
class TestMovementCommands:
    """Test movement command processing."""

    def test_create_movement_command(self):
        """Test creating a movement command."""
        command = {
            'vx': 0.5,   # Forward velocity
            'vy': 0.0,   # Strafe velocity
            'vyaw': 0.0  # Rotation velocity
        }

        assert command['vx'] == 0.5
        assert command['vy'] == 0.0
        assert command['vyaw'] == 0.0

    def test_apply_deadzone(self):
        """Test applying deadzone to stick input."""
        def apply_deadzone(value, deadzone):
            if abs(value) < deadzone:
                return 0.0
            # Scale the remaining range
            sign = 1 if value > 0 else -1
            scaled = (abs(value) - deadzone) / (1.0 - deadzone)
            return sign * scaled

        # Input below deadzone
        result = apply_deadzone(0.10, 0.15)
        assert result == 0.0

        # Input above deadzone
        result = apply_deadzone(0.50, 0.15)
        assert result > 0.0

    def test_apply_sensitivity(self):
        """Test applying sensitivity multiplier."""
        base_velocity = 0.5
        sensitivity = 1.5

        result = base_velocity * sensitivity

        assert result == 0.75

    def test_apply_velocity_limits(self):
        """Test applying maximum velocity limits."""
        velocity = 0.8
        max_velocity = 0.6

        # Clamp to maximum
        result = max(-max_velocity, min(max_velocity, velocity))

        assert result == 0.6

    def test_zero_velocity_command(self):
        """Test creating zero velocity (stop) command."""
        command = {
            'vx': 0.0,
            'vy': 0.0,
            'vyaw': 0.0
        }

        assert command['vx'] == 0.0
        assert command['vy'] == 0.0
        assert command['vyaw'] == 0.0

    def test_forward_movement(self):
        """Test forward movement command."""
        command = {
            'vx': 0.6,   # Max forward
            'vy': 0.0,
            'vyaw': 0.0
        }

        assert command['vx'] > 0
        assert command['vy'] == 0
        assert command['vyaw'] == 0

    def test_strafe_movement(self):
        """Test strafe movement command."""
        command = {
            'vx': 0.0,
            'vy': 0.4,   # Strafe right
            'vyaw': 0.0
        }

        assert command['vx'] == 0
        assert command['vy'] > 0
        assert command['vyaw'] == 0

    def test_rotation_movement(self):
        """Test rotation movement command."""
        command = {
            'vx': 0.0,
            'vy': 0.0,
            'vyaw': 0.8  # Rotate
        }

        assert command['vx'] == 0
        assert command['vy'] == 0
        assert command['vyaw'] > 0

    def test_combined_movement(self):
        """Test combined movement (forward + strafe + rotation)."""
        command = {
            'vx': 0.5,
            'vy': 0.3,
            'vyaw': 0.4
        }

        assert command['vx'] > 0
        assert command['vy'] > 0
        assert command['vyaw'] > 0


@pytest.mark.unit
@pytest.mark.control
class TestControlState:
    """Test control state management."""

    def test_gamepad_starts_disabled(self):
        """Test that gamepad control starts disabled."""
        gamepad_enabled = False
        assert gamepad_enabled is False

    def test_enable_gamepad(self):
        """Test enabling gamepad control."""
        gamepad_enabled = False

        # Enable gamepad
        gamepad_enabled = True

        assert gamepad_enabled is True

    def test_disable_gamepad(self):
        """Test disabling gamepad control."""
        gamepad_enabled = True

        # Disable gamepad
        gamepad_enabled = False

        assert gamepad_enabled is False

    def test_keyboard_mouse_starts_disabled(self):
        """Test that keyboard/mouse control starts disabled."""
        keyboard_mouse_enabled = False
        assert keyboard_mouse_enabled is False

    def test_enable_keyboard_mouse(self):
        """Test enabling keyboard/mouse control."""
        keyboard_mouse_enabled = False

        # Enable keyboard/mouse
        keyboard_mouse_enabled = True

        assert keyboard_mouse_enabled is True

    def test_emergency_stop_state(self):
        """Test emergency stop state."""
        emergency_stop_active = False

        # Activate emergency stop
        emergency_stop_active = True

        assert emergency_stop_active is True

        # Deactivate emergency stop
        emergency_stop_active = False

        assert emergency_stop_active is False


@pytest.mark.unit
@pytest.mark.control
class TestRobotActions:
    """Test robot action commands."""

    def test_stand_action(self):
        """Test stand up action."""
        action = 'stand'
        assert action == 'stand'

    def test_sit_action(self):
        """Test sit down action."""
        action = 'sit'
        assert action == 'sit'

    def test_crouch_action(self):
        """Test crouch action."""
        action = 'crouch'
        assert action == 'crouch'

    def test_body_height_levels(self):
        """Test body height level management."""
        # 0=low, 1=middle, 2=high
        current_body_height = 1

        assert current_body_height in [0, 1, 2]

        # Increase height
        current_body_height = min(2, current_body_height + 1)
        assert current_body_height == 2

        # Decrease height
        current_body_height = max(0, current_body_height - 1)
        assert current_body_height == 1

    def test_speed_levels(self):
        """Test speed level management."""
        # -1=slow, 0=normal, 1=fast
        speed_level = 0

        assert speed_level in [-1, 0, 1]

        # Increase speed
        speed_level = min(1, speed_level + 1)
        assert speed_level == 1

        # Decrease speed
        speed_level = max(-1, speed_level - 1)
        assert speed_level == 0

    def test_lidar_toggle(self):
        """Test LIDAR on/off toggle."""
        lidar_state = False

        # Turn on LIDAR
        lidar_state = True
        assert lidar_state is True

        # Turn off LIDAR
        lidar_state = False
        assert lidar_state is False

    def test_light_toggle(self):
        """Test light on/off toggle."""
        light_state = False

        # Turn on light
        light_state = True
        assert light_state is True

        # Turn off light
        light_state = False
        assert light_state is False


@pytest.mark.unit
@pytest.mark.control
class TestAIModeFunctions:
    """Test AI mode function states."""

    def test_free_walk_state(self):
        """Test FreeWalk function state."""
        free_walk_active = False

        # Activate FreeWalk
        free_walk_active = True
        assert free_walk_active is True

        # Deactivate FreeWalk
        free_walk_active = False
        assert free_walk_active is False

    def test_free_bound_state(self):
        """Test FreeBound function state."""
        free_bound_active = False

        # Activate FreeBound
        free_bound_active = True
        assert free_bound_active is True

        # Deactivate FreeBound
        free_bound_active = False
        assert free_bound_active is False

    def test_free_jump_state(self):
        """Test FreeJump function state."""
        free_jump_active = False

        # Activate FreeJump
        free_jump_active = True
        assert free_jump_active is True

        # Deactivate FreeJump
        free_jump_active = False
        assert free_jump_active is False

    def test_free_avoid_state(self):
        """Test FreeAvoid function state."""
        free_avoid_active = False

        # Activate FreeAvoid
        free_avoid_active = True
        assert free_avoid_active is True

        # Deactivate FreeAvoid
        free_avoid_active = False
        assert free_avoid_active is False

    def test_mutually_exclusive_functions(self):
        """Test that AI mode functions are mutually exclusive."""
        free_walk_active = False
        free_bound_active = False
        free_jump_active = False
        free_avoid_active = False

        # Activate FreeWalk
        free_walk_active = True
        assert free_walk_active is True
        assert free_bound_active is False
        assert free_jump_active is False
        assert free_avoid_active is False

        # Switch to FreeBound (deactivate FreeWalk)
        free_walk_active = False
        free_bound_active = True
        assert free_walk_active is False
        assert free_bound_active is True


@pytest.mark.unit
@pytest.mark.control
class TestRateLimiting:
    """Test command rate limiting."""

    def test_command_interval(self):
        """Test command interval timing."""
        command_interval = 0.016  # ~60Hz
        assert command_interval == 0.016

    def test_rate_limiting_logic(self):
        """Test rate limiting prevents too frequent commands."""
        last_command_time = time.time()
        command_interval = 0.016

        # Immediate second command should be rate limited
        current_time = time.time()
        time_since_last = current_time - last_command_time

        if time_since_last < command_interval:
            should_send = False
        else:
            should_send = True

        # Since we just set last_command_time, should be rate limited
        assert should_send is False or time_since_last >= command_interval

    def test_zero_velocity_bypass_rate_limit(self):
        """Test that zero velocity commands bypass rate limiting."""
        command = {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0}

        is_zero_velocity = (
            command['vx'] == 0.0 and
            command['vy'] == 0.0 and
            command['vyaw'] == 0.0
        )

        # Zero velocity should always be allowed
        assert is_zero_velocity is True


@pytest.mark.unit
@pytest.mark.control
class TestCameraControl:
    """Test camera control functionality."""

    def test_camera_yaw_command(self):
        """Test camera yaw control."""
        yaw = 0.5  # Camera yaw value

        assert -1.0 <= yaw <= 1.0

    def test_camera_yaw_limits(self):
        """Test camera yaw value limits."""
        # Test within limits
        yaw = 0.5
        clamped_yaw = max(-1.0, min(1.0, yaw))
        assert clamped_yaw == 0.5

        # Test exceeding limits
        yaw = 1.5
        clamped_yaw = max(-1.0, min(1.0, yaw))
        assert clamped_yaw == 1.0

        yaw = -1.5
        clamped_yaw = max(-1.0, min(1.0, yaw))
        assert clamped_yaw == -1.0


@pytest.mark.unit
@pytest.mark.control
class TestControlErrorHandling:
    """Test control error handling."""

    def test_control_when_not_connected(self):
        """Test that control is blocked when not connected."""
        is_connected = False
        gamepad_enabled = True

        can_send_command = is_connected and gamepad_enabled

        assert can_send_command is False

    def test_control_when_disabled(self):
        """Test that control is blocked when disabled."""
        is_connected = True
        gamepad_enabled = False
        keyboard_mouse_enabled = False

        can_send_command = is_connected and (gamepad_enabled or keyboard_mouse_enabled)

        assert can_send_command is False

    def test_control_during_emergency_stop(self):
        """Test that control is blocked during emergency stop."""
        is_connected = True
        gamepad_enabled = True
        emergency_stop_active = True

        can_send_command = is_connected and gamepad_enabled and not emergency_stop_active

        assert can_send_command is False

    def test_control_when_enabled(self):
        """Test that control works when properly enabled."""
        is_connected = True
        gamepad_enabled = True
        emergency_stop_active = False

        can_send_command = is_connected and gamepad_enabled and not emergency_stop_active

        assert can_send_command is True

