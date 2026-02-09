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

        # Slew Rate Limiter State (prevents jerky "freaking out" movements)
        # Tracks current velocity and time to implement smooth acceleration ramps
        self.last_cmd_time = time.time()
        self.current_vx = 0.0      # Current linear velocity (m/s)
        self.current_vy = 0.0      # Current strafe velocity (m/s)
        self.current_vyaw = 0.0    # Current rotation velocity (rad/s)
        self.current_pitch = 0.0   # Current pitch angle (rad)

        # Acceleration Limits (units per second squared)
        # These control how fast the robot can change velocity
        # Lower values = smoother/slower ramp-up, Higher values = snappier response
        # Example: MAX_YAW_ACCEL = 10.0 means it takes 0.9s to reach 9.0 rad/s from rest
        self.MAX_LINEAR_ACCEL = 5.0   # m/s² (tune for linear movement smoothness)
        self.MAX_STRAFE_ACCEL = 3.0   # m/s² (tune for strafe movement smoothness)
        self.MAX_YAW_ACCEL = 10.0     # rad/s² (tune for rotation smoothness)
        self.MAX_PITCH_ACCEL = 0.5    # rad/s² (tune for pitch smoothness)

        # Hardware limits: the robot's physical maximum capabilities
        # These MUST match HARDWARE_LIMITS in static/js/curve-utils.js
        # Used for re-normalization when sending to WirelessController topic
        # WirelessController expects normalized [-1, 1] values where 1.0 = robot's full speed
        self.HARDWARE_LIMIT_LINEAR = 5.0    # m/s - max forward/back velocity
        self.HARDWARE_LIMIT_STRAFE = 1.0    # m/s - max strafe velocity
        self.HARDWARE_LIMIT_ROTATION = 3.0  # rad/s - max yaw rotation velocity
        self.HARDWARE_LIMIT_PITCH = 0.35    # rad - max pitch angle (~20°)
        
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
                self.reset_slew_rate_limiter()  # Reset velocity state when disabling control
                self.logger.info("Keyboard/mouse control disabled")
            
            return {'status': 'success', 'enabled': self.state.keyboard_mouse_enabled}
        
        except Exception as e:
            self.logger.error(f"Enable keyboard/mouse error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def reset_slew_rate_limiter(self):
        """
        Reset slew rate limiter state to zero.
        Call this when:
        - Emergency stop is triggered
        - Control is disabled
        - Robot is commanded to stop
        """
        self.current_vx = 0.0
        self.current_vy = 0.0
        self.current_vyaw = 0.0
        self.last_cmd_time = time.time()
        self.logger.debug("Slew rate limiter reset to zero")

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

            # ═══════════════════════════════════════════════════════════════════
            # POSE MODE: Position-based control (bypass velocity pipeline)
            # Frontend sends accumulated joystick position values in [-1, 1].
            # Pass them directly to WirelessController — no slew rate limiter,
            # no re-normalization, no axis inversions (already correct from frontend).
            # ═══════════════════════════════════════════════════════════════════
            if data.get('pose_mode') or self.state.pose_mode_active:
                lx = max(-1.0, min(1.0, float(data.get('lx', 0.0))))  # roll
                ly = max(-1.0, min(1.0, float(data.get('ly', 0.0))))  # height
                rx = max(-1.0, min(1.0, float(data.get('rx', 0.0))))  # yaw
                ry = max(-1.0, min(1.0, float(data.get('ry', 0.0))))  # pitch

                is_zero = (abs(lx) < 0.001 and abs(ly) < 0.001 and abs(rx) < 0.001 and abs(ry) < 0.001)

                if not is_zero:
                    self.logger.info(f"🎯 [POSE MODE] lx(roll)={lx:.3f}, ly(height)={ly:.3f}, rx(yaw)={rx:.3f}, ry(pitch)={ry:.3f}")

                return self.send_movement_command_sync(lx, ly, rx, ry, is_zero)

            # ═══════════════════════════════════════════════════════════════════
            # NORMAL AI MODE: Velocity-based control (existing pipeline)
            # ═══════════════════════════════════════════════════════════════════

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
            # Only apply deadzone to ry for gamepad input
            # Keyboard/mouse pitch already has its own deadzone applied in frontend
            if data.get('source', 'gamepad') != 'keyboard_mouse' and abs(ry) < deadzone_right:
                ry = 0.0

            # Check if this is keyboard/mouse input (already has curves applied)
            # or gamepad input (needs sensitivity/speed multipliers)
            source = data.get('source', 'gamepad')
            is_keyboard_mouse = (source == 'keyboard_mouse')

            # Only apply gamepad sensitivity/speed multipliers to gamepad inputs
            # Keyboard/mouse inputs already have exponential curves applied in frontend
            if not is_keyboard_mouse:
                # Apply sensitivity multipliers (gamepad only)
                ly *= self.state.gamepad_settings['sensitivity_linear']
                lx *= self.state.gamepad_settings['sensitivity_strafe']
                rx *= self.state.gamepad_settings['sensitivity_rotation']

                # Apply speed multiplier (gamepad only)
                speed_mult = self.state.gamepad_settings['speed_multiplier']
                ly *= speed_mult
                lx *= speed_mult
                rx *= speed_mult

            # Use velocity limits from command data if provided (keyboard/mouse), otherwise use gamepad settings
            max_linear = data.get('max_linear', self.state.gamepad_settings['max_linear_velocity'])
            max_strafe = data.get('max_strafe', self.state.gamepad_settings['max_strafe_velocity'])
            max_rotation = data.get('max_rotation', self.state.gamepad_settings['max_rotation_velocity'])
            max_pitch = data.get('max_pitch', 0.35)  # Default to 0.35 rad (~20°) if not provided

            # CRITICAL FIX: Scale normalized input (-1.0 to 1.0) by max velocity BEFORE clamping
            # Frontend sends normalized values (0.0-1.0), backend must multiply by max velocity
            # to get actual physical velocity (e.g., 0.81 * 9.0 = 7.29 rad/s)

            # Step 1: Calculate Target Velocities (scale normalized input by max velocity)
            raw_target_vx = ly * max_linear          # Forward/back from left stick Y
            raw_target_vy = -lx * max_strafe         # Strafe from left stick X (inverted)
            raw_target_vyaw = -rx * max_rotation     # Yaw from right stick X (inverted)
            raw_target_pitch = ry * max_pitch        # Pitch angle (rad) - NOT inverted

            # Step 2: Apply Slew Rate Limiter (prevents jerky "freaking out" movements)
            # This smoothly ramps velocity changes over time instead of allowing instant jumps
            # UNLESS RAGE MODE is enabled (bypasses all smoothing)

            # For keyboard/mouse: pitch uses INSTANT response (no slew rate limiter)
            # because the frontend already handles pitch smoothing
            # For gamepad: pitch goes through the slew rate limiter like other axes
            pitch = raw_target_pitch

            # Check if RAGE MODE is enabled
            rage_mode = data.get('rage_mode', False)

            if rage_mode:
                # RAGE MODE: Bypass slew rate limiter, use raw velocities directly
                vx = raw_target_vx
                vy = raw_target_vy
                vyaw = raw_target_vyaw

                self.logger.warning(f"🔥 [RAGE MODE] RAW VELOCITIES: vx={vx:.3f}, vy={vy:.3f}, vyaw={vyaw:.3f}")
            else:
                # Normal mode: Apply slew rate limiter

                # Get ramp-up time from command data (if provided by frontend)
                # Ramp-up time = time to reach max velocity from standstill
                linear_ramp_time = data.get('linear_ramp_time', 1.0)
                strafe_ramp_time = data.get('strafe_ramp_time', 0.2)
                rotation_ramp_time = data.get('rotation_ramp_time', 0.9)
                pitch_ramp_time = data.get('pitch_ramp_time', 0.8)

                # Convert ramp-up time to acceleration limit
                # Formula: MAX_ACCEL = max_velocity / ramp_time
                # Edge case: If ramp_time = 0, use very high acceleration (instant response)
                MAX_LINEAR_ACCEL = max_linear / linear_ramp_time if linear_ramp_time > 0.01 else 1000.0
                MAX_STRAFE_ACCEL = max_strafe / strafe_ramp_time if strafe_ramp_time > 0.01 else 1000.0
                MAX_YAW_ACCEL = max_rotation / rotation_ramp_time if rotation_ramp_time > 0.01 else 1000.0
                MAX_PITCH_ACCEL = max_pitch / pitch_ramp_time if pitch_ramp_time > 0.01 else 1000.0

                # Calculate time delta since last command
                now = time.time()
                dt = now - self.last_cmd_time
                self.last_cmd_time = now

                # Edge case: If connection dropped for a while (>100ms), reset dt to avoid huge jumps
                if dt > 0.1:
                    dt = 0.033  # Use typical 30Hz polling rate as fallback

                # Apply ASYMMETRIC slew rate limiter to each axis
                # Acceleration: ramp up smoothly using configured ramp_time
                # Deceleration: instant response (follow frontend target directly)
                # This implements FPS convention: instant stop on key release,
                # smooth start on key press. The ramp_time setting only controls
                # how fast the robot accelerates, never how fast it decelerates.

                # Linear (Forward/Back)
                if abs(raw_target_vx) < abs(self.current_vx):
                    # Decelerating (target closer to zero): instant response
                    self.current_vx = raw_target_vx
                else:
                    # Accelerating (target further from zero): apply slew rate limiter
                    delta_vx = raw_target_vx - self.current_vx
                    max_step_vx = MAX_LINEAR_ACCEL * dt
                    self.current_vx += max(-max_step_vx, min(max_step_vx, delta_vx))

                # Strafe (Left/Right)
                if abs(raw_target_vy) < abs(self.current_vy):
                    # Decelerating: instant response
                    self.current_vy = raw_target_vy
                else:
                    # Accelerating: apply slew rate limiter
                    delta_vy = raw_target_vy - self.current_vy
                    max_step_vy = MAX_STRAFE_ACCEL * dt
                    self.current_vy += max(-max_step_vy, min(max_step_vy, delta_vy))

                # Rotation (Yaw)
                if abs(raw_target_vyaw) < abs(self.current_vyaw):
                    # Decelerating: instant response
                    self.current_vyaw = raw_target_vyaw
                else:
                    # Accelerating: apply slew rate limiter
                    delta_vyaw = raw_target_vyaw - self.current_vyaw
                    max_step_vyaw = MAX_YAW_ACCEL * dt
                    self.current_vyaw += max(-max_step_vyaw, min(max_step_vyaw, delta_vyaw))

                # Pitch (Body Tilt) - only apply slew rate for gamepad
                if is_keyboard_mouse:
                    # Keyboard/mouse: instant pitch (frontend handles smoothing)
                    self.current_pitch = raw_target_pitch
                else:
                    # Gamepad: apply slew rate limiter
                    delta_pitch = raw_target_pitch - self.current_pitch
                    max_step_pitch = MAX_PITCH_ACCEL * dt
                    safe_delta_pitch = max(-max_step_pitch, min(max_step_pitch, delta_pitch))
                    self.current_pitch += safe_delta_pitch

                # Step 3: Final Safety Clamp (absolute limits - should rarely trigger now)
                vx = max(-max_linear, min(max_linear, self.current_vx))
                vy = max(-max_strafe, min(max_strafe, self.current_vy))
                vyaw = max(-max_rotation, min(max_rotation, self.current_vyaw))
                pitch = max(-max_pitch, min(max_pitch, self.current_pitch))

            # Debug logging for keyboard/mouse commands (shows slew rate limiter in action)
            if is_keyboard_mouse and (abs(vx) > 0.01 or abs(vy) > 0.01 or abs(vyaw) > 0.01 or abs(pitch) > 0.005):
                if rage_mode:
                    self.logger.info(f"[KB/Mouse Backend RAGE] vx={vx:.3f}, vy={vy:.3f}, vyaw={vyaw:.3f}, pitch={pitch:.3f}")
                else:
                    self.logger.info(f"[KB/Mouse Backend] rx={rx:.3f} → vyaw={vyaw:.3f}, ry={ry:.3f} → pitch={pitch:.3f} (dt={dt*1000:.1f}ms)")

            # Check if all velocities AND pitch are zero
            is_zero_velocity = (abs(vx) < 0.01 and abs(vy) < 0.01 and abs(vyaw) < 0.01 and abs(pitch) < 0.005)

            # Reset slew rate limiter state when robot stops (prevents drift)
            if is_zero_velocity:
                self.current_vx = 0.0
                self.current_vy = 0.0
                self.current_vyaw = 0.0
                self.current_pitch = 0.0

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

            # Re-normalize for WirelessController (joystick values -1 to 1)
            # BUG FIX: Previously divided by max_linear/max_strafe/max_rotation (the user's
            # slider values), which cancelled out the slider effect entirely:
            #   lx_norm = vy / max_strafe = (input * max_strafe) / max_strafe = input
            # The robot always saw ±1.0 regardless of slider position.
            #
            # FIX: Divide by HARDWARE LIMITS (the robot's physical maximum capability).
            # Now when user sets max_strafe=0.6 and hardware limit is 1.2:
            #   lx_norm = 0.6 / 1.2 = 0.5 → robot runs at 50% of its full strafe speed
            ly_norm = round(vx / self.HARDWARE_LIMIT_LINEAR, 4) if self.HARDWARE_LIMIT_LINEAR > 0 else 0.0
            lx_norm = round(-vy / self.HARDWARE_LIMIT_STRAFE, 4) if self.HARDWARE_LIMIT_STRAFE > 0 else 0.0
            rx_norm = round(-vyaw / self.HARDWARE_LIMIT_ROTATION, 4) if self.HARDWARE_LIMIT_ROTATION > 0 else 0.0
            ry_norm = round(pitch / self.HARDWARE_LIMIT_PITCH, 4) if self.HARDWARE_LIMIT_PITCH > 0 else 0.0

            # Clamp normalized values to [-1, 1] for safety
            ly_norm = max(-1.0, min(1.0, ly_norm))
            lx_norm = max(-1.0, min(1.0, lx_norm))
            rx_norm = max(-1.0, min(1.0, rx_norm))
            ry_norm = max(-1.0, min(1.0, ry_norm))

            # Calculate processing time
            processing_time = (time.time() - request_start_time) * 1000  # Convert to ms
            if processing_time > 10:  # Log if processing takes more than 10ms
                self.logger.warning(f"Slow command processing: {processing_time:.1f}ms")

            return {
                'status': 'success',
                'zero_velocity': is_zero_velocity,
                'should_send': should_send,
                'velocities': {
                    'vx': round(vx, 3), 'vy': round(vy, 3), 'vyaw': round(vyaw, 3), 'pitch': round(pitch, 3),
                    'lx': lx_norm, 'ly': ly_norm, 'rx': rx_norm, 'ry': ry_norm
                },
                'processing_time_ms': round(processing_time, 2)
            }

        except Exception as e:
            self.logger.error(f"Movement command error: {e}")
            return {'status': 'error', 'message': str(e)}

    def send_movement_command_sync(self, lx: float, ly: float, rx: float, ry: float, is_zero_velocity: bool) -> dict:
        """
        Synchronous wrapper for send_movement_command.

        Schedules async send_movement_command() in event loop (fire-and-forget).
        Returns immediately without waiting for completion.

        Args:
            lx: Normalized strafe (-1 to 1, +right -left)
            ly: Normalized forward/back (-1 to 1, +forward -backward)
            rx: Normalized yaw rotation (-1 to 1)
            ry: Normalized pitch (-1 to 1) - currently unused, reserved for future pitch implementation
            is_zero_velocity: Whether this is a zero velocity command

        Returns:
            dict: Result with status (always success if scheduled)
        """
        if self.state.event_loop and self.state.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.send_movement_command(lx, ly, rx, ry, is_zero_velocity),
                self.state.event_loop
            )
            return {'status': 'success', 'message': 'Movement command scheduled'}
        else:
            self.logger.error(
                f"Event loop not running! state.event_loop={self.state.event_loop}, "
                f"is_running={self.state.event_loop.is_running() if self.state.event_loop else 'N/A'}"
            )
            return {'status': 'error', 'message': 'Event loop not running'}

    async def send_movement_command(self, lx: float, ly: float, rx: float, ry: float, is_zero_velocity: bool):
        """
        Send movement command to robot via WirelessController topic.

        Uses rt/wirelesscontroller (joystick emulation) for movement control.
        This works in all modes including AI mode.

        Note: ry is accepted but NOT sent to the robot. The Euler API (1007) was
        tested for pitch control but it switches the robot out of AI mode into
        Pose Mode, breaking WASD movement and yaw control. Pitch control requires
        a different approach (TBD).

        Args:
            lx: Normalized strafe (-1 to 1, +right -left)
            ly: Normalized forward/back (-1 to 1, +forward -backward)
            rx: Normalized yaw rotation (-1 to 1)
            ry: Normalized pitch (-1 to 1) - currently IGNORED (pitch not sent to robot)
            is_zero_velocity: Whether this is a zero velocity command
        """
        try:
            from unitree_webrtc_connect.constants import RTC_TOPIC

            # Debug logging for non-trivial commands
            if abs(ly) > 0.01 or abs(lx) > 0.01 or abs(rx) > 0.01:
                self.logger.info(
                    f"🤖 [ROBOT COMMAND] WirelessController: lx={lx:.3f}, ly={ly:.3f}, rx={rx:.3f}"
                )

            # Send via WirelessController topic (joystick emulation)
            # In normal AI mode: ry is 0 (Euler API breaks AI mode)
            # In Pose mode (1028): ry controls pitch via WirelessController natively
            ry_value = round(ry, 4) if self.state.pose_mode_active else 0.0
            self.state.connection.datachannel.pub_sub.publish_without_callback(
                RTC_TOPIC["WIRELESS_CONTROLLER"],
                {"lx": round(lx, 4), "ly": round(ly, 4), "rx": round(rx, 4), "ry": ry_value, "keys": 0}
            )

            # Log zero velocity commands for debugging
            if is_zero_velocity:
                self.logger.info("✓ Zero velocity command sent - robot should stop immediately")

        except Exception as e:
            self.logger.error(f"Error sending WirelessController command: {e}")

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
            result = {'status': 'success', 'action': action, 'message': f'Action {action} scheduled'}

            # Height adjustment disabled - BodyHeight API (1013) returns code 3203 in AI mode
            # height_names = ['low', 'middle', 'high']
            # if action == 'increase_height':
            #     predicted = min(self.state.current_body_height + 1, 2)
            #     result['height_level'] = predicted
            #     result['height_name'] = height_names[predicted]
            # elif action == 'decrease_height':
            #     predicted = max(self.state.current_body_height - 1, 0)
            #     result['height_level'] = predicted
            #     result['height_name'] = height_names[predicted]

            return result
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

            elif action == 'leash_mode':
                # Toggle Leash Mode (Lead Follow mode)
                # Use LeadFollow API 1045 to toggle the mode
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["LeadFollow"]}
                )
                self.logger.info("Leash Mode (Lead Follow) toggle command sent")

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

            # Height adjustment disabled - BodyHeight API (1013) returns code 3203 in AI mode
            # elif action == 'increase_height': ...
            # elif action == 'decrease_height': ...

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

            elif action == 'enter_pose_mode':
                # Enter Pose Mode: stop movement, then send Pose API (1028)
                # WirelessController axes are automatically remapped in Pose mode:
                #   lx → roll, ly → height, rx → yaw, ry → pitch
                if self.state.pose_mode_active:
                    self.logger.warning("Already in Pose Mode - ignoring enter request")
                    return {'status': 'success', 'action': action, 'message': 'Already in pose mode'}

                # Stop movement first
                await self.send_movement_command(0.0, 0.0, 0.0, 0.0, True)
                await asyncio.sleep(0.2)

                # Enter Pose Mode
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["Pose"]}
                )
                self.state.pose_mode_active = True
                self.logger.info("✓ Entered Pose Mode (API 1028) - ry now controls pitch")

            elif action == 'exit_pose_mode':
                # Exit Pose Mode: RecoveryStand (1006) is the ONLY command that works
                if not self.state.pose_mode_active:
                    self.logger.warning("Not in Pose Mode - ignoring exit request")
                    return {'status': 'success', 'action': action, 'message': 'Not in pose mode'}

                # RecoveryStand restores FreeWalk movement
                await self.state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["SPORT_MOD"],
                    {"api_id": SPORT_CMD["RecoveryStand"]}
                )
                await asyncio.sleep(1.0)  # Wait for robot to stabilize

                self.state.pose_mode_active = False
                self.logger.info("✓ Exited Pose Mode (RecoveryStand 1006) - FreeWalk restored")

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

