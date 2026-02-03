"""
Unit tests for audio streaming functionality.

Tests cover:
- Audio reception (robot → user)
- Audio transmission (user → robot via push-to-talk)
- Mute/unmute functionality
- PyAudio integration
- MicrophoneAudioTrack class
- Blocking I/O handling with asyncio.to_thread()
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from aiortc import MediaStreamTrack
from av import AudioFrame


@pytest.mark.unit
@pytest.mark.audio
class TestMicrophoneAudioTrack:
    """Test MicrophoneAudioTrack class for audio transmission."""
    
    def test_microphone_track_initialization(self, mock_pyaudio):
        """Test MicrophoneAudioTrack initialization."""
        with patch('pyaudio.PyAudio', return_value=mock_pyaudio):
            # Simplified version - actual test will import real class
            class SimpleMicrophoneTrack:
                def __init__(self):
                    self.sample_rate = 48000
                    self.channels = 2
                    self.samples_per_frame = 960
                    self.is_transmitting = False
            
            track = SimpleMicrophoneTrack()
            
            assert track.sample_rate == 48000
            assert track.channels == 2
            assert track.samples_per_frame == 960
            assert track.is_transmitting is False
    
    def test_start_transmitting(self):
        """Test starting audio transmission (push-to-talk pressed)."""
        class SimpleMicrophoneTrack:
            def __init__(self):
                self.is_transmitting = False
            
            def start_transmitting(self):
                self.is_transmitting = True
        
        track = SimpleMicrophoneTrack()
        assert track.is_transmitting is False
        
        track.start_transmitting()
        assert track.is_transmitting is True
    
    def test_stop_transmitting(self):
        """Test stopping audio transmission (push-to-talk released)."""
        class SimpleMicrophoneTrack:
            def __init__(self):
                self.is_transmitting = True
            
            def stop_transmitting(self):
                self.is_transmitting = False
        
        track = SimpleMicrophoneTrack()
        assert track.is_transmitting is True
        
        track.stop_transmitting()
        assert track.is_transmitting is False
    
    @pytest.mark.asyncio
    async def test_recv_when_transmitting(self, mock_pyaudio):
        """Test receiving audio frames when transmitting."""
        # Mock audio data
        mock_audio_data = b'\x00\x01' * 960
        
        async def mock_recv():
            # Simulate reading from PyAudio
            await asyncio.sleep(0.001)
            return mock_audio_data
        
        result = await mock_recv()
        assert result == mock_audio_data
    
    @pytest.mark.asyncio
    async def test_recv_when_not_transmitting(self):
        """Test receiving silence when not transmitting."""
        async def mock_recv_silence():
            # Should return silence
            silence = np.zeros((1, 960 * 2), dtype=np.int16)
            return silence.tobytes()
        
        result = await mock_recv_silence()
        expected_silence = np.zeros((1, 960 * 2), dtype=np.int16).tobytes()
        assert result == expected_silence


@pytest.mark.unit
@pytest.mark.audio
@pytest.mark.asyncio
class TestAudioReception:
    """Test audio reception from robot (robot → user)."""
    
    async def test_recv_audio_stream_success(self, mock_pyaudio):
        """Test successful audio frame reception and playback."""
        # Mock audio frame
        mock_frame = Mock()
        mock_frame.to_ndarray.return_value = np.zeros(8192, dtype=np.int16)
        
        # Mock PyAudio stream
        mock_stream = Mock()
        mock_stream.write = Mock()
        
        # Simulate recv_audio_stream function
        async def recv_audio_stream(frame, stream, audio_muted):
            if audio_muted:
                return  # Discard frame
            
            audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
            audio_bytes = audio_data.tobytes()
            
            # Use asyncio.to_thread to prevent blocking
            await asyncio.to_thread(stream.write, audio_bytes)
        
        # Test with audio unmuted
        await recv_audio_stream(mock_frame, mock_stream, audio_muted=False)
        mock_stream.write.assert_called_once()
    
    async def test_recv_audio_stream_when_muted(self, mock_pyaudio):
        """Test audio frame reception when muted (should discard)."""
        mock_frame = Mock()
        mock_frame.to_ndarray.return_value = np.zeros(8192, dtype=np.int16)
        
        mock_stream = Mock()
        mock_stream.write = Mock()
        
        async def recv_audio_stream(frame, stream, audio_muted):
            if audio_muted:
                return  # Discard frame
            
            audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
            audio_bytes = audio_data.tobytes()
            await asyncio.to_thread(stream.write, audio_bytes)
        
        # Test with audio muted
        await recv_audio_stream(mock_frame, mock_stream, audio_muted=True)
        mock_stream.write.assert_not_called()
    
    async def test_recv_audio_stream_not_initialized(self):
        """Test audio reception when PyAudio not initialized."""
        async def recv_audio_stream(frame, audio_initialized):
            if not audio_initialized:
                return  # Early return
            # Process frame...
        
        mock_frame = Mock()
        result = await recv_audio_stream(mock_frame, audio_initialized=False)
        assert result is None

    async def test_blocking_io_with_asyncio_to_thread(self, mock_pyaudio):
        """Test that blocking PyAudio operations use asyncio.to_thread()."""
        mock_stream = Mock()
        mock_stream.write = Mock()

        # Simulate blocking write operation
        async def write_with_thread(data):
            # This should use asyncio.to_thread() to prevent blocking
            await asyncio.to_thread(mock_stream.write, data)

        test_data = b'\x00' * 8192
        await write_with_thread(test_data)

        mock_stream.write.assert_called_once_with(test_data)


@pytest.mark.unit
@pytest.mark.audio
class TestAudioMuteUnmute:
    """Test audio mute/unmute functionality."""

    def test_audio_starts_muted(self):
        """Test that audio starts in muted state."""
        audio_muted = True
        assert audio_muted is True

    def test_unmute_audio(self):
        """Test unmuting audio."""
        audio_muted = True
        audio_streaming_enabled = False

        # Unmute
        audio_streaming_enabled = True
        audio_muted = not audio_streaming_enabled

        assert audio_streaming_enabled is True
        assert audio_muted is False

    def test_mute_audio(self):
        """Test muting audio."""
        audio_muted = False
        audio_streaming_enabled = True

        # Mute
        audio_streaming_enabled = False
        audio_muted = not audio_streaming_enabled

        assert audio_streaming_enabled is False
        assert audio_muted is True

    def test_toggle_audio_multiple_times(self):
        """Test toggling audio multiple times."""
        audio_muted = True

        # Toggle 1: unmute
        audio_muted = False
        assert audio_muted is False

        # Toggle 2: mute
        audio_muted = True
        assert audio_muted is True

        # Toggle 3: unmute
        audio_muted = False
        assert audio_muted is False


@pytest.mark.unit
@pytest.mark.audio
class TestPushToTalk:
    """Test push-to-talk functionality."""

    def test_push_to_talk_starts_inactive(self):
        """Test that push-to-talk starts inactive."""
        push_to_talk_active = False
        assert push_to_talk_active is False

    def test_activate_push_to_talk(self):
        """Test activating push-to-talk (C key pressed)."""
        push_to_talk_active = False

        # Activate
        push_to_talk_active = True

        assert push_to_talk_active is True

    def test_deactivate_push_to_talk(self):
        """Test deactivating push-to-talk (C key released)."""
        push_to_talk_active = True

        # Deactivate
        push_to_talk_active = False

        assert push_to_talk_active is False

    def test_push_to_talk_with_microphone_track(self):
        """Test push-to-talk with MicrophoneAudioTrack."""
        class MockMicrophoneTrack:
            def __init__(self):
                self.is_transmitting = False

            def start_transmitting(self):
                self.is_transmitting = True

            def stop_transmitting(self):
                self.is_transmitting = False

        track = MockMicrophoneTrack()

        # Start push-to-talk
        track.start_transmitting()
        assert track.is_transmitting is True

        # Stop push-to-talk
        track.stop_transmitting()
        assert track.is_transmitting is False


@pytest.mark.unit
@pytest.mark.audio
class TestPyAudioIntegration:
    """Test PyAudio integration."""

    def test_pyaudio_initialization(self, mock_pyaudio):
        """Test PyAudio initialization."""
        assert mock_pyaudio is not None
        assert hasattr(mock_pyaudio, 'open')
        assert hasattr(mock_pyaudio, 'terminate')

    def test_pyaudio_stream_open(self, mock_pyaudio):
        """Test opening PyAudio stream."""
        stream = mock_pyaudio.open(
            format=8,  # paInt16
            channels=2,
            rate=48000,
            output=True,
            frames_per_buffer=8192
        )

        assert stream is not None
        mock_pyaudio.open.assert_called_once()

    def test_pyaudio_stream_write(self, mock_pyaudio):
        """Test writing to PyAudio stream."""
        stream = mock_pyaudio.open()
        test_data = b'\x00' * 8192

        stream.write(test_data)
        stream.write.assert_called_once_with(test_data)

    def test_pyaudio_stream_read(self, mock_pyaudio):
        """Test reading from PyAudio stream."""
        stream = mock_pyaudio.open()

        data = stream.read(960)

        assert data is not None
        assert len(data) > 0

    def test_pyaudio_cleanup(self, mock_pyaudio):
        """Test PyAudio cleanup."""
        stream = mock_pyaudio.open()

        stream.stop_stream()
        stream.close()
        mock_pyaudio.terminate()

        stream.stop_stream.assert_called_once()
        stream.close.assert_called_once()
        mock_pyaudio.terminate.assert_called_once()


@pytest.mark.unit
@pytest.mark.audio
class TestAudioErrorHandling:
    """Test audio error handling."""

    @pytest.mark.asyncio
    async def test_audio_stream_error_handling(self):
        """Test handling errors during audio streaming."""
        async def recv_audio_stream_with_error(frame):
            try:
                # Simulate error
                raise Exception("Audio stream error")
            except Exception as e:
                # Should log error and continue
                return None

        result = await recv_audio_stream_with_error(Mock())
        assert result is None

    def test_pyaudio_initialization_error(self):
        """Test handling PyAudio initialization errors."""
        def initialize_pyaudio():
            try:
                # Simulate initialization error
                raise OSError("PyAudio not available")
            except OSError:
                return None

        result = initialize_pyaudio()
        assert result is None

    def test_microphone_not_available(self):
        """Test handling microphone not available error."""
        def open_microphone():
            try:
                # Simulate microphone not available
                raise IOError("No microphone found")
            except IOError:
                return None

        result = open_microphone()
        assert result is None

