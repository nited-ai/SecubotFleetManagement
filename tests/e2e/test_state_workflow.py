"""
End-to-end tests for StateService workflow.

Tests complete state management workflows that simulate real application usage,
including connection lifecycle, video/audio streaming, and control commands.
"""

import pytest
import asyncio
import threading
import time
import numpy as np
from queue import Queue
from app.services import StateService


class TestStateWorkflow:
    """End-to-end workflow tests for StateService."""
    
    def test_connection_lifecycle_workflow(self):
        """Test complete connection lifecycle with state management."""
        state = StateService()
        
        # Initial state - disconnected
        assert state.is_connected is False
        assert state.connection is None
        
        # Simulate connection
        state.connection = "mock_connection"
        state.event_loop = asyncio.new_event_loop()
        state.loop_thread = threading.current_thread()
        state.is_connected = True
        
        # Verify connected state
        assert state.is_connected is True
        assert state.connection == "mock_connection"
        assert state.event_loop is not None
        
        # Simulate disconnection
        state.reset_connection_state()
        
        # Verify disconnected state
        assert state.is_connected is False
        assert state.connection is None
        assert state.event_loop is None
    
    def test_video_streaming_workflow(self):
        """Test video streaming workflow with frame buffering."""
        state = StateService()
        
        # Simulate receiving video frames
        for i in range(50):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:, :] = i  # Mark frame with sequence number
            
            # Update latest frame
            state.latest_frame = frame
            
            # Add to queue (with overflow handling)
            if state.frame_queue.full():
                try:
                    state.frame_queue.get_nowait()
                except:
                    pass
            state.frame_queue.put(frame)
        
        # Verify state
        assert state.latest_frame is not None
        assert state.latest_frame.shape == (480, 640, 3)
        assert not state.frame_queue.empty()
        
        # Simulate frame consumption
        frames_consumed = 0
        while not state.frame_queue.empty():
            frame = state.frame_queue.get()
            frames_consumed += 1
        
        assert frames_consumed > 0
    
    def test_audio_streaming_workflow(self):
        """Test audio streaming workflow with mute/unmute."""
        state = StateService()
        
        # Initial state - audio muted
        assert state.audio_muted is True
        assert state.audio_initialized is False
        
        # Simulate audio initialization
        state.audio_initialized = True
        state.pyaudio_instance = "mock_pyaudio"
        state.pyaudio_stream = "mock_stream"
        
        # Unmute audio
        state.audio_muted = False
        assert state.audio_muted is False
        
        # Simulate audio playback (add frames to queue)
        for i in range(10):
            state.audio_output_queue.put(f"audio_frame_{i}")
        
        assert state.audio_output_queue.qsize() == 10
        
        # Mute audio
        state.audio_muted = True
        assert state.audio_muted is True
        
        # Cleanup
        state.reset_audio_state()
        assert state.audio_initialized is False
        assert state.audio_output_queue.empty()
    
    def test_push_to_talk_workflow(self):
        """Test push-to-talk workflow."""
        state = StateService()
        
        # Initial state - not transmitting
        assert state.push_to_talk_active is False
        assert state.microphone_audio_track is None
        
        # Simulate push-to-talk activation
        state.microphone_audio_track = "mock_mic_track"
        state.push_to_talk_active = True
        
        assert state.push_to_talk_active is True
        assert state.microphone_audio_track is not None
        
        # Simulate push-to-talk deactivation
        state.push_to_talk_active = False
        
        assert state.push_to_talk_active is False
    
    def test_gamepad_control_workflow(self):
        """Test gamepad control workflow with settings."""
        state = StateService()
        
        # Initial state - gamepad disabled
        assert state.gamepad_enabled is False
        
        # Enable gamepad
        state.gamepad_enabled = True
        assert state.gamepad_enabled is True
        
        # Update settings
        state.update_gamepad_settings({
            'sensitivity_linear': 1.5,
            'max_linear_velocity': 0.8
        })
        
        # Simulate sending commands
        for i in range(10):
            state.last_command_time = time.time()
            state.update_last_sent_velocities(0.5, 0.2, 0.1)
            time.sleep(0.016)  # 60Hz
        
        # Verify state
        assert state.last_command_time > 0
        assert state.last_sent_velocities['vx'] == 0.5
        
        # Stop movement (zero velocity)
        state.update_last_sent_velocities(0.0, 0.0, 0.0)
        state.zero_velocity_sent = True
        
        assert state.zero_velocity_sent is True
        assert state.last_sent_velocities == {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0}
        
        # Disable gamepad
        state.gamepad_enabled = False
        assert state.gamepad_enabled is False
    
    def test_emergency_stop_workflow(self):
        """Test emergency stop workflow."""
        state = StateService()
        
        # Enable control
        state.gamepad_enabled = True
        state.update_last_sent_velocities(0.5, 0.3, 0.2)
        
        # Trigger emergency stop
        state.emergency_stop_active = True
        state.update_last_sent_velocities(0.0, 0.0, 0.0)
        state.zero_velocity_sent = True
        
        # Verify emergency stop state
        assert state.emergency_stop_active is True
        assert state.last_sent_velocities == {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0}
        
        # Release emergency stop
        state.emergency_stop_active = False
        state.zero_velocity_sent = False
        
        assert state.emergency_stop_active is False

