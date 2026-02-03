"""
VideoService - Video frame processing and MJPEG streaming.

This service encapsulates all video-related functionality:
- Video frame reception from WebRTC
- Frame queue management
- JPEG encoding
- MJPEG stream generation

Thread Safety:
- Uses StateService for thread-safe state access
- Frame reception runs in asyncio event loop
- Frame generation runs in Flask thread
"""

import asyncio
import logging
import time
from queue import Empty
from typing import Generator, Optional

import cv2
import numpy as np
from aiortc import MediaStreamTrack


class VideoService:
    """
    Service for video frame processing and MJPEG streaming.
    
    This service handles:
    - Receiving video frames from WebRTC track
    - Managing frame queue and latest frame
    - Encoding frames as JPEG
    - Generating MJPEG stream for HTTP response
    
    Example usage:
        state = StateService()
        video_service = VideoService(state)
        
        # Use as WebRTC callback
        conn.video.add_track_callback(video_service.recv_camera_stream)
        
        # Use in Flask route
        @app.route('/video_feed')
        def video_feed():
            return Response(video_service.generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
    """
    
    def __init__(self, state_service):
        """
        Initialize VideoService.
        
        Args:
            state_service: StateService instance for state management
        """
        self.state = state_service
        self.logger = logging.getLogger(__name__)
        
        # JPEG encoding quality (0-100, higher is better quality)
        self.jpeg_quality = 85
        
        # Blank frame settings
        self.blank_frame_timeout = 2.0  # Show "waiting" message after 2 seconds
        self.blank_frame_size = (640, 480)  # Width x Height
        
        # Frame generation settings
        self.frame_timeout = 0.1  # Queue get timeout in seconds
        self.target_fps = 30  # Target frames per second
        self.frame_interval = 1.0 / self.target_fps  # ~0.033 seconds
    
    async def recv_camera_stream(self, track: MediaStreamTrack):
        """
        Receive video frames from the robot and put them in the queue.
        
        This async callback is triggered when video frames are received from WebRTC.
        It runs in the asyncio event loop.
        
        Args:
            track: MediaStreamTrack from WebRTC connection
        """
        frame_count = 0
        
        while True:
            try:
                frame = await track.recv()
                img = frame.to_ndarray(format="bgr24")
                
                frame_count += 1
                
                # Update the latest frame (property handles locking internally)
                self.state.latest_frame = img.copy()
                
                # Also add to queue for buffering
                if self.state.frame_queue.full():
                    # Remove old frame if queue is full
                    try:
                        self.state.frame_queue.get_nowait()
                    except Empty:
                        pass
                
                self.state.frame_queue.put(img)
                
                # Log every 30 frames
                if frame_count % 30 == 0:
                    self.logger.info(
                        f"Received {frame_count} video frames, "
                        f"queue size: {self.state.frame_queue.qsize()}"
                    )
            
            except Exception as e:
                self.logger.error(f"Error receiving video frame: {e}")
                break
    
    def _encode_jpeg(self, frame: np.ndarray, quality: Optional[int] = None) -> Optional[bytes]:
        """
        Encode frame as JPEG.
        
        Args:
            frame: NumPy array (BGR format)
            quality: JPEG quality (0-100), uses self.jpeg_quality if None
        
        Returns:
            JPEG bytes or None if encoding failed
        """
        if quality is None:
            quality = self.jpeg_quality
        
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ret:
            return buffer.tobytes()
        return None
    
    def _create_blank_frame(self) -> np.ndarray:
        """
        Create a blank frame with "Waiting for video..." message.
        
        Returns:
            NumPy array (BGR format)
        """
        blank_frame = np.zeros((self.blank_frame_size[1], self.blank_frame_size[0], 3), dtype=np.uint8)
        cv2.putText(
            blank_frame,
            "Waiting for video...",
            (150, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2
        )
        return blank_frame

    def generate_frames(self) -> Generator[bytes, None, None]:
        """
        Generate frames for MJPEG streaming.

        This generator function yields JPEG frames in MJPEG format for HTTP streaming.
        It runs in the Flask thread (not the asyncio event loop).

        Yields:
            bytes: MJPEG frame data (multipart/x-mixed-replace format)
        """
        last_frame_time = time.time()
        blank_frame = None

        while True:
            try:
                frame_to_send = None

                # Try to get frame from queue with timeout
                try:
                    frame_to_send = self.state.frame_queue.get(timeout=self.frame_timeout)
                except Empty:
                    # If queue is empty, use the latest frame we have (property handles locking)
                    if self.state.latest_frame is not None:
                        frame_to_send = self.state.latest_frame.copy()

                if frame_to_send is not None:
                    # We have a valid frame to send
                    last_frame_time = time.time()

                    # Encode frame as JPEG
                    frame_bytes = self._encode_jpeg(frame_to_send)
                    if frame_bytes:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                else:
                    # Only show "waiting" message if we haven't received frames for a while
                    if time.time() - last_frame_time > self.blank_frame_timeout:
                        # Create blank frame only once
                        if blank_frame is None:
                            blank_frame = self._create_blank_frame()

                        frame_bytes = self._encode_jpeg(blank_frame)
                        if frame_bytes:
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    else:
                        # Just wait a bit and try again
                        time.sleep(self.frame_interval)

            except Exception as e:
                self.logger.error(f"Error generating frame: {e}")
                time.sleep(0.1)

