"""
HTTP API routes for Unitree WebRTC Connect.

This module contains all HTTP API endpoints for robot control and management.
"""

import asyncio
import logging
import time
from flask import Blueprint, request, jsonify, current_app

api_bp = Blueprint('api', __name__)


@api_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to the robot"""
    try:
        # Get services from app config
        state = current_app.config['STATE_SERVICE']
        connection_service = current_app.config['CONNECTION_SERVICE']
        video_service = current_app.config['VIDEO_SERVICE']
        audio_service = current_app.config['AUDIO_SERVICE']
        
        data = request.json
        connection_method = data.get('connection_method')
        ip = data.get('ip', '')
        serial_number = data.get('serial_number', '')
        username = data.get('username', '')
        password = data.get('password', '')

        # Audio configuration
        audio_config = {
            'format': audio_service.format,
            'channels': audio_service.channels,
            'rate': audio_service.sample_rate,
            'frames_per_buffer': audio_service.frames_per_buffer
        }

        # Use ConnectionService to establish connection
        connection_service.connect_sync(
            method=connection_method,
            video_callback=video_service.recv_camera_stream,
            audio_callback=audio_service.recv_audio_stream,
            microphone_track_class=audio_service.create_microphone_track,
            audio_config=audio_config,
            ip=ip if ip else None,
            serial_number=serial_number if serial_number else None,
            username=username if username else None,
            password=password if password else None,
            timeout=30
        )

        return jsonify({
            'status': 'success',
            'message': 'Connected to robot successfully',
            'audio_enabled': state.audio_streaming_enabled
        })

    except Exception as e:
        logging.error(f"Connection error: {e}", exc_info=True)
        error_msg = str(e)

        # Provide user-friendly error messages based on error type
        if "already connected" in error_msg.lower() or "busy" in error_msg.lower():
            error_msg = "Robot is already connected to another client. Close the Unitree mobile app and try again."
        elif "unreachable" in error_msg.lower() or "timeout" in error_msg.lower():
            error_msg = f"Cannot reach robot. Check IP address and network connection."
        elif "invalid username or password" in error_msg.lower() or "authentication failed" in error_msg.lower():
            # Authentication errors - pass through the detailed message
            pass
        elif "error 567" in error_msg.lower() or "temporarily unavailable" in error_msg.lower():
            # HTTP 567 / service unavailable errors - pass through the detailed message
            pass
        elif "rate limit" in error_msg.lower() or "too many" in error_msg.lower():
            # Rate limiting errors - pass through the detailed message
            pass
        elif "cannot connect to unitree cloud" in error_msg.lower() or "connection to unitree" in error_msg.lower():
            # Network/cloud service errors - pass through the detailed message
            pass
        elif "invalid json" in error_msg.lower() or "expecting value" in error_msg.lower():
            error_msg = "Unitree cloud service returned an invalid response. The service may be temporarily unavailable. Please try again later."

        return jsonify({'status': 'error', 'message': error_msg}), 500


@api_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from the robot"""
    try:
        logging.info("=" * 60)
        logging.info("DISCONNECT API ENDPOINT CALLED")
        logging.info("=" * 60)

        # Get services from app config
        state = current_app.config['STATE_SERVICE']
        connection_service = current_app.config['CONNECTION_SERVICE']

        logging.info(f"Current connection state: is_connected={state.is_connected}")

        # Use ConnectionService to disconnect
        # Note: This handles ALL cleanup including audio resources
        logging.info("Calling connection_service.disconnect_sync()...")
        connection_service.disconnect_sync(timeout=10)
        logging.info("✓ disconnect_sync() completed")

        logging.info("=" * 60)
        logging.info("DISCONNECT API ENDPOINT COMPLETED SUCCESSFULLY")
        logging.info("=" * 60)

        return jsonify({
            'status': 'success',
            'message': 'Disconnected from robot'
        })

    except Exception as e:
        logging.error("=" * 60)
        logging.error(f"DISCONNECT API ENDPOINT ERROR: {e}")
        logging.error("=" * 60)
        logging.error(f"Full traceback:", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/control/gamepad/enable', methods=['POST'])
def enable_gamepad():
    """Enable or disable gamepad control"""
    try:
        control_service = current_app.config['CONTROL_SERVICE']
        connection_service = current_app.config['CONNECTION_SERVICE']

        data = request.json
        enable = data.get('enable', False)

        result = control_service.enable_gamepad(enable, connection_service)

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"Enable gamepad error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/control/keyboard_mouse/enable', methods=['POST'])
def enable_keyboard_mouse():
    """Enable or disable keyboard/mouse control"""
    try:
        control_service = current_app.config['CONTROL_SERVICE']
        connection_service = current_app.config['CONNECTION_SERVICE']

        data = request.json
        enable = data.get('enable', False)

        result = control_service.enable_keyboard_mouse(enable, connection_service)

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"Enable keyboard/mouse error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/audio/toggle', methods=['POST'])
def toggle_audio_streaming():
    """
    Mute or unmute audio playback dynamically (no reconnection required).
    Audio stream is always connected, this just controls playback.
    """
    try:
        audio_service = current_app.config['AUDIO_SERVICE']

        data = request.json
        enable = data.get('enable', False)

        result = audio_service.toggle_audio(enable)

        return jsonify(result)

    except Exception as e:
        logging.error(f"Toggle audio error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/audio/test', methods=['POST'])
def test_audio():
    """Test audio playback with a simple beep/tone"""
    try:
        state = current_app.config['STATE_SERVICE']
        audio_service = current_app.config['AUDIO_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        if not audio_service.pyaudio_initialized:
            return jsonify({'status': 'error', 'message': 'Audio not initialized'}), 400

        # Generate a simple 440Hz tone (A4 note) for 0.5 seconds
        import numpy as np
        duration = 0.5  # seconds
        frequency = 440  # Hz
        sample_rate = audio_service.sample_rate

        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        tone = np.sin(2 * np.pi * frequency * t)

        # Convert to 16-bit PCM
        tone_int16 = (tone * 32767).astype(np.int16)

        # Convert to bytes
        tone_bytes = tone_int16.tobytes()

        # Play the tone using asyncio.to_thread to avoid blocking
        if state.event_loop and state.event_loop.is_running():
            async def play_test_tone():
                try:
                    await asyncio.to_thread(audio_service.pyaudio_stream.write, tone_bytes)
                    logging.info("Test tone played successfully")
                except Exception as e:
                    logging.error(f"Error playing test tone: {e}")

            asyncio.run_coroutine_threadsafe(play_test_tone(), state.event_loop)

        return jsonify({
            'status': 'success',
            'message': 'Test tone played (440Hz for 0.5s)'
        })

    except Exception as e:
        logging.error(f"Audio test error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/control/command', methods=['POST'])
def control_command():
    """Send gamepad or keyboard/mouse movement command to robot"""
    try:
        state = current_app.config['STATE_SERVICE']
        control_service = current_app.config['CONTROL_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        if not state.gamepad_enabled and not state.keyboard_mouse_enabled:
            return jsonify({'status': 'error', 'message': 'Control not enabled'}), 400

        data = request.json

        # Process movement command
        result = control_service.process_movement_command(data)

        if result['status'] == 'error':
            return jsonify(result), 400

        # If should send, actually send the command to the robot
        if result.get('should_send', False):
            velocities = result['velocities']
            send_result = control_service.send_movement_command_sync(
                velocities.get('lx', 0.0),
                velocities.get('ly', 0.0),
                velocities.get('rx', 0.0),
                velocities.get('ry', 0.0),
                result['zero_velocity']
            )
            # Merge send result with process result
            result['send_status'] = send_result['status']

        return jsonify(result)

    except Exception as e:
        logging.error(f"Control command error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/control/settings', methods=['GET'])
def get_control_settings():
    """Get current control settings"""
    control_service = current_app.config['CONTROL_SERVICE']
    result = control_service.get_settings()
    return jsonify(result)


@api_bp.route('/control/settings', methods=['POST'])
def update_control_settings():
    """Update control settings"""
    try:
        control_service = current_app.config['CONTROL_SERVICE']

        data = request.json
        result = control_service.update_settings(data)

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"Error updating control settings: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/control/settings/preset', methods=['POST'])
def apply_control_preset():
    """Apply a preset configuration"""
    try:
        control_service = current_app.config['CONTROL_SERVICE']

        data = request.json
        preset = data.get('preset', 'normal')

        result = control_service.apply_preset(preset)

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"Error applying preset: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/control/action', methods=['POST'])
def control_action():
    """Handle control button actions (gamepad/keyboard)"""
    try:
        state = current_app.config['STATE_SERVICE']
        control_service = current_app.config['CONTROL_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        data = request.json
        action = data.get('action')

        if not action:
            return jsonify({'status': 'error', 'message': 'No action specified'}), 400

        # Use synchronous wrapper to schedule async action in event loop
        result = control_service.send_robot_action_sync(action)

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"Control action error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/control/camera', methods=['POST'])
def control_camera():
    """Handle camera control (gamepad triggers/keyboard)"""
    try:
        state = current_app.config['STATE_SERVICE']
        control_service = current_app.config['CONTROL_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        data = request.json
        yaw = data.get('yaw', 0)

        result = control_service.send_camera_control(yaw)

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"Control camera error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/status')
def status():
    """Get connection status"""
    state = current_app.config['STATE_SERVICE']

    return jsonify({
        'connected': state.is_connected,
        'gamepad_enabled': state.gamepad_enabled,
        'keyboard_mouse_enabled': state.keyboard_mouse_enabled,
        'emergency_stop': state.emergency_stop_active
    })


@api_bp.route('/ping')
def ping():
    """Lightweight ping endpoint for network latency testing"""
    return jsonify({'pong': time.time()})


@api_bp.route('/robot/status')
def robot_status():
    """Get current robot status for HUD display"""
    try:
        state = current_app.config['STATE_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        # Get real battery level from LOW_STATE subscription
        battery = state.battery_level if state.battery_level is not None else 0

        # Get real ping from periodic MOTION_SWITCHER query round-trip time
        ping = state.ping_ms if state.ping_ms is not None else 999

        # Get maximum temperature from all sensors
        temperature = state.max_temperature if state.max_temperature is not None else 0

        # Mode display temporarily disabled - investigating LF_SPORT_MOD_STATE subscription
        # gait = state.current_mode if state.current_mode else 'unknown'
        # gait_display_names = {
        #     'idle': 'Idle',
        #     'trot': 'Trot',
        #     'climb_stairs': 'Climb Stairs',
        #     'trot_obstacle': 'Trot Obstacle',
        #     'unknown': 'Unknown'
        # }
        # mode_display = gait_display_names.get(gait, gait.replace('_', ' ').title())

        status_data = {
            'battery': battery,
            'ping': ping,
            'temperature': temperature,
            # 'mode': mode_display,  # Temporarily disabled
            'connected': True
        }

        return jsonify(status_data)

    except Exception as e:
        logging.error(f"Robot status error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/robot/light', methods=['GET'])
def get_light_level():
    """
    Get current robot LED brightness level via VUI API 1006.

    Returns:
        {
            "success": true,
            "level": 5  // 0-10 discrete brightness level
        }
    """
    try:
        state = current_app.config['STATE_SERVICE']

        if not state.is_connected:
            return jsonify({'success': False, 'message': 'Robot not connected'}), 400

        from unitree_webrtc_connect.constants import RTC_TOPIC
        import asyncio
        import json as json_mod

        async def query_brightness():
            """Query current brightness from robot via VUI API 1006."""
            try:
                response = await state.connection.datachannel.pub_sub.publish_request_new(
                    RTC_TOPIC["VUI"],
                    {"api_id": 1006}
                )

                if response and 'data' in response:
                    if 'header' in response['data']:
                        status_code = response['data']['header'].get('status', {}).get('code', -1)
                        if status_code == 0:
                            data_str = response['data'].get('data', '{}')
                            data_parsed = json_mod.loads(data_str) if isinstance(data_str, str) else data_str
                            brightness = data_parsed.get('brightness', 0)
                            logging.info(f"💡 Current LED brightness: {brightness}/10")
                            return brightness

                logging.warning(f"Failed to query LED brightness: {response}")
                return None

            except Exception as e:
                logging.error(f"Error querying LED brightness: {e}")
                return None

        future = asyncio.run_coroutine_threadsafe(query_brightness(), state.event_loop)
        brightness = future.result(timeout=5)

        if brightness is not None:
            return jsonify({'success': True, 'level': brightness})
        else:
            return jsonify({'success': False, 'message': 'Failed to query brightness'}), 500

    except Exception as e:
        logging.error(f"Get light level error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/robot/light', methods=['POST'])
def set_light_level():
    """
    Set robot LED brightness level (flashlight/headlight).

    IMPORTANT: This uses the new set_led_brightness() method which handles
    flashlight/RGB LED interaction (pausing RAGE MODE, queuing RGB changes, etc.)

    Request body:
        {
            "level": 5  // 0-10 discrete brightness level
        }

    Returns:
        {
            "success": true,
            "level": 5
        }
    """
    try:
        control_service = current_app.config['CONTROL_SERVICE']
        state = current_app.config['STATE_SERVICE']

        if not state.is_connected:
            return jsonify({'success': False, 'message': 'Robot not connected'}), 400

        data = request.get_json()
        brightness = data.get('level', 0)

        # Validate brightness level (0-10)
        if not isinstance(brightness, int) or brightness < 0 or brightness > 10:
            return jsonify({'success': False, 'message': 'Brightness must be between 0 and 10'}), 400

        # Use the control service method which handles flashlight/RGB interaction
        import asyncio

        future = asyncio.run_coroutine_threadsafe(
            control_service.set_led_brightness(brightness),
            state.event_loop
        )
        future.result(timeout=5)

        return jsonify({'success': True, 'level': brightness})

    except Exception as e:
        logging.error(f"Light level error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@api_bp.route('/webrtc/test_direct_command', methods=['POST'])
def webrtc_test_direct_command():
    """
    Test endpoint to send a command directly via WebRTC data channel
    This bypasses HTTP for the actual command, only using HTTP to trigger it
    Used for latency comparison testing
    """
    try:
        state = current_app.config['STATE_SERVICE']
        control_service = current_app.config['CONTROL_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        data = request.json
        vx = data.get('vx', 0)
        vy = data.get('vy', 0)
        vyaw = data.get('vyaw', 0)

        # Send command directly via WebRTC
        result = control_service.send_movement_command(vx, vy, vyaw, is_zero_velocity=False)

        if result['status'] == 'error':
            return jsonify(result), 400

        return jsonify(result)

    except Exception as e:
        logging.error(f"WebRTC test command error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================================
# LED CONTROL ENDPOINTS (VUI API)
# ============================================================================

@api_bp.route('/led/rage_mode', methods=['POST'])
def led_rage_mode():
    """Start or stop RAGE MODE pulsating LED effect"""
    try:
        control_service = current_app.config['CONTROL_SERVICE']
        state = current_app.config['STATE_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        data = request.json
        enabled = data.get('enabled', False)

        # Schedule async LED control in event loop (fire-and-forget)
        if state.event_loop and state.event_loop.is_running():
            if enabled:
                asyncio.run_coroutine_threadsafe(
                    control_service.start_rage_mode_pulsating(),
                    state.event_loop
                )
                return jsonify({'status': 'success', 'message': 'RAGE MODE LED started'})
            else:
                asyncio.run_coroutine_threadsafe(
                    control_service.stop_rage_mode_pulsating(),
                    state.event_loop
                )
                return jsonify({'status': 'success', 'message': 'RAGE MODE LED stopped'})
        else:
            return jsonify({'status': 'error', 'message': 'Event loop not running'}), 500

    except Exception as e:
        logging.error(f"LED RAGE MODE error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/led/preset_flash', methods=['POST'])
def led_preset_flash():
    """Flash LED color for sensitivity preset selection"""
    try:
        control_service = current_app.config['CONTROL_SERVICE']
        state = current_app.config['STATE_SERVICE']

        if not state.is_connected:
            return jsonify({'status': 'error', 'message': 'Robot not connected'}), 400

        data = request.json
        preset = data.get('preset', 'normal')

        # Schedule async LED control in event loop (fire-and-forget)
        if state.event_loop and state.event_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                control_service.flash_preset_color(preset),
                state.event_loop
            )
            return jsonify({'status': 'success', 'preset': preset})
        else:
            return jsonify({'status': 'error', 'message': 'Event loop not running'}), 500

    except Exception as e:
        logging.error(f"LED preset flash error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

