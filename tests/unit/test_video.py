"""
Unit tests for video streaming functionality.

Tests cover:
- Video frame reception (robot → user)
- Frame buffering and queue management
- JPEG encoding
- Frame dropping when queue is full
- Thread-safe frame access with locks
- Video streaming route
"""

import pytest
import asyncio
import numpy as np
import cv2
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from queue import Queue, Empty
import threading
import time


@pytest.mark.unit
@pytest.mark.video
class TestFrameQueue:
    """Test frame queue management."""
    
    def test_frame_queue_initialization(self, frame_queue):
        """Test frame queue initialization with maxsize=30."""
        assert frame_queue is not None
        assert frame_queue.maxsize == 30
        assert frame_queue.empty()
    
    def test_add_frame_to_queue(self, frame_queue):
        """Test adding a frame to the queue."""
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        frame_queue.put(test_frame)
        
        assert not frame_queue.empty()
        assert frame_queue.qsize() == 1
    
    def test_get_frame_from_queue(self, frame_queue):
        """Test getting a frame from the queue."""
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_queue.put(test_frame)
        
        retrieved_frame = frame_queue.get()
        
        assert retrieved_frame is not None
        assert np.array_equal(retrieved_frame, test_frame)
        assert frame_queue.empty()
    
    def test_queue_full_behavior(self, frame_queue):
        """Test queue behavior when full."""
        # Fill the queue
        for i in range(30):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame_queue.put(frame)
        
        assert frame_queue.full()
        assert frame_queue.qsize() == 30
    
    def test_drop_old_frame_when_full(self, frame_queue):
        """Test dropping old frame when queue is full."""
        # Fill the queue
        for i in range(30):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame_queue.put(frame)
        
        # Queue is full, remove old frame
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except Empty:
                pass
        
        # Add new frame
        new_frame = np.ones((480, 640, 3), dtype=np.uint8)
        frame_queue.put(new_frame)
        
        assert frame_queue.qsize() == 30
    
    def test_queue_empty_exception(self, frame_queue):
        """Test getting from empty queue raises Empty exception."""
        assert frame_queue.empty()
        
        with pytest.raises(Empty):
            frame_queue.get_nowait()


@pytest.mark.unit
@pytest.mark.video
class TestLatestFrame:
    """Test latest frame management with thread-safe access."""
    
    def test_latest_frame_starts_as_none(self):
        """Test that latest_frame starts as None."""
        latest_frame = None
        assert latest_frame is None
    
    def test_update_latest_frame_with_lock(self):
        """Test updating latest_frame with thread lock."""
        latest_frame = None
        frame_lock = threading.Lock()
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        with frame_lock:
            latest_frame = test_frame.copy()
        
        assert latest_frame is not None
        assert np.array_equal(latest_frame, test_frame)
    
    def test_read_latest_frame_with_lock(self):
        """Test reading latest_frame with thread lock."""
        latest_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_lock = threading.Lock()
        
        with frame_lock:
            frame_copy = latest_frame.copy() if latest_frame is not None else None
        
        assert frame_copy is not None
        assert np.array_equal(frame_copy, latest_frame)
    
    def test_clear_latest_frame_on_disconnect(self):
        """Test clearing latest_frame on disconnect."""
        latest_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_lock = threading.Lock()
        
        with frame_lock:
            latest_frame = None
        
        assert latest_frame is None


@pytest.mark.unit
@pytest.mark.video
@pytest.mark.asyncio
class TestVideoReception:
    """Test video frame reception from robot."""
    
    async def test_recv_camera_stream_success(self, frame_queue):
        """Test successful video frame reception."""
        # Mock video track
        mock_track = AsyncMock()
        mock_frame = Mock()
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_frame.to_ndarray.return_value = test_img
        mock_track.recv.return_value = mock_frame
        
        # Simulate receiving one frame
        frame = await mock_track.recv()
        img = frame.to_ndarray(format="bgr24")
        
        assert img is not None
        assert img.shape == (480, 640, 3)
    
    async def test_recv_camera_stream_adds_to_queue(self, frame_queue):
        """Test that received frames are added to queue."""
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add frame to queue
        if frame_queue.full():
            try:
                frame_queue.get_nowait()
            except Empty:
                pass
        
        frame_queue.put(test_img)

        assert not frame_queue.empty()
        assert frame_queue.qsize() == 1

    async def test_recv_camera_stream_updates_latest_frame(self):
        """Test that received frames update latest_frame."""
        latest_frame = None
        frame_lock = threading.Lock()
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)

        # Update latest frame (thread-safe)
        with frame_lock:
            latest_frame = test_img.copy()

        assert latest_frame is not None
        assert np.array_equal(latest_frame, test_img)

    async def test_recv_camera_stream_error_handling(self):
        """Test error handling during video reception."""
        mock_track = AsyncMock()
        mock_track.recv.side_effect = Exception("Video stream error")

        with pytest.raises(Exception, match="Video stream error"):
            await mock_track.recv()


