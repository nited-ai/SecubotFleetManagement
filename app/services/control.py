"""
Control service for Unitree Go2 robot.

This service handles all robot control functionality including:
- Gamepad/keyboard/mouse enable/disable
- Movement command processing
- Settings management (deadzones, sensitivity, velocity limits)
- Preset configurations
- Robot actions (stand, sit, crouch, body height, speed, etc.)
- Camera control
- Emergency stop management
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional


class ControlService:
    """
    Service for managing robot control functionality.
    
    Handles:
    - Gamepad and keyboard/mouse control enable/disable
    - Movement command processing with deadzones, sensitivity, and velocity limits
    - Settings management and presets
    - Robot actions (stand, sit, crouch, body height, speed, lidar, light)
    - Camera control (yaw)
    - Emergency stop management
    """
    
    def __init__(self, state_service):
        """Initialize ControlService."""
        self.state = state_service
        self.logger = logging.getLogger(__name__)
        
        # Preset configurations
        self.presets = {
            'beginner': {
                'deadzone_left_stick': 0.15,
                'deadzone_right_stick': 0.15,
                'sensitivity_linear': 0.7,
                'sensitivity_strafe': 0.7,
                'sensitivity_rotation': 0.7,
                'max_linear_velocity': 0.4,
                'max_strafe_velocity': 0.3,
                'max_rotation_velocity': 0.5,
                'speed_multiplier': 0.7
            },
            'normal': {
                'deadzone_left_stick': 0.1,
                'deadzone_right_stick': 0.1,
                'sensitivity_linear': 1.0,
                'sensitivity_strafe': 1.0,
                'sensitivity_rotation': 1.0,
                'max_linear_velocity': 0.6,
                'max_strafe_velocity': 0.4,
                'max_rotation_velocity': 0.8,
                'speed_multiplier': 1.0
            },
            'advanced': {
                'deadzone_left_stick': 0.05,
                'deadzone_right_stick': 0.05,
                'sensitivity_linear': 1.3,
                'sensitivity_strafe': 1.3,
                'sensitivity_rotation': 1.3,
                'max_linear_velocity': 0.6,
                'max_strafe_velocity': 0.4,
                'max_rotation_velocity': 0.8,
                'speed_multiplier': 1.3
            },
            'sport': {
                'deadzone_left_stick': 0.05,
                'deadzone_right_stick': 0.05,
                'sensitivity_linear': 1.5,
                'sensitivity_strafe': 1.5,
                'sensitivity_rotation': 1.5,
                'max_linear_velocity': 0.6,
                'max_strafe_velocity': 0.4,
                'max_rotation_velocity': 0.8,
                'speed_multiplier': 1.5
            }
        }
    
    def enable_gamepad(self, enable: bool, connection_service) -> dict:
        """Enable or disable gamepad control."""
        try:
            if not self.state.is_connected:
                return {'status': 'error', 'message': 'Robot not connected'}
            
            self.state.gamepad_enabled = enable
            if enable:
                self.state.emergency_stop_active = False
                self.logger.info("=" * 50)
                self.logger.info("GAMEPAD CONTROL ENABLED")
                self.logger.info("=" * 50)
                
                # Initialize robot asynchronously
                connection_service.initialize_robot_sync()
            else:
                self.logger.info("Gamepad control disabled")
            
            return {'status': 'success', 'enabled': self.state.gamepad_enabled}
        
        except Exception as e:
            self.logger.error(f"Enable gamepad error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def enable_keyboard_mouse(self, enable: bool, connection_service) -> dict:
        """Enable or disable keyboard/mouse control."""
        try:
            if not self.state.is_connected:
                return {'status': 'error', 'message': 'Robot not connected'}
            
            self.state.keyboard_mouse_enabled = enable
            if enable:
                self.state.emergency_stop_active = False
                self.logger.info("=" * 50)
                self.logger.info("KEYBOARD/MOUSE CONTROL ENABLED")
                self.logger.info("=" * 50)
                
                # Initialize robot asynchronously
                connection_service.initialize_robot_sync()
            else:
                self.logger.info("Keyboard/mouse control disabled")
            
            return {'status': 'success', 'enabled': self.state.keyboard_mouse_enabled}
        
        except Exception as e:
            self.logger.error(f"Enable keyboard/mouse error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_settings(self) -> dict:
        """Get current gamepad settings."""
        return {'status': 'success', 'settings': self.state.gamepad_settings}
    
    def update_settings(self, data: dict) -> dict:
        """Update gamepad settings with validation."""
        try:
            # Update settings with validation using StateService methods
            if 'deadzone_left_stick' in data:
                self.state.set_gamepad_setting('deadzone_left_stick', max(0.0, min(1.0, float(data['deadzone_left_stick']))))
            if 'deadzone_right_stick' in data:
                self.state.set_gamepad_setting('deadzone_right_stick', max(0.0, min(1.0, float(data['deadzone_right_stick']))))
            if 'sensitivity_linear' in data:
                self.state.set_gamepad_setting('sensitivity_linear', max(0.1, min(2.0, float(data['sensitivity_linear']))))
            if 'sensitivity_strafe' in data:
                self.state.set_gamepad_setting('sensitivity_strafe', max(0.1, min(2.0, float(data['sensitivity_strafe']))))
            if 'sensitivity_rotation' in data:
                self.state.set_gamepad_setting('sensitivity_rotation', max(0.1, min(2.0, float(data['sensitivity_rotation']))))
            if 'max_linear_velocity' in data:
                self.state.set_gamepad_setting('max_linear_velocity', max(0.1, min(1.0, float(data['max_linear_velocity']))))
            if 'max_strafe_velocity' in data:
                self.state.set_gamepad_setting('max_strafe_velocity', max(0.1, min(0.8, float(data['max_strafe_velocity']))))
            if 'max_rotation_velocity' in data:
                self.state.set_gamepad_setting('max_rotation_velocity', max(0.1, min(1.5, float(data['max_rotation_velocity']))))
            if 'speed_multiplier' in data:
                self.state.set_gamepad_setting('speed_multiplier', max(0.1, min(2.0, float(data['speed_multiplier']))))

            self.logger.info(f"Gamepad settings updated: {self.state.gamepad_settings}")
            return {'status': 'success', 'settings': self.state.gamepad_settings}

        except Exception as e:
            self.logger.error(f"Error updating gamepad settings: {e}")
            return {'status': 'error', 'message': str(e)}

    def apply_preset(self, preset: str) -> dict:
        """Apply a preset configuration."""
        try:
            if preset in self.presets:
                # Use StateService method to update settings
                self.state.update_gamepad_settings(self.presets[preset])
                self.logger.info(f"Applied '{preset}' preset: {self.state.gamepad_settings}")
                return {'status': 'success', 'preset': preset, 'settings': self.state.gamepad_settings}
            else:
                return {'status': 'error', 'message': 'Invalid preset'}

        except Exception as e:
            self.logger.error(f"Error applying preset: {e}")
            return {'status': 'error', 'message': str(e)}

    def process_movement_command(self, data: dict) -> dict:
        """
        Process movement command from gamepad or keyboard/mouse.

        Args:
            data: Command data containing lx, ly, rx, ry values and optional velocity limits

        Returns:
            dict: Result with status, velocities, and processing time
        """
        request_start_time = time.time()

        try:
            # Check if control is active
            if not self.state.is_connected or (not self.state.gamepad_enabled and not self.state.keyboard_mouse_enabled) or self.state.emergency_stop_active:
                return {'status': 'error', 'message': 'Control not active'}

            # Update last command time
            self.state.last_command_time = time.time()

            # Get input values
            lx = float(data.get('lx', 0.0))  # Lateral (strafe)
            ly = float(data.get('ly', 0.0))  # Linear (forward/back)
            rx = float(data.get('rx', 0.0))  # Yaw (rotation)
            ry = float(data.get('ry', 0.0))  # Pitch (head up/down)

            # Apply dead zones
            deadzone_left = self.state.gamepad_settings['deadzone_left_stick']
            deadzone_right = self.state.gamepad_settings['deadzone_right_stick']

            if abs(lx) < deadzone_left:
                lx = 0.0
            if abs(ly) < deadzone_left:
                ly = 0.0
            if abs(rx) < deadzone_right:
                rx = 0.0
            if abs(ry) < deadzone_right:
                ry = 0.0

            # Apply sensitivity multipliers
            ly *= self.state.gamepad_settings['sensitivity_linear']
            lx *= self.state.gamepad_settings['sensitivity_strafe']
            rx *= self.state.gamepad_settings['sensitivity_rotation']

            # Apply speed multiplier
            speed_mult = self.state.gamepad_settings['speed_multiplier']
            ly *= speed_mult
            lx *= speed_mult
            rx *= speed_mult

            # Use velocity limits from command data if provided (keyboard/mouse), otherwise use gamepad settings
            max_linear = data.get('max_linear', self.state.gamepad_settings['max_linear_velocity'])
            max_strafe = data.get('max_strafe', self.state.gamepad_settings['max_strafe_velocity'])
            max_rotation = data.get('max_rotation', self.state.gamepad_settings['max_rotation_velocity'])

            # Apply velocity limits and axis mapping
            vx = max(-max_linear, min(max_linear, ly))      # Forward/back from left stick Y
            vy = max(-max_strafe, min(max_strafe, -lx))     # Strafe from left stick X (inverted)
            vyaw = max(-max_rotation, min(max_rotation, -rx))  # Yaw from right stick X (inverted)

            # Check if all velocities are zero
            is_zero_velocity = (abs(vx) < 0.01 and abs(vy) < 0.01 and abs(vyaw) < 0.01)

            # Determine if we should send the command
            should_send = True
            if is_zero_velocity and self.state.zero_velocity_sent:
                # Already sent zero velocity, no need to send again
                should_send = False

            # Update tracking variables
            self.state.last_sent_velocities['vx'] = vx
            self.state.last_sent_velocities['vy'] = vy
            self.state.last_sent_velocities['vyaw'] = vyaw
            self.state.zero_velocity_sent = is_zero_velocity

            # Calculate processing time
            processing_time = (time.time() - request_start_time) * 1000  # Convert to ms
            if processing_time > 10:  # Log if processing takes more than 10ms
                self.logger.warning(f"Slow command processing: {processing_time:.1f}ms")

            return {
                'status': 'success',
                'zero_velocity': is_zero_velocity,
                'should_send': should_send,
                'velocities': {'vx': round(vx, 3), 'vy': round(vy, 3), 'vyaw': round(vyaw, 3)},
                'processing_time_ms': round(processing_time, 2)
            }

        except Exception as e:
            self.logger.error(f"Movement command error: {e}")
            return {'status': 'error', 'message': str(e)}

    def send_movement_command_sync(self, vx: float, vy: float, vyaw: float, is_zero_velocity: bool) -> dict:
        """
        Synchronous wrapper for send_movement_command.

        Schedules async send_movement_command() in event loop (fire-and-forget).
        Returns immediately without waiting for completion.

        Args:
            vx: Forward/back velocity
            vy: Left/right velocity
            vyaw: Rotation velocity
            is_zero_velocity: Whether this is a zero velocity command

        Returns:
            dict: Result with status (always success if scheduled)
        """
        if self.state.event_loop and self.state.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_movement_command(vx, vy, vyaw, is_zero_velocity),
                self.state.event_loop
            )
            return {'status': 'success', 'message': 'Movement command scheduled'}
        else:
            self.logger.error(
                f"Event loop not running! state.event_loop={self.state.event_loop}, "
                f"is_running={self.state.event_loop.is_running() if self.state.event_loop else 'N/A'}"
            )
            return {'status': 'error', 'message': 'Event loop not running'}

    async def send_movement_command(self, vx: float, vy: float, vyaw: float, is_zero_velocity: bool):
        """
        Send movement command to robot asynchronously.

        Args:
            vx: Forward/back velocity
            vy: Strafe velocity
            vyaw: Yaw (rotation) velocity
            is_zero_velocity: Whether this is a zero velocity command
        """
        try:
            from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

            # Create task without awaiting to avoid blocking
            asyncio.create_task(
                self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["Move"],
                        "parameter": {"x": vx, "y": vy, "z": vyaw}
                    }
                )
            )

            # Log zero velocity commands for debugging
            if is_zero_velocity:
                self.logger.info("✓ Zero velocity command sent - robot should stop immediately")

        except Exception as e:
            self.logger.error(f"Error sending Move command: {e}")

    def send_robot_action_sync(self, action: str) -> dict:
        """
        Synchronous wrapper for send_robot_action.

        Schedules async send_robot_action() in event loop (fire-and-forget).
        Returns immediately without waiting for completion.

        Args:
            action: Action to perform

        Returns:
            dict: Result with status (always success if scheduled)
        """
        if self.state.event_loop and self.state.event_loop.is_running():
            self.logger.info(f"Scheduling robot action: {action}")
            asyncio.run_coroutine_threadsafe(self.send_robot_action(action), self.state.event_loop)
            return {'status': 'success', 'action': action, 'message': f'Action {action} scheduled'}
        else:
            self.logger.error(
                f"Event loop not running! state.event_loop={self.state.event_loop}, "
                f"is_running={self.state.event_loop.is_running() if self.state.event_loop else 'N/A'}"
            )
            return {'status': 'error', 'message': 'Event loop not running'}

    async def send_robot_action(self, action: str) -> dict:
        """
        Send robot action command asynchronously.

        Args:
            action: Action to perform

        Returns:
            dict: Result with status and action
        """
        try:
            from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

            if action == 'emergency_stop':
                # Emergency stop - damp all motors
                self.state.emergency_stop_active = True
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["Damp"]}
                )
                self.logger.warning("EMERGENCY STOP ACTIVATED")

            elif action == 'clear_emergency':
                self.state.emergency_stop_active = False
                self.logger.info("Emergency stop cleared")

            elif action == 'free_walk':
                # Enter Free Walk mode (Agile Mode) - AI mode obstacle avoidance
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["FreeWalk"]}
                )
                self.logger.info("FreeWalk (Agile Mode) command sent - obstacle avoidance enabled")

            elif action == 'stand_up':
                # Stand up first
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["StandUp"]}
                )
                self.logger.info("Stand up command sent")

                # Wait for stand up to complete, then enter BalanceStand for AI mode movement
                await asyncio.sleep(1.5)
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["BalanceStand"]}
                )
                self.logger.info("BalanceStand command sent - robot ready for AI movement")

            elif action == 'crouch':
                # Crouch down (StandDown)
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["StandDown"]}
                )
                self.logger.info("Crouch command sent")

            elif action == 'sit_down':
                # Sit down
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["Sit"]}
                )
                self.logger.info("Sit down command sent")

            elif action == 'toggle_height':
                # Cycle through heights: 0 (low), 1 (middle), 2 (high)
                self.state.current_body_height = (self.state.current_body_height + 1) % 3
                height_values = [-0.18, 0.0, 0.15]  # Low, middle, high
                height_value = height_values[self.state.current_body_height]
                height_name = ['low', 'middle', 'high'][self.state.current_body_height]

                self.logger.info(f"Attempting to change body height to: {height_name} ({height_value})")
                self.logger.warning("Note: BodyHeight command may not work in AI mode")

                try:
                    response = await self.state.connection.datachannel.pub_sub.publish_request_new(
                        RTC_TOPIC["SPORT_MOD"],
                        {
                            "api_id": SPORT_CMD["BodyHeight"],
                            "parameter": {"height": height_value}
                        }
                    )
                    self.logger.info(f"Body height command sent. Response: {response}")

                    if response and 'data' in response:
                        self.logger.info(f"Body height changed to: {height_name}")
                    else:
                        self.logger.warning(f"Body height command may have failed - no response data")
                except Exception as e:
                    self.logger.error(f"Error changing body height: {e}")

            elif action == 'lidar_switch':
                # Toggle lidar using publish_without_callback
                self.state.lidar_state = not self.state.lidar_state
                switch_value = "on" if self.state.lidar_state else "off"

                self.logger.info(f"Toggling lidar to: {switch_value}")
                try:
                    # If turning lidar ON, must disable traffic saving first
                    if self.state.lidar_state:
                        self.logger.info("Disabling traffic saving for lidar...")
                        await self.state.connection.datachannel.disableTrafficSaving(True)
                        self.logger.info("Traffic saving disabled")

                    # Now toggle the lidar
                    self.state.connection.datachannel.pub_sub.publish_without_callback(
                        RTC_TOPIC["ULIDAR_SWITCH"],
                        switch_value
                    )
                    self.logger.info(f"Lidar switched {switch_value} successfully")
                except Exception as e:
                    self.logger.error(f"Error toggling lidar: {e}")
                    self.state.lidar_state = not self.state.lidar_state  # Revert state on error

            elif action == 'stop_move':
                # Stop all movement
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["StopMove"]}
                )
                self.logger.info("Stop move command sent")

            elif action == 'enable_walk_mode':
                # In AI mode, robot is already in BalanceStand which allows movement
                self.logger.info("Walk mode enabled - robot ready to move (AI mode)")

            elif action == 'disable_walk_mode':
                # Stop movement by sending Move command with zero velocities
                self.logger.info("Walk mode disabled - stopping movement")
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["Move"],
                        "parameter": {"x": 0.0, "y": 0.0, "z": 0.0}
                    }
                )

            elif action == 'speed_level_up':
                # Increase speed level
                self.state.speed_level = min(1, self.state.speed_level + 1)  # Clamp to max 1
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["SpeedLevel"],
                        "parameter": {"level": self.state.speed_level}
                    }
                )
                speed_name = {-1: "slow", 0: "normal", 1: "fast"}[self.state.speed_level]
                self.logger.info(f"Speed level set to: {self.state.speed_level} ({speed_name})")

            elif action == 'speed_level_down':
                # Decrease speed level
                self.state.speed_level = max(-1, self.state.speed_level - 1)  # Clamp to min -1
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["SpeedLevel"],
                        "parameter": {"level": self.state.speed_level}
                    }
                )
                speed_name = {-1: "slow", 0: "normal", 1: "fast"}[self.state.speed_level]
                self.logger.info(f"Speed level set to: {self.state.speed_level} ({speed_name})")

            elif action == 'toggle_free_bound':
                # Toggle FreeBound mode (Bound Run Mode)
                self.state.free_bound_active = not self.state.free_bound_active
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["FreeBound"],
                        "parameter": {"data": self.state.free_bound_active}
                    }
                )
                self.logger.info(f"FreeBound (Bound Run) mode: {'enabled' if self.state.free_bound_active else 'disabled (returned to Agile Mode)'}")

            elif action == 'toggle_free_jump':
                # Toggle FreeJump mode (Jump Mode)
                self.state.free_jump_active = not self.state.free_jump_active
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["FreeJump"],
                        "parameter": {"data": self.state.free_jump_active}
                    }
                )
                self.logger.info(f"FreeJump (Jump) mode: {'enabled' if self.state.free_jump_active else 'disabled (returned to Agile Mode)'}")

            elif action == 'toggle_free_avoid':
                # Toggle FreeAvoid mode (Avoidance Mode)
                self.state.free_avoid_active = not self.state.free_avoid_active
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {
                        "api_id": SPORT_CMD["FreeAvoid"],
                        "parameter": {"data": self.state.free_avoid_active}
                    }
                )
                self.logger.info(f"FreeAvoid (Avoidance) mode: {'enabled' if self.state.free_avoid_active else 'disabled (returned to Agile Mode)'}")

            elif action == 'toggle_walk_pose':
                # Toggle between walk and pose mode (legacy - kept for compatibility)
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["Pose"]}
                )
                self.logger.info("Walk/Pose mode toggled")

            else:
                return {'status': 'error', 'message': f'Unknown action: {action}'}

            return {'status': 'success', 'action': action}

        except Exception as e:
            self.logger.error(f"Robot action error: {e}")
            return {'status': 'error', 'message': str(e)}

    async def send_camera_control(self, yaw: float):
        """
        Send camera control command asynchronously.

        Args:
            yaw: Camera yaw angle
        """
        try:
            from unitree_webrtc_connect.constants import RTC_TOPIC, SPORT_CMD

            await self.state.connection.datachannel.pub_sub.publish_request_new(
                RTC_TOPIC["SPORT_MOD"],
                {
                    "api_id": SPORT_CMD["Euler"],
                    "parameter": {"roll": 0.0, "pitch": 0.0, "yaw": yaw}
                }
            )
        except Exception as e:
            self.logger.error(f"Error sending camera control command: {e}")

