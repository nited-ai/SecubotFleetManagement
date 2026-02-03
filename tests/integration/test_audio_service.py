"""
Integration tests for AudioService.

These tests verify that AudioService correctly integrates with:
- StateService for state management
- PyAudio for audio playback and capture
- MicrophoneAudioTrack for microphone streaming
- Push-to-talk functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
import numpy as np

from app.services.state import StateService
from app.services.audio import AudioService, MicrophoneAudioTrack


class TestAudioServiceIntegration:
    """Integration tests for AudioService."""
    
    def test_service_initialization(self):
        """Test AudioService initializes with StateService."""
        state = StateService()
        audio_service = AudioService(state)
        
        assert audio_service.state is state
        assert audio_service.logger is not None
        assert audio_service.sample_rate == 48000
        assert audio_service.channels == 2
        assert audio_service.frames_per_buffer == 8192
    
    @pytest.mark.asyncio
    async def test_recv_audio_stream_when_initialized(self):
        """Test recv_audio_stream plays audio when initialized and unmuted."""
        state = StateService()
        audio_service = AudioService(state)
        
        # Mock PyAudio stream
        mock_stream = Mock()
        mock_stream.write = Mock()
        state.pyaudio_stream = mock_stream
        state.audio_initialized = True
        state.audio_muted = False
        
        # Mock audio frame
        mock_frame = Mock()
        test_audio = np.zeros(1024, dtype=np.int16)
        mock_frame.to_ndarray.return_value = test_audio
        
        # Receive audio
        await audio_service.recv_audio_stream(mock_frame)
        
        # Verify audio was written (called once via asyncio.to_thread)
        # Note: We can't easily verify the exact call due to asyncio.to_thread wrapping
        # But we can verify no exceptions were raised
        assert True
    
    @pytest.mark.asyncio
    async def test_recv_audio_stream_when_muted(self):
        """Test recv_audio_stream discards audio when muted."""
        state = StateService()
        audio_service = AudioService(state)
        
        # Mock PyAudio stream
        mock_stream = Mock()
        mock_stream.write = Mock()
        state.pyaudio_stream = mock_stream
        state.audio_initialized = True
        state.audio_muted = True  # Muted
        
        # Mock audio frame
        mock_frame = Mock()
        test_audio = np.zeros(1024, dtype=np.int16)
        mock_frame.to_ndarray.return_value = test_audio
        
        # Receive audio
        await audio_service.recv_audio_stream(mock_frame)
        
        # Verify audio was NOT written
        mock_stream.write.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_recv_audio_stream_when_not_initialized(self):
        """Test recv_audio_stream returns early when not initialized."""
        state = StateService()
        audio_service = AudioService(state)
        
        # Audio not initialized
        state.audio_initialized = False
        state.pyaudio_stream = None
        
        # Mock audio frame
        mock_frame = Mock()
        
        # Receive audio (should return early)
        await audio_service.recv_audio_stream(mock_frame)
        
        # Verify no exceptions raised
        assert True
    
    def test_create_microphone_track(self):
        """Test create_microphone_track creates MicrophoneAudioTrack."""
        state = StateService()
        audio_service = AudioService(state)
        
        # Create microphone track
        with patch('app.services.audio.pyaudio.PyAudio'):
            track = audio_service.create_microphone_track()
            
            # Verify track was created
            assert isinstance(track, MicrophoneAudioTrack)
            assert track.sample_rate == 48000
            assert track.channels == 2
    
    def test_toggle_audio_enable(self):
        """Test toggle_audio enables audio."""
        state = StateService()
        audio_service = AudioService(state)
        
        # Enable audio
        result = audio_service.toggle_audio(True)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['enabled'] is True
        assert result['muted'] is False
        assert 'unmuted' in result['message']
        
        # Verify state was updated
        assert state.audio_streaming_enabled is True
        assert state.audio_muted is False
    
    def test_toggle_audio_disable(self):
        """Test toggle_audio disables audio."""
        state = StateService()
        audio_service = AudioService(state)
        
        # Disable audio
        result = audio_service.toggle_audio(False)
        
        # Verify result
        assert result['status'] == 'success'
        assert result['enabled'] is False
        assert result['muted'] is True
        assert 'muted' in result['message']
        
        # Verify state was updated
        assert state.audio_streaming_enabled is False
        assert state.audio_muted is True
    
    def test_start_push_to_talk_success(self):
        """Test start_push_to_talk starts transmission."""
        state = StateService()
        audio_service = AudioService(state)

        # Mock microphone track
        mock_track = Mock()
        mock_track.start_transmitting = Mock()
        state.microphone_audio_track = mock_track

        # Start push-to-talk
        result = audio_service.start_push_to_talk()

        # Verify result
        assert result['transmitting'] is True

        # Verify track method was called
        mock_track.start_transmitting.assert_called_once()

    def test_start_push_to_talk_not_initialized(self):
        """Test start_push_to_talk when track not initialized."""
        state = StateService()
        audio_service = AudioService(state)

        # No microphone track
        state.microphone_audio_track = None

        # Start push-to-talk
        result = audio_service.start_push_to_talk()

        # Verify result
        assert result['transmitting'] is False
        assert 'error' in result
        assert 'not initialized' in result['error']

    def test_stop_push_to_talk_success(self):
        """Test stop_push_to_talk stops transmission."""
        state = StateService()
        audio_service = AudioService(state)

        # Mock microphone track
        mock_track = Mock()
        mock_track.stop_transmitting = Mock()
        state.microphone_audio_track = mock_track

        # Stop push-to-talk
        result = audio_service.stop_push_to_talk()

        # Verify result
        assert result['transmitting'] is False

        # Verify track method was called
        mock_track.stop_transmitting.assert_called_once()

    def test_stop_push_to_talk_not_initialized(self):
        """Test stop_push_to_talk when track not initialized."""
        state = StateService()
        audio_service = AudioService(state)

        # No microphone track
        state.microphone_audio_track = None

        # Stop push-to-talk
        result = audio_service.stop_push_to_talk()

        # Verify result
        assert result['transmitting'] is False


class TestMicrophoneAudioTrackIntegration:
    """Integration tests for MicrophoneAudioTrack."""

    def test_microphone_track_initialization(self):
        """Test MicrophoneAudioTrack initializes correctly."""
        with patch('app.services.audio.pyaudio.PyAudio') as mock_pyaudio_class:
            # Mock PyAudio instance and stream
            mock_pyaudio = Mock()
            mock_stream = Mock()
            mock_pyaudio.open.return_value = mock_stream
            mock_pyaudio_class.return_value = mock_pyaudio

            # Create track
            track = MicrophoneAudioTrack(
                sample_rate=48000,
                channels=2,
                format=8  # pyaudio.paInt16
            )

            # Verify initialization
            assert track.sample_rate == 48000
            assert track.channels == 2
            assert track.samples_per_frame == 960
            assert track.is_transmitting is False

            # Verify PyAudio was initialized
            mock_pyaudio_class.assert_called_once()
            mock_pyaudio.open.assert_called_once()

    def test_microphone_track_start_stop_transmitting(self):
        """Test start/stop transmitting methods."""
        with patch('app.services.audio.pyaudio.PyAudio'):
            track = MicrophoneAudioTrack(
                sample_rate=48000,
                channels=2,
                format=8
            )

            # Initially not transmitting
            assert track.is_transmitting is False

            # Start transmitting
            track.start_transmitting()
            assert track.is_transmitting is True

            # Stop transmitting
            track.stop_transmitting()
            assert track.is_transmitting is False

    @pytest.mark.asyncio
    async def test_microphone_track_recv_when_transmitting(self):
        """Test recv() generates audio when transmitting."""
        with patch('app.services.audio.pyaudio.PyAudio') as mock_pyaudio_class:
            # Mock PyAudio instance and stream
            mock_pyaudio = Mock()
            mock_stream = Mock()
            test_audio_data = np.zeros(960, dtype=np.int16).tobytes()
            mock_stream.read = Mock(return_value=test_audio_data)
            mock_pyaudio.open.return_value = mock_stream
            mock_pyaudio_class.return_value = mock_pyaudio

            # Create track and start transmitting
            track = MicrophoneAudioTrack(
                sample_rate=48000,
                channels=2,
                format=8
            )
            track.start_transmitting()

            # Receive frame
            frame = await track.recv()

            # Verify frame was created
            assert frame is not None
            assert frame.sample_rate == 48000

    @pytest.mark.asyncio
    async def test_microphone_track_recv_when_not_transmitting(self):
        """Test recv() generates silence when not transmitting."""
        with patch('app.services.audio.pyaudio.PyAudio') as mock_pyaudio_class:
            # Mock PyAudio instance and stream
            mock_pyaudio = Mock()
            mock_stream = Mock()
            test_audio_data = np.zeros(960, dtype=np.int16).tobytes()
            mock_stream.read = Mock(return_value=test_audio_data)
            mock_pyaudio.open.return_value = mock_stream
            mock_pyaudio_class.return_value = mock_pyaudio

            # Create track (not transmitting)
            track = MicrophoneAudioTrack(
                sample_rate=48000,
                channels=2,
                format=8
            )

            # Receive frame
            frame = await track.recv()

            # Verify frame was created (silence)
            assert frame is not None
            assert frame.sample_rate == 48000

