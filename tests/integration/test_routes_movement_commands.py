"""
Integration tests for movement command routes.

Tests the HTTP and WebSocket routes to ensure they properly call both
process_movement_command() and send_movement_command_sync().
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_socketio import SocketIO
from app.services import StateService, ControlService
from app.routes import api_bp, register_websocket_handlers


class TestHTTPMovementCommandRoute:
    """Test the HTTP /control/command endpoint."""

    @pytest.fixture
    def app(self):
        """Create a Flask app for testing."""
        app = Flask(__name__)
        app.config['TESTING'] = True

        # Create mock services
        state = Mock(spec=StateService)
        state.is_connected = True
        state.gamepad_enabled = True
        state.keyboard_mouse_enabled = False

        control_service = Mock(spec=ControlService)

        # Store services in app config
        app.config['STATE_SERVICE'] = state
        app.config['CONTROL_SERVICE'] = control_service

        # Register blueprint
        app.register_blueprint(api_bp)

        return app

    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return app.test_client()

    def test_gamepad_command_calls_both_process_and_send(self, client, app):
        """Test that /control/command calls both process and send methods."""
        control_service = app.config['CONTROL_SERVICE']

        # Mock process_movement_command to return success with should_send=True
        control_service.process_movement_command.return_value = {
            'status': 'success',
            'should_send': True,
            'zero_velocity': False,
            'velocities': {'vx': 0.3, 'vy': 0.0, 'vyaw': 0.0},
            'processing_time_ms': 1.5
        }

        # Mock send_movement_command_sync to return success
        control_service.send_movement_command_sync.return_value = {
            'status': 'success',
            'message': 'Movement command scheduled'
        }

        # Send command
        response = client.post('/control/command', json={
            'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0
        })

        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['send_status'] == 'success'

        # Verify both methods were called
        control_service.process_movement_command.assert_called_once()
        control_service.send_movement_command_sync.assert_called_once_with(
            0.3, 0.0, 0.0, False
        )

    def test_gamepad_command_does_not_send_when_should_send_false(self, client, app):
        """Test that send is skipped when should_send=False."""
        control_service = app.config['CONTROL_SERVICE']

        # Mock process_movement_command to return should_send=False
        control_service.process_movement_command.return_value = {
            'status': 'success',
            'should_send': False,  # Don't send (e.g., duplicate zero velocity)
            'zero_velocity': True,
            'velocities': {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0},
            'processing_time_ms': 1.2
        }

        # Send command
        response = client.post('/control/command', json={
            'lx': 0.0, 'ly': 0.0, 'rx': 0.0, 'ry': 0.0
        })

        # Verify response
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'send_status' not in data  # Should not have send_status

        # Verify process was called but send was NOT called
        control_service.process_movement_command.assert_called_once()
        control_service.send_movement_command_sync.assert_not_called()

    def test_gamepad_command_handles_process_error(self, client, app):
        """Test error handling when process_movement_command fails."""
        control_service = app.config['CONTROL_SERVICE']

        # Mock process_movement_command to return error
        control_service.process_movement_command.return_value = {
            'status': 'error',
            'message': 'Control not active'
        }

        # Send command
        response = client.post('/control/command', json={
            'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0
        })

        # Verify error response
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

        # Verify send was NOT called
        control_service.send_movement_command_sync.assert_not_called()

    def test_gamepad_command_when_not_connected(self, client, app):
        """Test that command fails when not connected."""
        state = app.config['STATE_SERVICE']
        state.is_connected = False

        # Send command
        response = client.post('/control/command', json={
            'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0
        })

        # Verify error response
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'not connected' in data['message'].lower()


class TestWebSocketMovementCommandHandler:
    """Test the WebSocket control_command handler."""

    @pytest.fixture
    def app(self):
        """Create a Flask app with SocketIO for testing."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_secret_key'

        # Create SocketIO instance
        socketio = SocketIO(app, async_mode='threading')

        # Create mock services
        state = Mock(spec=StateService)
        state.is_connected = True
        state.gamepad_enabled = True
        state.keyboard_mouse_enabled = False

        control_service = Mock(spec=ControlService)

        # Store services in app config
        app.config['STATE_SERVICE'] = state
        app.config['CONTROL_SERVICE'] = control_service

        # Register WebSocket handlers
        register_websocket_handlers(socketio)

        return app, socketio

    @pytest.fixture
    def client(self, app):
        """Create a SocketIO test client."""
        flask_app, socketio = app
        return socketio.test_client(flask_app)

    def test_websocket_gamepad_command_calls_both_process_and_send(self, app, client):
        """Test that WebSocket handler calls both process and send methods."""
        flask_app, socketio = app
        control_service = flask_app.config['CONTROL_SERVICE']

        # Mock process_movement_command to return success with should_send=True
        control_service.process_movement_command.return_value = {
            'status': 'success',
            'should_send': True,
            'zero_velocity': False,
            'velocities': {'vx': 0.3, 'vy': 0.0, 'vyaw': 0.0},
            'processing_time_ms': 1.5
        }

        # Mock send_movement_command_sync to return success
        control_service.send_movement_command_sync.return_value = {
            'status': 'success',
            'message': 'Movement command scheduled'
        }

        # Send WebSocket event
        client.emit('control_command', {
            'lx': 0.5, 'ly': 0.5, 'rx': 0.0, 'ry': 0.0
        })

        # Verify both methods were called
        control_service.process_movement_command.assert_called_once()
        control_service.send_movement_command_sync.assert_called_once_with(
            0.3, 0.0, 0.0, False
        )

