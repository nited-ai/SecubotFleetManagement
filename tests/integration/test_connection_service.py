"""
Integration tests for ConnectionService.

These tests verify that ConnectionService correctly integrates with:
- StateService for state management
- Event loop management
- WebRTC connection creation
- Audio/video callback setup
- Robot initialization
"""

import pytest
import asyncio
import threading
import time
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import pyaudio

from app.services.state import StateService
from app.services.connection import ConnectionService


class TestConnectionServiceIntegration:
    """Integration tests for ConnectionService."""
    
    def test_service_initialization(self):
        """Test ConnectionService initializes with StateService."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        assert conn_service.state is state
        assert conn_service.logger is not None
    
    def test_ensure_event_loop_creates_loop(self):
        """Test ensure_event_loop creates and starts event loop."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        # Initially no event loop
        assert state.event_loop is None
        
        # Ensure event loop
        conn_service.ensure_event_loop()
        
        # Event loop should be created and running
        assert state.event_loop is not None
        assert state.event_loop.is_running()
        assert state.loop_thread is not None
        assert state.loop_thread.is_alive()
        
        # Cleanup
        state.event_loop.call_soon_threadsafe(state.event_loop.stop)
        state.loop_thread.join(timeout=2)
    
    def test_ensure_event_loop_reuses_existing_loop(self):
        """Test ensure_event_loop reuses existing running loop."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        # Create first loop
        conn_service.ensure_event_loop()
        first_loop = state.event_loop
        first_thread = state.loop_thread
        
        # Call again
        conn_service.ensure_event_loop()
        
        # Should reuse same loop
        assert state.event_loop is first_loop
        assert state.loop_thread is first_thread
        
        # Cleanup
        state.event_loop.call_soon_threadsafe(state.event_loop.stop)
        state.loop_thread.join(timeout=2)
    
    def test_create_connection_local_ap(self):
        """Test creating LocalAP connection."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        with patch('app.services.connection.UnitreeWebRTCConnection') as mock_conn:
            conn = conn_service.create_connection('LocalAP')
            
            mock_conn.assert_called_once()
            assert mock_conn.call_args[0][0].name == 'LocalAP'
    
    def test_create_connection_local_sta_with_ip(self):
        """Test creating LocalSTA connection with IP."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        with patch('app.services.connection.UnitreeWebRTCConnection') as mock_conn:
            conn = conn_service.create_connection('LocalSTA', ip='192.168.8.181')
            
            mock_conn.assert_called_once()
            assert mock_conn.call_args[0][0].name == 'LocalSTA'
            assert mock_conn.call_args[1]['ip'] == '192.168.8.181'
    
    def test_create_connection_local_sta_with_serial(self):
        """Test creating LocalSTA connection with serial number."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        with patch('app.services.connection.UnitreeWebRTCConnection') as mock_conn:
            conn = conn_service.create_connection('LocalSTA', serial_number='B42D2000XXXXXXXX')
            
            mock_conn.assert_called_once()
            assert mock_conn.call_args[0][0].name == 'LocalSTA'
            assert mock_conn.call_args[1]['serialNumber'] == 'B42D2000XXXXXXXX'
    
    def test_create_connection_local_sta_missing_params(self):
        """Test creating LocalSTA connection without IP or serial raises error."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        with pytest.raises(ValueError, match='IP or Serial Number required'):
            conn_service.create_connection('LocalSTA')
    
    def test_create_connection_remote(self):
        """Test creating Remote connection."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        with patch('app.services.connection.UnitreeWebRTCConnection') as mock_conn:
            conn = conn_service.create_connection(
                'Remote',
                serial_number='B42D2000XXXXXXXX',
                username='test@example.com',
                password='password123'
            )
            
            mock_conn.assert_called_once()
            assert mock_conn.call_args[0][0].name == 'Remote'
            assert mock_conn.call_args[1]['serialNumber'] == 'B42D2000XXXXXXXX'
            assert mock_conn.call_args[1]['username'] == 'test@example.com'
            assert mock_conn.call_args[1]['password'] == 'password123'
    
    def test_create_connection_remote_missing_params(self):
        """Test creating Remote connection without credentials raises error."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        with pytest.raises(ValueError, match='Serial Number, Username, and Password required'):
            conn_service.create_connection('Remote', serial_number='B42D2000XXXXXXXX')
    
    def test_create_connection_invalid_method(self):
        """Test creating connection with invalid method raises error."""
        state = StateService()
        conn_service = ConnectionService(state)
        
        with pytest.raises(ValueError, match='Invalid connection method'):
            conn_service.create_connection('InvalidMethod')
    
    def test_cleanup_audio_resources(self):
        """Test cleanup_audio_resources cleans up PyAudio."""
        state = StateService()
        conn_service = ConnectionService(state)

        # Setup mock PyAudio resources
        mock_stream = Mock()
        mock_instance = Mock()
        state.pyaudio_stream = mock_stream
        state.pyaudio_instance = mock_instance
        state.microphone_audio_track = Mock()
        state.audio_initialized = True
        state.audio_muted = False

        # Cleanup
        conn_service.cleanup_audio_resources()

        # Verify cleanup methods were called on the mocks
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()
        mock_instance.terminate.assert_called_once()

        # Verify state was reset
        assert state.pyaudio_stream is None
        assert state.pyaudio_instance is None
        assert state.microphone_audio_track is None
        assert state.audio_initialized is False
        assert state.audio_muted is True

    def test_cleanup_connection(self):
        """Test cleanup_connection cleans up connection and audio."""
        state = StateService()
        conn_service = ConnectionService(state)

        # Setup mock resources
        state.connection = Mock()
        state.pyaudio_stream = Mock()
        state.pyaudio_instance = Mock()

        # Cleanup
        conn_service.cleanup_connection()

        # Verify cleanup
        assert state.connection is None
        assert state.pyaudio_stream is None
        assert state.pyaudio_instance is None

    @pytest.mark.asyncio
    async def test_setup_connection_success(self):
        """Test setup_connection successfully sets up video and audio."""
        state = StateService()
        conn_service = ConnectionService(state)

        # Mock connection
        mock_conn = Mock()
        mock_conn.connect = AsyncMock()
        mock_conn.video = Mock()
        mock_conn.audio = Mock()
        mock_conn.pc = Mock()

        # Mock callbacks
        video_callback = Mock()
        audio_callback = Mock()
        microphone_track_class = Mock(return_value=Mock())

        # Audio config
        audio_config = {
            'format': 8,  # pyaudio.paInt16
            'channels': 2,
            'rate': 48000,
            'frames_per_buffer': 8192
        }

        # Mock PyAudio
        with patch('app.services.connection.pyaudio.PyAudio') as mock_pyaudio_class:
            mock_pyaudio = Mock()
            mock_stream = Mock()
            mock_pyaudio.open.return_value = mock_stream
            mock_pyaudio_class.return_value = mock_pyaudio

            # Setup connection
            await conn_service.setup_connection(
                mock_conn,
                video_callback,
                audio_callback,
                microphone_track_class,
                audio_config
            )

        # Verify connection setup
        mock_conn.connect.assert_called_once()
        mock_conn.video.switchVideoChannel.assert_called_once_with(True)
        mock_conn.video.add_track_callback.assert_called_once_with(video_callback)
        mock_conn.audio.switchAudioChannel.assert_called_once_with(True)
        mock_conn.audio.add_track_callback.assert_called_once_with(audio_callback)
        mock_conn.pc.addTrack.assert_called_once()

        # Verify state updated
        assert state.connection is mock_conn
        assert state.is_connected is True
        assert state.audio_initialized is True
        assert state.pyaudio_instance is not None
        assert state.pyaudio_stream is not None
        assert state.microphone_audio_track is not None

    @pytest.mark.asyncio
    async def test_initialize_robot_success(self):
        """Test initialize_robot switches to AI mode and sends FreeWalk."""
        state = StateService()
        conn_service = ConnectionService(state)

        # Mock connection
        mock_conn = Mock()
        mock_datachannel = Mock()
        mock_pub_sub = Mock()
        mock_pub_sub.publish_request_new = AsyncMock()
        mock_datachannel.pub_sub = mock_pub_sub
        mock_conn.datachannel = mock_datachannel
        state.connection = mock_conn

        # Mock response (current mode is "sport")
        mock_pub_sub.publish_request_new.return_value = {
            'data': {
                'data': '{"name": "sport"}'
            }
        }

        # Initialize robot
        await conn_service.initialize_robot()

        # Verify calls
        assert mock_pub_sub.publish_request_new.call_count == 3
        # First call: check mode
        # Second call: switch to AI mode
        # Third call: send FreeWalk

    @pytest.mark.asyncio
    async def test_disconnect_connection(self):
        """Test disconnect_connection closes WebRTC connection."""
        state = StateService()
        conn_service = ConnectionService(state)

        # Mock connection
        mock_conn = Mock()
        mock_conn.disconnect = AsyncMock()
        state.connection = mock_conn
        state.is_connected = True

        # Disconnect
        await conn_service.disconnect_connection()

        # Verify
        mock_conn.disconnect.assert_called_once()
        assert state.is_connected is False

    def test_initialize_robot_sync_schedules_coroutine(self):
        """Test initialize_robot_sync schedules coroutine in event loop."""
        state = StateService()
        conn_service = ConnectionService(state)

        # Create event loop
        conn_service.ensure_event_loop()

        # Mock connection
        mock_conn = Mock()
        mock_datachannel = Mock()
        mock_pub_sub = Mock()
        mock_pub_sub.publish_request_new = AsyncMock(return_value={'data': {'data': '{"name": "ai"}'}})
        mock_datachannel.pub_sub = mock_pub_sub
        mock_conn.datachannel = mock_datachannel
        state.connection = mock_conn

        # Initialize robot (fire-and-forget)
        conn_service.initialize_robot_sync()

        # Give it time to schedule
        time.sleep(0.5)

        # Cleanup
        state.event_loop.call_soon_threadsafe(state.event_loop.stop)
        state.loop_thread.join(timeout=2)


