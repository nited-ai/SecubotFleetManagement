"""
Shared pytest fixtures for Unitree WebRTC Connect tests.

This module provides common fixtures used across unit, integration, and E2E tests.
"""

import asyncio
import pytest
from unittest.mock import Mock, MagicMock, AsyncMock
from queue import Queue
import threading


# ============================================================================
# Asyncio Event Loop Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for the test session."""
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test function."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    # Clean up pending tasks
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.close()


# ============================================================================
# Mock WebRTC Connection Fixtures
# ============================================================================

@pytest.fixture
def mock_webrtc_connection():
    """Mock WebRTC connection object."""
    connection = AsyncMock()
    connection.connect = AsyncMock(return_value=True)
    connection.disconnect = AsyncMock(return_value=True)
    connection.is_connected = Mock(return_value=True)
    connection.send_command = AsyncMock(return_value=True)
    return connection


@pytest.fixture
def mock_peer_connection():
    """Mock aiortc RTCPeerConnection."""
    pc = AsyncMock()
    pc.addTrack = Mock()
    pc.createDataChannel = Mock()
    pc.setRemoteDescription = AsyncMock()
    pc.createAnswer = AsyncMock()
    pc.setLocalDescription = AsyncMock()
    pc.close = AsyncMock()
    return pc


# ============================================================================
# Mock Audio/Video Track Fixtures
# ============================================================================

@pytest.fixture
def mock_audio_track():
    """Mock audio track for testing."""
    track = AsyncMock()
    track.kind = "audio"
    track.recv = AsyncMock()
    return track


@pytest.fixture
def mock_video_track():
    """Mock video track for testing."""
    track = AsyncMock()
    track.kind = "video"
    track.recv = AsyncMock()
    return track


# ============================================================================
# Mock PyAudio Fixtures
# ============================================================================

@pytest.fixture
def mock_pyaudio():
    """Mock PyAudio instance."""
    pyaudio_mock = Mock()
    stream_mock = Mock()
    stream_mock.write = Mock()
    stream_mock.read = Mock(return_value=b'\x00' * 8192)
    stream_mock.stop_stream = Mock()
    stream_mock.close = Mock()
    pyaudio_mock.open = Mock(return_value=stream_mock)
    pyaudio_mock.terminate = Mock()
    return pyaudio_mock


# ============================================================================
# Frame Queue Fixtures
# ============================================================================

@pytest.fixture
def frame_queue():
    """Create a frame queue for testing."""
    return Queue(maxsize=30)


@pytest.fixture
def frame_lock():
    """Create a threading lock for frame access."""
    return threading.Lock()


# ============================================================================
# Mock Flask App Fixtures
# ============================================================================

@pytest.fixture
def mock_flask_app():
    """Mock Flask application."""
    from flask import Flask
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def flask_client(mock_flask_app):
    """Flask test client."""
    return mock_flask_app.test_client()


# ============================================================================
# Mock SocketIO Fixtures
# ============================================================================

@pytest.fixture
def mock_socketio():
    """Mock Flask-SocketIO instance."""
    socketio_mock = Mock()
    socketio_mock.emit = Mock()
    socketio_mock.on = Mock()
    return socketio_mock


@pytest.fixture
def mock_socketio_client(mock_flask_app, mock_socketio):
    """Mock SocketIO test client."""
    from flask_socketio import SocketIOTestClient
    return SocketIOTestClient(mock_flask_app, mock_socketio)


# ============================================================================
# Gamepad Settings Fixtures
# ============================================================================

@pytest.fixture
def default_gamepad_settings():
    """Default gamepad settings for testing."""
    return {
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


# ============================================================================
# Robot Command Fixtures
# ============================================================================

@pytest.fixture
def sample_move_command():
    """Sample robot move command."""
    return {
        'vx': 0.5,
        'vy': 0.0,
        'vyaw': 0.0
    }


@pytest.fixture
def sample_sport_command():
    """Sample sport mode command."""
    return {
        'command': 'stand_up'
    }