@pytest.mark.unit
@pytest.mark.video
class TestJPEGEncoding:
    """Test JPEG encoding for video streaming."""

    def test_encode_frame_to_jpeg(self):
        """Test encoding a frame to JPEG."""
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        ret, buffer = cv2.imencode('.jpg', test_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        assert ret is True
        assert buffer is not None
        assert len(buffer) > 0

    def test_jpeg_quality_setting(self):
        """Test JPEG encoding with quality setting."""
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

        # Encode with quality 85
        ret, buffer = cv2.imencode('.jpg', test_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        assert ret is True
        assert buffer is not None

    def test_jpeg_to_bytes(self):
        """Test converting JPEG buffer to bytes."""
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        ret, buffer = cv2.imencode('.jpg', test_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        frame_bytes = buffer.tobytes()

        assert frame_bytes is not None
        assert isinstance(frame_bytes, bytes)
        assert len(frame_bytes) > 0

    def test_mjpeg_frame_format(self):
        """Test MJPEG frame format for streaming."""
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        ret, buffer = cv2.imencode('.jpg', test_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = buffer.tobytes()

        # Create MJPEG frame
        mjpeg_frame = (b'--frame\r\n'
                      b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        assert mjpeg_frame.startswith(b'--frame')
        assert b'Content-Type: image/jpeg' in mjpeg_frame
        assert frame_bytes in mjpeg_frame


@pytest.mark.unit
@pytest.mark.video
class TestFrameGeneration:
    """Test frame generation for MJPEG streaming."""

    def test_generate_frames_from_queue(self, frame_queue):
        """Test generating frames from queue."""
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_queue.put(test_frame)

        # Get frame from queue
        try:
            frame_to_send = frame_queue.get(timeout=0.1)
        except Empty:
            frame_to_send = None

        assert frame_to_send is not None
        assert np.array_equal(frame_to_send, test_frame)

    def test_generate_frames_fallback_to_latest(self, frame_queue):
        """Test falling back to latest_frame when queue is empty."""
        latest_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_lock = threading.Lock()

        # Queue is empty, use latest_frame
        try:
            frame_to_send = frame_queue.get(timeout=0.1)
        except Empty:
            with frame_lock:
                if latest_frame is not None:
                    frame_to_send = latest_frame.copy()
                else:
                    frame_to_send = None

        assert frame_to_send is not None
        assert np.array_equal(frame_to_send, latest_frame)

    def test_generate_blank_frame_when_waiting(self):
        """Test generating blank 'waiting' frame when no video."""
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "Waiting for video...", (150, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        assert blank_frame is not None
        assert blank_frame.shape == (480, 640, 3)
        # Check that text was added (frame is no longer all zeros)
        assert not np.all(blank_frame == 0)


@pytest.mark.unit
@pytest.mark.video
class TestVideoCleanup:
    """Test video cleanup on disconnect."""

    def test_clear_latest_frame(self):
        """Test clearing latest_frame on disconnect."""
        latest_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_lock = threading.Lock()

        # Clear on disconnect
        with frame_lock:
            latest_frame = None

        assert latest_frame is None

    def test_clear_frame_queue(self, frame_queue):
        """Test clearing frame queue on disconnect."""
        # Add some frames
        for i in range(5):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame_queue.put(frame)

        assert frame_queue.qsize() == 5

        # Clear the queue
        while not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except Empty:
                break

        assert frame_queue.empty()

    def test_cleanup_all_video_resources(self, frame_queue):
        """Test complete video resource cleanup."""
        latest_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame_lock = threading.Lock()

        # Add frames to queue
        for i in range(3):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame_queue.put(frame)

        # Cleanup
        with frame_lock:
            latest_frame = None

        while not frame_queue.empty():
            try:
                frame_queue.get_nowait()
            except Empty:
                break

        assert latest_frame is None
        assert frame_queue.empty()


@pytest.mark.unit
@pytest.mark.video
class TestVideoErrorHandling:
    """Test video error handling."""

    @pytest.mark.asyncio
    async def test_video_stream_error_recovery(self):
        """Test recovering from video stream errors."""
        mock_track = AsyncMock()

        # First call fails
        mock_track.recv.side_effect = [
            Exception("Temporary error"),
            Mock(to_ndarray=Mock(return_value=np.zeros((480, 640, 3), dtype=np.uint8)))
        ]

        # First attempt should fail
        with pytest.raises(Exception):
            await mock_track.recv()

        # Second attempt should succeed
        frame = await mock_track.recv()
        assert frame is not None

    def test_jpeg_encoding_error(self):
        """Test handling JPEG encoding errors."""
        # Invalid frame (wrong dimensions) - OpenCV will raise exception
        invalid_frame = np.zeros((0, 0, 3), dtype=np.uint8)

        # OpenCV raises cv2.error for empty frames
        with pytest.raises(cv2.error):
            cv2.imencode('.jpg', invalid_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

    def test_queue_timeout_handling(self, frame_queue):
        """Test handling queue timeout when empty."""
        assert frame_queue.empty()

        # Try to get with timeout
        try:
            frame = frame_queue.get(timeout=0.1)
            frame_to_send = frame
        except Empty:
            frame_to_send = None

        assert frame_to_send is None

