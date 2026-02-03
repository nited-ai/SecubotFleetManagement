"""
WebSocket handlers for Unitree WebRTC Connect.

This module contains all WebSocket event handlers for real-time communication.
"""

import logging
from flask import current_app
from flask_socketio import emit


def register_websocket_handlers(socketio):
    """
    Register WebSocket handlers with the SocketIO instance.
    
    Args:
        socketio: Flask-SocketIO instance
    """
    
    @socketio.on('control_command')
    def handle_websocket_control_command(data):
        """
        WebSocket handler for gamepad or keyboard/mouse movement commands
        This provides lower latency than HTTP by using persistent WebSocket connection
        """
        try:
            state = current_app.config['STATE_SERVICE']
            control_service = current_app.config['CONTROL_SERVICE']

            if not state.is_connected:
                emit('command_response', {
                    'status': 'error',
                    'message': 'Robot not connected'
                })
                return

            if not state.gamepad_enabled and not state.keyboard_mouse_enabled:
                emit('command_response', {
                    'status': 'error',
                    'message': 'Control not enabled'
                })
                return

            # Process movement command
            result = control_service.process_movement_command(data)

            if result['status'] == 'error':
                emit('command_response', result)
                return

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

            # Send response back to client
            emit('command_response', result)

        except Exception as e:
            logging.error(f"WebSocket control command error: {e}")
            emit('command_response', {
                'status': 'error',
                'message': str(e)
            })
    
    @socketio.on('start_microphone')
    def handle_start_microphone():
        """Start transmitting microphone audio (push-to-talk pressed)"""
        try:
            audio_service = current_app.config['AUDIO_SERVICE']
            result = audio_service.start_push_to_talk()
            emit('microphone_status', result)
        except Exception as e:
            logging.error(f"Error starting microphone: {e}")
            emit('microphone_status', {'transmitting': False, 'error': str(e)})
    
    @socketio.on('stop_microphone')
    def handle_stop_microphone():
        """Stop transmitting microphone audio (push-to-talk released)"""
        try:
            audio_service = current_app.config['AUDIO_SERVICE']
            result = audio_service.stop_push_to_talk()
            emit('microphone_status', result)
        except Exception as e:
            logging.error(f"Error stopping microphone: {e}")

