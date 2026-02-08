"""
AudioService - Audio streaming management for Unitree WebRTC Connect.

This service encapsulates all audio-related functionality:
- Audio reception from robot (robot → user)
- Audio transmission to robot (user → robot via microphone)
- Push-to-talk functionality
- Audio mute/unmute control
- PyAudio resource management

CRITICAL THREAD SAFETY:
- All state access goes through StateService properties (thread-safe)
- PyAudio operations use asyncio.to_thread() to prevent event loop blocking
"""

import logging
import asyncio
import fractions
import numpy as np
import pyaudio
from aiortc import AudioStreamTrack
from av import AudioFrame as AVAudioFrame


class AudioService:
    """
    Service for managing audio streaming (bidirectional).
    
    Handles:
    - Audio reception from robot (playback through speakers)
    - Audio transmission to robot (microphone capture)
    - Push-to-talk functionality
    - Mute/unmute control
    """
    
    def __init__(self, state_service):
        """
        Initialize AudioService.
        
        Args:
            state_service: StateService instance for state management
        """
        self.state = state_service
        self.logger = logging.getLogger(__name__)
        
        # Audio format constants (matching robot's audio format)
        self.sample_rate = 48000
        self.channels = 2  # Stereo
        self.format = pyaudio.paInt16
        self.frames_per_buffer = 8192
    
    async def recv_audio_stream(self, frame):
        """
        Receive audio frames from the robot and play them through speakers.
        This callback is triggered when audio frames are received from the robot.
        
        CRITICAL: Uses asyncio.to_thread() to prevent blocking the event loop.
        PyAudio's write() is a synchronous blocking operation that would otherwise
        block video frame processing, causing latency and artifacts.
        
        Audio stream is always connected, but playback is controlled by state.audio_muted flag.
        This allows instant mute/unmute without reconnecting.
        
        Args:
            frame: Audio frame from WebRTC
        """
        try:
            if not self.state.audio_initialized or self.state.pyaudio_stream is None:
                return
            
            # Check if audio is muted - if so, discard the frame without playing
            if self.state.audio_muted:
                return
            
            # Convert the frame to audio data (16-bit PCM)
            audio_data = np.frombuffer(frame.to_ndarray(), dtype=np.int16)
            audio_bytes = audio_data.tobytes()
            
            # Run the blocking PyAudio write in a separate thread to avoid blocking the event loop
            # This prevents audio from interfering with video frame processing
            await asyncio.to_thread(self.state.pyaudio_stream.write, audio_bytes)
        
        except Exception as e:
            self.logger.error(f"Error playing audio frame: {e}")
    
    def create_microphone_track(self):
        """
        Factory method to create a MicrophoneAudioTrack instance.
        
        Returns:
            MicrophoneAudioTrack: New microphone track instance
        """
        return MicrophoneAudioTrack(
            sample_rate=self.sample_rate,
            channels=self.channels,
            format=self.format
        )
    
    def toggle_audio(self, enable: bool) -> dict:
        """
        Enable or disable audio streaming.
        
        Args:
            enable: True to unmute audio, False to mute
            
        Returns:
            dict: Status response with enabled/muted state
        """
        try:
            # Properties handle locking internally, no need for explicit lock
            self.state.audio_streaming_enabled = enable
            self.state.audio_muted = not enable  # Muted when disabled, unmuted when enabled
            
            if enable:
                self.logger.info("=" * 50)
                self.logger.info("AUDIO UNMUTED - Playback enabled")
                self.logger.info("=" * 50)
            else:
                self.logger.info("=" * 50)
                self.logger.info("AUDIO MUTED - Playback disabled")
                self.logger.info("=" * 50)
            
            return {
                'status': 'success',
                'enabled': self.state.audio_streaming_enabled,
                'muted': self.state.audio_muted,
                'message': 'Audio ' + ('unmuted (playing)' if enable else 'muted (silent)')
            }
        
        except Exception as e:
            self.logger.error(f"Toggle audio error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def start_push_to_talk(self) -> dict:
        """
        Start transmitting microphone audio (push-to-talk pressed).

        Returns:
            dict: Status response with transmitting state
        """
        try:
            if self.state.microphone_audio_track:
                self.state.microphone_audio_track.start_transmitting()
                return {'transmitting': True}
            else:
                self.logger.error("❌ Microphone track not initialized")
                return {'transmitting': False, 'error': 'Microphone not initialized'}

        except Exception as e:
            self.logger.error(f"Error starting microphone: {e}")
            return {'transmitting': False, 'error': str(e)}

    def stop_push_to_talk(self) -> dict:
        """
        Stop transmitting microphone audio (push-to-talk released).

        Returns:
            dict: Status response with transmitting state
        """
        try:
            if self.state.microphone_audio_track:
                self.state.microphone_audio_track.stop_transmitting()
                return {'transmitting': False}
            else:
                self.logger.error("❌ Microphone track not initialized")
                return {'transmitting': False}

        except Exception as e:
            self.logger.error(f"Error stopping microphone: {e}")
            return {'transmitting': False}


class MicrophoneAudioTrack(AudioStreamTrack):
    """
    Custom audio track that streams PC microphone audio to the robot.
    Captures audio directly from PC microphone using PyAudio (server-side).
    Based on working example from GitHub issue #483.
    Supports push-to-talk mode.
    """

    def __init__(self, sample_rate: int, channels: int, format: int):
        """
        Initialize MicrophoneAudioTrack.

        Args:
            sample_rate: Audio sample rate (e.g., 48000)
            channels: Number of audio channels (e.g., 2 for stereo)
            format: PyAudio format (e.g., pyaudio.paInt16)
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.samples_per_frame = 960  # 20ms at 48kHz
        self.audio_samples = 0  # Track timestamps
        self.is_transmitting = False  # Push-to-talk state

        # Initialize PyAudio for microphone capture (server-side)
        self.p = pyaudio.PyAudio()
        self.mic_stream = self.p.open(
            format=format,
            channels=1,  # Capture mono from microphone
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.samples_per_frame
        )

        logging.info("🎤 MicrophoneAudioTrack initialized - capturing from PC microphone (push-to-talk mode)")

    def start_transmitting(self):
        """Start transmitting microphone audio"""
        self.is_transmitting = True
        logging.info("🎤 Microphone transmission started")

    def stop_transmitting(self):
        """Stop transmitting microphone audio (send silence)"""
        self.is_transmitting = False
        logging.info("🎤 Microphone transmission stopped")

    async def recv(self):
        """
        Generate audio frames from PC microphone for WebRTC transmission.
        Sends silence when not transmitting (push-to-talk).

        CRITICAL: Uses asyncio.to_thread() to prevent blocking the event loop.
        PyAudio's read() is a synchronous blocking operation that would otherwise
        block video frame processing.

        Returns:
            AVAudioFrame: Audio frame for WebRTC transmission
        """
        try:
            # Always read from microphone to prevent buffer overflow
            # Run the blocking PyAudio read in a separate thread
            mic_data = await asyncio.to_thread(
                self.mic_stream.read,
                self.samples_per_frame,
                exception_on_overflow=False
            )

            # If not transmitting, send silence instead
            if not self.is_transmitting:
                silence = np.zeros((1, self.samples_per_frame * self.channels), dtype=np.int16)
                frame = AVAudioFrame.from_ndarray(silence, format='s16', layout='stereo')
                frame.sample_rate = self.sample_rate
                frame.pts = self.audio_samples
                frame.time_base = fractions.Fraction(1, self.sample_rate)
                self.audio_samples += frame.samples
                return frame

            # Convert bytes to numpy array (mono, int16)
            audio_array = np.frombuffer(mic_data, dtype=np.int16)

            # Convert mono to stereo by duplicating the channel
            audio_stereo = np.column_stack((audio_array, audio_array))

            # Reshape to packed format (1, samples*channels)
            total_samples = self.samples_per_frame * self.channels
            audio_packed = audio_stereo.flatten().reshape((1, total_samples))

            # Create audio frame
            frame = AVAudioFrame.from_ndarray(
                audio_packed,
                format='s16',
                layout='stereo'
            )
            frame.sample_rate = self.sample_rate

            # Set proper timestamp
            frame.pts = self.audio_samples
            frame.time_base = fractions.Fraction(1, self.sample_rate)
            self.audio_samples += frame.samples

            return frame

        except Exception as e:
            # During disconnect, asyncio.to_thread() may raise "cannot schedule new futures after shutdown"
            # This is expected behavior when the event loop is shutting down
            error_msg = str(e).lower()
            if "cannot schedule" in error_msg or "shutdown" in error_msg:
                # Expected error during disconnect - log at DEBUG level
                logging.debug(f"Microphone stream closed (expected during disconnect): {e}")
            else:
                # Unexpected error - log at ERROR level
                logging.error(f"Error reading microphone: {e}")

            # Return silence on error
            silence = np.zeros((1, self.samples_per_frame * self.channels), dtype=np.int16)
            frame = AVAudioFrame.from_ndarray(silence, format='s16', layout='stereo')
            frame.sample_rate = self.sample_rate
            frame.pts = self.audio_samples
            frame.time_base = fractions.Fraction(1, self.sample_rate)
            self.audio_samples += frame.samples
            return frame

    def stop(self):
        """Clean up microphone resources"""
        try:
            if self.mic_stream:
                self.mic_stream.stop_stream()
                self.mic_stream.close()
            if self.p:
                self.p.terminate()
            logging.info("🎤 Microphone resources cleaned up")
        except Exception as e:
            logging.error(f"Error cleaning up microphone: {e}")

