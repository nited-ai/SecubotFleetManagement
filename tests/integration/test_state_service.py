"""
Integration tests for StateService.

Tests the StateService integration with the web interface, ensuring thread-safe
state management and proper state transitions during application lifecycle.
"""

import pytest
import threading
import time
from queue import Queue
from app.services import StateService


class TestStateServiceIntegration:
    """Integration tests for StateService."""
    
    def test_state_initialization(self):
        """Test that StateService initializes with correct default values."""
        state = StateService()
        
        # Connection state
        assert state.connection is None
        assert state.event_loop is None
        assert state.loop_thread is None
        assert state.is_connected is False
        
        # Video state
        assert isinstance(state.frame_queue, Queue)
        assert state.frame_queue.maxsize == 30
        assert state.latest_frame is None
        
        # Audio state
        assert state.audio_streaming_enabled is False
        assert state.audio_initialized is False
        assert state.push_to_talk_active is False
        assert state.microphone_audio_track is None
        assert state.pyaudio_instance is None
        assert state.audio_muted is True
        assert state.pyaudio_stream is None
        assert isinstance(state.audio_output_queue, Queue)
        
        # Control state
        assert state.gamepad_enabled is False
        assert state.keyboard_mouse_enabled is False
        assert state.emergency_stop_active is False
        assert state.last_command_time == 0
        assert state.command_interval == 0.016
        assert state.current_body_height == 1
        assert state.lidar_state is False
        
        # AI mode state
        assert state.speed_level == 0
        assert state.free_bound_active is False
        assert state.free_jump_active is False
        assert state.free_avoid_active is False
        
        # Velocity tracking
        assert state.last_sent_velocities == {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0}
        assert state.zero_velocity_sent is False
    
    def test_thread_safe_frame_access(self):
        """Test thread-safe access to latest_frame."""
        state = StateService()
        import numpy as np
        
        # Simulate multiple threads writing frames
        def write_frames(thread_id):
            for i in range(10):
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                frame[:, :] = thread_id  # Mark frame with thread ID
                state.latest_frame = frame
                time.sleep(0.001)
        
        threads = [threading.Thread(target=write_frames, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have a valid frame at the end
        assert state.latest_frame is not None
        assert state.latest_frame.shape == (480, 640, 3)
    
    def test_thread_safe_gamepad_enabled(self):
        """Test thread-safe access to gamepad_enabled."""
        state = StateService()
        
        def toggle_gamepad():
            for _ in range(100):
                state.gamepad_enabled = not state.gamepad_enabled
                time.sleep(0.001)
        
        threads = [threading.Thread(target=toggle_gamepad) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have a valid boolean value
        assert isinstance(state.gamepad_enabled, bool)
    
    def test_thread_safe_audio_state(self):
        """Test thread-safe access to audio state."""
        state = StateService()
        
        def toggle_audio():
            for _ in range(50):
                state.audio_muted = not state.audio_muted
                state.audio_initialized = not state.audio_initialized
                time.sleep(0.001)
        
        threads = [threading.Thread(target=toggle_audio) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have valid boolean values
        assert isinstance(state.audio_muted, bool)
        assert isinstance(state.audio_initialized, bool)
    
    def test_gamepad_settings_management(self):
        """Test gamepad settings update and retrieval."""
        state = StateService()
        
        # Get initial settings
        settings = state.gamepad_settings
        assert settings['deadzone_left_stick'] == 0.15
        assert settings['sensitivity_linear'] == 1.0
        
        # Update settings
        state.update_gamepad_settings({
            'deadzone_left_stick': 0.2,
            'sensitivity_linear': 1.5
        })
        
        # Verify updates
        assert state.get_gamepad_setting('deadzone_left_stick') == 0.2
        assert state.get_gamepad_setting('sensitivity_linear') == 1.5
        
        # Set individual setting
        state.set_gamepad_setting('max_linear_velocity', 0.8)
        assert state.get_gamepad_setting('max_linear_velocity') == 0.8

    def test_velocity_tracking(self):
        """Test velocity tracking functionality."""
        state = StateService()

        # Initial state
        assert state.last_sent_velocities == {'vx': 0.0, 'vy': 0.0, 'vyaw': 0.0}
        assert state.zero_velocity_sent is False

        # Update velocities
        state.update_last_sent_velocities(0.5, 0.2, 0.3)
        assert state.last_sent_velocities == {'vx': 0.5, 'vy': 0.2, 'vyaw': 0.3}

        # Set zero velocity flag
        state.zero_velocity_sent = True
        assert state.zero_velocity_sent is True

    def test_reset_connection_state(self):
        """Test resetting connection state."""
        state = StateService()

        # Set some connection state
        state.connection = "mock_connection"
        state.event_loop = "mock_loop"
        state.is_connected = True

        # Reset
        state.reset_connection_state()

        # Verify reset
        assert state.connection is None
        assert state.event_loop is None
        assert state.loop_thread is None
        assert state.is_connected is False

    def test_reset_audio_state(self):
        """Test resetting audio state."""
        state = StateService()

        # Set some audio state
        state.audio_streaming_enabled = True
        state.audio_initialized = True
        state.audio_muted = False
        state.push_to_talk_active = True

        # Add items to audio queue
        state.audio_output_queue.put("audio_data_1")
        state.audio_output_queue.put("audio_data_2")

        # Reset
        state.reset_audio_state()

        # Verify reset
        assert state.audio_streaming_enabled is False
        assert state.audio_initialized is False
        assert state.audio_muted is True
        assert state.push_to_talk_active is False
        assert state.microphone_audio_track is None
        assert state.pyaudio_instance is None
        assert state.pyaudio_stream is None
        assert state.audio_output_queue.empty()

    def test_reset_control_state(self):
        """Test resetting control state."""
        state = StateService()

        # Set some control state
        state.gamepad_enabled = True
        state.keyboard_mouse_enabled = True
        state.emergency_stop_active = True
        state.last_command_time = 12345.67
        state.zero_velocity_sent = True

        # Reset
        state.reset_control_state()

        # Verify reset
        assert state.gamepad_enabled is False
        assert state.keyboard_mouse_enabled is False
        assert state.emergency_stop_active is False
        assert state.last_command_time == 0
        assert state.zero_velocity_sent is False

    def test_reset_all_state(self):
        """Test resetting all state."""
        state = StateService()
        import numpy as np

        # Set various state
        state.connection = "mock_connection"
        state.is_connected = True
        state.latest_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        state.frame_queue.put("frame_data")
        state.gamepad_enabled = True
        state.audio_muted = False
        state.speed_level = 1
        state.free_bound_active = True
        state.current_body_height = 2
        state.lidar_state = True

        # Reset all
        state.reset_all_state()

        # Verify all reset
        assert state.connection is None
        assert state.is_connected is False
        assert state.latest_frame is None
        assert state.frame_queue.empty()
        assert state.gamepad_enabled is False
        assert state.audio_muted is True
        assert state.speed_level == 0
        assert state.free_bound_active is False
        assert state.current_body_height == 1
        assert state.lidar_state is False

    def test_concurrent_state_access(self):
        """Test concurrent access to multiple state properties."""
        state = StateService()
        errors = []

        def worker(worker_id):
            try:
                for i in range(50):
                    # Read and write various state
                    state.gamepad_enabled = (i % 2 == 0)
                    _ = state.gamepad_enabled

                    state.audio_muted = (i % 3 == 0)
                    _ = state.audio_muted

                    state.emergency_stop_active = (i % 5 == 0)
                    _ = state.emergency_stop_active

                    state.update_last_sent_velocities(float(i), float(i+1), float(i+2))
                    _ = state.last_sent_velocities

                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0, f"Errors occurred: {errors}"

