"""
Thread Safety Regression Tests for StateService

These tests verify that StateService properties are thread-safe when accessed
directly (without external locking), serving as regression tests to prevent
the double-locking deadlock bug from being reintroduced.

The double-locking bug occurred when external code used explicit locks
(e.g., `with state._frame_lock:`) before accessing properties that already
use internal locking, causing deadlocks that froze the entire application.
"""

import pytest
import threading
import time
import numpy as np
from queue import Queue

from app.services.state import StateService


class TestStateServiceThreadSafety:
    """Test thread-safety of StateService properties."""
    
    def test_latest_frame_concurrent_access(self):
        """Test that latest_frame can be safely accessed from multiple threads."""
        state = StateService()
        num_threads = 10
        iterations = 100
        errors = []
        
        def writer_thread(thread_id):
            """Write frames concurrently."""
            try:
                for i in range(iterations):
                    # Create unique frame for this thread/iteration
                    frame = np.ones((480, 640, 3), dtype=np.uint8) * (thread_id + 1)
                    # ✅ Direct property access (thread-safe)
                    state.latest_frame = frame
                    time.sleep(0.001)  # Small delay to increase contention
            except Exception as e:
                errors.append(f"Writer {thread_id}: {e}")
        
        def reader_thread(thread_id):
            """Read frames concurrently."""
            try:
                for i in range(iterations):
                    # ✅ Direct property access (thread-safe)
                    frame = state.latest_frame
                    if frame is not None:
                        assert frame.shape == (480, 640, 3)
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"Reader {thread_id}: {e}")
        
        # Create threads
        threads = []
        for i in range(num_threads // 2):
            threads.append(threading.Thread(target=writer_thread, args=(i,)))
            threads.append(threading.Thread(target=reader_thread, args=(i,)))
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=10)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Thread safety errors: {errors}"
    
    def test_audio_properties_concurrent_access(self):
        """Test that audio properties can be safely accessed from multiple threads."""
        state = StateService()
        num_threads = 10
        iterations = 100
        errors = []
        
        def toggle_audio(thread_id):
            """Toggle audio properties concurrently."""
            try:
                for i in range(iterations):
                    # ✅ Direct property access (thread-safe)
                    state.audio_muted = (i % 2 == 0)
                    state.audio_streaming_enabled = (i % 2 == 1)
                    state.push_to_talk_active = (i % 3 == 0)
                    
                    # Read properties
                    muted = state.audio_muted
                    enabled = state.audio_streaming_enabled
                    ptt = state.push_to_talk_active
                    
                    assert isinstance(muted, bool)
                    assert isinstance(enabled, bool)
                    assert isinstance(ptt, bool)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Create and start threads
        threads = [threading.Thread(target=toggle_audio, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=10)
        
        # Verify no errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"
    
    def test_gamepad_properties_concurrent_access(self):
        """Test that gamepad properties can be safely accessed from multiple threads."""
        state = StateService()
        num_threads = 10
        iterations = 100
        errors = []
        
        def update_gamepad(thread_id):
            """Update gamepad properties concurrently."""
            try:
                for i in range(iterations):
                    # ✅ Direct property access (thread-safe)
                    state.gamepad_enabled = (i % 2 == 0)
                    state.gamepad_sensitivity = 0.5 + (i % 10) * 0.05
                    
                    # Read properties
                    enabled = state.gamepad_enabled
                    sensitivity = state.gamepad_sensitivity
                    
                    assert isinstance(enabled, bool)
                    assert isinstance(sensitivity, float)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Create and start threads
        threads = [threading.Thread(target=update_gamepad, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join(timeout=10)
        
        # Verify no errors
        assert len(errors) == 0, f"Thread safety errors: {errors}"
    
    def test_no_deadlock_with_direct_property_access(self):
        """
        Regression test: Verify that direct property access doesn't cause deadlocks.
        
        This test simulates the video/audio callback pattern that previously caused
        deadlocks when external code used explicit locks.
        """
        state = StateService()
        completed = Queue()
        
        def simulate_video_callback():
            """Simulate video frame callback (previously deadlocked)."""
            try:
                for i in range(50):
                    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                    # ✅ This should NOT deadlock (property handles locking)
                    state.latest_frame = frame.copy()
                    time.sleep(0.01)
                completed.put('video_done')
            except Exception as e:
                completed.put(f'video_error: {e}')
        
        def simulate_audio_callback():
            """Simulate audio toggle (previously deadlocked)."""
            try:
                for i in range(50):
                    # ✅ This should NOT deadlock (properties handle locking)
                    state.audio_muted = (i % 2 == 0)
                    state.audio_streaming_enabled = (i % 2 == 1)
                    time.sleep(0.01)
                completed.put('audio_done')
            except Exception as e:
                completed.put(f'audio_error: {e}')
        
        # Start threads
        video_thread = threading.Thread(target=simulate_video_callback)
        audio_thread = threading.Thread(target=simulate_audio_callback)
        
        video_thread.start()
        audio_thread.start()
        
        # Wait for completion with timeout
        video_thread.join(timeout=5)
        audio_thread.join(timeout=5)
        
        # Verify both threads completed
        results = []
        while not completed.empty():
            results.append(completed.get())
        
        assert 'video_done' in results, "Video thread did not complete (possible deadlock)"
        assert 'audio_done' in results, "Audio thread did not complete (possible deadlock)"
        assert all('error' not in r for r in results), f"Errors occurred: {results}"

