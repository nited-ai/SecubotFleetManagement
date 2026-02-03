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
        connection_method = data.get('method')
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
        logging.error(f"Connection error: {e}")
        error_msg = str(e)
        
        # Provide user-friendly error messages
        if "already connected" in error_msg.lower() or "busy" in error_msg.lower():
            error_msg = "Robot is already connected to another client. Close the Unitree mobile app and try again."
        elif "unreachable" in error_msg.lower() or "timeout" in error_msg.lower():
            error_msg = f"Cannot reach robot at the specified address. Check IP and network connection. Error: {error_msg}"
        return jsonify({'status': 'error', 'message': error_msg}), 500


@api_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from the robot"""
    try:
        # Get services from app config
        state = current_app.config['STATE_SERVICE']
        connection_service = current_app.config['CONNECTION_SERVICE']
        audio_service = current_app.config['AUDIO_SERVICE']
        
        # Use ConnectionService to disconnect
        connection_service.disconnect_sync(timeout=10)
        
        # Clean up audio resources
        audio_service.cleanup()
        
        return jsonify({
            'status': 'success',
            'message': 'Disconnected from robot'
        })

    except Exception as e:
        logging.error(f"Disconnect error: {e}")
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
                velocities['vx'],
                velocities['vy'],
                velocities['vyaw'],
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

