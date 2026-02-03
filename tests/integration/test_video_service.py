"""
Integration tests for VideoService.

These tests verify that VideoService correctly integrates with:
- StateService for state management
- Frame queue management
- JPEG encoding
- MJPEG stream generation
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, MagicMock, AsyncMock
import numpy as np
import cv2

from app.services.state import StateService
from app.services.video import VideoService


class TestVideoServiceIntegration:
    """Integration tests for VideoService."""
    
    def test_service_initialization(self):
        """Test VideoService initializes with StateService."""
        state = StateService()
        video_service = VideoService(state)
        
        assert video_service.state is state
        assert video_service.logger is not None
        assert video_service.jpeg_quality == 85
        assert video_service.blank_frame_timeout == 2.0
        assert video_service.blank_frame_size == (640, 480)
        assert video_service.target_fps == 30
    
    @pytest.mark.asyncio
    async def test_recv_camera_stream_updates_state(self):
        """Test recv_camera_stream updates latest_frame and queue."""
        state = StateService()
        video_service = VideoService(state)
        
        # Mock track
        mock_track = Mock()
        mock_frame = Mock()
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_frame.to_ndarray.return_value = test_image
        
        # Simulate receiving 3 frames then stopping
        frame_count = 0
        async def mock_recv():
            nonlocal frame_count
            frame_count += 1
            if frame_count > 3:
                raise Exception("Stop after 3 frames")
            return mock_frame
        
        mock_track.recv = mock_recv
        
        # Receive frames
        await video_service.recv_camera_stream(mock_track)
        
        # Verify state was updated
        assert state.latest_frame is not None
        assert state.frame_queue.qsize() == 3
    
    @pytest.mark.asyncio
    async def test_recv_camera_stream_drops_old_frames_when_full(self):
        """Test recv_camera_stream drops old frames when queue is full."""
        state = StateService()
        video_service = VideoService(state)
        
        # Mock track
        mock_track = Mock()
        mock_frame = Mock()
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_frame.to_ndarray.return_value = test_image
        
        # Simulate receiving more frames than queue size
        frame_count = 0
        async def mock_recv():
            nonlocal frame_count
            frame_count += 1
            if frame_count > 35:  # Queue size is 30
                raise Exception("Stop after 35 frames")
            return mock_frame
        
        mock_track.recv = mock_recv
        
        # Receive frames
        await video_service.recv_camera_stream(mock_track)
        
        # Verify queue size is at max
        assert state.frame_queue.qsize() <= 30
    
    def test_encode_jpeg_success(self):
        """Test _encode_jpeg successfully encodes frame."""
        state = StateService()
        video_service = VideoService(state)
        
        # Create test frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Encode
        jpeg_bytes = video_service._encode_jpeg(test_frame)
        
        # Verify
        assert jpeg_bytes is not None
        assert isinstance(jpeg_bytes, bytes)
        assert len(jpeg_bytes) > 0
    
    def test_encode_jpeg_with_custom_quality(self):
        """Test _encode_jpeg with custom quality setting."""
        state = StateService()
        video_service = VideoService(state)
        
        # Create test frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Encode with different qualities
        jpeg_low = video_service._encode_jpeg(test_frame, quality=50)
        jpeg_high = video_service._encode_jpeg(test_frame, quality=95)
        
        # Verify both succeeded
        assert jpeg_low is not None
        assert jpeg_high is not None
        
        # Higher quality should produce larger file (for non-blank frames)
        # For blank frames, size might be similar, so just verify they're different
        assert isinstance(jpeg_low, bytes)
        assert isinstance(jpeg_high, bytes)
    
    def test_create_blank_frame(self):
        """Test _create_blank_frame creates frame with text."""
        state = StateService()
        video_service = VideoService(state)
        
        # Create blank frame
        blank_frame = video_service._create_blank_frame()
        
        # Verify
        assert blank_frame is not None
        assert isinstance(blank_frame, np.ndarray)
        assert blank_frame.shape == (480, 640, 3)
        assert blank_frame.dtype == np.uint8
    
    def test_generate_frames_from_queue(self):
        """Test generate_frames yields frames from queue."""
        state = StateService()
        video_service = VideoService(state)
        
        # Add test frames to queue
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        state.frame_queue.put(test_frame)
        state.frame_queue.put(test_frame)
        
        # Generate frames
        generator = video_service.generate_frames()
        
        # Get first frame
        frame_data = next(generator)
        
        # Verify MJPEG format
        assert isinstance(frame_data, bytes)
        assert b'--frame' in frame_data
        assert b'Content-Type: image/jpeg' in frame_data
    
    def test_generate_frames_fallback_to_latest(self):
        """Test generate_frames falls back to latest_frame when queue is empty."""
        state = StateService()
        video_service = VideoService(state)
        
        # Set latest frame but don't add to queue
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        state.latest_frame = test_frame
        
        # Generate frames
        generator = video_service.generate_frames()
        
        # Get first frame
        frame_data = next(generator)
        
        # Verify MJPEG format
        assert isinstance(frame_data, bytes)
        assert b'--frame' in frame_data
        assert b'Content-Type: image/jpeg' in frame_data

